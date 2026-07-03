#!/usr/bin/env python3
"""Teste das correcoes: autoavaliacao + autoloop."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRAutoLoop, MarkovUniversal, MCR

mk = MarkovUniversal('teste')
pergunta = 'Explique o sistema SPA do MCR'

casos = [
    ('PERFEITA',  202, 'SPA = Sistema de Progressao do Aventureiro, que gerencia habilidades e progressao em dominios elementais como Fogo, Gelo, Terra e Energia. O SPA permite que o jogador evolua suas capacidades elementais atraves de combate e exploracao.'),
    ('MEDIANA',    80, 'SPA significa Sistema de Progressao do Aventureiro. Ele gerencia as habilidades do personagem.'),
    ('FRACA',      50, 'SPA e um sistema do MCR. O SPA foi implementado no pipeline.'),
    ('IRRELEVANT', 80, '5 metodos em master_agent.py: _processar_emergencia, _amostrar_top_k.'),
    ('CURTA',      25, 'SPA e um sistema.'),
    ('REPETITIVA', 200, 'SPA e um sistema do MCR. SPA e um sistema do MCR. SPA e um sistema do MCR. SPA e um sistema do MCR. SPA e um sistema.'),
    ('VAZIA',       2, 'ok'),
]

print('=' * 70)
print('  TESTE 1: COSSENO vs JACCARD (qual discrimina melhor?)')
print('=' * 70)
print(f'\n  Pergunta: "{pergunta}"\n')
print(f'  {"Nome":12s} {"Tam":4s} {"Jaccard":8s} {"Cosseno":8s}  {"Esperado":10s}')
print(f'  {"-"*12} {"-"*4} {"-"*8} {"-"*8}  {"-"*10}')

for nome, tam, resposta in casos:
    jac = mk.jaccard_bytes(pergunta, resposta)
    sim = mk.similaridade_transicoes(pergunta, resposta)
    esperado = 'ALTO' if nome == 'PERFEITA' else 'BAIXO' if nome in ('IRRELEVANT', 'VAZIA') else 'MEDIO'
    print(f'  {nome:12s} {tam:4d} {jac:8.3f} {sim:8.3f}  {esperado}')

print()
print('  CRITERIO: PERFEITA > MEDIANA > FRACA > IRRELEVANT > VAZIA')

# ============================================================
print()
print('=' * 70)
print('  TESTE 2: NOVA AUTOAVALIACAO (nota reflete qualidade real?)')
print('=' * 70)

mcr = MCR()

print(f'\n  {"Nome":12s} {"Nota":6s} {"Sim":6s} {"Tam":4s} {"Penal":5s}  Resposta')
print(f'  {"-"*12} {"-"*6} {"-"*6} {"-"*4} {"-"*5}  {"-"*30}')

for nome, tam, resposta in casos:
    nota, met = mcr._autoavaliar(resposta, pergunta)
    tam = met.get("tamanho_chars", 0)
    pen = met.get("penalidade", 0)
    cov = met.get("cobertura", 0)
    riq = met.get("riqueza", 0)
    print(f'  {nome:12s} {nota:6.1f} cob={cov:.2f} riq={riq:.2f} tam={tam:3d} pen={pen:.0f}  {resposta[:40]}')

print()
ordem_esperada = ['PERFEITA', 'MEDIANA', 'REPETITIVA', 'FRACA', 'CURTA', 'IRRELEVANT', 'VAZIA']
notas_obtidas = {}
for nome, tam, resposta in casos:
    nota, _ = mcr._autoavaliar(resposta, pergunta)
    notas_obtidas[nome] = nota

print('  Ordem esperada (decrescente):')
print(f'    {ordem_esperada}')
print('  Notas obtidas:')
ordem_real = sorted(notas_obtidas.items(), key=lambda x: -x[1])
print(f'    {[n for n,_ in ordem_real]}')

# Verifica se PERFEITA > todas as outras
perfeita_nota = notas_obtidas.get('PERFEITA', 0)
todas_menores = all(notas_obtidas[n] <= perfeita_nota for n in notas_obtidas if n != 'PERFEITA')
if perfeita_nota > 0 and todas_menores:
    print(f'  [PASS] PERFEITA ({perfeita_nota}) > todas as outras')
else:
    print(f'  [FAIL] PERFEITA ({perfeita_nota}) nao e a maior')

# Verifica se IRRELEVANT < FRACA
irr_nota = notas_obtidas.get('IRRELEVANT', 0)
fraca_nota = notas_obtidas.get('FRACA', 0)
if irr_nota < fraca_nota:
    print(f'  [PASS] IRRELEVANT ({irr_nota}) < FRACA ({fraca_nota})')
else:
    print(f'  [FAIL] IRRELEVANT ({irr_nota}) >= FRACA ({fraca_nota})')

# Verifica se VAZIA e a menor
vazia_nota = notas_obtidas.get('VAZIA', 0)
if vazia_nota <= min(notas_obtidas.values()):
    print(f'  [PASS] VAZIA ({vazia_nota}) e a menor nota')
else:
    print(f'  [FAIL] VAZIA ({vazia_nota}) nao e a menor')

# ============================================================
print()
print('=' * 70)
print('  TESTE 3: AUTOLOOP CORRIGIDO (expande conhecimento de verdade)')
print('=' * 70)

loop = MCRAutoLoop()

perguntas = [
    'Explique o sistema SPA do MCR',
    'Crie um NPC ferreiro em Eridanus',
    'O que e Canary no contexto do MCR',
]

for p in perguntas:
    res = loop.processar(p)
    nota = res['nota']
    
    # Julgamento real
    termos = [w.lower() for w in p.split() if len(w) > 3]
    resp_lower = res['resposta'].lower()
    cobertura = sum(1 for t in termos if t in resp_lower) / max(len(termos), 1)
    tem_conteudo = len(res['resposta']) > 50
    ferramentas_usou = len(res['ferramentas']) > 0 if res['ferramentas'] else False
    
    # Nota real (humana)
    if cobertura > 0.3 and tem_conteudo and ferramentas_usou:
        julgamento = 'OTIMA'
    elif cobertura > 0.2 and tem_conteudo:
        julgamento = 'BOA'
    elif tem_conteudo:
        julgamento = 'REGULAR'
    else:
        julgamento = 'FRACA'
    
    print(f'''
  Pergunta: {p}
    Nota MCR: {nota}/10
    Ciclos usados: {res["ciclos"]}
    Ferramentas: {res["ferramentas"]}
    Conhecimento acum: {res.get("conhecimento", 0)} chars
    Notas por ciclo: {res["notas"]}
    Julgamento real: {julgamento}
    Cobertura termos: {cobertura:.0%}
    Resposta ({len(res["resposta"])} chars):
      {res["resposta"][:150]}
''')

print('=' * 70)
print('  RESUMO')
print('=' * 70)
print(f'''
  Antes (Jaccard sets + formula antiga):
    PERFEITA = 6.2/10  (PUNIDA por ser longa)
    FRACA    = 9.2/10  (PREMIADA por ser curta)
    INVERTIDO! Nota nao refletia qualidade.

  Depois (Cosseno + nova formula):
    PERFEITA = ? (deve ser a maior)
    FRACA    = ? (deve ser menor que PERFEITA)
    VAZIA    = 0.0 (correto)
    
  AutoLoop antes:
    8 ciclos, 0 ferramentas, 0 conhecimento -> nota artificial
  
  AutoLoop depois:
    Deve usar ferramentas variadas e parar quando nota estabilizar
''')
