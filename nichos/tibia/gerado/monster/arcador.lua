local monster = Game.createMonsterType("Arcador")
monster:register()

monster.name = "Arcador"
monster.description = "a Arcador"
monster.experience = 484
monster.outfit = {
	lookType = 611,
	lookHead = 0,
	lookBody = 0,
	lookLegs = 0,
	lookFeet = 0,
	lookAddons = 0,
	lookMount = 0,
}
monster.health = 476
monster.maxHealth = 550
monster.race = "blood"
monster.raceId = 57
monster.corpse = 21091
monster.speed = 118
monster.manaCost = 0

monster.changeTarget = true
monster.strategies = {"retreat"}
monster.flags = {
	ignoreSpawnBlock = false,
	pushCreatures = false,
	clientAnimations = true,
	attackPlayers = true,
}

monster.defenses = {
	defense = 22,
	armor = 16,
	
}

monster.loot = {
	{id = 16122, chance = 10000, maxCount = 10},
}

monster.attacks = {
	{name = "combat", interval = 1000, chance = 15},
}

monster.voices = {
	interval = 15000,
	chance = 50,
	{text = "mess with you, intruder!", yell = true},
	{text = "You can't hope to penetrate my shields!", yell = true},
	{text = "Pain sweet pain!", yell = false},
}

monster.immunities = {
	{type = "energy", condition = true},
}

monster:register()