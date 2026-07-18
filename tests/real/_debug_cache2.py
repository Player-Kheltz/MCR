import sys; sys.path.insert(0, '.')
from mcr.coupling import MCRCoupling
import json, random

c = MCRCoupling()
with open('tests/experimento_rigoroso/dataset_500.json','r',encoding='utf-8') as f:
    dados = json.load(f)
random.seed(42); random.shuffle(dados)
n = len(dados); n_treino = int(n*0.8)
treino = dados[:n_treino]

# Treinar tudo
for d in treino:
    c.alimentar(d['input'], d['expected_action'])

# Estado final
print('valide em _palavra_acao?', 'valide' in c._palavra_acao)
print('valide em _cache_assinatura?', 'valide' in getattr(c, '_cache_assinatura', {}))
print('cache tamanho:', len(getattr(c, '_cache_assinatura', {})))
# Limpar cache
c._cache_assinatura = {}
sig_fresh = c._assinatura_palavra('valide')
print('SIG FRESCA:', sig_fresh)
# Verificar _palavra_acao['valide']
print('_palavra_acao[valide]:', dict(c._palavra_acao.get('valide', {})))
