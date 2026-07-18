import sys, re
sys.path.insert(0, '.')
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

# Ver palavras-chave dos erros
for w in ['aprenda','busque','planeje','edite','monstro','monstros','npc','npcHandler','funcoes','funcao','estrutura','forte','criacao','looktype']:
    dist = c._palavra_acao.get(w, {})
    print(f'{w:<15} conhecido={bool(dist)} dist={dict(dist)}')
print()
# Verificar heranca das variantes verbais
for w in ['aprenda','busque','planeje','edite']:
    h = c._heranca_morfologica(w)
    acoes = {k:v for k,v in h.items() if k.startswith('acao:') and v > 0}
    print(f'heranca({w}): {acoes}')
print()
# Verificar frase completa
for frase, esp in [('aprenda a estrutura dos monstros','aprender'),
                    ('busque funcoes que usam npcHandler','buscar'),
                    ('planeje a criacao de um npc complexo','planejar'),
                    ('edite o looktype do npc vendedor','editar')]:
    palavras = re.findall(r'[a-zà-ÿ]{3,}', frase.lower())
    print(f'\n{frase} (esp={esp})')
    for p in set(palavras):
        dist = c._palavra_acao.get(p, {})
        if dist:
            print(f'  {p}: CONHECIDO dist={dict(dist)}')
        else:
            h = c._heranca_morfologica(p)
            acoes = {k:v for k,v in h.items() if k.startswith('acao:') and v > 0}
            proxies = c.palavras_similares(p, threshold=0.20)
            print(f'  {p}: NOVO heranca_acoes={acoes} proxies={proxies[:2]}')
    print(f'  _dist_palavras: {c._dist_palavras(frase)}')
    print(f'  decidir: {c.decidir(frase, (None, 0.0))}')
