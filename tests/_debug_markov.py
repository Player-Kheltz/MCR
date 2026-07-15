import sys, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'E:/MCR')
from mcr.mcr import MCR
from collections import Counter

mcr = MCR()
print('History entries:', len(mcr._historico))
if mcr._historico:
    actions = Counter(h.get('acao') for h in mcr._historico)
    print('History by action:', dict(actions))

print('Markov transitions:', len(mcr.mk.transicoes) if hasattr(mcr.mk, 'transicoes') else 'N/A')

# Check what action Markov predicts for various inputs
test_inputs = [
    'Crie um NPC alquimista',
    'Gere um dragao de fogo',
    'Qual a diferenca entre knight e paladin?',
    'Crie um sprite de escudo',
    'Explique como funciona Markov',
    'Gere um monstro orc',
    'crie sprite de machado',
    'npc ferreiro',
    'responda sobre tibia',
]
for inp in test_inputs:
    estado = mcr._perceber(inp)
    acao, conf = mcr._decidir(estado)
    print(f'  "{inp[:50]}" -> {acao} (conf={conf:.3f})')

# Check Markov state per action
print('\nMarkov state analysis:')
for action in ['gerar_npc', 'gerar_monstro', 'responder', 'gerar_sprite', 'gerar_quest']:
    matching = [k for k in mcr.mk.transicoes.keys() if action in str(mcr.mk.transicoes.get(k, {}))]
    print(f'  {action}: {len(matching)} transition keys')
