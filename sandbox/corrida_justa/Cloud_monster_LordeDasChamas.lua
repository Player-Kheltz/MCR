-- Monster: Lorde das Chamas — Completo
-- Gerado pelo Cloud via python + write

local mon = Monster("Lorde das Chamas")

-- Stats base
mon:setHealth(3500)
mon:setMaxHealth(3500)
mon:setAttack(120)
mon:setDefense(50)
mon:setExperience(1800)
mon:setLevel(75)
mon:setSpeed(90)
mon:setArmor(25)

-- Elementos
mon:setElement(COMBAT_FIREDAMAGE)
mon:setWeakness(COMBAT_ICEDAMAGE, 1.5)
mon:setWeakness(COMBAT_ENERGYDAMAGE, 1.2)
mon:setResistance(COMBAT_FIREDAMAGE, 0.3)
mon:setResistance(COMBAT_PHYSICALDAMAGE, 0.7)

-- Comportamento
mon:setBehavior("aggressive")
mon:setAggression(0.9)
mon:setFleeThreshold(0.05)
mon:setSpawnTime(120)
mon:setTargetDistance(3)
mon:setAttackSpeed(2000)

-- Loot table (5 itens)
mon:addLoot(6501, 0.9)  -- Chama Eterna (sempre)
mon:addLoot(6502, 0.6)  -- Cinzas do Lorde
mon:addLoot(6503, 0.4)  -- Fragmento Igneo
mon:addLoot(6504, 0.2)  -- Coracao de Fogo
mon:addLoot(6505, 0.05) -- Essencia do Lorde (raro)

-- Habilidades
mon:addSpell(3001, 0.4)  -- Bola de Fogo
mon:addSpell(3002, 0.3)  -- Escudo de Chamas
mon:addSpell(3003, 0.15) -- Erupcao (ultimate)
mon:addSpell(3004, 0.1)  -- Meteoro (boss only)

-- Visual
mon:setOutfit({ lookType = 35, lookHead = 0, lookBody = 94, lookLegs = 76, lookFeet = 0 })
mon:setCorpse(6081)
mon:setSummonCost(0)

print("Monster Lorde das Chamas carregado.")