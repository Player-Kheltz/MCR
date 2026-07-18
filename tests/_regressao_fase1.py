"""Regressao FASE 1 — valida que compor() nao quebrou a classificacao zero-shot.
Referencia: 100% (113/113) em 80/20 split do dataset_500.json.
"""
import sys, os, json, time, random
sys.path.insert(0, 'E:/MCR')

from mcr.coupling import MCRCoupling

random.seed(42)

caminho = 'E:/MCR/tests/experimento_rigoroso/dataset_500.json'
with open(caminho, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

pares = [(d['input'], d['expected_action']) for d in dataset]
random.shuffle(pares)

n = len(pares)
n_treino = int(n * 0.8)
treino = pares[:n_treino]
teste = pares[n_treino:]

print(f'Dataset: {n} entradas, treino={n_treino}, teste={n-n_treino}')

c = MCRCoupling()
t0 = time.time()
c.alimentar_swarm(treino)
t_alim = time.time() - t0
print(f'Treinamento: {t_alim:.2f}s')

corretos = 0
erros = []
latencias = []
for texto, esperado in teste:
    t0 = time.time()
    acao, conf = c.decidir(texto, (None, 0.0))
    dt = (time.time() - t0) * 1000
    latencias.append(dt)
    if acao == esperado:
        corretos += 1
    else:
        erros.append((texto[:40], esperado, acao, round(conf, 3)))

acc = corretos / len(teste) * 100
lat_med = sum(latencias) / len(latencias)

print(f'\nAccuracy: {corretos}/{len(teste)} = {acc:.1f}%')
print(f'Latencia media: {lat_med:.2f}ms')
print(f'Referencia: 100% (113/113), ~20ms')

if erros:
    print(f'\nErros ({len(erros)}):')
    for txt, esp, pred, conf in erros[:20]:
        print(f'  "{txt}" | esperado={esp} | predito={pred} (conf={conf})')

regressao = corretos < 113
print(f'\n{"REGRESSAO DETECTADA" if regressao else "OK — 113/113"}')
sys.exit(1 if regressao else 0)
