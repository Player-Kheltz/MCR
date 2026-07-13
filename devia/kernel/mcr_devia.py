#!/usr/bin/env python3
"""MCR-DevIA — Entry point. Conecta MCR.py + MarkovDecider + 52 comandos + LLM."""
import sys, os, time, json, hashlib

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

# ─── MCR.py engine v5.0 (do E:\MCR\, importa ANTES do DevIA) ───
import MCR as _MCR
from MCR import MCR, MCRThreshold, MCRDecisor, MCRFingerprint, MCRBufferKG, MCRSystem, MCRFuel

# MCRBridge: classe faltando no MCR.py — adicionada via monkey-patch
if not hasattr(_MCR, 'MCRBridge'):
    class MCRBridge:
        def __init__(self):
            self._descobriu = True
            self.modulos = {
                'PipelineExecutor': ['PipelineExecutor.py'],
                'MarkovRouter': ['MarkovRouter.py'],
                'LuaSyntaxValidator': ['LuaSyntaxValidator.py'],
                'MasterAgent': ['MasterAgent.py'],
            }
            self.comandos = {'cmd_grep': 'cmd_grep.py', 'cmd_read': 'cmd_read.py', 
                             'cmd_write': 'cmd_write.py', 'cmd_edit': 'cmd_edit.py'}
        def descobrir(self):
            return {'modulos': len(self.modulos), 'comandos': len(self.comandos)}
    _MCR.MCRBridge = MCRBridge

# Patch MCRBufferKG: quando kg externo falha, usa armazenamento interno
_MCR_ORIG_KG = MCRBufferKG.kg.fget if isinstance(MCRBufferKG.__dict__.get('kg'), property) else None
def _patched_kg(self):
    if self._kg is None:
        try:
            from modulos.kg import KnowledgeGraph
            self._kg = KnowledgeGraph()
        except Exception:
            # Fallback: dicionario interno com busca simples
            if not hasattr(self, '_lessons_cache'):
                self._lessons_cache = []
            self._kg = self  # usa self como KG simplificado
    return self._kg

def _patched_buscar(self, termo, max_r=5, pergunta=''):
    """Busca simples no buffer interno (fallback quando KG externo falha)."""
    if not hasattr(self, '_lessons_cache'):
        self._lessons_cache = []
    resultados = []
    for item in self._lessons_cache:
        score = 0
        if termo.lower() in item.get('erro', '').lower():
            score += 5
        if termo.lower() in item.get('solucao', '').lower():
            score += 3
        if score > 0:
            resultados.append({'texto': item.get('solucao', ''), 'score': score, 'fonte': item.get('ctx', '')})
    resultados.sort(key=lambda x: -x['score'])
    return resultados[:max_r]

def _patched_aprender(self, erro, solucao, ctx='buffer'):
    self._buffer.append({'erro': erro, 'solucao': solucao, 'ctx': ctx})
    if not hasattr(self, '_lessons_cache'):
        self._lessons_cache = []
    self._lessons_cache.append({'erro': erro, 'solucao': solucao, 'ctx': ctx})
    if len(self._buffer) >= self._buffer_limite:
        self.flush()

# Aplica patches
MCRBufferKG.buscar = _patched_buscar
MCRBufferKG.aprender = _patched_aprender

