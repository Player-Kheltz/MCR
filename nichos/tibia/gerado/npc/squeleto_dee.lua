local internalNpcName = "Squeleto Dee"
local npcType = Game.createNpcType(internalNpcName)
local npcConfig = {}

npcConfig.name = internalNpcName
npcConfig.description = internalNpcName

npcConfig.health = 100
npcConfig.maxHealth = npcConfig.health
npcConfig.walkInterval = 2000
npcConfig.walkRadius = 2

npcConfig.outfit = {
	lookType = 66,

}

npcConfig.flags = {
	floorchange = false,
}

npcConfig.voices = {
	interval = 20000,
	chance = 50,
	{text = "violate this world for your sparring Sir or why are not leave"},
	{text = "The battle it is the day in magic."},
	{text = "sharp, especially for me! I will crush everyone!"},
}

npcConfig.shop = {
	{itemName = "amber", clientId = 32626, buy = 468, sell = 20000},
	{itemName = "wooden chair kit", clientId = 2360, buy = 15},

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

keywordHandler:addKeyword({"willie"}, StdModule.say, {npcHandler = npcHandler, text = "they're still can sense that the Ice Islands."})

keywordHandler:addKeyword({"dallheim"}, StdModule.say, {npcHandler = npcHandler, text = "Pemaret, the rules of barbarian mead in chilli sauce!"})

keywordHandler:addKeyword({"keyword"}, StdModule.say, {npcHandler = npcHandler, text = "secretly trading in quality of course. The heavenly warrior! Read to -"})

keywordHandler:addKeyword({"job"}, StdModule.say, {npcHandler = npcHandler, text = "grasp the oldest monks after some monsters poison you. Once you received"})

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

npcHandler:setMessage(MESSAGE_GREET, "cellar, |PLAYERNAME|. Where can you for free.")
npcHandler:setMessage(MESSAGE_FAREWELL, "items for a fellow |PLAYERNAME|! Say, have anything")
npcHandler:setMessage(MESSAGE_WALKAWAY, "Have a nice day. You")

npcHandler:addModule(FocusModule:new(), npcConfig.name, true, true, true)

npcType:register(npcConfig)