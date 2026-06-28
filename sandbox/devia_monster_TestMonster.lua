-- monster: TestMonster
local monster = Monster("TestMonster")

function setSpeed(speed)
    monster:setSpeed(speed)
end

function setOutfit(outfit)
    monster:setOutfit(outfit)
end

function setMaster(master)
    monster:setMaster(master)
end

function setMaxHealth(maxHealth)
    monster:setMaxHealth(maxHealth)
end

function addHealth(health)
    monster:addHealth(health)
end

function setCustomName(customName)
    monster:setCustomName(customName)
end

function setDropLoot(dropLoot)
    monster:setDropLoot(dropLoot)
end

function setPetBehavior(petBehavior)
    monster:setPetBehavior(petBehavior)
end

print("monster TestMonster carregado.")