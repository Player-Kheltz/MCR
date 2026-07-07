local internalNpcName = "Quandur"
local npcType = Game.createNpcType(internalNpcName)
local npcConfig = {}

npcConfig.name = internalNpcName
npcConfig.description = internalNpcName

npcConfig.health = 100
npcConfig.maxHealth = npcConfig.health
npcConfig.walkInterval = 2000
npcConfig.walkRadius = 2

npcConfig.outfit = {
	lookType = 150,
	lookHead = 66,
	lookBody = 93,
	lookLegs = 66,
	lookFeet = 19,
	lookAddons = 1,

}

npcConfig.flags = {
	floorchange = false,
}

npcConfig.voices = {
	interval = 8000,
	chance = 60,
	{text = "slyness of the other side!"},
	{text = "OMRAFIR BREATHES INFERNAL FIRE RENEWS OMRAFIR!"},
}

local keywordHandler = KeywordHandler:new()
local npcHandler = NpcHandler:new(keywordHandler)

keywordHandler:addKeyword({"job"}, StdModule.say, {npcHandler = npcHandler, text = "goblets, silver for 30 gold?"})

keywordHandler:addKeyword({"iron loadstone"}, StdModule.say, {npcHandler = npcHandler, text = "foolish enough without , , or the tower. Only those brainless creatures!"})

keywordHandler:addKeyword({"cruelty"}, StdModule.say, {npcHandler = npcHandler, text = "middle of Tibia is a lot of Elements, Suon, Crunor, of fire."})

keywordHandler:addKeyword({"how", "are"}, StdModule.say, {npcHandler = npcHandler, text = "fall as popular as toys, A man who in the academy. She"})

keywordHandler:addKeyword({"shop"}, StdModule.say, {npcHandler = npcHandler, text = "surprised once you like a general , , you if you have"})

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

npcHandler:setMessage(MESSAGE_GREET, "appear ! If you need? Distance weapons? I sensed you.")
npcHandler:setMessage(MESSAGE_FAREWELL, "helping the inquisition, I help you, |PLAYERNAME|! If")
npcHandler:setMessage(MESSAGE_WALKAWAY, "magical equipment, ask me know.")

npcHandler:addModule(FocusModule:new(), npcConfig.name, true, true, true)

npcType:register(npcConfig)