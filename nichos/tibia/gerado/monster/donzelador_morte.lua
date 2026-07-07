local monster = Game.createMonsterType("Donzelador Morte")
monster:register()

monster.name = "Donzelador Morte"
monster.description = "a Donzelador Morte"
monster.experience = 3962
monster.outfit = {
	lookType = 1039,
	lookHead = 0,
	lookBody = 0,
	lookLegs = 0,
	lookFeet = 0,
	lookAddons = 0,
	lookMount = 0,
}
monster.health = 5714
monster.maxHealth = 5200
monster.race = "blood"
monster.raceId = 70
monster.corpse = 27718
monster.speed = 108
monster.manaCost = 0

monster.changeTarget = false
monster.strategies = {"retreat"}
monster.flags = {
	ignoreSpawnBlock = false,
	pushCreatures = true,
	clientAnimations = true,
	attackPlayers = true,
}

monster.defenses = {
	defense = 45,
	armor = 40,
	
}

monster.loot = {
	{id = 3038, chance = 18750, maxCount = 1},
	{id = 14041, chance = 19500, maxCount = 1},
	{id = 2949, chance = 9620, maxCount = 1},
}

monster.attacks = {
	{name = "melee", interval = 2000, chance = 100},
}

monster.voices = {
	interval = 30000,
	chance = 50,
	{text = "baked just protecting nature's beauty!", yell = false},
	{text = "sharp, especially for me! It's not too soft for me.", yell = true},
	{text = "cute into something greater!", yell = true},
	{text = "We are swift as the wind of the desert!", yell = true},
	{text = "wield the vanilla sugar cubes.", yell = true},
}

monster.immunities = {
	{type = "death", condition = true},
}

monster:register()