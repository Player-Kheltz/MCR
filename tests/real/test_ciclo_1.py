"""Teste REAL e COMPLETO do sistema MCR — Ciclo 1."""
import sys
import time
import json
import pytest
sys.path.insert(0, 'E:\\MCR')

PASS = 0
FAIL = 0
WARN = 0

def testar(nome, fn):
    global PASS, FAIL, WARN
    try:
        ok, msg = fn()
        if ok == 'warn':
            WARN += 1
            print(f'  WARN {nome}: {msg}')
        elif ok:
            PASS += 1
            print(f'  PASS {nome}: {msg}')
        else:
            FAIL += 1
            print(f'  FAIL {nome}: {msg}')
    except Exception as e:
        FAIL += 1
        print(f'  FAIL {nome}: {type(e).__name__}: {str(e)[:100]}')

print('=' * 70)
print('  MCR — TESTE REAL CICLO 1')
print('=' * 70)

# ─── 1. IMPORTS ────────────────────────────────────────────
print('\n--- 1. IMPORTS ---')

def test_mcr_engine():
    from devia.kernel.mcr_kernel.engine import MCR
    m = MCR("test")
    m.aprender("a", "b")
    m.aprender("b", "c")
    prox, conf = m.predizer("a")
    assert prox == "b", f"Esperado 'b', got {prox}"
    return True, f"predizer(a)={prox}, conf={conf:.3f}"

def test_mcr_signature():
    from devia.kernel.mcr_kernel.signature import MCRFingerprint
    fp = MCRFingerprint.gerar("hello world")
    assert fp, "Fingerprint vazio"
    return True, f"fp_len={len(fp)}"

def test_mcr_registry():
    from mcr.registry import MCRRegistry
    r = MCRRegistry()
    r.registrar('teste', lambda: 42)
    assert r.selecionar('teste') is not None
    return True, f"tools={len(r.listar())}"

def test_mcr_unificado():
    from mcr.mcr_unificado import MCRUnificado
    mcr = MCRUnificado()
    return True, "instancia criada"

def test_mcr_bootstrap():
    from mcr.bootstrap import bootstrap
    from mcr.registry import MCRRegistry
    r = MCRRegistry()
    bootstrap(r)
    stats = r.stats()
    return True, f"{stats['total_tools']} tools, {len(stats['dominios'])} dominios"

def test_mcr_sqlite():
    from mcr.mcr_sqlite import MCRSQLite
    m = MCRSQLite(":memory:")
    m.aprender("ola", "mundo")
    return True, "SQLite OK"

def test_sqlite_markov():
    from mcr.sqlite_markov import SQLiteMarkov
    return True, "import OK"

def test_pipeline_conectado():
    from mcr.adaptadores import PipelineConectado
    return True, "import OK"

def test_emergir():
    from mcr.emergir_unificado import EmergirUnificado
    return True, "import OK"

def test_gerador_codigo():
    from mcr.gerador_codigo import GeradorCodigo
    return True, "import OK"

def test_npc_criativo():
    pytest.importorskip('mcr.npc_criativo')
    from mcr.npc_criativo import NPCCriativo
    return True, "import OK"

def test_raciocinador():
    from mcr.raciocinador import Raciocinador
    return True, "import OK"

def test_mentepura():
    pytest.importorskip('mcr.mcr_mente_pura')
    from mcr.mcr_mente_pura import MCRMentePura
    return True, "import OK"

def test_mente():
    pytest.importorskip('mcr.mcr_mente')
    from mcr.mcr_mente import MCRMente
    return True, "import OK"

def test_self():
    from mcr.mcr_self import MCRSelf
    return True, "import OK"

def test_internal_monologue():
    from mcr.internal_monologue import InternalMonologue
    return True, "import OK"

def test_autobiography():
    from mcr.mcr_autobiography import Autobiography
    return True, "import OK"

def test_metacognicao():
    from mcr.metacognicao import Metacognicao
    return True, "import OK"

def test_auto_evolution():
    from mcr.mcr_auto_evolution import MCRAutoEvolution
    return True, "import OK"

def test_cache_hierarquico():
    from mcr.cache_hierarquico import CacheHierarquico
    return True, "import OK"

def test_world_system():
    from mcr.mcr_world_system import MCRWorldSystem
    return True, "import OK"

def test_dialogue_trainer():
    from mcr.dialogue_trainer import DialogueTrainer
    return True, "import OK"

def test_planejador():
    from mcr.planejador import Planejador
    return True, "import OK"

def test_chain_of_verification():
    from mcr.chain_of_verification import ChainOfVerification
    return True, "import OK"

