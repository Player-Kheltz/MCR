"""Teste do RADAR numerico por delta fingerprint."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from MCR import *
import math

SEQUENCIAS = [
    {'nome': 'Fibonacci',  'seq': [1, 1, 2, 3, 5, 8, 13], 'resposta': 21},
    {'nome': 'Quadrados',  'seq': [1, 4, 9, 16, 25, 36, 49], 'resposta': 64},
    {'nome': 'Primos',     'seq': [2, 3, 5, 7, 11, 13, 17], 'resposta': 19},
    {'nome': 'Pot2',       'seq': [1, 2, 4, 8, 16, 32, 64], 'resposta': 128},
    {'nome': 'Binario',    'seq': [1, 10, 11, 100, 101, 110, 111], 'resposta': 1000},
]

radar = MCRRadar()
acertos = 0

print('')
print('RADAR NUMERICO: predicao por consistencia de delta')
print('')

for seq in SEQUENCIAS:
    nome = seq['nome']
    elementos = seq['seq']
    resposta = seq['resposta']

    palpite, conf = radar.predizer_sequencia(elementos, max_candidato=2000)
    acertou = (palpite == resposta)
    status = 'SIM' if acertou else 'NAO'

    seq_str = ' '.join(str(x) for x in elementos)
    print(f'  [{nome}]')
    print(f'    Sequencia: {seq_str}')
    print(f'    Resposta:  {resposta}')
    print(f'    MCR disse: {palpite} (conf={conf:.4f})  {status}')

    deltas = []
    for i in range(len(elementos) - 1):
        d = MCRRadar.delta_fingerprint(str(elementos[i]), str(elementos[i+1]))
        deltas.append(d)
    mags = [round(MCRRadar._mag(d), 2) for d in deltas]
    print(f'    Deltas:    {mags}')

    if acertou:
        acertos += 1
    print()

print(f'  RESULTADO: {acertos}/{len(SEQUENCIAS)}')
print()

# Analise do top 5 para cada sequencia
print('  ANALISE TOP 5:')
for seq in SEQUENCIAS:
    nome = seq['nome']
    elementos = seq['seq']
    resposta = seq['resposta']

    deltas = []
    for i in range(len(elementos) - 1):
        deltas.append(MCRRadar.delta_fingerprint(str(elementos[i]), str(elementos[i+1])))

    scores = []
    for c in range(1, 100):
        d = MCRRadar.delta_fingerprint(str(elementos[-1]), str(c))
        mag = MCRRadar._mag(d)
        if mag == 0:
            continue
        sims = [MCRRadar._sim_delta(d, d_ant) for d_ant in deltas if MCRRadar._mag(d_ant) > 0]
        if not sims:
            continue
        sim_med = sum(sims) / len(sims)
        scores.append((sim_med, c))

    scores.sort(key=lambda x: -x[0])
    top5 = [(c, round(s, 3)) for s, c in scores[:5]]
    rank = 'nao encontrado'
    for i, (s, c) in enumerate(scores):
        if c == resposta:
            rank = str(i + 1)
            break
    print(f'  {nome}: top5={top5}  resposta={resposta} rank={rank}')

print('')
print('OK!')
