"""Nivel 1: Cenarios simples para o MCR-DevIA aprender"""
import os, subprocess

BASE = r'E:\Projeto MCR\sandbox\training_nivel1'
os.makedirs(BASE, exist_ok=True)

# 3 arquivos, 1 erro obvio cada
arquivos = {
    'npc_simples.lua': '-- NPC: Joao\nlocal n = NPC("Joao"\nn:setSaudacao("Ola")\nn:addItem(101, 50)\n',
    'monster_teste.lua': '-- Monster: Teste\nlocal m = Monster("Teste")\nm:setHealth("cem")\nm:setAttack(30)\nm:addLoot(201, 0.5)\n',
    'item_sem_tipo.lua': '-- Item: SemTipo\nlocal i = Item(999, "SemTipo")\ni:setWeight(10)\n',
}

for nome, conteudo in arquivos.items():
    with open(os.path.join(BASE, nome), 'w') as f:
        f.write(conteudo)

print(f'Nivel 1: {len(arquivos)} arquivos criados')
for nome in arquivos:
    print(f'  - {nome}')

# Detectar com o que ja temos: usar o scanner existente
print('\nEscaneando com MCR-DevIA...')
r = subprocess.run(
    ['python', 'E:/Projeto MCR/sandbox/resolver_ultra.py'],
    capture_output=True, text=True, timeout=30
)
# Adaptar: mudar BASE no scanner...
# Na verdade, vamos criar um scanner proprio pra esse nivel
print('Scanner existente precisa de adaptacao. Criando scanner local...')
