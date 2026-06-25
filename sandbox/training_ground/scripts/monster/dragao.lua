-- Monster: Dragao
local mon = Monster("Dragao")
mon:setHealth(500)
mon:setAttack(50)
mon:setDefense(25)
mon:setInvisibility(false)  -- FUNCAO ALTERADA para setInvisibility
mon:setFlyMode(true)     -- FUNCAO ALTERADA para setFlyMode
mon:addLoot(201, 0.5)
print("Monster Dragao carregado.")