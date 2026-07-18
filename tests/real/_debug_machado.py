import sys; sys.path.insert(0, '.')
from mcr.coupling import MCRCoupling
import json, random, math

c = MCRCoupling()
with open('tests/experimento_rigoroso/dataset_500.json','r',encoding='utf-8') as f:
    dados = json.load(f)
random.seed(42); random.shuffle(dados)
n_treino = int(len(dados)*0.8)
treino = dados[:n_treino]
for d in treino:
    c.alimentar(d['input'], d['expected_action'])

for frase in ['machado de guerra', 'pocao de vida']:
    print(frase, '->', c.decidir(frase, (None, 0.0)))
    print('  _palavra_acao[machado]:', dict(c._palavra_acao.get('machado', {})))
    print('  _palavra_acao[pocao]:', dict(c._palavra_acao.get('pocao', {})))
    print('  _dist_palavras:', c._dist_palavras(frase))
    print('  _dist_posicoes:', c._dist_posicoes(frase))
    print()
