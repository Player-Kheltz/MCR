"""Teste FINAL consolidado — MCR validação completa.
Ciclo 1 + Ciclo 2 + validação de import chain.
"""
import sys
import time
import pytest
sys.path.insert(0, 'E:\\MCR')

PASS = 0
FAIL = 0
total_tests = 0

def testar(nome, fn):
    global PASS, FAIL, total_tests
    total_tests += 1
    try:
        ok, msg = fn()
        if ok:
            PASS += 1
            print(f'  PASS {nome}: {msg}')
        else:
            FAIL += 1
            print(f'  FAIL {nome}: {msg}')
    except Exception as e:
        FAIL += 1
        print(f'  FAIL {nome}: {type(e).__name__}: {str(e)[:100]}')

print('=' * 70)
print('  MCR — TESTE FINAL CONSOLIDADO')
print('=' * 70)
t_start = time.time()

# ═══════════════════════════════════════════════════════════
# A. IMPORT CHAIN (mcr/ + devia/)
# ═══════════════════════════════════════════════════════════
print('\n--- A. IMPORT CHAIN ---')

def test_import_mcr_all():
    import importlib
    from pathlib import Path
    mcr_dir = Path('E:/MCR/mcr')
    modules = [f.stem for f in mcr_dir.glob('*.py')
               if f.stem != '__init__' and not f.stem.startswith('_')]
    erros = []
    for mod_name in modules:
        try:
            importlib.import_module(f'mcr.{mod_name}')
        except Exception as e:
            erros.append(f'{mod_name}: {str(e)[:50]}')
    assert not erros, f'{len(erros)} erros: {"; ".join(erros[:5])}'
    return True, f'{len(modules)}/mcr OK'

def test_import_devia_kernel():
    import importlib
    from pathlib import Path
    pkg = Path('E:/MCR/devia/kernel')
    modules = [f.stem for f in pkg.glob('*.py')
               if f.stem != '__init__' and not f.stem.startswith('_')]
    erros = []
    for mod_name in modules:
        try:
            importlib.import_module(f'devia.kernel.{mod_name}')
        except Exception as e:
            erros.append(f'{mod_name}: {str(e)[:50]}')
    assert not erros, f'{len(erros)} erros: {"; ".join(erros[:5])}'
    return True, f'{len(modules)}/devia.kernel OK'

def test_import_devia_mcr_kernel():
    import importlib
    from pathlib import Path
    pkg = Path('E:/MCR/devia/kernel/mcr_kernel')
    modules = [f.stem for f in pkg.glob('*.py')
               if f.stem != '__init__' and not f.stem.startswith('_')]
    erros = []
    for mod_name in modules:
        try:
            importlib.import_module(f'devia.kernel.mcr_kernel.{mod_name}')
        except Exception as e:
            erros.append(f'{mod_name}: {str(e)[:50]}')
    assert not erros, f'{len(erros)} erros: {"; ".join(erros[:5])}'
    return True, f'{len(modules)}/mcr_kernel OK'

def test_import_devia_modules():
    import importlib
    from pathlib import Path
    pkg = Path('E:/MCR/devia/modules')
    modules = [f.stem for f in pkg.glob('*.py')
               if f.stem != '__init__' and not f.stem.startswith('_')]
    erros = []
    for mod_name in modules:
        try:
            importlib.import_module(f'devia.modules.{mod_name}')
        except Exception as e:
            erros.append(f'{mod_name}: {str(e)[:50]}')
    assert not erros, f'{len(erros)} erros: {"; ".join(erros[:5])}'
    return True, f'{len(modules)}/devia.modules OK'

def test_import_mcr_init():
    import mcr
    assert hasattr(mcr, 'ROOT_DIR')
    return True, f'mcr.ROOT_DIR={mcr.ROOT_DIR}'

