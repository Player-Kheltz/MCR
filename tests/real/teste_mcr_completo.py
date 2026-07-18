import sys, os, json, time, random
sys.path.insert(0, 'E:/MCR')

from mcr.mcr import MCR

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

m = MCR()

# Treinar: alimentar o coupling diretamente (rapido)
t0 = time.time()
for texto, acao in treino:
    m._coupling.alimentar(texto, acao)
    # Tambem alimentar o mk (markov de estados)
    estado = m._perceber(texto)
    m.mk.aprender(estado, acao)
    # Trigrama
    palavras = texto.lower().split()
    for p in palavras:
        if len(p) >= 3:
            for j in range(len(p) - 2):
                trig = p[j:j+3]
                m.mk_trigrama.aprender(trig, acao)
    # Palavra (transicoes)
    for i in range(len(palavras) - 1):
        if len(palavras[i]) >= 3 and len(palavras[i+1]) >= 3:
            m.mk_palavra.aprender(palavras[i], palavras[i+1])
    # Padrao estrutural
    niveis = m._extrair_niveis(texto)
    padrao = niveis.get('padrao', '')
    if padrao:
        m.mk_padrao.aprender(padrao, acao)
    # Esfera: alimentar cross-level
    for nivel, valor in niveis.items():
        if valor and nivel != 'acao':
            m._esfera.alimentar_par(nivel, 'acao', valor, acao)
t_alim = time.time() - t0
print(f'Treinamento: {t_alim:.2f}s')

corretos = 0
erros = []
latencias = []
for texto, esperado in teste:
    t0 = time.time()
    # Usar _decidir do MCR (superposition completa)
    estado = m._perceber(texto)
    acao, conf = m._decidir(estado, texto)
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

if erros:
    print(f'\nErros ({len(erros)}):')
    for txt, esp, pred, conf in erros[:20]:
        print(f'  "{txt}" | esperado={esp} | predito={pred} (conf={conf})')
