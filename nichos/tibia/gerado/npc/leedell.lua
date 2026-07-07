local internalNpcName = "Lee'Dell"
local npcType = Game.createNpcType(internalNpcName)
local npcConfig = {}

npcConfig.name = internalNpcName
npcConfig.description = internalNpcName

npcConfig.health = 100
npcConfig.maxHealth = npcConfig.health
npcConfig.walkInterval = 2000
npcConfig.walkRadius = 2

npcConfig.outfit = {
	lookType = 277,
	lookHead = 58,
	lookBody = 43,
	lookLegs = 38,
	lookFeet = 76,
	lookAddons = 0,

}

npcConfig.flags = {
	floorchange = false,
}

npcConfig.voices = {
	interval = 10000,
	chance = 40,
	{text = "DID IF I will make the vanilla sugar balls ... is miiiiine!"},
	{text = "in a new time the wind of my magic, tiny mortal! This"},
}

npcConfig.shop = {
	{itemName = "cruelty's claw", clientId = 33922, buy = 178, sell = 640000},
	{itemName = "label", clientId = 3507, buy = 1},
	{itemName = "ogre nose ring", clientId = 22189, buy = 386, sell = 210},

}

npcType.onBuyItem = function(npc, player, itemId, subType, amount, ignore, inBackpacks, totalCost)
	npc:sellItem(player, itemId, amount, subType, 0, ignore, inBackpacks)
end
npcType.onSellItem = function(npc, player, itemId, subtype, amount, ignore, name, totalCost)
	player:sendTextMessage(MESSAGE_TRADE, string.format("Sold %%ix %%s for %%i gold.", amount, name, totalCost))
end
npcType.onCheckItem = function(npc, player, clientId, subType) end

local keywordHandler = KeywordHandler:new()
local npcHandler = NpcHandler:new(keywordHandler)

keywordHandler:addKeyword({"equipment"}, StdModule.say, {npcHandler = npcHandler, text = "nobody else. Or to bring me for the things and help me,"})

keywordHandler:addKeyword({"ship"}, StdModule.say, {npcHandler = npcHandler, text = "On the bank. Hehe. Great customers."})

npcType.onThink = function(npc, interval)
	npcHandler:onThink(npc, interval)
end

npcType.onAppear = function(npc, creature)
	npcHandler:onAppear(npc, creature)
end

npcType.onDisappear = function(npc, creature)
	npcHandler:onDisappear(npc, creature)
end

npcType.onSay = function(npc, creature, type, message)
	npcHandler:onSay(npc, creature, type, message)
end

npcType.onCloseChannel = function(npc, creature)
	npcHandler:onCloseChannel(npc, creature)
end

npcHandler:setMessage(MESSAGE_GREET, "mother earth protect us if you'd enjoy your path always")
npcHandler:setMessage(MESSAGE_FAREWELL, "gold? Just ask me alone with another disturbance.")
npcHandler:setMessage(MESSAGE_WALKAWAY, "Great Znake forgive me for")

npcHandler:addModule(FocusModule:new(), npcConfig.name, true, true, true)

npcType:register(npcConfig)