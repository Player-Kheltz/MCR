import sys; sys.path.insert(0, '.')
from mcr.coupling import MCRCoupling
import json, random, re

c = MCRCoupling()
with open('tests/experimento_rigoroso/dataset_500.json','r',encoding='utf-8') as f:
    dados = json.load(f)
random.seed(42); random.shuffle(dados)
n_treino = int(len(dados)*0.8)
treino = dados[:n_treino]
for d in treino:
    c.alimentar(d['input'], d['expected_action'])

frase = 'valide se o codigo esta correto'
print('Frase:', frase)
print()
palavras = re.findall(r'[a-zà-ÿ]{3,}', frase.lower())
print('Tokens:', palavras)
print()
for p in set(palavras):
    dist = c._palavra_acao.get(p, {})
    print(f'  {p}: em_vocab={bool(dist)} dist={dict(dist)}')
print()
print('_dist_palavras:', c._dist_palavras(frase))
print('_dist_posicoes:', c._dist_posicoes(frase))
print()
pred, conf = c.decidir(frase, (None, 0.0))
print('pred:', pred, 'conf:', round(conf,3))

# Comparar com versao sem heranca: desabilitar e rodar
print()
print('=== DESABILITANDO HERANCA ===')
c._cache_assinatura = {}
original = MCRCoupling._heranca_morfologica
MCRCoupling._heranca_morfologica = lambda self, p, **kw: {}
pred2, conf2 = c.decidir(frase, (None, 0.0))
print('pred (sem heranca):', pred2, 'conf:', round(conf2,3))
