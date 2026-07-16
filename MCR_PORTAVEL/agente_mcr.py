#!/usr/bin/env python3
"""MCR Agent — O MCR como cerebro principal, LLM como executor de ferramentas.

Arquitetura:
    Usuario → MCR (Markov + Cache) → se souber, responde direto
                                   → se nao souber, chama phi4-mini pra executar ferramenta
                                   → aprende com o resultado
                                   → proxima vez responde sozinho
"""
import sys, os, json, time, glob as _glob_mod, subprocess, re
try:
    import readline
except ImportError:
    pass
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

OLLAMA_URL = "http://localhost:11434/api/generate"
try:
    import requests as _req
except ImportError:
    import urllib.request as _urllib
    class _Req:
        @staticmethod
        def post(url, json, timeout):
            b = __import__('json').dumps(json).encode()
            r = _urllib.Request(url, data=b, headers={"Content-Type": "application/json"})
            with _urllib.urlopen(r, timeout=timeout) as f:
                return __import__('json').loads(f.read())
    _req = _Req()

from mcr.engine import MCR as MarkovEngine
from mcr.cache_hierarquico import CacheHierarquico

# ─── Ferramentas disponiveis ─────────────────────────────────

def tool_glob(padrao):
    """Lista arquivos por padrao."""
    return "\n".join(_glob_mod.glob(padrao, recursive=True)) or "(nenhum arquivo encontrado)"

def tool_grep(padrao, path="."):
    """Busca texto em arquivos."""
    try:
        r = subprocess.run(["rg" if sys.platform != "win32" else "findstr", padrao],
                         capture_output=True, text=True, timeout=10, shell=True)
        return r.stdout[:2000] or "(sem resultados)"
    except:
        return "(grep falhou)"

def tool_read(caminho):
    """Le conteudo de arquivo."""
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            return f.read()[:2000]
    except:
        return f"(nao foi possivel ler {caminho})"

def tool_bash(comando):
    """Executa comando shell."""
    try:
        r = subprocess.run(comando, capture_output=True, text=True, timeout=30, shell=True)
        saida = r.stdout + r.stderr
        return saida[:2000] or "(comando executado sem saida)"
    except subprocess.TimeoutExpired:
        return "(comando excedeu timeout)"
    except Exception as e:
        return f"(erro: {e})"

FERRAMENTAS = {
    "glob": tool_glob,
    "grep": tool_grep,
    "read": tool_read,
    "bash": tool_bash,
    "ls": lambda p=".": tool_bash(f"ls {p}" if sys.platform != "win32" else f"dir {p} /b"),
}

TOOLS_DESC = """
Ferramentas:
- glob <padrao> — lista arquivos (ex: glob **/*.py)
- grep <texto> — busca texto em arquivos
- read <caminho> — le conteudo de arquivo
- bash <comando> — executa comando shell
- ls <dir> — lista diretorio

Responda APENAS com: FERRAMENTA <argumentos>
"""


def llm_tool_exec(pergunta):
    """Chama phi4-mini para decidir qual ferramenta usar."""
    prompt = (
        f"{TOOLS_DESC}\n"
        f"Com base na solicitacao do usuario, escolha UMA ferramenta e responda "
        f"EXATAMENTE no formato: FERRAMENTA <argumentos>\n"
        f"Nao explique nada, apenas o comando.\n\n"
        f"Usuario: {pergunta}\n"
        f"Resposta:"
    )
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


def extrair_comando(texto):
    """Extrai ferramenta e argumentos da resposta do LLM."""
    for nome in FERRAMENTAS:
        padrao = re.compile(rf'\b{nome}\s+(.*)', re.IGNORECASE)
        m = padrao.search(texto)
        if m:
            return nome, m.group(1).strip()
    return None, texto


def executar(ferramenta, args):
    """Executa a ferramenta escolhida."""
    if ferramenta in FERRAMENTAS:
        try:
            return FERRAMENTAS[ferramenta](args)
        except Exception as e:
            return f"(erro ao executar {ferramenta}: {e})"
    return f"(ferramenta '{ferramenta}' desconhecida)"


class MCR_Agent:
    def __init__(self):
        print("Inicializando MCR Agent...")
        self.markov = MarkovEngine("agente_mcr")
        try:
            self.markov.load()
        except:
            pass
        self.cache = CacheHierarquico()
        self.total_perguntas = 0
        self.hits_markov = 0
        self.hits_cache = 0
        self.chamadas_llm = 0
        print("MCR Agent pronto!")
        print(f"Comandos disponiveis: {', '.join(FERRAMENTAS.keys())}")
        print("Digite 'sair' para encerrar.\n")

    def processar(self, entrada):
        self.total_perguntas += 1
        t0 = time.time()

        # 1. Tenta Cache (L1 + L3 Jaccard)
        resposta_cache = self.cache.buscar(entrada)
        if resposta_cache:
            self.hits_cache += 1
            print(f"  [Cache L1/L3] {time.time()-t0:.3f}s")
            return resposta_cache

        # 2. Tenta Markov
        estado = entrada.lower().strip()
        acao, confianca = self.markov.predizer(estado)
        if acao and confianca > 0.3:
            self.hits_markov += 1
            print(f"  [Markov] {confianca:.0%} confianca | {time.time()-t0:.3f}s")
            return acao

        # 3. Fallback: LLM decide ferramenta
        self.chamadas_llm += 1
        print(f"  [LLM] Markov nao sabe (conf={confianca:.2f}). Chamando phi4-mini...")
        resposta_llm = llm_tool_exec(entrada)
        
        ferramenta, args = extrair_comando(resposta_llm)
        if ferramenta:
            print(f"  [LLM] Decidiu: {ferramenta} {args}")
            resultado = executar(ferramenta, args)
            
            # Aprende: estado -> resultado
            if resultado and not resultado.startswith("(erro"):
                self.markov.aprender(estado, resultado)
                self.markov.save()
                self.cache.aprender(entrada, resultado)
            
            return resultado
        else:
            # LLM nao entendeu, tenta bash direto
            resultado = tool_bash(entrada)
            self.markov.aprender(estado, resultado)
            return resultado

    def estatisticas(self):
        print("\n--- MCR Agent: Estatisticas ---")
        print(f"Total de perguntas: {self.total_perguntas}")
        print(f"Cache hits (L1+L3): {self.hits_cache}")
        print(f"Markov hits: {self.hits_markov}")
        print(f"Chamadas LLM: {self.chamadas_llm}")
        if self.total_perguntas:
            pct = (self.hits_cache + self.hits_markov) / self.total_perguntas * 100
            print(f"Taxa de acerto MCR: {pct:.0f}%")
        print(f"Estados no Markov: {len(self.markov.transicoes)}")
        entropia = self.markov.entropia_media()
        print(f"Entropia media: {entropia:.2f} (0 = certeza maxima)")
        print("-----------------------------\n")


def main():
    agent = MCR_Agent()

    while True:
        try:
            entrada = input("mcr> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando.")
            break

        if not entrada:
            continue
        if entrada.lower() in ("sair", "exit", "quit"):
            break
        if entrada.lower() == "stats":
            agent.estatisticas()
            continue

        t0 = time.time()
        resposta = agent.processar(entrada)
        tempo = time.time() - t0

        print(f"\n{resposta}")
        print(f"\n  [{tempo:.1f}s]")

    agent.estatisticas()


if __name__ == "__main__":
    main()
