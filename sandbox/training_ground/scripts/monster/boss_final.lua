-- Monster: Boss Final
local mon = Monster("Boss Final")
mon:setHealth(5000)
mon:setAttack(200)
mon:setDefense(100)
mon:addLoot(901, 1.0)    -- Correção: chance ajustada para 1.0 (100%)
mon:addLoot(902, 0.5)
mon:addLoot(903, 0.3)
print("Monster Boss Final carregado.")