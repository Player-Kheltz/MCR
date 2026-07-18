"""Teste Ciclo 2 — Pipeline com bootstrap integrado."""
import sys
import pytest
sys.path.insert(0, 'E:\\MCR')

PASS = 0
FAIL = 0

def testar(nome, fn):
    global PASS, FAIL
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
print('  MCR — TESTE CICLO 2: Bootstrap + Pipeline Integrado')
print('=' * 70)

# ─── 1. Pipeline com auto-bootstrap ────────────────────────
print('\n--- 1. PIPELINE AUTO-BOOTSTRAP ---')

def test_pipeline_auto_bootstrap():
    from mcr.mcr_unificado import MCRUnificado
    mcr = MCRUnificado()
    tools = mcr._registry.listar()
    assert len(tools) > 50, f"Poucas tools: {len(tools)}"
    return True, f"{len(tools)} tools auto-bootstrapped"

def test_pipeline_executar_com_tools():
    from mcr.mcr_unificado import MCRUnificado
    mcr = MCRUnificado()
    r = mcr.executar("Gere um NPC ferreiro")
    assert r['classificacao'] is not None
    assert len(r['resultados']) > 0
    tool_usada = r['resultados'][0]['resultado'].get('tool', 'nenhuma')
    return True, f"tool={tool_usada}, nota={r['nota']}, subtarefas={r['n_subtarefas']}, tempo={r['tempo_total']:.4f}s"

def test_pipeline_multi_com_bootstrap():
    from mcr.mcr_unificado import MCRUnificado
    mcr = MCRUnificado()
    entradas = [
        "Ola mundo",
        "Gere codigo Lua para um NPC",
        "Crie um monstro dragao",
        "Analise o padrao de transicao",
        "Quanto e 15 + 27?",
    ]
    resultados = []
    for e in entradas:
        r = mcr.executar(e)
        tool = r['resultados'][0]['resultado'].get('tool', '?') if r['resultados'] else '?'
        resultados.append((e[:30], tool, r['nota']))
    return True, f"{len(entradas)} entradas processadas"

def test_pipeline_historico_aprendizado():
    from mcr.mcr_unificado import MCRUnificado
    mcr = MCRUnificado()
    for i in range(5):
        mcr.executar(f"Teste {i}")
    stats = mcr.stats()
    assert stats['historico'] >= 5, f"Menos de 5 no historico: {stats['historico']}"
    return True, f"historico={stats['historico']}"

def test_pipeline_compatibility():
    from mcr.mcr_unificado import MCRUnificado
    mcr = MCRUnificado()
    r = mcr.processar("Ola!")
    assert 'intencao' in r, "Sem campo 'intencao'"
    assert 'resposta' in r, "Sem campo 'resposta'"
    assert 'tempo' in r, "Sem campo 'tempo'"
    return True, f"compat OK: intencao={r['intencao']}"

testar("Pipeline auto-bootstrap", test_pipeline_auto_bootstrap)
testar("Pipeline executar com tools", test_pipeline_executar_com_tools)
testar("Pipeline multi-entrada", test_pipeline_multi_com_bootstrap)
testar("Pipeline historico", test_pipeline_historico_aprendizado)
testar("Pipeline compatibilidade", test_pipeline_compatibility)

# ─── 2. Bootstrap completo ─────────────────────────────────
print('\n--- 2. BOOTSTRAP COMPLETO ---')

def test_bootstrap_scan_mcr():
    from mcr.bootstrap import bootstrap
    from mcr.registry import MCRRegistry
    r = MCRRegistry()
    bootstrap(r)
    stats = r.stats()
    return True, f"scan: {stats['total_tools']} tools, dominios={stats['dominios']}"

def test_bootstrap_migrate():
    from mcr.bootstrap import bootstrap_desde_executor
    from mcr.registry import MCRRegistry
    r = MCRRegistry()
    bootstrap_desde_executor(r)
    stats = r.stats()
    return True, f"migracao: {stats['total_tools']} tools"

def test_bootstrap_full():
    from mcr.bootstrap import inicializar
    from mcr.registry import MCRRegistry
    r = MCRRegistry()
    inicializar(r)
    stats = r.stats()
    # Verifica que tem tools de todos os dominios
    dominios_esperados = {'kernel', 'modules', 'mcr_core', 'mcr_criativo', 'mcr_world', 'mcr_infra'}
    dominios_atuais = set(stats['dominios'])
    faltando = dominios_esperados - dominios_atuais
    assert not faltando, f"Dominios faltando: {faltando}"
    return True, f"full: {stats['total_tools']} tools, todos dominios presentes"

testar("Bootstrap scan mcr/", test_bootstrap_scan_mcr)
testar("Bootstrap migration", test_bootstrap_migrate)
testar("Bootstrap full", test_bootstrap_full)

# ─── 3. Markov funcional profundo ─────────────────────────
print('\n--- 3. MARKOV PROFUNDO ---')

def test_markov_cadeia_longa():
    from devia.kernel.mcr_kernel.engine import MCR
    m = MCR("longa")
    for i in range(100):
        m.aprender(str(i), str(i+1))
    prox, conf = m.predizer("50")
    assert prox == "51", f"Esperado '51', got {prox}"
    return True, f"cadeia 100, predizer(50)={prox}, conf={conf:.3f}"

