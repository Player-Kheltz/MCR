#!/usr/bin/env python3
"""
TESTE CEGO ULTRA — Erros dificeis de identificar
==================================================
Problemas sutis que um programador experiente levaria minutos pra achar.
Cryptic errors, race conditions, logic bugs, encoding issues, etc.
"""

import os

BASE = r'E:\Projeto MCR\sandbox\teste_cego_ultra'
os.makedirs(BASE, exist_ok=True)

i = 0
gabarito = []

# 1. Off-by-one em loot (chance 1.0 = 100%, mas 1.01 invalida)
i += 1
with open(os.path.join(BASE, 'monster_boss.lua'), 'w') as f:
    f.write('-- Boss final\nlocal m = Monster("Boss")\nm:setHealth(5000)\nm:addLoot(101, 0.5)\nm:addLoot(102, 0.3)\nm:addLoot(103, 1.01)\n')
gabarito.append(f'{i}. monster_boss.lua: loot chance = 1.01 (invalido, max 1.0)')

# 2. Variavel global sem declaracao (polui escopo)
i += 1
with open(os.path.join(BASE, 'util_calculo.lua'), 'w') as f:
    f.write('-- Util de calculo\nfunction calcularBonus(nivel)\n    bonus = nivel * 2  -- falta 'local'\n    return bonus\nend\n')
gabarito.append(f'{i}. util_calculo.lua: variavel global 'bonus' sem declaracao local')

# 3. Comparacao de string com numero (always false)
i += 1
with open(os.path.join(BASE, 'verificar_item.lua'), 'w') as f:
    f.write('-- Verificador de item\nfunction podeUsar(item)\n    if item.id == "123" then  -- string vs number\n        return true\n    end\n    return false\nend\n')
gabarito.append(f'{i}. verificar_item.lua: comparacao string == number (sempre false)')

# 4. Divisao por zero potencial
i += 1
with open(os.path.join(BASE, 'calcular_dano.lua'), 'w') as f:
    f.write('-- Calculo de dano\nfunction danoFinal(atk, def)\n    return atk / (def - 10)  -- divisao por zero se def = 10\nend\n')
gabarito.append(f'{i}. calcular_dano.lua: divisao por zero potencial (def - 10)')

# 5. Arquivo com nome extremamente longo (Windows path limit)
i += 1
with open(os.path.join(BASE, 'item_raro_edicao_limitada_suprema_hyper_ultra_mega_blaster_plus_pro_max_ultimate_2026_edicao_especial.lua'), 'w') as f:
    f.write('-- Item raro\nlocal item = Item(999, "Item")\n')
gabarito.append(f'{i}. item_nome_longo.lua: nome de arquivo excessivamente longo')

# 6. Heranca mal feita (tabela com metatable quebrada)
i += 1
with open(os.path.join(BASE, 'npc_especial.lua'), 'w') as f:
    f.write('-- NPC Especial\nlocal npc = NPC("Especial")\nnpc:setSaudacao("Ola!")\nsetmetatable(npc, {})  -- sobrescreve metatable padrao\n')
gabarito.append(f'{i}. npc_especial.lua: setmetatable sobrescreve metatable do NPC')

# 7. Encoding Latin-1 vs UTF-8 (caractere acentuado corrompido)
i += 1
with open(os.path.join(BASE, 'npc_acentos.lua'), 'w', encoding='latin-1') as f:
    f.write('-- NPC: S\xe1bio\nlocal npc = NPC("S\xe1bio")\nnpc:setSaudacao("Ol\xe1!")\n')
gabarito.append(f'{i}. npc_acentos.lua: encoding Latin-1 em vez de UTF-8 (acentos corrompidos)')

# 8. Codigo morto apos return
i += 1
with open(os.path.join(BASE, 'funcao_otimizada.lua'), 'w') as f:
    f.write('-- Funcao\nfunction calcular(x)\n    return x * 2\n    local y = x * 3  -- codigo morto\n    y = y + 1\nend\n')
gabarito.append(f'{i}. funcao_otimizada.lua: codigo morto apos return')

# 9. Tabela com chave string vs numero (confusao)
i += 1
with open(os.path.join(BASE, 'config_monstros.lua'), 'w') as f:
    f.write('-- Config\nlocal config = {\n    [1] = "Goblin",\n    ["1"] = "Dragão",  -- string "1" vs number 1\n}\n')
gabarito.append(f'{i}. config_monstros.lua: chave "1" (string) vs 1 (numero) - confusao')

# 10. Loop infinito potencial
i += 1
with open(os.path.join(BASE, 'buscar_item.lua'), 'w') as f:
    f.write('-- Busca\nfunction buscarItem(player, id)\n    while true do\n        local item = player:getItem(id)\n        if item then return item end\n        -- sem contador, sem break, loop infinito se item nao for encontrado\n    end\nend\n')
gabarito.append(f'{i}. buscar_item.lua: loop infinito (while true sem saida)')

# 11. SQL injection potencial
i += 1
with open(os.path.join(BASE, 'db_query.lua'), 'w') as f:
    f.write('-- DB\nfunction buscarPlayer(nome)\n    db.query("SELECT * FROM players WHERE name = \'" .. nome .. "\'")  -- SQL injection\nend\n')
gabarito.append(f'{i}. db_query.lua: SQL injection potencial (concatenacao de string)')

# 12. Memset/zero init esquecido (tabela com nil)
i += 1
with open(os.path.join(BASE, 'criar_pocao.lua'), 'w') as f:
    f.write('-- Criar pocao\nfunction criarPocao(tipo)\n    local p = {}\n    p.tipo = tipo\n    p.efeito = nil  -- explicitamente nil (desnecessario)\n    return p\nend\n')
gabarito.append(f'{i}. criar_pocao.lua: campo explicitamente nil (desnecessario, mas nao e erro grave)')

# Salva gabarito
with open(os.path.join(BASE, '.GABARITO.txt'), 'w') as f:
    f.write('TESTE CEGO ULTRA - GABARITO\n')
    f.write('='*60 + '\n')
    for g in gabarito:
        f.write(g + '\n')
    f.write('='*60 + '\n')

print(f'=== TESTE CEGO ULTRA CRIADO ===')
print(f'{len(gabarito)} problemas COMPLEXOS em: {BASE}')
print()
for g in gabarito:
    print(f'  {g}')
print()
print('Agora escaneando com MCR-DevIA...')
