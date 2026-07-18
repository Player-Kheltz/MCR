import sys; sys.path.insert(0, '.')
from mcr.coupling import MCRCoupling
import json, random

c = MCRCoupling()
with open('tests/experimento_rigoroso/dataset_500.json','r',encoding='utf-8') as f:
    dados = json.load(f)
random.seed(42); random.shuffle(dados)
n = len(dados); n_treino = int(n*0.8)
treino = dados[:n_treino]

# Rastrear quando 'valide' entra no vocabulario
for i, d in enumerate(treino):
    antes = 'valide' in c._palavra_acao
    c.alimentar(d['input'], d['expected_action'])
    depois = 'valide' in c._palavra_acao
    if not antes and depois:
        print(f'[{i}] valide entrou no vocabulario: input="{d["input"]}" acao={d["expected_action"]}')
        print(f'  cache foi limpo? {"sim" if not hasattr(c,"_cache_assinatura") or not c._cache_assinatura else "NAO - BUG"}')
        # Quebrar e ver a assinatura antes/depois
        if 'valide' in c._cache_assinatura:
            print('  ASSINATURA CACHEADA (errada):', c._cache_assinatura['valide'])
        # Calcular assinatura fresca
        sig_fresh = c._assinatura_palavra('valide')
        print('  ASSINATURA FRESCA:', sig_fresh)
        # Quebrar cache e recalcular
        c._cache_assinatura = {}
        sig_fresh2 = c._assinatura_palavra('valide')
        print('  ASSINATURA SEM CACHE:', sig_fresh2)
        break