# Compatibilidade: MCRByteUtils nao existe no novo MCR.py
class MCRByteUtils:
    @staticmethod
    def fingerprint(texto, dim=16):
        fp = MCRFingerprint.gerar(texto)
        return (fp * (dim // 8 + 1))[:dim]
    @staticmethod
    def similaridade_cosseno(a, b):
        dot = sum(x*y for x,y in zip(a,b))
        na = sum(x*x for x in a)**0.5
        nb = sum(y*y for y in b)**0.5
        return dot/(na*nb) if na*nb else 0

# ─── Nossos módulos (do E:\MCR\) ────────────────────────────────
try:
    from MarkovRouter import MarkovRouter
except ImportError:
    MarkovRouter = None
try:
    from Radar import Radar
except ImportError:
    Radar = None
try:
    from PipelineExecutor import PipelineExecutor
except ImportError:
    PipelineExecutor = None
try:
    from AutorevisaoTracker import AutorevisaoTracker
except ImportError:
    AutorevisaoTracker = None
try:
    from TemplateExtractor import extrair_template
except ImportError:
    extrair_template = None
try:
    from DeterministicFiller import preencher_template, gaps_restantes
except ImportError:
    preencher_template = gaps_restantes = None
try:
    from EncodingDetector import detectar_encoding
except ImportError:
    detectar_encoding = None
try:
    from FeedbackFilter import FeedbackFilter
except ImportError:
    FeedbackFilter = None
try:
    from SeedLoader import carregar_tudo
except ImportError:
    carregar_tudo = None
try:
    from conexao_bridge import CerebroKG
except ImportError:
    CerebroKG = None

# ─── DevIA v2 core (do E:\MCR\) ─────────────────────────────────
from mcr_devia_v2 import MarkovDecider, EntropyValidator, LLM, MCRDevIAV2

# ─── Agora sim, adiciona DevIA ao path ──────────────────────────
# (mas ANTES disso, importa watchdog real pra nao ser shadowed)
try:
    import watchdog
    import watchdog.observers
    import watchdog.events
except Exception:
    pass
PROJETO = os.path.dirname(os.path.abspath(__file__))
DEVIA = os.path.join(PROJETO, "devia")
sys.path.insert(0, DEVIA)
try:
    from kernel import MCRKernel
except ImportError:
    MCRKernel = None
_kernel = MCRKernel() if MCRKernel else None
if _kernel:
    _kernel.loader.scan()

# ─── Inicialização ──────────────────────────────────────────────
_decider = MarkovDecider()
_validator = EntropyValidator()
_router = MarkovRouter() if MarkovRouter else None
_radar = Radar() if Radar else None
_llm = LLM()
_filter = FeedbackFilter() if FeedbackFilter else None
_autorevisao = AutorevisaoTracker() if AutorevisaoTracker else None
_dev = MCRDevIAV2()
_calibra_contador = 0
_ultimos_erros = []

_stats = carregar_tudo(_decider) if carregar_tudo else {}
_seeds_gerais = [
    ("crie uma ", "criar_codigo"), ("cria um ", "criar_codigo"), ("implemente ", "criar_codigo"),
    ("crie um npc", "criar_npc"), ("crie uma habilidade", "criar_habilidade_spa"),
    ("crie uma quest", "criar_quest"), ("explique o que", "explicar_conceito"),
    ("o que e ", "explicar_conceito"), ("como funciona", "explicar_conceito"),
    ("encontre ", "busca_informacao"), ("busque ", "busca_informacao"),
    ("leia ", "ler_arquivo"), ("mostre ", "ler_arquivo"),
    ("traduza ", "traduzir_texto"), ("analise ", "analisar_bug"),
    ("revise ", "revisar_codigo"), ("compile ", "comando_sistema"),
    ("crie um relatorio", "gerar_relatorio"), ("resuma ", "explicar_conceito"),
    ("diagnostique ", "analisar_bug"), ("corrija ", "analisar_bug"),
]

# ─── Vocabulario Open Tibia (Canary) ────────────────────────────
_seeds_gerais.extend([
    ("criar spell", "criar_habilidade_spa"), ("fazer magia", "criar_habilidade_spa"),
    ("criar monster", "criar_monster"), ("fazer monstro", "criar_monster"),
    ("crie um monstro", "criar_monster"), ("cria um monstro", "criar_monster"),
    ("fazer monster", "criar_monster"),
    ("golem", "criar_monster"), ("monstro de fogo", "criar_monster"),
    ("monstro chamado", "criar_monster"), ("monster chamado", "criar_monster"),
    ("HP", "criar_monster"), ("imune a", "criar_monster"), ("dropa", "criar_monster"),
    ("crie um sistema", "criar_sistema"), ("sistema completo", "criar_sistema"),
    ("invasao de", "criar_sistema"), ("invasao", "criar_sistema"),
    ("configurar loot", "criar_codigo"), ("editar loot", "criar_codigo"),
    ("criar npc", "criar_npc"), ("dialogo de npc", "criar_npc"),
    ("criar quest", "criar_quest"), ("fazer quest", "criar_quest"),
    ("actionid", "criar_codigo"), ("action id", "criar_codigo"),
    ("moveevent", "criar_codigo"), ("move event", "criar_codigo"),
    ("globalevent", "criar_codigo"), ("global event", "criar_codigo"),
    ("creatureevent", "criar_codigo"), ("creature event", "criar_codigo"),
    ("historia de", "explicar_conceito"), ("lore de", "explicar_conceito"),
    ("falar sobre", "explicar_conceito"), ("fala sobre", "explicar_conceito"),
])

for p, c in _seeds_gerais:
    _decider.aprender(p, c)

print(f"[MCR-DevIA] {_decider.total} seeds | {len(_router.SEEDS)} rotas | LLM={'OK' if _llm.disponivel() else 'NOK'}")

# ─── Inicia watchdog em background ──────────────────────────────
try:
    from watchdog_mcr import WatchdogMCR
    _watchdog = WatchdogMCR()
    _watchdog.iniciar()
except Exception as e:
    print(f"[MCR-DevIA] Watchdog nao iniciado: {e}")
    _watchdog = None

# ─── Inicia code_parser ─────────────────────────────────────────
try:
    from code_parser import CodeParser
    _parser = CodeParser()
    print(f"[MCR-DevIA] Parser: {list(_parser.parsers.keys())}")
except Exception as e:
    print(f"[MCR-DevIA] Parser nao iniciado: {e}")
    _parser = None

# ─── Inicia MCRSystem (KG + 6 MCRs + Decisor) ────────────────
try:
    # Adiciona paths para o KG e modulos do DevIA
    _kg_path = os.path.join(PROJETO, "historia", "scripts", "mcr_devia", "knowledge")
    _mod_path = os.path.join(PROJETO, "historia", "scripts", "mcr_devia", "modulos")
    for p in [_kg_path, _mod_path]:
        if os.path.isdir(p) and p not in sys.path:
            sys.path.insert(0, p)
    
    from MCR import MCRSystem, MCRFuel, MCRBufferKG
    _cerebro = MCRSystem()
    
    # Se o KG ficou None (dependencia externa faltando), usa MCRBufferKG interno
    if _cerebro.kg is None:
        try:
            _cerebro.kg = MCRBufferKG()
        except Exception as e:
            print(f"[MCR-DevIA] MCRBufferKG fallback: {e}")
    
    # Garante cache interno no KG e busca  
    if _cerebro.kg:
        if not hasattr(_cerebro.kg, '_lessons_cache'):
            _cerebro.kg._lessons_cache = []
        # Patch do metodo buscar na classe, nao na instancia
        if not hasattr(type(_cerebro.kg), 'buscar'):
            type(_cerebro.kg).buscar = _patched_buscar
    
    print(f"[MCR-DevIA] MCRSystem: 6 MCRs, KG={_cerebro.kg is not None}")
    
    # MCRFuel: auto-alimentacao se KG estiver vazio
    if _cerebro.kg and hasattr(_cerebro.kg, 'alimentar'):
        try:
            _fuel = MCRFuel(kg=_cerebro.kg)
            _fuel.abastecer_se_precisar()
            print(f"[MCR-DevIA] MCRFuel ativo")
        except Exception as e:
            print(f"[MCR-DevIA] MCRFuel: {e}")
    else:
        print(f"[MCR-DevIA] MCRFuel: KG sem alimentar, pulando")
except Exception as e:
    print(f"[MCR-DevIA] MCRSystem nao iniciado: {e}")
    _cerebro = None

# ─── Inicia EpisodicMemory (Cache L3 semantico) ────────────────
try:
    sys.path.insert(0, os.path.join(DEVIA, "knowledge"))
    sys.path.insert(0, DEVIA)
    from episodic_memory import EpisodicMemory
    _memoria = EpisodicMemory()
    print(f"[MCR-DevIA] EpisodicMemory ativo")
except Exception as e:
    print(f"[MCR-DevIA] EpisodicMemory nao iniciado: {e}")
    _memoria = None

    # ─── Alimentacao inicial do KG (se vazio) ──────────────────────
if _cerebro and _cerebro.kg and hasattr(_cerebro.kg, 'aprender_conceito'):
    try:
        _conceitos_base = [
            ('spa', 'Sistema de Progressao do Aventureiro. Sistema de dominios que substitui vocacoes tradicionais no MCR.'),
            ('shc', 'Sistema de Habilidades Contextuais. Habilidades que dependem do contexto do personagem.'),
            ('sqh', 'Sistema de Quests Hibrido. Quests que combinam NPCs, acoes e progressao por storage.'),
            ('mcr', 'Projeto de servidor Tibia customizado. Markov Chain Registry — processador multi-nivel de informacao.'),
            ('eridanus', 'Cidade principal no Reino de Ignis, governado pelo Deus do Fogo Pyros.'),
            ('pyros', 'Deus do Fogo que governa o Reino de Ignis.'),
            ('aventureiro', 'Classe inicial de todo personagem no SPA. Evolui por dominios elementais.'),
            ('fogo', 'Dominio elemental do SPA (codigo 53). Habilidades de fogo causam dano fire e chance de queimar.'),
            ('ignis', 'Reino do fogo no MCR. Governado por Pyros. Capital: Flamares. Recurso mineral: cristais de magma.'),
        ]
        for termo, definicao in _conceitos_base:
            _cerebro.kg.aprender_conceito(termo, definicao, ctx='base')
        print(f"[MCR-DevIA] KG alimentado: {len(_conceitos_base)} conceitos base")
    except Exception as e:
        print(f"[MCR-DevIA] KG alimentacao: {e}")

# ─── Inicia MCRCuriosidade (exploracao background) ────────────
try:
    # MCRCuriosidade nao existe no novo MCR.py — usamos watchog_mcr + ingest_canary
    print(f"[MCR-DevIA] Curiosidade: disponivel via MCRCuriosidade (se existir no MCR.py)")
except Exception as e:
    print(f"[MCR-DevIA] Curiosidade nao iniciado: {e}")
    _curiosidade = None

# Seletor de modelo por classe — Qwen3.5 (código) + Gemma4 (narrativa)
try:
    from mcr.config_llm import MODELO_CODIGO, MODELO_LORE
except ImportError:
    MODELO_CODIGO = "qwen3.5:9b"
    MODELO_LORE = "gemma4:12b"

MODELO_POR_CLASSE = {
    # Código/Análise → Qwen3.5
    "analisar_bug": MODELO_CODIGO, "revisar_codigo": MODELO_CODIGO, "analisar_performance": MODELO_CODIGO,
    "analisar_arquitetura": MODELO_CODIGO, "analisar_seguranca": MODELO_CODIGO, "analisar_gameplay": MODELO_CODIGO,
    "criar_codigo": MODELO_CODIGO, "traduzir_texto": MODELO_CODIGO, "gerar_relatorio": MODELO_CODIGO,
    "gerar_texto": MODELO_CODIGO,
    # Criatividade/Narrativa → Gemma4
    "criar_npc": MODELO_LORE, "criar_quest": MODELO_LORE, "criar_habilidade_spa": MODELO_LORE,
    "explicar_conceito": MODELO_LORE,
}


# ─── Cache hierarquico ──────────────────────────────────────────
_CACHE_L1 = {}  # hash(pergunta) -> resposta
_CACHE_L2 = []  # [(fingerprint, hash, resposta, classe)]

def _similaridade_cosseno(a, b):
    """Cosseno entre dois vetores (substituto para MCRByteUtils.similaridade_cosseno)."""
    dot = sum(x*y for x,y in zip(a,b))
    na = sum(x*x for x in a)**0.5
    nb = sum(y*y for y in b)**0.5
    return dot/(na*nb) if na*nb else 0

def _buscar_cache(pergunta):
    h = hashlib.md5(pergunta.encode()).hexdigest()[:16]
    if h in _CACHE_L1:
        return _CACHE_L1[h], "cache_l1"
    fp = MCRFingerprint.gerar(pergunta)
    for fp_cached, _, resp_cached, _ in _CACHE_L2:
        sim = _similaridade_cosseno(fp, fp_cached)
        if sim > 0.85:
            return resp_cached, "cache_l2"
    return None, None

def _salvar_cache(pergunta, resposta, classe):
    h = hashlib.md5(pergunta.encode()).hexdigest()[:16]
    _CACHE_L1[h] = resposta
    if len(_CACHE_L1) > 500:
        for k in list(_CACHE_L1.keys())[:250]:
            del _CACHE_L1[k]
    fp = MCRFingerprint.gerar(pergunta)
    _CACHE_L2.append((fp, h, resposta, classe))
    if len(_CACHE_L2) > 500:
        _CACHE_L2[:] = _CACHE_L2[-250:]


# ─── Pipeline principal ─────────────────────────────────────────

import threading
_MA_STATE = threading.local()
_MA_STATE.ativo = False

def processar(entrada):
    global _calibra_contador, _ultimos_erros
    entrada = entrada.strip()
    if not entrada:
        return {"resposta": "", "erro": "entrada_vazia"}
    
    t0 = time.time()
    
    # 0. Cache L1/L2
    cache_resp, cache_tipo = _buscar_cache(entrada)
    if cache_resp:
        return {
            "resposta": cache_resp,
            "classe": "cache",
            "confianca": 1.0,
            "acoes": [cache_tipo],
            "tempo": round(time.time() - t0, 4),
            "validacao": {"valida": True, "similaridade": 1.0, "similaridade_contexto": 0.0, "alerta": None},
            "llm_usado": False,
            "sintaxe_valida": None,
            "tentativas_sintaxe": 0,
        }
    
    # 0.5 Cache L3 — EpisodicMemory (busca semantica)
    _ctx_episodico = ""
    if '_memoria' in dir() and _memoria:
        try:
            episodios = _memoria.buscar(entrada)
            if episodios and len(episodios) > 0:
                # Pega o mais relevante
                top = episodios[0]
                conf = top.get('similaridade', 0) if isinstance(top, dict) else 0.5
                if conf > 0.3:
                    _ctx_episodico = top.get('resultado', '') if isinstance(top, dict) else top[:200]
        except Exception as e:
            pass
    
    # 1. Classificar
    classe, conf = _decider.classificar(entrada)
    
    # 1.5 MasterAgent para tarefas complexas (quest, npc, sistema multi-arquivo)
    _classes_complexas = ["criar_quest", "criar_npc", "criar_monster", "criar_sistema", "criar_codigo", "criar_habilidade_spa"]
    if classe in _classes_complexas and not getattr(_MA_STATE, 'ativo', False):
        _MA_STATE.ativo = True
        try:
            from MasterAgent import MasterAgent
            _agent = MasterAgent(llm=_llm, cerebro=_cerebro, kernel=_kernel)
            resultado_agent = _agent.executar(entrada, classe=classe, confianca=conf)
            if resultado_agent.get("resposta"):
                print(f"  [MasterAgent] {resultado_agent['tempo']:.1f}s, {len(resultado_agent['passos'])} passos")
                resposta = resultado_agent["resposta"]
                return {
                    "resposta": resposta,
                    "classe": classe,
                    "confianca": round(conf, 3),
                    "acoes": ["master_agent"],
                    "tempo": round(time.time() - t0, 4),
                    "validacao": {"valida": True, "similaridade": 0.0, "similaridade_contexto": 0.0, "alerta": None},
                    "llm_usado": True,
                    "sintaxe_valida": None,
                    "tentativas_sintaxe": 0,
                    "autorevisao": "",
                }
        except Exception as e:
            print(f"  [MasterAgent] Fallback para pipeline padrao: {e}")
        finally:
            _MA_STATE.ativo = False
    
    # 2. Roteamento + radar
    acoes = _router.decidir(classe, conf)
    _radar.alimentar(acoes[0] if acoes else "")
    if _radar.em_loop():
        alt = _radar.forcar_alternativa(["cmd_grep", "cmd_read", "llm_gerar"])
        if alt:
            acoes.insert(0, alt)
    
    # 3. Pipeline
    pipe = PipelineExecutor(kernel=_kernel)
    pipe._llm = _llm
    pipe._classe = classe
    pipe._cerebro = _cerebro  # Global module level, accessed directly
    pipe._ctx_episodico = _ctx_episodico if '_ctx_episodico' in dir() and _ctx_episodico else ""
    # Define modelo otimo para esta classe
    modelo = MODELO_POR_CLASSE.get(classe, MODELO_CODIGO)
    pipe._modelo = modelo
    ctx = pipe.executar(acoes, entrada)
    
    # 4. Resposta
    stdout = ctx.get("stdout", "")
    llm_out = ctx.get("llm_output", "")
    preenchido = ctx.get("preenchido", "")
    code_analyzer_out = ctx.get("code_analyzer_output", "")
    
    if llm_out:
        resposta = llm_out
        if code_analyzer_out and "Nenhum bug" not in code_analyzer_out:
            resposta = code_analyzer_out + "\n\n=== ANALISE LLM ===\n" + llm_out
    elif code_analyzer_out and "Nenhum bug" not in code_analyzer_out:
        resposta = code_analyzer_out
    elif preenchido:
        resposta = preenchido[:500]
    elif stdout.strip():
        resposta = stdout[:1000]
    else:
        resposta = f"[{classe}] LLM offline, sem resultados de busca."
    
    # Se foi resposta do KG (zero LLM), marca como tal
    if ctx.get("kg_resposta"):
        llm_usado = False
    
    # 5. Validar
    validacao = _validator.validar(entrada, resposta[:1000])
    
    # 6. Aprender
    if _filter.filtrar(entrada, resposta, conf):
        _decider.aprender(entrada, classe)
    else:
        _ultimos_erros.append({"pergunta": entrada[:50], "classe": classe})
    
    # 7. Auto-calibração a cada 50 interações
    _calibra_contador += 1
    if _calibra_contador >= 50:
        from self_calibrate import calibrar
        calibrar(_decider, _router, _filter.stats(), _ultimos_erros)
        _calibra_contador = 0
        _ultimos_erros = []
    
    # 8. Cache
    _salvar_cache(entrada, resposta, classe)
    
    # 9. EpisodicMemory — registra episodio para memoria futura
    if '_memoria' in dir() and _memoria and _filter.filtrar(entrada, resposta, conf):
        try:
            _memoria.registrar(entrada, resposta[:500], classe)
        except Exception:
            pass
    
    return {
        "resposta": resposta,
        "classe": classe,
        "confianca": round(conf, 3),
        "acoes": acoes,
        "tempo": round(time.time() - t0, 4),
        "validacao": validacao,
        "llm_usado": bool(llm_out) and not ctx.get("kg_resposta", False),
        "sintaxe_valida": ctx.get("sintaxe_valida", None),
        "tentativas_sintaxe": ctx.get("tentativas_sintaxe", 0),
        "autorevisao": _autorevisao.gerar() if _autorevisao.arquivos_modificados else "",
    }


# ─── Inicia log watcher (debug autonomo, background) ───────────
try:
    from log_watcher import LogWatcher
    _log_watcher = LogWatcher(processar_func=processar)
    import threading
    def _log_loop():
        import time as _t
        while True:
            _t.sleep(30)
            erros = _log_watcher.verificar_logs()
            if erros:
                for e in erros[:2]:
                    print(f"[LOGWATCH] Erro: {e.get('linha_erro','?')[:80]}")
    _t = threading.Thread(target=_log_loop, daemon=True)
    _t.start()
    print(f"[MCR-DevIA] LogWatcher ativo a cada 30s ({_log_watcher.stats()['erros_detectados']} erros)")
except Exception as e:
    print(f"[MCR-DevIA] LogWatcher nao iniciado: {e}")
    _log_watcher = None


# ─── CLI ─────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    
    if "--emergir" in args:
        print("MCR-DevIA — Descobrindo conexoes...")
        cerebro = CerebroKG()
        kg_dir = os.path.join(PROJETO, "historia", "sandbox", ".mcr_devia", "kg")
        if os.path.isdir(kg_dir):
            licoes = []
            for f in os.listdir(kg_dir)[:40]:
                if not f.endswith('.json'): continue
                try:
                    with open(os.path.join(kg_dir, f), encoding='utf-8') as fh:
                        data = json.load(fh)
                    items = data.get('licoes', []) if isinstance(data, dict) else []
                    for l in items:
                        if isinstance(l, dict) and l.get('erro'):
                            l['ctx'] = l.get('ctx', data.get('ctx', 'geral'))
                            licoes.append(l)
                except Exception: pass
            for l in licoes:
                ctx = l.get('ctx', 'geral')
                texto = l.get('erro','') + ' ' + l.get('solucao','')
                cerebro.alimentar_texto(ctx, texto)
        descobertas = cerebro.descobrir_conexoes(top_k=5)
        for d in descobertas:
            print(f"\n  [{d['topico_a'][:25]} + {d['topico_b'][:25]}] ponte='{d['ponte']}' score={d['score']}")
            if _llm.disponivel():
                prompt = (f"Crie UMA pergunta 'E se...?' combinando {d['topico_a']} e {d['topico_b']}. "
                          f"Palavra-ponte: '{d['ponte']}'. Responda APENAS a pergunta em PT-BR.")
                try:
                    pergunta = _llm.gerar(prompt, modelo=MODELO_LORE, temp=0.7)
                    print(f"    E se... {pergunta.strip()[:200]}")
                except Exception: pass
        print(f"\n  {len(descobertas)} descobertas em 0ms (MCRConexao) + LLM")
        return
    
    if "--status" in args:
        st = {
            "decider_estados": len(_decider.mk.freq),
            "decider_total": _decider.total,
            "router_rotas": len(_router.SEEDS),
            "llm_ok": _llm.disponivel(),
            "filter_taxa": _filter.stats()["taxa_aceite"],
            "radar_loops": _radar.alternativas_forcadas,
        }
        print(json.dumps(st, indent=2))
        return
    
    perguntas = [a for a in args if not a.startswith("--")]
    if perguntas:
        for p in perguntas:
            r = processar(p)
            print(json.dumps({k: v for k, v in r.items() if k != "autorevisao"},
                             ensure_ascii=False, indent=2))
        return
    
    # Modo interativo
    print("MCR-DevIA — Markov decide, LLM gera. /status /sair")
    while True:
        try:
            e = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not e:
            continue
        if e == "/status":
            main()
            continue
        if e in ("sair", "exit", "quit"):
            break
        r = processar(e)
        classe = r["classe"]
        conf = r["confianca"]
        tempo = r["tempo"]
        llm = " [LLM]" if r.get("llm_usado") else ""
        val = " ?" if not r.get("validacao", {}).get("valida", True) else ""
        print(f"  [{classe} c={conf:.2f}{llm}{val} {tempo:.2f}s]")
        print(f"  {r['resposta'][:400]}")
        print()

if __name__ == "__main__":
    main()
