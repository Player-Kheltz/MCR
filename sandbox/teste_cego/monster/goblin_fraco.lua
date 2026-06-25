-- Monster: Goblin Fraco
local m = Monster("GoblinFraco")
m:setHealth(50) -- Correção: HP não pode ser negativo
m:setAttack(5)
m:addLoot(101, 0.3)