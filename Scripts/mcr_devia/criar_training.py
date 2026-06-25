#!/usr/bin/env python3
"""
TRAINING GROUND — Projeto MCR Falso com Problemas
===================================================
Um campo de treinamento para o MCR-DevIA aprender a:
  - Detectar erros de sintaxe
  - Identificar funcoes faltando
  - Corrigir templates desatualizados
  - Perceber inconsistencias
  - E VOLTAR para contar o que aprendeu

Cada arquivo tem problemas OCULTOS. O MCR-DevIA precisa
encontrar, diagnosticar e corrigir.
"""

import os

BASE = r'E:\Projeto MCR\sandbox\training_ground'
os.makedirs(BASE, exist_ok=True)
os.makedirs(os.path.join(BASE, 'scripts', 'npc'), exist_ok=True)
os.makedirs(os.path.join(BASE, 'scripts', 'monster'), exist_ok=True)
os.makedirs(os.path.join(BASE, 'scripts', 'item'), exist_ok=True)

PROBLEMAS = []

# ============================================================
# PROBLEMA 1: NPC com chaves desbalanceadas
# ============================================================
p1 = '''-- NPC: Ferreiro
local npc = NPC("Ferreiro")
npc:setSaudacao("Bem-vindo!")
npc:addItem(101, 50)
npc:addItem(102, 100
npc:setQuest("ajude o ferreiro")
-- NOTA: O npc:addItem(102, 100 esta sem fechar parenteses
print("NPC Ferreiro carregado.")
'''
with open(os.path.join(BASE, 'scripts', 'npc', 'ferreiro.lua'), 'w', encoding='utf-8') as f:
    f.write(p1)
PROBLEMAS.append('NPC ferreiro.lua: parenteses desbalanceados')

# ============================================================
# PROBLEMA 2: Monster com funcao inexistente
# ============================================================
p2 = '''-- Monster: Dragao
local mon = Monster("Dragao")
mon:setHealth(500)
mon:setAttack(50)
mon:setDefense(25)
mon:setInvisibility(true)  -- FUNCAO NAO EXISTE no template!
mon:setFlyMode(true)       -- FUNCAO NAO EXISTE no template!
mon:addLoot(201, 0.5)
print("Monster Dragao carregado.")
'''
with open(os.path.join(BASE, 'scripts', 'monster', 'dragao.lua'), 'w', encoding='utf-8') as f:
    f.write(p2)
PROBLEMAS.append('Monster dragao.lua: funcoes inexistentes (setInvisibility, setFlyMode)')

# ============================================================
# PROBLEMA 3: Item com template antigo (setAttack/setDefense em vez de setAttribute)
# ============================================================
p3 = '''-- Item: Espada Magica
local item = Item(3001, "Espada Magica")
item:setType("weapon")
item:setAttack(50)     -- TEMPLATE ANTIGO! MCR usa setAttribute
item:setDefense(20)    -- TEMPLATE ANTIGO! MCR usa setAttribute
item:setWeight(30)
print("Item Espada Magica carregado.")
'''
with open(os.path.join(BASE, 'scripts', 'item', 'espada_magica.lua'), 'w', encoding='utf-8') as f:
    f.write(p3)
PROBLEMAS.append('Item espada_magica.lua: usa setAttack (antigo) em vez de setAttribute')

# ============================================================
# PROBLEMA 4: NPC com dialogo quebrado (falta fechar tabela)
# ============================================================
p4 = '''-- NPC: Guarda
local npc = NPC("Guarda")
npc:setSaudacao("Pare! Identifique-se.")

npc:addDialog("quest", {
    {"O que faz aqui?", "Patrulho a cidade."},
    {"Posso passar?", "So se tiver permissao."},
    {"Tenho permissao", "Entao pode passar."},
    -- NOTA: tabela de dialogo nao foi fechada corretamente

print("NPC Guarda carregado.")
'''
with open(os.path.join(BASE, 'scripts', 'npc', 'guarda.lua'), 'w', encoding='utf-8') as f:
    f.write(p4)
