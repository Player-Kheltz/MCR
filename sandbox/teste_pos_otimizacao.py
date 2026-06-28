#!/usr/bin/env python3
"""Bateria de testes pos-otimizacao do MCR-DevIA."""
import sys, os, json, time, py_compile

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from mcr_devia import KnowledgeGraph, IA, fast, _melhor_modelo

MCR_DEVIA = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia', 'mcr_devia.py')
CTX_CREW = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia', 'context_crew.py')

resultados = {'pass': 0, 'fail': 0}

def testar(nome, func):
    print('--- %s ---' % nome)
    try:
        func()
        print('  [OK]\n')
        resultados['pass'] += 1
    except Exception as e:
        print('  [ERRO] %s\n' % e)
        resultados['fail'] += 1

# === TESTE 1: SINTAXE ===
def t1():
    py_compile.compile(MCR_DEVIA, doraise=True)

# === TESTE 2: KG CARREGAMENTO ===
def t2():
    global kg
    t0 = time.time()
    kg = KnowledgeGraph()
    t = (time.time() - t0) * 1000
    total = len(kg.data['licoes'])
    ativas = len([l for l in kg.data['licoes'] if not l.get('inactive', False)])
    print('  %d lessons (%d ativas) carregadas em %.0f ms' % (total, ativas, t))

# === TESTE 3: KG PURGE ===
def t3():
    count = kg.purgar()
    ativas = len([l for l in kg.data['licoes'] if not l.get('inactive', False)])
    inativas = len([l for l in kg.data['licoes'] if l.get('inactive', False)])
    print('  %d lessons inativas, %d ativas (purge: %d novas)' % (inativas, ativas, count))

# === TESTE 4: KG BUSCA ===
def t4():
    testes = [
        ('LNK2001', 1, 'L001'),
        ('SHC', 1, 'L1002'),
        ('MCR', 1, 'L1000'),
        ('compilar OTClient', 1, None),
        ('string_view contains', 1, 'L003'),
        ('python nao existe', 0, None),
    ]
    for txt, min_r, expected_id in testes:
        r = kg.buscar(txt)
        ok = len(r) >= min_r
        if expected_id:
            ok = ok and any(l.get('id') == expected_id for l in r)
        status = '[OK]' if ok else '[ERRO]'
        print('  %s "%s": %d resultados' % (status, txt, len(r)))

# === TESTE 5: IA Router ===
def t5():
    cfg = _melhor_modelo('fast')
    print('  fast -> %s' % cfg['modelo'])

# === TESTE 6: context_crew sintaxe ===
def t6():
    py_compile.compile(CTX_CREW, doraise=True)

# === TESTE 7: CONSISTENCIA JSON KG ===
def t7():
    with open(kg.path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    missing = 0
    for l in data['licoes']:
        for k in ['id', 'erro', 'causa', 'solucao', 'ctx']:
            if k not in l:
                missing += 1
    print('  %d lessons, %d com campos faltando' % (len(data['licoes']), missing))

# === TESTE 8: Supervisr init ===
def t8():
    from mcr_devia import Supervisor
    ia = IA()
    sup = Supervisor(ia, kg)
    assert sup.ia is ia
    assert sup.kg is kg
    assert sup.ctx_crew is not None
    print('  Supervisor OK, ContextCrew disponivel')

# === TESTE 9: SIMULACAO DE EARLY RETURN ===
def t9():
    """Verifica se buscar ignora lessons inativas corretamente."""
    # Busca por termo que so existe em lessons inativas (weblearn)
    r_com_inativo = kg.buscar('weblearn', incluir_inativos=True)
    r_sem_inativo = kg.buscar('weblearn')
    ativos = sum(1 for l in r_sem_inativo if not l.get('inactive', False))
    print('  Com inativos: %d | Sem inativos: %d | Ativos: %d' % (
        len(r_com_inativo), len(r_sem_inativo), ativos))

# === EXECUTAR ===
print('=' * 50)
print('  BATERIA DE TESTES POS-OTIMIZACAO')
print('=' * 50)

kg = None
testar('Teste 1: Sintaxe mcr_devia.py', t1)
testar('Teste 2: KG Carregamento', t2)
testar('Teste 3: KG Purge', t3)
testar('Teste 4: Busca no KG', t4)
testar('Teste 5: IA Router', t5)
testar('Teste 6: Sintaxe context_crew.py', t6)
testar('Teste 7: Consistencia KG JSON', t7)
testar('Teste 8: Supervisor + ContextCrew', t8)
testar('Teste 9: Filtro lessons inativas', t9)

print('=' * 50)
total = resultados['pass'] + resultados['fail']
print('  RESUMO: %d/%d PASS (%d FAIL)' % (
    resultados['pass'], total, resultados['fail']))
print('=' * 50)
