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

for frase, esp in [('criar sprite de escudo','gerar_sprite'), ('pocao de vida','responder'), ('mago orc que coleta ervas raras e conhec','gerar_npc')]:
    palavras = re.findall(r'[a-zà-ÿ]{3,}', frase.lower())
    partes = frase.lower().split()
    pos_map = {}
    for i, p in enumerate(partes):
        if len(p) >= 3 and p not in pos_map:
            pos_map[p] = i
    print(f'\n=== {frase} (esp={esp}) ===')
    for p in set(palavras):
        pos = pos_map.get(p, 0)
        peso = 2.0 ** (-pos)
        dist = c._palavra_acao.get(p, {})
        print(f'  {p:<15} pos={pos} peso={peso:.4f} dist={dict(dist)}')
    print(f'  _dist_palavras: {c._dist_palavras(frase)}')
    print(f'  _dist_posicoes: {c._dist_posicoes(frase)}')
    print(f'  decidir: {c.decidir(frase, (None, 0.0))}')
