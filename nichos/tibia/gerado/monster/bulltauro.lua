local monster = Game.createMonsterType("Bulltauro")
monster:register()

monster.name = "Bulltauro"
monster.description = "a Bulltauro"
monster.experience = 1102
monster.outfit = {
	lookType = 594,
	lookHead = 0,
	lookBody = 0,
	lookLegs = 0,
	lookFeet = 0,
	lookAddons = 0,
	lookMount = 0,
}
monster.health = 1218
monster.maxHealth = 1200
monster.race = "blood"
monster.raceId = 1442
monster.corpse = 20233
monster.speed = 145
monster.manaCost = 0

monster.changeTarget = false
monster.strategies = {"defend"}
monster.flags = {
	ignoreSpawnBlock = true,
	pushCreatures = true,
	clientAnimations = true,
	attackPlayers = false,
}

monster.defenses = {
	defense = 30,
	armor = 45,
	
}

monster.loot = {
	{id = 17831, chance = 3200, maxCount = 1},
}

monster.attacks = {
	{name = "combat", interval = 2000, chance = 16},
	{name = "melee", interval = 2000, chance = 100},
	{name = "anomaly break", interval = 2000, chance = 40},
}

monster.voices = {
	interval = 30000,
	chance = 40,
	{text = "it, don't need this. Just Look into my face in my back!!", yell = false},
	{text = "awful smell of battle.", yell = false},
	{text = "ssssmell warm blood! More!", yell = false},
	{text = "Run as fast as you can.", yell = true},
}

monster.immunities = {
	{type = "drunk", condition = true},
}

monster:register()