def test_hybrid_router():
    pytest.importorskip('mcr.hybrid_router')
    from mcr.hybrid_router import HybridRouter
    return True, "import OK"

def test_bridge_api():
    from mcr.bridge_api import BridgeAPI
    return True, "import OK"

def test_generator_multinivel():
    from mcr.generator_multinivel import GeradorMultinivel
    return True, "import OK"

def test_auto_curiosidade():
    from mcr.auto_curiosidade import AutoCuriosidade
    return True, "import OK"

def test_hdc_kg_memory():
    from mcr.hdc_kg_memory import HDCKGMemory
    return True, "import OK"

testar("mcr.engine.MCR", test_mcr_engine)
testar("mcr.signature.MCRFingerprint", test_mcr_signature)
testar("mcr.registry.MCRRegistry", test_mcr_registry)
testar("mcr.mcr_unificado.MCRUnificado", test_mcr_unificado)
testar("mcr.bootstrap", test_mcr_bootstrap)
testar("mcr.mcr_sqlite", test_mcr_sqlite)
testar("mcr.sqlite_markov", test_sqlite_markov)
testar("mcr.pipeline_conectado", test_pipeline_conectado)
testar("mcr.emergir_unificado", test_emergir)
testar("mcr.gerador_codigo", test_gerador_codigo)
testar("mcr.npc_criativo", test_npc_criativo)
testar("mcr.raciocinador", test_raciocinador)
testar("mcr.mcr_mente_pura", test_mentepura)
testar("mcr.mcr_mente", test_mente)
testar("mcr.mcr_self", test_self)
testar("mcr.internal_monologue", test_internal_monologue)
testar("mcr.mcr_autobiography", test_autobiography)
testar("mcr.metacognicao", test_metacognicao)
testar("mcr.mcr_auto_evolution", test_auto_evolution)
testar("mcr.cache_hierarquico", test_cache_hierarquico)
testar("mcr.mcr_world_system", test_world_system)
testar("mcr.dialogue_trainer", test_dialogue_trainer)
testar("mcr.planejador", test_planejador)
testar("mcr.chain_of_verification", test_chain_of_verification)
testar("mcr.hybrid_router", test_hybrid_router)
testar("mcr.bridge_api", test_bridge_api)
testar("mcr.generator_multinivel", test_generator_multinivel)
testar("mcr.auto_curiosidade", test_auto_curiosidade)
testar("mcr.hdc_kg_memory", test_hdc_kg_memory)

# ─── 2. MARKOV FUNCTIONAL ─────────────────────────────────
print('\n--- 2. MARKOV FUNCTIONAL ---')

def test_markov_learn_predict():
    from devia.kernel.mcr_kernel.engine import MCR
    m = MCR("functional")
    m.aprender("inicio", "meio")
    m.aprender("meio", "fim")
    m.aprender("meio", "fim")
    prox, conf = m.predizer("meio")
    assert prox == "fim", f"Esperado 'fim', got {prox}"
    return True, f"predizer(meio)={prox}, conf={conf:.3f}"

def test_markov_entropy():
    from devia.kernel.mcr_kernel.engine import MCR
    m = MCR("entropy")
    m.aprender("a", "b")
    m.aprender("a", "c")
    m.aprender("a", "d")
    h = m.entropia("a")
    assert h > 0, f"Entropia deveria ser > 0, got {h}"
    return True, f"entropia(a)={h:.3f}"

def test_markov_jaccard():
    from devia.kernel.mcr_kernel.engine import MCR
    m1 = MCR("j1")
    m1.aprender("x", "y")
    m2 = MCR("j2")
    m2.aprender("x", "y")
    j = m1.jaccard(m2)
    assert j > 0, f"Jaccard deveria ser > 0, got {j}"
    return True, f"jaccard={j:.3f}"

def test_markov_generate():
    from devia.kernel.mcr_kernel.engine import MCR
    m = MCR("gen")
    m.aprender("1", "2")
    m.aprender("2", "3")
    m.aprender("3", "4")
    seq = m.gerar("1", 5)
    assert len(seq) >= 2, f"Sequencia muito curta: {seq}"
    return True, f"gerar(1,5)={seq}"

def test_markov_batch():
    from devia.kernel.mcr_kernel.engine import MCR
    m = MCR("batch")
    m.aprender_batch([["a","b","c"], ["x","y","z"], ["a","b","d"]])
    assert len(m.transicoes) > 0, "Sem transições após batch"
    return True, f"estados={len(m.transicoes)}, transicoes={sum(len(v) for v in m.transicoes.values())}"

def test_compose_state():
    from devia.kernel.mcr_kernel.engine import compose_state
    r = compose_state("return", {"em_bloco": "metodo"})
    assert "|" in r, f"compose_state falhou: {r}"
    return True, f"compose_state={r}"

