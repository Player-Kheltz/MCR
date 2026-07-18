import sys, os, json
sys.path.insert(0, '.')
from mcr.coupling import MCRCoupling
c = MCRCoupling()
with open('tests/experimento_rigoroso/dataset_500.json','r',encoding='utf-8') as f:
    dados = json.load(f)
# Replicar split da regressao
random_state = 42
import random
random.seed(random_state)
random.shuffle(dados)
n = len(dados)
n_treino = int(n * 0.8)
treino = dados[:n_treino]
teste = dados[n_treino:]
for d in treino: c.alimentar(d['input'], d['expected_action'])
# Casos que mudaram
for frase, esp in [('valide se o codigo esta correto','validar'),('aprenda a estrutura dos monstros','aprender')]:
    pred, conf = c.decidir(frase, (None,0.0))
    print(frase,'| esp=',esp,'| pred=',pred,'conf=',round(conf,3))
print()
print('valide sig:', dict(c._assinatura_palavra('valide')))
print('validar sig:', dict(c._assinatura_palavra('validar')))
print()
# Verificar quem sao as doadoras
herd = c._heranca_morfologica('valide')
print('heranca valide:', herd)
