--- CANARY MONSTER TEMPLATE — API 100% real do servidor
--- PROIBIDO usar Game.createMonster() para definir monstros. Use Game.createMonsterType().
--- PROIBIDO usar classes como Quest(). Use Action() e monsterConfig.

--- ARQUIVO: goblin_chefe.lua ---
-- Monstro customizado do Canary
local internalMonsterName = "Goblin Chefe"
local monsterType = Game.createMonsterType(internalMonsterName)
local monsterConfig = {}

monsterConfig.name = internalMonsterName
monsterConfig.description = "Um goblin maior e mais forte."
monsterConfig.maxHealth = 5000
monsterConfig.health = 5000
monsterConfig.experience = 2000
monsterConfig.outfit = { lookType = 61 }

monsterConfig.flags = { attackable = true, hostile = true, rewardBoss = false }

-- Loot Table
monsterConfig.dropList = {
    { id = 2160, chance = 100000, maxCount = 5 },
}

monsterType:register(monsterConfig)

--- ARQUIVO: action_spawn_goblins.lua ---
-- Action que invoca monstros (Canary)
local invasionAction = Action()

function invasionAction.onUse(player, item, fromPosition, target, toPosition, isHotkey)
    if item:getId() == 1732 then
        player:sendTextMessage(MESSAGE_EVENT_ADVANCE, "A invasao comecou!")
        local pos = player:getPosition()
        for i = 1, 10 do
            local monster = Game.createMonster("Goblin", pos, false, true, 0)
            if monster then
                monster:setTarget(player)
            end
        end
        Game.createMonster("Goblin Chefe", pos, false, true, 0)
        return true
    end
    return false
end

invasionAction:uid(6000)
invasionAction:register()