testar("Markov.aprender+predizer", test_markov_learn_predict)
testar("Markov.entropia", test_markov_entropy)
testar("Markov.jaccard", test_markov_jaccard)
testar("Markov.gerar", test_markov_generate)
testar("Markov.batch", test_markov_batch)
testar("compose_state", test_compose_state)

# ─── 3. PIPELINE UNIFICADO (FUNCTIONAL) ───────────────────
print('\n--- 3. PIPELINE UNIFICADO ---')

def test_pipeline_executar():
    from mcr.mcr_unificado import MCRUnificado
    mcr = MCRUnificado()
    r = mcr.executar("Gere um NPC ferreiro")
    assert 'classificacao' in r, "Sem classificacao"
    assert 'resultados' in r, "Sem resultados"
    assert isinstance(r['nota'], float), f"Nota não é float: {type(r['nota'])}"
    return True, f"nota={r['nota']}, subtarefas={r['n_subtarefas']}, tempo={r['tempo_total']:.4f}s"

def test_pipeline_processar_compat():
    from mcr.mcr_unificado import MCRUnificado
    mcr = MCRUnificado()
    r = mcr.processar("Ola mundo")
    assert 'intencao' in r, "Sem intencao (compat)"
    assert 'resposta' in r, "Sem resposta (compat)"
    return True, f"intencao={r['intencao']}, tempo={r['tempo']:.4f}s"

def test_pipeline_rapido():
    from mcr.mcr_unificado import MCRUnificado
    mcr = MCRUnificado()
    r = mcr.executar_rapido("Analise isso")
    return True, f"resultado={'sim' if r is not None else 'None'}"

def test_pipeline_stats():
    from mcr.mcr_unificado import MCRUnificado
    mcr = MCRUnificado()
    s = mcr.stats()
    assert 'registry' in s, "Sem registry stats"
    return True, f"registry_tools={s['registry']['total_tools']}, historico={s['historico']}"

def test_pipeline_múltiplas_entradas():
    from mcr.mcr_unificado import MCRUnificado
    mcr = MCRUnificado()
    entradas = ["Ola", "Gere codigo Lua", "Crie um NPC", "Explique Markov", "15+27"]
    notas = []
    for e in entradas:
        r = mcr.executar(e)
        notas.append(r['nota'])
    media = sum(notas) / len(notas)
    return True, f"{len(entradas)} entradas, notas={[f'{n:.2f}' for n in notas]}, media={media:.3f}"

testar("Pipeline.executar()", test_pipeline_executar)
testar("Pipeline.processar() compat", test_pipeline_processar_compat)
testar("Pipeline.executar_rapido()", test_pipeline_rapido)
testar("Pipeline.stats()", test_pipeline_stats)
testar("Pipeline multi-entrada", test_pipeline_múltiplas_entradas)

# ─── 4. REGISTRY ──────────────────────────────────────────
print('\n--- 4. REGISTRY ---')

def test_registry_registrar_executar():
    from mcr.registry import MCRRegistry
    r = MCRRegistry()
    r.registrar('soma', lambda a=0, b=0: a+b, params=['a', 'b'])
    result = r.executar('soma', a=3, b=4)
    assert result == 7, f"Esperado 7, got {result}"
    return True, f"soma(3,4)={result}"

def test_registry_dominios():
    from mcr.registry import MCRRegistry
    r = MCRRegistry()
    r.registrar('lua_gen', lambda: 'lua', dominio='lua')
    r.registrar('npc_gen', lambda: 'npc', dominio='npc')
    lua_tools = r.listar(dominio='lua')
    assert 'lua_gen' in lua_tools
    return True, f"lua_tools={lua_tools}"

def test_registry_persistencia():
    from mcr.registry import MCRRegistry
    import tempfile, os
    r = MCRRegistry()
    r.registrar('persist_test', lambda: 99)
    r.selecionar('persist_test').executar()
    r.salvar()
    r2 = MCRRegistry()
    r2.registrar('persist_test', lambda: 99)
    r2.carregar()
    assert r2.selecionar('persist_test').usos == 1, "Persistência falhou"
    return True, "persistência OK"

testar("Registry registrar+executar", test_registry_registrar_executar)
testar("Registry dominios", test_registry_dominios)
testar("Registry persistência", test_registry_persistencia)

# ─── 5. BOOTSTRAP ─────────────────────────────────────────
print('\n--- 5. BOOTSTRAP ---')

def test_bootstrap_full():
    from mcr.bootstrap import bootstrap
    from mcr.registry import MCRRegistry
    r = MCRRegistry()
    bootstrap(r)
    stats = r.stats()
    assert stats['total_tools'] > 50, f"Poucas tools: {stats['total_tools']}"
    return True, f"{stats['total_tools']} tools, dominios={stats['dominios']}"

