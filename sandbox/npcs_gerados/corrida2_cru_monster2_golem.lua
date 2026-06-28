-- CRU: Monster — Golem de Pedra (guarda a Chama)
local mon = Monster("Golem de Pedra")
mon:setHealth(500)
mon:setAttack(25)
mon:setDefense(30)
mon:setExperience(350)
mon:setType("construct")
mon:addLoot(41002, 1.0) -- Chama da Sabedoria
mon:addLoot(40002, 0.4) -- Pocao de mana
mon:addLoot(40001, 0.3) -- Pocao de cura
mon:setWeakness("ice")
print("Monster Golem de Pedra carregado.")
