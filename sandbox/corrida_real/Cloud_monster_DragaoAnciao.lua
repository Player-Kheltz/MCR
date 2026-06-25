-- Monster: DragaoAnciao — Completo
-- Gerado pelo Cloud
local mon = Monster("DragaoAnciao")

-- Stats
mon:setHealth(2000)
mon:setMaxHealth(2000)
mon:setAttack(85)
mon:setDefense(40)
mon:setExperience(1000)
mon:setLevel(20)
mon:setSpeed(80)
mon:setArmor(20)

-- Elementos
mon:setElement(COMBAT_FIREDAMAGE)
mon:setWeakness(COMBAT_ICEDAMAGE, 1.5)
mon:setResistance(COMBAT_PHYSICALDAMAGE, 0.8)

-- Comportamento
mon:setBehavior("aggressive")
mon:setAggression(0.8)
mon:setFleeThreshold(0.1)
mon:setSpawnTime(60)
mon:setTargetDistance(4)

-- Loot table (multiplos itens)
mon:addLoot(6001, 0.9)
mon:addLoot(6002, 0.45)
mon:addLoot(6003, 0.27)
mon:addLoot(6004, 0.09000000000000001)

-- Habilidades
mon:addSpell(2001, 0.3)
mon:addSpell(2002, 0.1)
mon:addSpell(2003, 0.05)

-- Visual
mon:setOutfit( Mention(35, 0, 0, 0, 0) )
mon:setCorpse(6080)

print("Monster DragaoAnciao carregado.")