testar("mcr/ import chain", test_import_mcr_all)
testar("devia/kernel import chain", test_import_devia_kernel)
testar("devia/kernel/mcr_kernel chain", test_import_devia_mcr_kernel)
testar("devia/modules import chain", test_import_devia_modules)
testar("mcr.__init__ OK", test_import_mcr_init)

# ═══════════════════════════════════════════════════════════
# B. CORE ENGINE
# ═══════════════════════════════════════════════════════════
print('\n--- B. CORE ENGINE ---')

def test_mcr_aprender_predizer():
    from devia.kernel.mcr_kernel.engine import MCR
    m = MCR("core")
    m.aprender("ola", "mundo")
    m.aprender("mundo", "belo")
    p, c = m.predizer("ola")
    return p == "mundo", f"predizer(ola)={p}, conf={c:.3f}"

def test_mcr_entropia():
    from devia.kernel.mcr_kernel.engine import MCR
    m = MCR("ent")
    m.aprender("a", "b")
    m.aprender("a", "c")
    h = m.entropia("a")
    return h > 0, f"entropia(a)={h:.3f}"

def test_mcr_jaccard():
    from devia.kernel.mcr_kernel.engine import MCR
    m1 = MCR("j1"); m1.aprender("x","y"); m1.aprender("y","z")
    m2 = MCR("j2"); m2.aprender("x","y"); m2.aprender("y","z")
    j = m1.jaccard(m2)
    return j == 1.0, f"jaccard={j:.3f}"

def test_mcr_gerar():
    from devia.kernel.mcr_kernel.engine import MCR
    m = MCR("gen")
    m.aprender_batch([["1","2","3"],["4","5","6"],["1","2","4"]])
    seq = m.gerar("1", 10)
    return len(seq) >= 3, f"gerar(1,10)={seq}"

def test_mcr_compose():
    from devia.kernel.mcr_kernel.engine import compose_state, compor_contexto
    cs = compose_state("return", {"em_bloco": "metodo"})
    ctx = compor_contexto(["class", "Foo", "{"], {})
    return "|" in cs and "em_bloco" in cs, f"compose={cs}, ctx={ctx}"

def test_mcr_signature():
    from devia.kernel.mcr_kernel.signature import MCRFingerprint
    fp = MCRFingerprint.gerar("test data 123")
    return len(fp) > 0, f"fp_len={len(fp)}"

def test_mcr_stats():
    from devia.kernel.mcr_kernel.engine import MCR
    m = MCR("stats"); m.aprender("a","b"); m.aprender("b","c")
    s = m.stats()
    return s['estados'] == 2, f"stats={s}"

testar("MCR.aprender+predizer", test_mcr_aprender_predizer)
testar("MCR.entropia", test_mcr_entropia)
testar("MCR.jaccard", test_mcr_jaccard)
testar("MCR.gerar", test_mcr_gerar)
testar("MCR.compose_state+compor_contexto", test_mcr_compose)
testar("MCRFingerprint", test_mcr_signature)
testar("MCR.stats", test_mcr_stats)

# ═══════════════════════════════════════════════════════════
# C. REGISTRY
# ═══════════════════════════════════════════════════════════
print('\n--- C. REGISTRY ---')

def test_registry_basico():
    from mcr.registry import MCRRegistry
    r = MCRRegistry()
    r.registrar('soma', lambda a=0,b=0: a+b, params=['a','b'], dominio='math')
    r.registrar('mult', lambda a=0,b=0: a*b, params=['a','b'], dominio='math')
    assert r.executar('soma', a=5, b=3) == 8
    assert r.executar('mult', a=5, b=3) == 15
    return True, f"soma=8, mult=15"

def test_registry_dominios():
    from mcr.registry import MCRRegistry
    r = MCRRegistry()
    r.registrar('a', lambda: 1, dominio='x')
    r.registrar('b', lambda: 2, dominio='y')
    r.registrar('c', lambda: 3, dominio='x')
    return r.listar(dominio='x') == ['a', 'c'], f"dominio_x={r.listar(dominio='x')}"

