-- CRU: Boss — Guardiao Subterraneo
local mon = Monster("Guardiao Subterraneo")
mon:setHealth(1000)
mon:setAttack(50)
mon:setDefense(20)
mon:setExperience(1000)
mon:setType("boss")
mon:addLoot(41003, 1.0) -- Coracao da Terra
mon:addLoot(41004, 0.8) -- Amuleto do Heroi (recompensa)
mon:addLoot(40001, 0.6)
mon:addLoot(40003, 0.3) -- Pocao de experiencia
print("Monster Guardiao Subterraneo carregado.")