def test_bootstrap_migration():
    from mcr.bootstrap import bootstrap_desde_executor
    from mcr.registry import MCRRegistry
    r = MCRRegistry()
    bootstrap_desde_executor(r)
    stats = r.stats()
    return True, f"{stats['total_tools']} tools migradas"

def test_bootstrap_completo():
    from mcr.bootstrap import inicializar
    from mcr.registry import MCRRegistry
    r = MCRRegistry()
    inicializar(r)
    stats = r.stats()
    assert stats['total_tools'] > 100, f"Poucas tools: {stats['total_tools']}"
    return True, f"{stats['total_tools']} tools (bootstrap completo)"

testar("Bootstrap.scan()", test_bootstrap_full)
testar("Bootstrap.migration()", test_bootstrap_migration)
testar("Bootstrap.inicializar()", test_bootstrap_completo)

# ─── 6. DEVIA KERNEL ──────────────────────────────────────
print('\n--- 6. DEVIA KERNEL ---')

def test_kernel_decisor():
    from devia.kernel.mcr_kernel.decisor import MCRThreshold
    return True, "import OK"

def test_kernel_memory():
    from devia.kernel.mcr_kernel.memory import MCRConector, MCRCadeia
    return True, "import OK"

def test_kernel_meta():
    from devia.kernel.mcr_kernel.meta import MCRMetaNivel
    return True, "import OK"

def test_kernel_evolution():
    from devia.kernel.mcr_kernel.evolution import MCRAutoMelhoria
    return True, "import OK"

def test_kernel_feedback():
    from devia.kernel.mcr_kernel.feedback import MCRFeedback, MCRFilosofia
    return True, "import OK"

def test_kernel_system():
    from devia.kernel.mcr_kernel.system import MCRSystem, MCRPergunta
    return True, "import OK"

def test_kernel_persistence():
    from devia.kernel.mcr_kernel.persistence import MCRPersistencia
    return True, "import OK"

testar("kernel.decisor", test_kernel_decisor)
testar("kernel.memory", test_kernel_memory)
testar("kernel.meta", test_kernel_meta)
testar("kernel.evolution", test_kernel_evolution)
testar("kernel.feedback", test_kernel_feedback)
testar("kernel.system", test_kernel_system)
testar("kernel.persistence", test_kernel_persistence)

# ─── 7. DEVIA MODULES ─────────────────────────────────────
print('\n--- 7. DEVIA MODULES ---')

def test_modules_master():
    from devia.modules.master_agent import MasterAgent
    return True, "import OK"

def test_modules_supervisor():
    from devia.modules.supervisor import Supervisor
    return True, "import OK"

def test_modules_orquestrador():
    from devia.modules.orquestrador import Orquestrador
    return True, "import OK"

def test_modules_intention():
    from devia.modules.intention_engine import IntentionEngine
    return True, "import OK"

def test_modules_episodic():
    from devia.modules.episodic_memory import EpisodicMemory
    return True, "import OK"

def test_modules_context():
    from devia.modules.context_enricher import ContextEnricher
    return True, "import OK"

testar("modules.master_agent", test_modules_master)
testar("modules.supervisor", test_modules_supervisor)
testar("modules.orquestrador", test_modules_orquestrador)
testar("modules.intention_engine", test_modules_intention)
testar("modules.episodic_memory", test_modules_episodic)
testar("modules.context_enricher", test_modules_context)

# ─── 8. CODE GENERATION (REAL) ────────────────────────────
print('\n--- 8. CODE GENERATION ---')

def test_gerar_lua_npc():
    pytest.importorskip('mcr.golden_templates')
    from mcr.golden_templates import gerar_npc_canary
    codigo = gerar_npc_canary({"nome": "Ferreiro", "profissao": "shop", "cidade": "Thais"})
    assert codigo and len(codigo) > 50, f"Código muito curto: {str(codigo)[:100]}"
    return True, f"lua_len={len(codigo)} chars"

testar("golden_templates.gerar_npc_canary", test_gerar_lua_npc)

# ─── RESUMO ────────────────────────────────────────────────
print('\n' + '=' * 70)
total = PASS + FAIL + WARN
print(f'  RESULTADO: {PASS}/{total} PASS  |  {FAIL}/{total} FAIL  |  {WARN}/{total} WARN')
if FAIL == 0:
    print('  STATUS: TODOS OS TESTES PASSARAM')
else:
    print(f'  STATUS: {FAIL} FALHA(S) - CORRIGIR')
print('=' * 70)
