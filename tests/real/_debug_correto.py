import sys; sys.path.insert(0, '.')
from mcr.coupling import MCRCoupling
import json, random

c = MCRCoupling()
with open('tests/experimento_rigoroso/dataset_500.json','r',encoding='utf-8') as f:
    dados = json.load(f)
random.seed(42); random.shuffle(dados)
n_treino = int(len(dados)*0.8)
treino = dados[:n_treino]
for d in treino:
    c.alimentar(d['input'], d['expected_action'])

print('heranca correto:', c._heranca_morfologica('correto'))
print()
print('assinatura correto:', c._assinatura_palavra('correto'))
print()
# Quem sao as doadoras?
from mcr.semantic_router import similaridade as ngram_sim
sims = [(k, ngram_sim('correto', k)) for k in c._palavra_acao.keys()]
sims.sort(key=lambda x: -x[1])
print('top 5 vizinhos morfologicos de correto:')
for k, s in sims[:5]:
    print(f'  {k}: ngram={s:.3f} | _palavra_acao={dict(c._palavra_acao[k])}')
print()
print('palavras_similares(correto, 0.20):')
for p, s in c.palavras_similares('correto', threshold=0.20):
    print(f'  {p}: sim={s:.3f}')