def test_registry_stats():
    from mcr.registry import MCRRegistry
    r = MCRRegistry()
    r.registrar('t1', lambda: 1)
    r.selecionar('t1').executar()
    s = r.stats()
    return s['total_tools'] == 1 and s['mais_usadas'][0][1] == 1, f"stats={s}"

testar("Registry basico", test_registry_basico)
testar("Registry dominios", test_registry_dominios)
testar("Registry stats", test_registry_stats)

# ═══════════════════════════════════════════════════════════
# D. BOOTSTRAP
# ═══════════════════════════════════════════════════════════
print('\n--- D. BOOTSTRAP ---')

def test_bootstrap_descobre():
    from mcr.bootstrap import bootstrap
    from mcr.registry import MCRRegistry
    r = MCRRegistry()
    bootstrap(r)
    s = r.stats()
    return s['total_tools'] > 100, f"{s['total_tools']} tools, {len(s['dominios'])} dominios"

def test_bootstrap_migra():
    from mcr.bootstrap import bootstrap_desde_executor
    from mcr.registry import MCRRegistry
    r = MCRRegistry()
    bootstrap_desde_executor(r)
    s = r.stats()
    return s['total_tools'] > 50, f"{s['total_tools']} tools migradas"

def test_bootstrap_inicializar():
    from mcr.bootstrap import inicializar
    from mcr.registry import MCRRegistry
    r = MCRRegistry()
    inicializar(r)
    s = r.stats()
    return s['total_tools'] > 200, f"{s['total_tools']} tools (completo)"

testar("Bootstrap descoberta", test_bootstrap_descobre)
testar("Bootstrap migração", test_bootstrap_migra)
testar("Bootstrap inicializar", test_bootstrap_inicializar)

# ═══════════════════════════════════════════════════════════
# E. PIPELINE UNIFICADO
# ═══════════════════════════════════════════════════════════
print('\n--- E. PIPELINE UNIFICADO ---')

def test_pipeline_auto_bootstrap():
    from mcr.mcr_unificado import MCRUnificado
    mcr = MCRUnificado()
    tools = mcr._registry.listar()
    return len(tools) > 100, f"{len(tools)} tools auto-bootstrapped"

def test_pipeline_executar():
    from mcr.mcr_unificado import MCRUnificado
    mcr = MCRUnificado()
    r = mcr.executar("Gere um NPC ferreiro em Thais")
    assert 'classificacao' in r
    assert 'resultados' in r
    tool = r['resultados'][0]['resultado'].get('tool', '?') if r['resultados'] else '?'
    return True, f"tool={tool}, nota={r['nota']}, tempo={r['tempo_total']:.4f}s"

def test_pipeline_completa():
    from mcr.mcr_unificado import MCRUnificado
    mcr = MCRUnificado()
    entradas = [
        "Ola!", "Gere codigo Lua", "Crie um NPC guarda",
        "Analise padroes Markov", "Quanto e 100/5?",
    ]
    for e in entradas:
        mcr.executar(e)
    stats = mcr.stats()
    return stats['historico'] >= 5, f"{len(entradas)} entradas, historico={stats['historico']}"

def test_pipeline_compat():
    from mcr.mcr_unificado import MCRUnificado
    mcr = MCRUnificado()
    r = mcr.processar("Teste de compatibilidade")
    return 'intencao' in r and 'resposta' in r, f"campos={list(r.keys())}"

def test_pipeline_executar_rapido():
    from mcr.mcr_unificado import MCRUnificado
    mcr = MCRUnificado()
    r = mcr.executar_rapido("Algo rapido")
    return True, f"resultado={'sim' if r else 'None'}"

testar("Pipeline auto-bootstrap", test_pipeline_auto_bootstrap)
testar("Pipeline executar", test_pipeline_executar)
testar("Pipeline completa", test_pipeline_completa)
testar("Pipeline compatibilidade", test_pipeline_compat)
testar("Pipeline rapido", test_pipeline_executar_rapido)