def test_markov_multi_transicoes():
    from devia.kernel.mcr_kernel.engine import MCR
    m = MCR("multi")
    m.aprender("a", "b")
    m.aprender("a", "c")
    m.aprender("a", "d")
    m.aprender("b", "e")
    m.aprender("c", "e")
    m.aprender("d", "e")
    assert len(m.transicoes["a"]) == 3, f"Esperado 3 transicoes de 'a'"
    return True, f"transicoes_a={len(m.transicoes['a'])}, total_estados={len(m.transicoes)}"

def test_markov_similaridade():
    from devia.kernel.mcr_kernel.engine import MCR
    m1 = MCR("s1")
    m1.aprender_batch([["a","b","c"], ["x","y","z"]])
    m2 = MCR("s2")
    m2.aprender_batch([["a","b","c"], ["x","y","w"]])
    j = m1.jaccard(m2)
    assert 0 < j <= 1, f"Jaccard deveria ser entre 0 e 1, got {j}"
    return True, f"jaccard={j:.3f}"

def test_markov_entropia_baixa():
    from devia.kernel.mcr_kernel.engine import MCR
    m = MCR("baixa")
    for _ in range(50):
        m.aprender("x", "y")
    h = m.entropia("x")
    assert h == 0.0, f"Entropia deveria ser 0 (deterministica), got {h}"
    return True, f"entropia={h:.3f} (deterministica)"

def test_markov_serializacao():
    from devia.kernel.mcr_kernel.engine import MCR
    import json
    m = MCR("serial")
    m.aprender("a", "b")
    m.aprender("b", "c")
    stats = m.stats()
    assert 'estados' in stats
    return True, f"stats={json.dumps(stats)}"

testar("Markov cadeia longa", test_markov_cadeia_longa)
testar("Markov multi transicoes", test_markov_multi_transicoes)
testar("Markov similaridade", test_markov_similaridade)
testar("Markov entropia baixa", test_markov_entropia_baixa)
testar("Markov serializacao", test_markov_serializacao)

# ─── 4. Code Generation REAL ──────────────────────────────
print('\n--- 4. CODE GENERATION REAL ---')

def test_lua_npc_real():
    pytest.importorskip('mcr.golden_templates')
    from mcr.golden_templates import gerar_npc_canary
    codigo = gerar_npc_canary({
        "nome": "Gorn",
        "profissao": "shop",
        "cidade": "Thais",
        "itens": ["espada de aco", "escudo de ferro"]
    })
    assert len(codigo) > 200, f"Lua muito curto: {len(codigo)}"
    assert "function" in codigo or "local" in codigo, "Sem keywords Lua"
    return True, f"lua_npc: {len(codigo)} chars"

def test_lua_monstro_real():
    pytest.importorskip('mcr.golden_templates')
    from mcr.golden_templates import gerar_monstro_parametrizado
    codigo = gerar_monstro_parametrizado({
        "nome": "Dragon",
        "nivel": 50,
        "hp": 3000,
        "attack": 200,
    })
    assert len(codigo) > 100, f"Monstro muito curto: {len(codigo)}"
    return True, f"lua_monstro: {len(codigo)} chars"

testar("Lua NPC real", test_lua_npc_real)
testar("Lua Monstro real", test_lua_monstro_real)

# ─── 5. Signature / Fingerprint ────────────────────────────
print('\n--- 5. SIGNATURE / FINGERPRINT ---')

def test_fingerprint_unico():
    from devia.kernel.mcr_kernel.signature import MCRFingerprint
    fp1 = MCRFingerprint.gerar("hello world")
    fp2 = MCRFingerprint.gerar("hello world")
    fp3 = MCRFingerprint.gerar("goodbye world")
    assert fp1 == fp2, "Mesmo input, fingerprints diferentes"
    assert fp1 != fp3, "Inputs diferentes, fingerprints iguais"
    return True, f"fp1==fp2={fp1==fp2}, fp1!=fp3={fp1!=fp3}"

def test_signature_comparacao():
    from devia.kernel.mcr_kernel.signature import MCRSignature
    s1 = MCRSignature.extrair("hello")
    s2 = MCRSignature.extrair("hello")
    s3 = MCRSignature.extrair("world")
    assert s1['entropia'] == s2['entropia'], "Mesmo input, entropias diferentes"
    return True, f"sig1_entropia={s1['entropia']}, sig3_entropia={s3['entropia']}"

testar("Fingerprint unicidade", test_fingerprint_unico)
testar("Signature comparacao", test_signature_comparacao)

# ─── RESUMO ────────────────────────────────────────────────
print('\n' + '=' * 70)
total = PASS + FAIL
print(f'  RESULTADO CICLO 2: {PASS}/{total} PASS  |  {FAIL}/{total} FAIL')
if FAIL == 0:
    print('  STATUS: TODOS OS TESTES PASSARAM')
else:
    print(f'  STATUS: {FAIL} FALHA(S) - CORRIGIR')
print('=' * 70)
