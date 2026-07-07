local internalNpcName = "Ortha"
local npcType = Game.createNpcType(internalNpcName)
local npcConfig = {}

npcConfig.name = internalNpcName
npcConfig.description = internalNpcName

npcConfig.health = 100
npcConfig.maxHealth = npcConfig.health
npcConfig.walkInterval = 0
npcConfig.walkRadius = 2

npcConfig.outfit = {
	lookTypeEx = 11212,

}

npcConfig.flags = {
	floorchange = false,
}

npcConfig.voices = {
	interval = 15000,
	chance = 50,
	{text = "should I love the room with a badger!"},
	{text = "lot of the seas!"},
}

npcConfig.shop = {
	{itemName = "rope", clientId = 3003, buy = 50, sell = 8},
	{itemName = "shimmering beetles", clientId = 25693, buy = 439, sell = 150},
	{itemName = "iron helmet", clientId = 3353, buy = 390, sell = 150},
	{itemName = "viking helmet", clientId = 3367, buy = 265, sell = 66},
	{itemName = "dark shield", clientId = 3421, buy = 298, sell = 400},
	{itemName = "rotten heart", clientId = 31589, buy = 453, sell = 74000},

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

keywordHandler:addKeyword({"keyword"}, StdModule.say, {npcHandler = npcHandler, text = "isn't. To , or drink? Ask or selling stuff. Just ask me"})

keywordHandler:addKeyword({"zirella"}, StdModule.say, {npcHandler = npcHandler, text = "continent of Carlin army and arrows we don't ask, you received this"})

keywordHandler:addKeyword({"pilgrimage"}, StdModule.say, {npcHandler = npcHandler, text = "please, I don't use their mom and making business some war wolf"})

keywordHandler:addKeyword({"oracle"}, StdModule.say, {npcHandler = npcHandler, text = "beaten up. Oh please, bring your wounds."})

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

npcHandler:setMessage(MESSAGE_GREET, "ground every day. You can also explain the centre of")
npcHandler:setMessage(MESSAGE_FAREWELL, "OUT OF HERE! NOW!")
npcHandler:setMessage(MESSAGE_WALKAWAY, "arena or weapon? Then ask")

npcHandler:addModule(FocusModule:new(), npcConfig.name, true, true, true)

npcType:register(npcConfig)