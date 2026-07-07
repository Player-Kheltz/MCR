local internalNpcName = "Scrusheryn"
local npcType = Game.createNpcType(internalNpcName)
local npcConfig = {}

npcConfig.name = internalNpcName
npcConfig.description = internalNpcName

npcConfig.health = 100
npcConfig.maxHealth = npcConfig.health
npcConfig.walkInterval = 2000
npcConfig.walkRadius = 2

npcConfig.outfit = {
	lookType = 73,
	lookHead = 20,
	lookBody = 30,
	lookLegs = 40,
	lookFeet = 50,
	lookAddons = 1,

}

npcConfig.flags = {
	floorchange = false,
}

npcConfig.voices = {
	interval = 10000,
	chance = 40,
	{text = "activates its former self!"},
	{text = "POWERFUL ENOUGH TO THE RUTHLESS SEVEN!"},
}

npcConfig.shop = {
	{itemName = "candelabrum", clientId = 2911, buy = 8},
	{itemName = "elven amulet", clientId = 3082, buy = 500},
	{itemName = "model ship", clientId = 2994, buy = 137, sell = 1000},

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

keywordHandler:addKeyword({"demon"}, StdModule.say, {npcHandler = npcHandler, text = "|PLAYERNAME|. I help in the and . Which of town, indeed! I"})

keywordHandler:addKeyword({"academy"}, StdModule.say, {npcHandler = npcHandler, text = "Poodle, the main Tibian ? Or to Liberty Bay now. The spark"})

keywordHandler:addKeyword({"phoenix"}, StdModule.say, {npcHandler = npcHandler, text = "Judging by the elements in Kazordoon. I can be careful down to"})

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

npcHandler:setMessage(MESSAGE_GREET, "visits the respective people would.")
npcHandler:setMessage(MESSAGE_FAREWELL, "Port Hope! Would you are heavily wounded or")
npcHandler:setMessage(MESSAGE_WALKAWAY, "Bye now, Neutrala |PLAYERNAME|. Do")

npcHandler:addModule(FocusModule:new(), npcConfig.name, true, true, true)

npcType:register(npcConfig)