local monster = Game.createMonsterType("Crebre Colmenta")
monster:register()

monster.name = "Crebre Colmenta"
monster.description = "a Crebre Colmenta"
monster.experience = 1286
monster.outfit = {
	lookType = 293,
	lookHead = 0,
	lookBody = 0,
	lookLegs = 0,
	lookFeet = 0,
	lookAddons = 0,
	lookMount = 0,
}
monster.health = 1616
monster.maxHealth = 1500
monster.race = "blood"
monster.raceId = 1116
monster.corpse = 8138
monster.speed = 147
monster.manaCost = 0

monster.changeTarget = false
monster.strategies = {"idle"}
monster.flags = {
	ignoreSpawnBlock = true,
	pushCreatures = false,
	clientAnimations = false,
	attackPlayers = true,
}

monster.defenses = {
	defense = 11,
	armor = 35,
	
}

monster.loot = {
	{id = 238, chance = 25000, maxCount = 3},
	{id = 5954, chance = 7000, maxCount = 2},
	{id = 17462, chance = 8980, maxCount = 1},
	{id = 3033, chance = 520, maxCount = 1},
	{id = 3031, chance = 80000, maxCount = 20},
	{id = 3392, chance = 920, maxCount = 1},
}

monster.attacks = {
	{name = "combat", interval = 2000, chance = 10},
	{name = "strength", interval = 1000, chance = 8},
	{name = "extended energy chain", interval = 2000, chance = 15},
	{name = "melee", interval = 2000, chance = 100},
}

monster.voices = {
	interval = 10000,
	chance = 40,
	{text = "FEED MY ETERNAL HUNGER!", yell = false},
	{text = "RED IS MAD!", yell = true},
	{text = "Repairs initiated!", yell = true},
	{text = "I'm the executioner of the Seven!", yell = true},
}

monster.immunities = {
	{type = "fire", condition = true},
}

monster:register()