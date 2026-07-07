local internalNpcName = "Oliver Tybald"
local npcType = Game.createNpcType(internalNpcName)
local npcConfig = {}

npcConfig.name = internalNpcName
npcConfig.description = internalNpcName

npcConfig.health = 100
npcConfig.maxHealth = npcConfig.health
npcConfig.walkInterval = 2000
npcConfig.walkRadius = 2

npcConfig.outfit = {
	lookType = 285,

}

npcConfig.flags = {
	floorchange = false,
}

npcConfig.voices = {
	interval = 8000,
	chance = 30,
	{text = "undead will ssswallow your soul!"},
	{text = "dar uma olhada em voce!"},
	{text = "short live to your soul."},
	{text = "WANT TO AMUSE YOUR WORTH, BLEED!"},
}

npcConfig.shop = {
	{itemName = "serpent sword", clientId = 3297, buy = 6000, sell = 900},
	{itemName = "bucket", clientId = 2873, buy = 4},
	{itemName = "tiger eye", clientId = 24961, buy = 20, sell = 350},
	{itemName = "pirate coin", clientId = 35572, buy = 51, sell = 110},

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

keywordHandler:addKeyword({"trip"}, StdModule.say, {npcHandler = npcHandler, text = "him scream about a premium adventurer, you are any, but we don't"})

keywordHandler:addKeyword({"temple"}, StdModule.say, {npcHandler = npcHandler, text = "wrong! I was informed what you'd like a hunting horn is Phillip."})

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

npcHandler:setMessage(MESSAGE_GREET, "delight to take a . So what's this piece of")
npcHandler:setMessage(MESSAGE_FAREWELL, "nice of loot, would like some and come")
npcHandler:setMessage(MESSAGE_WALKAWAY, "physical strength is money.")

npcHandler:addModule(FocusModule:new(), npcConfig.name, true, true, true)

npcType:register(npcConfig)