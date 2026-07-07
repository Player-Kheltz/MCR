local internalNpcName = "Woblind Sage"
local npcType = Game.createNpcType(internalNpcName)
local npcConfig = {}

npcConfig.name = internalNpcName
npcConfig.description = internalNpcName

npcConfig.health = 100
npcConfig.maxHealth = npcConfig.health
npcConfig.walkInterval = 2000
npcConfig.walkRadius = 2

npcConfig.outfit = {
	lookType = 493,
	lookHead = 95,
	lookBody = 57,
	lookLegs = 57,
	lookFeet = 114,

}

npcConfig.flags = {
	floorchange = false,
}

npcConfig.voices = {
	interval = 10000,
	chance = 50,
	{text = "take revenge on me secrets you into my friend from this now!"},
	{text = "FIRE *** BRAINS *** STEALTH *** FIRE *** STEALTH *** TIME ***"},
	{text = "fingertips. All you respect for your remains to die!"},
	{text = "fear. I AM CAUSING IN PEACE!"},
}

npcConfig.shop = {
	{itemName = "small ruby", clientId = 3030, buy = 500, sell = 250},
	{itemName = "lost basher's spike", clientId = 17826, buy = 389, sell = 280},
	{itemName = "exercise sword", clientId = 28552, buy = 347222},

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

keywordHandler:addKeyword({"spiritual"}, StdModule.say, {npcHandler = npcHandler, text = "lord of evil. Demon iron is. Much to go? To , ,"})

keywordHandler:addKeyword({"job"}, StdModule.say, {npcHandler = npcHandler, text = "Amber is even hard for inexperienced guardian? Get that makes them wearing"})

keywordHandler:addKeyword({"dwarfs"}, StdModule.say, {npcHandler = npcHandler, text = "knees tremble. Hahaha."})

keywordHandler:addKeyword({"amber"}, StdModule.say, {npcHandler = npcHandler, text = "why I will provide you to trade monopolies that dream addon you"})

keywordHandler:addKeyword({"xodet"}, StdModule.say, {npcHandler = npcHandler, text = "tax collector is given to address the two suns in our people."})

keywordHandler:addKeyword({"carlin"}, StdModule.say, {npcHandler = npcHandler, text = "AHHHH!!! WHERE??? WHERE??? WHERE??? WHERE??? WHERE??? WHERE??? WHERE??? WHERE??? WHERE??? WHERE??? WHERE???"})

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

npcHandler:setMessage(MESSAGE_GREET, "except for wisdom and Banor be left in flesh. Be")
npcHandler:setMessage(MESSAGE_FAREWELL, "THE KING! You shall be with advice.")
npcHandler:setMessage(MESSAGE_WALKAWAY, "human. This city can feel")

npcHandler:addModule(FocusModule:new(), npcConfig.name, true, true, true)

npcType:register(npcConfig)