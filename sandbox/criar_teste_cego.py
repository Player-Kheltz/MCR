#!/usr/bin/env python3
"""
TESTE CEGO — Novos problemas que o MCR-DevIA nunca viu
=========================================================
Cria uma nova leva de problemas FRESCOS em um diretorio novo.
O MCR-DevIA NUNCA viu esses arquivos.
Ele precisa DETECTAR, DIAGNOSTICAR e CORRIGIR sozinho.
"""

import os, random

BASE = r'E:\Projeto MCR\sandbox\teste_cego'
os.makedirs(BASE, exist_ok=True)
os.makedirs(os.path.join(BASE, 'npc'), exist_ok=True)
os.makedirs(os.path.join(BASE, 'monster'), exist_ok=True)
os.makedirs(os.path.join(BASE, 'item'), exist_ok=True)

# GABARITO (secreto)
gabarito = []
i = 0

# Problema 1: NPC com nome inconsistente (MaiusculoMinusculo)
i += 1
with open(os.path.join(BASE, 'npc', 'MERCADOR_VIAGEM.lua'), 'w') as f:
    f.write('-- NPC: MERCADOR_VIAGEM\nlocal npc = NPC("Mercador")\nnpc:setSaudacao("Bom dia!")\nnpc:addItem(101, 50)\n')
gabarito.append(f'{i}. MERCADOR_VIAGEM.lua: nome inconsistente (maiusculas vs CamelCase)')

# Problema 2: Monster com HP negativo
i += 1
with open(os.path.join(BASE, 'monster', 'goblin_fraco.lua'), 'w') as f:
    f.write('-- Monster: Goblin Fraco\nlocal m = Monster("GoblinFraco")\nm:setHealth(-50)\nm:setAttack(5)\nm:addLoot(101, 0.3)\n')
gabarito.append(f'{i}. goblin_fraco.lua: HP negativo (-50)')

# Problema 3: Item com ID duplicado
i += 1
with open(os.path.join(BASE, 'item', 'pocao_mana.lua'), 'w') as f:
    f.write('-- Item: Pocao de Mana\nlocal item = Item(101, "Pocao de Mana")\nitem:setType("consumable")\n')
gabarito.append(f'{i}. pocao_mana.lua: ID 101 ja usado pelo NPC (possivel duplicata)')

# Problema 4: NPC com funcao que não existe no Canary
i += 1
with open(os.path.join(BASE, 'npc', 'mago.lua'), 'w') as f:
    f.write('-- NPC: Mago\nlocal npc = NPC("Mago")\nnpc:setSaudacao("Ola!")\nnpc:setMana(500)\nnpc:setMagicLevel(20)\nnpc:addItem(102, 100)\n')
gabarito.append(f'{i}. mago.lua: funcoes setMana/setMagicLevel nao existem em NPC')

# Problema 5: Monster com loot vazio (sem addLoot)
i += 1
with open(os.path.join(BASE, 'monster', 'slime.lua'), 'w') as f:
    f.write('-- Monster: Slime\nlocal m = Monster("Slime")\nm:setHealth(50)\nm:setAttack(2)\nm:setDefense(1)\n')
gabarito.append(f'{i}. slime.lua: monstro sem loot (addLoot ausente)')

# Problema 6: Arquivo com BOM (Byte Order Mark) simulado
i += 1
with open(os.path.join(BASE, 'item', 'item_especial.lua'), 'wb') as f:
    f.write(b'\xef\xbb\xbf-- Item: Especial\nlocal item = Item(103, "Especial")\nitem:setType("quest")\n')
gabarito.append(f'{i}. item_especial.lua: arquivo com BOM (Byte Order Mark)')

# Problema 7: NPC com saida padrao
i += 1
with open(os.path.join(BASE, 'npc', 'sem_saudacao.lua'), 'w') as f:
    f.write('-- NPC: Quieto\nlocal npc = NPC("Quieto")\nnpc:setAdeus("Tchau.")\nnpc:addItem(104, 25)\n')
gabarito.append(f'{i}. sem_saudacao.lua: NPC sem setSaudacao')

# Problema 8: Código identado com tabs (violacao de estilo)
i += 1
with open(os.path.join(BASE, 'monster', 'demonio.lua'), 'w') as f:
    f.write("-- Monster: Demonio\nlocal m = Monster(\"Demonio\")\n\tm:setHealth(9999)\n\tm:setAttack(999)\nm:addLoot(105, 0.1)\n")
gabarito.append(f'{i}. demonio.lua: indentacao mista (tabs + espacos)')

# Salva gabarito
with open(os.path.join(BASE, '.GABARITO.txt'), 'w') as f:
    f.write('TESTE CEGO - GABARITO\n')
    f.write('='*50 + '\n')
    for g in gabarito:
        f.write(g + '\n')
    f.write('='*50 + '\n')

print(f'=== TESTE CEGO CRIADO ===')
print(f'{len(gabarito)} problemas novos em: {BASE}')
print()
print(f'Problemas:')
for g in gabarito:
    print(f'  {g}')
print()
print(f'Gabarito em: {os.path.join(BASE, ".GABARITO.txt")}')
print()
print('Agora rode o MCR-DevIA apontando pra este diretorio')
print('e veja se ele detecta e corrige TUDO sozinho.')
