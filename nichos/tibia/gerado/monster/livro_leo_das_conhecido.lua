local monster = Game.createMonsterType("Livro Leo das Conhecido")
monster:register()

monster.name = "Livro Leo das Conhecido"
monster.description = "a Livro Leo das Conhecido"
monster.experience = 4135
monster.outfit = {
	lookType = 1136,
	lookHead = 47,
	lookBody = 7,
	lookLegs = 0,
	lookFeet = 85,
	lookAddons = 0,
	lookMount = 0,
}
monster.health = 4497
monster.maxHealth = 5200
monster.race = "blood"
monster.raceId = 1731
monster.corpse = 30127
monster.speed = 219
monster.manaCost = 0

monster.changeTarget = false
monster.strategies = {"defend"}
monster.flags = {
	ignoreSpawnBlock = true,
	pushCreatures = false,
	clientAnimations = true,
	attackPlayers = true,
}

monster.defenses = {
	defense = 20,
	armor = 76,
	-- mitigation = 1.0
}

monster.loot = {
	{id = 7401, chance = 190, maxCount = 1},
	{id = 8016, chance = 3760, maxCount = 3},
	{id = 3030, chance = 2200, maxCount = 2},
	{id = 23373, chance = 66666, maxCount = 6},
	{id = 21143, chance = 4000, maxCount = 1},
	{id = 3415, chance = 100, maxCount = 1},
	{id = 23535, chance = 16872, maxCount = 3},
	{id = 3038, chance = 12000, maxCount = 1},
}

monster.attacks = {
	{name = "combat", interval = 2000, chance = 10},
	{name = "melee", interval = 2000, chance = 100},
	{name = "speed", interval = 2000, chance = 20},
}

monster.voices = {
	interval = 10000,
	chance = 10,
	{text = "Come kiss the cook!", yell = true},
	{text = "<brrzz>", yell = false},
	{text = "yours souls to show a nice trophy!", yell = false},
	{text = "You'll never take me alive!", yell = true},
	{text = "Flee as you been in your eyes... I bring balance upon you!", yell = false},
}

monster.immunities = {
	{type = "paralyze", condition = true},
}

monster:register()