# ═══════════════════════════════════════════════════════════
# F. CODE GENERATION
# ═══════════════════════════════════════════════════════════
print('\n--- F. CODE GENERATION ---')

def test_lua_npc():
    pytest.importorskip('mcr.golden_templates')
    from mcr.golden_templates import gerar_npc_canary
    c = gerar_npc_canary({"nome":"Gorn","profissao":"shop","cidade":"Thais"})
    return len(c) > 200, f"lua_npc: {len(c)} chars"

def test_lua_monstro():
    pytest.importorskip('mcr.golden_templates')
    from mcr.golden_templates import gerar_monstro_parametrizado
    c = gerar_monstro_parametrizado({"nome":"Dragon","nivel":50,"hp":3000})
    return len(c) > 100, f"lua_monstro: {len(c)} chars"

testar("Lua NPC canary", test_lua_npc)
testar("Lua monstro parametrizado", test_lua_monstro)

# ═══════════════════════════════════════════════════════════
# G. DEVIA MODULES
# ═══════════════════════════════════════════════════════════
print('\n--- G. DEVIA MODULES ---')

def test_modules():
    from devia.modules.master_agent import MasterAgent
    from devia.modules.supervisor import Supervisor
    from devia.modules.orquestrador import Orquestrador
    from devia.modules.intention_engine import IntentionEngine
    from devia.modules.episodic_memory import EpisodicMemory
    from devia.modules.context_enricher import ContextEnricher
    from devia.kernel.mcr_kernel.decisor import MCRThreshold
    from devia.kernel.mcr_kernel.memory import MCRConector
    from devia.kernel.mcr_kernel.evolution import MCRAutoMelhoria
    from devia.kernel.mcr_kernel.feedback import MCRFeedback
    from devia.kernel.mcr_kernel.system import MCRSystem
    from devia.kernel.mcr_kernel.persistence import MCRPersistencia
    return True, "12 modules OK"

testar("DevIA modules + kernel", test_modules)

# ═══════════════════════════════════════════════════════════
# H. LIMPEZA
# ═══════════════════════════════════════════════════════════
print('\n--- H. LIMPEZA ---')

def test_no_bare_except_mcr():
    import re, os
    results = []
    for r, _, fs in os.walk('mcr'):
        for f in fs:
            if f.endswith('.py'):
                path = os.path.join(r, f)
                for i, l in enumerate(open(path, encoding='utf-8', errors='ignore')):
                    if re.match(r'\s*except\s*:', l):
                        results.append(f'{path}:{i+1}')
    return len(results) == 0, f"bare excepts={len(results)}"

def test_no_bare_except_devia_active():
    import re, os
    results = []
    for r, _, fs in os.walk('devia'):
        for f in fs:
            if f.endswith('.py') and 'MCR_legacy' not in f:
                path = os.path.join(r, f)
                for i, l in enumerate(open(path, encoding='utf-8', errors='ignore')):
                    if re.match(r'\s*except\s*:', l):
                        results.append(f'{path}:{i+1}')
    return len(results) == 0, f"bare excepts={len(results)}"

testar("mcr/ sem bare except", test_no_bare_except_mcr)
testar("devia/ ativo sem bare except", test_no_bare_except_devia_active)

# ═══════════════════════════════════════════════════════════
# RESUMO
# ═══════════════════════════════════════════════════════════
elapsed = time.time() - t_start
print('\n' + '=' * 70)
print(f'  MCR — RESULTADO FINAL')
print(f'  {PASS}/{total_tests} PASS  |  {FAIL}/{total_tests} FAIL')
print(f'  Tempo: {elapsed:.1f}s')
if FAIL == 0:
    print('  STATUS: SISTEMA VALIDADO — 0 FALHAS')
else:
    print(f'  STATUS: {FAIL} FALHA(S) — CORRIGIR')
print('=' * 70)
