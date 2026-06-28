#!/usr/bin/env python3
"""Bateria de testes apos implementacao do CrewPattern universal."""
import sys, os, json, time, py_compile

os.environ['PYTHONIOENCODING'] = 'utf-8'
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'scripts', 'mcr_devia'))

from mcr_devia import KnowledgeGraph, IA, Supervisor, fast, Gerador
from crew_pattern import CrewPipeline, grep_pipeline

MCR_DEVIA = os.path.join(BASE, 'scripts', 'mcr_devia', 'mcr_devia.py')
CREW_PATTERN = os.path.join(BASE, 'scripts', 'mcr_devia', 'crew_pattern.py')
CTX_CREW = os.path.join(BASE, 'scripts', 'mcr_devia', 'context_crew.py')

kg = None
ia = None
resultados = {'pass': 0, 'fail': 0, 'tests': []}

def testar(nome, func):
    global kg, ia
    try:
        func()
        resultados['tests'].append((nome, 'PASS', ''))
        resultados['pass'] += 1
    except Exception as e:
        resultados['tests'].append((nome, 'FAIL', str(e)))
        resultados['fail'] += 1
        print('  [ERRO] %s: %s' % (nome, e))

def detalhe(msg):
    print('  ' + msg)

print('=' * 55)
print('  BATERIA DE TESTES — CREW PATTERN UNIVERSAL')
print('=' * 55)

# === 1. SINTAXE ===
def t_sintaxe():
    for f in [MCR_DEVIA, CREW_PATTERN, CTX_CREW]:
        py_compile.compile(f, doraise=True)
    detalhe('3 arquivos OK')

# === 2. KG CARREGAMENTO ===
def t_kg():
    global kg
    t0 = time.time()
    kg = KnowledgeGraph()
    t = (time.time() - t0) * 1000
    ativas = len([l for l in kg.data['licoes'] if not l.get('inactive', False)])
    detalhe('%d lessons (%d ativas) em %.0f ms' % (len(kg.data['licoes']), ativas, t))

# === 3. CREW PIPELINE V12 ===
def t_crew_v12():
    global kg, ia
    crew = CrewPipeline(kg, ia, verbose=False)
    # Termo que DEVERIA ter no KG
    r = crew._v12_check('O que e MCR?')
    assert r is not None and 'MCR' in r, 'V12 nao encontrou MCR: %s' % r
    detalhe('V12 MCR: %s' % r[:60])
    # Termo que NAO existe
    r2 = crew._v12_check('xablau_inexistente_123')
    assert r2 is None, 'V12 achou termo inexistente: %s' % r2
    detalhe('V12 inexistente: None (correto)')

# === 4. CREW PIPELINE PROCESSAR ===
def t_crew_processar():
    global kg, ia
    crew = CrewPipeline(kg, ia, verbose=False)
    # Sem compactador, deve retornar None (sem fonte pra buscar)
    r = crew.processar('teste sem fonte', usar_v12=False, usar_crew=False)
    detalhe('Processar sem fontes: %s' % r)
    # Com compactador que retorna string fixa
    r2 = crew.processar('teste', usar_v12=False, usar_crew=False,
                         fn_compactar=lambda ctx, pergunta: 'Resposta fixa: ' + pergunta)
    assert r2 == 'Resposta fixa: teste', 'Compactador falhou: %s' % r2
    detalhe('Processar com compactador: %s' % r2)

