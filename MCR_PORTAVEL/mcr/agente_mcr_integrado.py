"""MCR Agent integrado ao SSE Server.
Usa Markov + Cache + LLM fallback para processar comandos via Dashboard.
"""
import sys, os, time, json, glob as _glob_mod, subprocess, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

OLLAMA_URL = "http://localhost:11434/api/generate"
try:
    import requests as _req
except ImportError:
    import urllib.request as _urllib
    class _Req:
        @staticmethod
        def post(url, json, timeout):
            b = json.dumps(json).encode()
            r = _urllib.Request(url, data=b, headers={"Content-Type": "application/json"})
            with _urllib.urlopen(r, timeout=timeout) as f:
                return json.loads(f.read())
    _req = _Req()

from mcr.engine import MCR as MarkovEngine
from mcr.cache_hierarquico import CacheHierarquico

# ─── Ferramentas ─────────────────────────────────────────────

def _glob(padrao):
    return "\n".join(_glob_mod.glob(padrao, recursive=True)) or "(vazio)"

def _grep(padrao, path="."):
    try:
        cmd = f'findstr /s /i "{padrao}" *.py' if sys.platform == "win32" else f'grep -r "{padrao}" {path}'
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15, shell=True)
        return r.stdout[:3000] or "(sem resultados)"
    except:
        return "(grep falhou)"

def _read(caminho):
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            return f.read()[:3000]
    except:
        return f"(erro ao ler {caminho})"

def _bash(comando):
    try:
        r = subprocess.run(comando, capture_output=True, text=True, timeout=30, shell=True)
        return (r.stdout + r.stderr)[:3000] or "(ok)"
    except Exception as e:
        return f"(erro: {e})"

def _ls(path="."):
    return _bash(f"dir {path} /b" if sys.platform == "win32" else f"ls {path}")

FERRAMENTAS = {
    "glob": _glob, "grep": _grep, "read": _read,
    "bash": _bash, "ls": _ls,
}

TOOLS_PROMPT = (
    "Ferramentas: glob <padrao>, grep <texto>, read <caminho>, bash <comando>, ls <dir>\n"
    "Responda APENAS com: FERRAMENTA <argumentos>\n"
)


def _llm_tool(pergunta):
    prompt = f"{TOOLS_PROMPT}\nUsuario: {pergunta}\nResposta:"
    try:
        r = _req.post(OLLAMA_URL, json={
            "model": "phi4-mini:latest",
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 100, "temperature": 0.1, "num_gpu": 999},
        }, timeout=30)
        return r.json().get("response", "").strip()
    except:
        return ""


def _extrair(texto):
    for nome in FERRAMENTAS:
        m = re.search(rf'\b{nome}\s+(.*)', texto, re.IGNORECASE)
        if m:
            return nome, m.group(1).strip()
    return None, texto


def _executar(ferramenta, args):
    if ferramenta in FERRAMENTAS:
        try:
            return FERRAMENTAS[ferramenta](args)
        except Exception as e:
            return f"(erro: {e})"
    return f"(ferramenta '{ferramenta}' desconhecida)"


# ─── Agente singleton ────────────────────────────────────────

_agente = None


def _get_agente():
    global _agente
    if _agente is None:
        _agente = {
            "markov": MarkovEngine("agente_mcr"),
            "cache": CacheHierarquico(),
            "stats": {"total": 0, "cache": 0, "markov": 0, "llm": 0},
        }
        try:
            _agente["markov"].load()
        except:
            pass
    return _agente


def processar_chat(entrada):
    """Processa entrada do chat via MCR Agent. Retorna dict com resposta + metadados."""
    import traceback
    try:
        ag = _get_agente()
        mk = ag["markov"]
        cache = ag["cache"]
        stats = ag["stats"]
        stats["total"] += 1
        t0 = time.time()

        # 1. Cache
        resp = cache.buscar(entrada)
        if resp:
            stats["cache"] += 1
            return {
                "resposta": resp,
                "fonte": "cache",
                "tempo": round(time.time() - t0, 3),
                "stats": {k: v for k, v in stats.items()},
            }

        # 2. Markov
        estado = entrada.lower().strip()
        acao, conf = mk.predizer(estado)
        if acao and conf > 0.3:
            stats["markov"] += 1
            return {
                "resposta": acao,
                "fonte": "markov",
                "confianca": round(conf, 2),
                "tempo": round(time.time() - t0, 3),
                "stats": {k: v for k, v in stats.items()},
            }

        # 3. LLM fallback
        stats["llm"] += 1
        resp_llm = _llm_tool(entrada)
        ferramenta, args = _extrair(resp_llm)
        if ferramenta:
            resultado = _executar(ferramenta, args) or f"(falha)"
        else:
            resultado = resp_llm or "(sem resposta)"

        if resultado and not resultado.startswith("(erro"):
            mk.aprender(estado, resultado)
            try:
                mk.save()
            except:
                pass
            cache.aprender(entrada, resultado)

        return {
            "resposta": resultado,
            "fonte": "llm",
            "ferramenta": ferramenta,
            "tempo": round(time.time() - t0, 3),
            "stats": {k: v for k, v in stats.items()},
        }
    except Exception as e:
        traceback.print_exc()
        return {"resposta": f"(erro: {e})", "fonte": "erro", "tempo": 0}


def get_stats():
    """Retorna estatisticas do agente."""
    ag = _get_agente()
    mk = ag["markov"]
    stats = ag["stats"]
    total = stats["total"] or 1
    return {
        "total": stats["total"],
        "cache_hits": stats["cache"],
        "markov_hits": stats["markov"],
        "llm_calls": stats["llm"],
        "taxa_acerto_mcr": f"{(stats['cache'] + stats['markov']) / total * 100:.0f}%",
        "estados_markov": len(mk.transicoes),
        "entropia_media": round(mk.entropia_media(), 2),
    }
