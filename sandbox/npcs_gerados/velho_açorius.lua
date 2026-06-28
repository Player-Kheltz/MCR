local internalNpcName = "Velho Açorius"
local npcType = Game.createNpcType(internalNpcName)
local npcConfig = {}

npcConfig.name = internalNpcName
npcConfig.description = "Quest NPC - Velho Açorius"

npcConfig.health = 100
npcConfig.maxHealth = npcConfig.health
npcConfig.walkInterval = 2000
npcConfig.walkRadius = 2

npcConfig.outfit = {
    lookType = 130,
    lookHead = 57,
    lookBody = 116,
    lookLegs = 97,
    lookFeet = 114,
    lookAddons = 0,
}

npcConfig.flags = {
    floorchange = false,
}



-- On buy npc shop message
npcType.onBuyItem = function(npc, player, itemId, subType, amount, ignore, inBackpacks, totalCost)
    npc:sellItem(player, itemId, amount, subType, 0, ignore, inBackpacks)
end
-- On sell npc shop message
npcType.onSellItem = function(npc, player, itemId, subtype, amount, ignore, name, totalCost)
    player:sendTextMessage(MESSAGE_TRADE, string.format("Sold %ix %s for %i gold.", amount, name, totalCost))
end
-- On check npc shop message (look item)
npcType.onCheckItem = function(npc, player, clientId, subType) end

local keywordHandler = KeywordHandler:new()
local npcHandler = NpcHandler:new(keywordHandler)

npcType.onThink = function(npc, interval)
    npcHandler:onThink(npc, interval)
end

npcType.onAppear = function(npc, creature)
    npcHandler:onAppear(npc, creature)
end

npcType.onDisappear = function(npc, creature)
    npcHandler:onDisappear(npc, creature)
end

npcType.onMove = function(npc, creature, fromPosition, toPosition)
    npcHandler:onMove(npc, creature, fromPosition, toPosition)
end

npcType.onSay = function(npc, creature, type, message)
    npcHandler:onSay(npc, creature, type, message)
end

npcType.onCloseChannel = function(npc, creature)
    npcHandler:onCloseChannel(npc, creature)
end

local function creatureSayCallback(npc, creature, type, message)
    local player = Player(creature)
    local playerId = player:getId()

    if not npcHandler:checkInteraction(npc, creature) then
        return false
    end

    if MsgContains(message, "mission") or MsgContains(message, "quest") then
        if player:getStorageValue(Storage.Quest.Custom.VELHOAÇORIUS) < 1 then
            npcHandler:say("I need your help!", npc, creature)
            npcHandler:setTopic(playerId, 1)
        else
            npcHandler:say("Have you completed the task yet?", npc, creature)
            npcHandler:setTopic(playerId, 2)
        end
    elseif MsgContains(message, "yes") then
        if npcHandler:getTopic(playerId) == 1 then
            player:setStorageValue(Storage.Quest.Custom.VELHOAÇORIUS, 1)
            npcHandler:say("Thank you! Now go and complete the task.", npc, creature)
            npcHandler:setTopic(playerId, 0)
        elseif npcHandler:getTopic(playerId) == 2 then
            if player:getItemCount(3031) >= 1 then
                player:removeItem(3031, 1)
                player:addItem(3031, 1) -- TODO: ajustar reward
                player:setStorageValue(Storage.Quest.Custom.VELHOAÇORIUS, 2)
                npcHandler:say("Well done! Here is your reward.", npc, creature)
            else
                npcHandler:say("You still need to bring me the required item.", npc, creature)
            end
            npcHandler:setTopic(playerId, 0)
        end
    end

    return true
end

npcHandler:setCallback(CALLBACK_MESSAGE_DEFAULT, creatureSayCallback)


npcHandler:setMessage(MESSAGE_GREET, "Greetings, adventurer! Are you looking for a {quest_term}?")

npcHandler:setCallback(CALLBACK_MESSAGE_DEFAULT, creatureSayCallback)

npcHandler:addModule(FocusModule:new(), npcConfig.name, true, true, true)

npcType:register(npcConfig)
