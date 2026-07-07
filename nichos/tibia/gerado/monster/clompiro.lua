local monster = Game.createMonsterType("Clompiro")
monster:register()

monster.name = "Clompiro"
monster.description = "a Clompiro"
monster.experience = 4823
monster.outfit = {
	lookType = 306,
	lookHead = 0,
	lookBody = 0,
	lookLegs = 0,
	lookFeet = 0,
	lookAddons = 0,
	lookMount = 0,
}
monster.health = 8308
monster.maxHealth = 8000
monster.race = "undead"
monster.raceId = 1675
monster.corpse = 8909
monster.speed = 143
monster.manaCost = 0

monster.changeTarget = false
monster.strategies = {"retreat"}
monster.flags = {
	ignoreSpawnBlock = false,
	pushCreatures = true,
	clientAnimations = false,
	attackPlayers = true,
}

monster.defenses = {
	defense = 45,
	armor = 85,
	
}

monster.loot = {
	{id = 3582, chance = 19660, maxCount = 4},
	{id = 3035, chance = 100000, maxCount = 15},
	{id = 22721, chance = 61220, maxCount = 1},
	{id = 3007, chance = 60, maxCount = 1},
	{id = 7368, chance = 12550, maxCount = 10},
}

monster.attacks = {
	{name = "melee", interval = 2000, chance = 100},
	{name = "speed", interval = 2000, chance = 15},
	{name = "energyfield", interval = 1000, chance = 8},
	{name = "extended energy chain", interval = 2000, chance = 15},
}

monster.voices = {
	interval = 20000,
	chance = 50,
	{text = "weasel will never stop! You will be here! This is so sorry", yell = false},
	{text = "yjou wjill njot sjufer the power of death!", yell = false},
	{text = "Tchky!", yell = false},
	{text = "I wish you a merry trip to hell!", yell = true},
	{text = "Hihihihi!", yell = true},
}

monster.immunities = {
	{type = "death", condition = true},
}

monster:register()