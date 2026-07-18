import sys, re; sys.path.insert(0,'E:/MCR')
from collections import defaultdict
from mcr.descobridor import DescobridorUniversal as DU

frases = [
    'crie um npc ferreiro', 'gere um monstro dragao',
    'create an npc blacksmith', 'generate a dragon',
    'crie uma quest', 'explique entropia',
    'crie um sprite', 'como funciona mcr',
    'faca um npc mago', 'gere um monstro lobo',
    'create a quest', 'explain entropy',
    'create a sprite', 'make an orc npc',
    'crie um npc guarda', 'gere um monstro demonio',
    'forge a wizard elf', 'build a goblin merchant',
]
todas = [re.findall(r'[a-zà-ÿ0-9]{2,}', f.lower()) for f in frases]
grupos = {}
for seq in todas:
    for i, token in enumerate(seq[:6]):
        k = f'Pos{i}'
        if k not in grupos: grupos[k] = []
        grupos[k].append([token])

r = DU.descobrir_em_dados(grupos, min_freq=0.15, min_razao=2.0)
for nome, info in sorted(r.items()):
    print(f'{nome}: {len(info["ancoras"])} ancoras -> {info["nome_automatico"][:60]}')
    if info['ancoras']:
        for t, f in info['ancoras'][:5]:
            print(f'  {t}: freq={f}')
