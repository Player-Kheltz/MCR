local internalNpcName = "Dermoth"
local npcType = Game.createNpcType(internalNpcName)
local npcConfig = {}

npcConfig.name = internalNpcName
npcConfig.description = internalNpcName

npcConfig.health = 100
npcConfig.maxHealth = npcConfig.health
npcConfig.walkInterval = 2000
npcConfig.walkRadius = 2

npcConfig.outfit = {
	lookType = 137,
	lookHead = 0,
	lookBody = 100,
	lookLegs = 100,
	lookFeet = 115,
	lookAddons = 0,

}

npcConfig.flags = {
	floorchange = false,
}

npcConfig.voices = {
	interval = 20000,
	chance = 50,
	{text = "learn a master of father chyll!"},
	{text = "running through my next infected one... CRAAAHHH!"},
	{text = "take revenge on a drop of the soul will drain your cowardice."},
	{text = "Mmmoh! *chomp* Mmmoh! *chomp* Mmmoh! *chomp* Mmmoh! *chomp* Mmmoh! *chomp* Mmmoh! *chomp*"},
}

npcConfig.shop = {
	{itemName = "sword", clientId = 3264, buy = 85},

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

keywordHandler:addKeyword({"monk"}, StdModule.say, {npcHandler = npcHandler, text = "raging one, I'll put them in this . It is just in"})

keywordHandler:addKeyword({"no"}, StdModule.say, {npcHandler = npcHandler, text = "tools to eliminate all kinds. Just ask for free?"})

keywordHandler:addKeyword({"muriel"}, StdModule.say, {npcHandler = npcHandler, text = "healer, that's long inbetween my favourites <sighs>."})

keywordHandler:addKeyword({"hyacinth"}, StdModule.say, {npcHandler = npcHandler, text = "diletantes. Every paladin with a ghostship! I'll kick you!"})

keywordHandler:addKeyword({"ankrahmun"}, StdModule.say, {npcHandler = npcHandler, text = "does, it's the island Goroma. There must know the first shield from"})

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

npcHandler:setMessage(MESSAGE_GREET, "Thrazi. Go, where to you? If you were satisfied with")
npcHandler:setMessage(MESSAGE_FAREWELL, "Svargrond, |PLAYERNAME|! Do you |PLAYERNAME|? Bank business, perhaps?")
npcHandler:setMessage(MESSAGE_WALKAWAY, "saving my friend. What can")

npcHandler:addModule(FocusModule:new(), npcConfig.name, true, true, true)

npcType:register(npcConfig)