PROBLEMAS.append('NPC guarda.lua: tabela de dialogo nao fechada')

# ============================================================
# PROBLEMA 5: Monster com loot desbalanceado (chance > 1.0)
# ============================================================
p5 = '''-- Monster: Boss Final
local mon = Monster("Boss Final")
mon:setHealth(5000)
mon:setAttack(200)
mon:setDefense(100)
mon:addLoot(901, 2.5)    -- ERRO: chance > 1.0 (maximo 100% = 1.0)
mon:addLoot(902, 0.5)
mon:addLoot(903, 0.3)
print("Monster Boss Final carregado.")
'''
with open(os.path.join(BASE, 'scripts', 'monster', 'boss_final.lua'), 'w', encoding='utf-8') as f:
    f.write(p5)
PROBLEMAS.append('Monster boss_final.lua: loot_chance = 2.5 (invalido, max 1.0)')

# ============================================================
# PROBLEMA 6: .cpp com sintaxe errada
# ============================================================
p6 = '''// Funcao de calculo de dano
#include <iostream>
using namespace std;

int calcularDano(int nivel, int forca) {
    return (nivel * forca) / 10
}  // FALTA PONTO E VIRGULA no return
'''
with open(os.path.join(BASE, 'calcular_dano.cpp'), 'w', encoding='utf-8') as f:
    f.write(p6)
PROBLEMAS.append('calcular_dano.cpp: falta ponto e virgula no return')

# ============================================================
# PROBLEMA 7: Lua com codigo morto (variavel nao usada)
# ============================================================
p7 = '''-- Script auxiliar
local function calcularBonus(nivel)
    local temp = nivel * 2  -- variavel temp nunca usada
    return nivel + 5
end

local xp = calcularBonus(10)
local y = 42  -- variavel y nunca usada
print("XP calculado: " .. xp)
'''
with open(os.path.join(BASE, 'scripts', 'calcular_bonus.lua'), 'w', encoding='utf-8') as f:
    f.write(p7)
PROBLEMAS.append('calcular_bonus.lua: variaveis nao utilizadas (temp, y)')

# ============================================================
# PROBLEMA 8: Arquivo com nome inconsistente (fora do padrao)
# ============================================================
p8 = '''-- Item especial (fora de pasta)
local item = Item(9999, "Item Secreto")
item:setType("quest")
print("Item secreto carregado.")
'''
with open(os.path.join(BASE, 'ITEM_SECRETO_v2_FINAL.lua'), 'w', encoding='utf-8') as f:
    f.write(p8)
PROBLEMAS.append('ITEM_SECRETO_v2_FINAL.lua: nome fora do padrao (maiusculas, sufixos)')

# ============================================================
# RELATORIO
# ============================================================
print('='*60)
print('  TRAINING GROUND CRIADO!')
print(f'  {len(PROBLEMAS)} problemas escondidos')
print('='*60)
for i, p in enumerate(PROBLEMAS, 1):
    print(f'  {i}. {p}')
print()
print(f'  Diretorio: {BASE}')
print()
print('  Agora execute o MCR-DevIA apontando pra ca:')
print(f'  python sandbox/mcr_loop.py --dir {BASE}')
print('  Ou apenas clique no atalho da area de trabalho')
print('  e veja se ele detecta os problemas.')
print('='*60)

# Salva gabarito
gabarito_path = os.path.join(BASE, '.GABARITO.txt')
with open(gabarito_path, 'w', encoding='utf-8') as f:
    f.write('GABARITO - Problemas no Training Ground\n')
    f.write('='*50 + '\n')
    for i, p in enumerate(PROBLEMAS, 1):
        f.write(f'{i}. {p}\n')
    f.write('='*50 + '\n')
    f.write('O MCR-DevIA deve encontrar e diagnosticar cada um.\n')
print(f'Gabarito salvo em: {gabarito_path}')