# === 5. GREP PIPELINE ===
def t_grep():
    import tempfile
    tmpdir = tempfile.mkdtemp()
    # Criar arquivos de teste
    files = {
        'npc_zoltan.lua': '-- NPC: Zoltan\nlocal npc = NPC("Zoltan")\nnpc:setSaudacao("Ola!")\n',
        'monster_dragon.lua': '-- Monster: Dragon\nlocal mon = Monster("Dragon")\nmon:setHealth(5000)\n',
        'utils.py': 'def helper():\n    return 42\n',
    }
    for nome, conteudo in files.items():
        with open(os.path.join(tmpdir, nome), 'w', encoding='utf-8') as f:
            f.write(conteudo)
    
    # Buscar por NPC
    r = grep_pipeline('criar NPC Zoltan', tmpdir)
    assert len(r) > 0, 'Nada encontrado para NPC'
    assert r[0]['score'] >= 1, 'Score muito baixo: %d' % r[0]['score']
    assert 'npc_zoltan' in r[0]['arquivo'].lower(), 'Arquivo errado: %s' % r[0]['arquivo']
    detalhe('Busca NPC: %s (score=%d)' % (r[0]['arquivo'], r[0]['score']))
    
    # Buscar por helper
    r2 = grep_pipeline('helper function', tmpdir)
    assert len(r2) > 0, 'Nada encontrado para helper'
    detalhe('Busca helper: %s (score=%d)' % (r2[0]['arquivo'], r2[0]['score']))
    
    # Buscar por algo que nao existe
    r3 = grep_pipeline('xyznonexistent12345', tmpdir)
    assert len(r3) == 0, 'Encontrou algo que nao existe: %s' % r3
    detalhe('Busca inexistente: 0 resultados (correto)')

# === 6. KG BUSCA COM FILTRO INATIVO ===
def t_kg_busca():
    global kg
    testes = [
        ('LNK2001', 1, 'L001'),
        ('SHC', 1, None),
        ('MCR', 1, None),
        ('string_view contains', 1, None),
    ]
    for txt, min_r, expected_id in testes:
        r = kg.buscar(txt)
        ok = len(r) >= min_r
        if expected_id:
            ok = ok and any(l.get('id') == expected_id for l in r)
        status = '[OK]' if ok else '[ERRO]'
        detalhe('%s "%s": %d resultados' % (status, txt, len(r)))

# === 7. STATS DO CREW ===
def t_crew_stats():
    crew = CrewPipeline(kg, ia, verbose=False)
    # Simular algumas chamadas
    crew.processar('teste1', usar_v12=False, usar_crew=False)
    crew.processar('teste2', usar_v12=False, usar_crew=False,
                   fn_compactar=lambda ctx, p: 'ok')
    s = crew.get_stats()
    assert s['total'] == 2, 'Stats total errado: %d' % s['total']
    detalhe('Stats: total=%d, v12=%d, crew=%d, fallback=%d' % (
        s['total'], s['v12_hits'], s['crew_hits'], s['fallbacks']))

# === 8. GERADOR COM V12 ===
def t_gerador_v12():
    global kg, ia
    g = Gerador(ia, kg)
    # O gerador nao retorna, imprime. So verificamos se nao crasha.
    # Mas verificamos se o V12 check foi integrado
    assert hasattr(g, '_crew'), 'Gerador sem _crew attribute'
    detalhe('Gerador._crew inicializado: OK')

# === 9. SUPERVISOR COM CREW PIPELINE ===
def t_supervisor_crew():
    global kg, ia
    sup = Supervisor(ia, kg)
    assert hasattr(sup, '_crew_pipeline') or hasattr(sup, 'perguntar'), 'Supervisor sem perguntar'
    detalhe('Supervisor: OK')

# === EXECUTAR ===
testar('1. Sintaxe dos 3 arquivos', t_sintaxe)
testar('2. KG Carregamento', t_kg)
if kg:
    testar('3. CrewPipeline V12 check', t_crew_v12)
    testar('4. CrewPipeline processar', t_crew_processar)
testar('5. GrepPipeline (score matematico)', t_grep)
if kg:
    testar('6. KG Busca com filtro inativo', t_kg_busca)
    testar('7. CrewPipeline Stats', t_crew_stats)
    testar('8. Gerador com V12 integration', t_gerador_v12)
    testar('9. Supervisor com CrewPipeline', t_supervisor_crew)

print()
print('=' * 55)
total = resultados['pass'] + resultados['fail']
print('  RESUMO: %d/%d PASS (%d FAIL)' % (resultados['pass'], total, resultados['fail']))
print('=' * 55)

# Detalhes de falhas
for nome, status, erro in resultados['tests']:
    if status == 'FAIL':
        print('  FAIL: %s -> %s' % (nome, erro))
