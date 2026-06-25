"""Fix string quoting in criar_teste_cego_ultra"""
import os

BASE = r'E:\Projeto MCR\sandbox\teste_cego_ultra'
os.makedirs(BASE, exist_ok=True)

gabarito = []

# 1. Loot chance > 1.0
i = 1
with open(os.path.join(BASE, 'monster_boss.lua'), 'w') as f:
    f.write('-- Boss final\nlocal m = Monster("Boss")\nm:setHealth(5000)\nm:addLoot(101, 0.5)\nm:addLoot(102, 0.3)\nm:addLoot(103, 1.01)\n')
gabarito.append(f'{i}. monster_boss.lua: loot chance = 1.01 (invalido, max 1.0)')

# 2. Variavel global
i += 1
with open(os.path.join(BASE, 'util_calculo.lua'), 'w') as f:
    f.write('-- Util de calculo\nfunction calcularBonus(nivel)\n    bonus = nivel * 2\n    return bonus\nend\n')
gabarito.append(f'{i}. util_calculo.lua: variavel global bonus sem local')

# 3. Comparacao string vs number
i += 1
with open(os.path.join(BASE, 'verificar_item.lua'), 'w') as f:
    f.write('-- Verificador\ndef verificar(item):\n    if item["id"] == 123:\n        return True\n    return False\n')
gabarito.append(f'{i}. verificar_item.lua: Python com sintaxe misturada')

# 4. Divisao por zero
i += 1
with open(os.path.join(BASE, 'calcular_dano.lua'), 'w') as f:
    f.write('-- Calculo de dano\nfunction danoFinal(atk, def)\n    return atk / (def - 10)\nend\n')
gabarito.append(f'{i}. calcular_dano.lua: divisao por zero potencial')

# 5. Nome longo
i += 1
with open(os.path.join(BASE, 'item_edicao_limitada_suprema_hyper_ultra_mega_blaster_plus_pro_max_ultimate.lua'), 'w') as f:
    f.write('-- Item\nlocal item = Item(999, "Item")\n')
gabarito.append(f'{i}. item_nome_longo.lua: nome excessivamente longo')

# 6. Metatable quebrada
i += 1
with open(os.path.join(BASE, 'npc_especial.lua'), 'w') as f:
    f.write('-- NPC Especial\nlocal npc = NPC("Especial")\nnpc:setSaudacao("Ola!")\nsetmetatable(npc, {})\n')
gabarito.append(f'{i}. npc_especial.lua: setmetatable sobrescreve metatable')

# 7. Encoding latin-1
i += 1
with open(os.path.join(BASE, 'npc_acentos.lua'), 'w', encoding='latin-1') as f:
    f.write('-- NPC: Sabio\nlocal npc = NPC("Sabio")\nnpc:setSaudacao("Ola!")\n')
gabarito.append(f'{i}. npc_acentos.lua: encoding Latin-1 em vez de UTF-8')

# 8. Codigo morto apos return
i += 1
with open(os.path.join(BASE, 'funcao_otimizada.lua'), 'w') as f:
    f.write('-- Funcao\nfunction calcular(x)\n    return x * 2\n    local y = x * 3\n    y = y + 1\nend\n')
gabarito.append(f'{i}. funcao_otimizada.lua: codigo morto apos return')

# 9. Tabela com chave confusa
i += 1
with open(os.path.join(BASE, 'config_monstros.lua'), 'w') as f:
    f.write('-- Config\nlocal config = {}\nconfig[1] = "Goblin"\nconfig["1"] = "Dragao"\n')
gabarito.append(f'{i}. config_monstros.lua: chave string 1 vs numero 1')

# 10. Loop infinito
i += 1
with open(os.path.join(BASE, 'buscar_item.lua'), 'w') as f:
    f.write('-- Busca\nfunction buscarItem(player, id)\n    while true do\n        local item = player:getItem(id)\n        if item then return item end\n    end\nend\n')
gabarito.append(f'{i}. buscar_item.lua: loop infinito sem saida')

# 11. SQL injection
i += 1
with open(os.path.join(BASE, 'db_query.lua'), 'w') as f:
    f.write('-- DB\nfunction buscarPlayer(nome)\n    db.query("SELECT * FROM players WHERE name = \'" .. nome .. "\'")\nend\n')
gabarito.append(f'{i}. db_query.lua: SQL injection potencial')

# 12. Nil desnecessario
i += 1
with open(os.path.join(BASE, 'criar_pocao.lua'), 'w') as f:
    f.write('-- Pocao\nfunction criarPocao(tipo)\n    local p = {}\n    p.tipo = tipo\n    p.efeito = nil\n    return p\nend\n')
gabarito.append(f'{i}. criar_pocao.lua: campo nil desnecessario')

with open(os.path.join(BASE, '.GABARITO.txt'), 'w') as f:
    f.write('TESTE CEGO ULTRA - GABARITO\n')
    for g in gabarito:
        f.write(g + '\n')

print(f'=== TESTE CEGO ULTRA: {len(gabarito)} problemas complexos ===')
for g in gabarito:
    print(f'  {g}')
