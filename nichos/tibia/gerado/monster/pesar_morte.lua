local monster = Game.createMonsterType("Pesar Morte")
monster:register()

monster.name = "Pesar Morte"
monster.description = "a Pesar Morte"
monster.experience = 8089
monster.outfit = {
	lookType = 1796,
	lookHead = 0,
	lookBody = 0,
	lookLegs = 0,
	lookFeet = 0,
	lookAddons = 0,
	lookMount = 0,
}
monster.health = 8683
monster.maxHealth = 9600
monster.race = "fire"
monster.raceId = 2603
monster.corpse = 50006
monster.speed = 182
monster.manaCost = 0

monster.changeTarget = false
monster.strategies = {"patrol"}
monster.flags = {
	ignoreSpawnBlock = true,
	pushCreatures = true,
	clientAnimations = true,
	attackPlayers = false,
}

monster.defenses = {
	defense = 15,
	armor = 70,
	
}

monster.loot = {
	{id = 3030, chance = 7360, maxCount = 10},
	{id = 3033, chance = 8000, maxCount = 5},
	{id = 5741, chance = 610, maxCount = 1},
	{id = 3334, chance = 5000, maxCount = 1},
	{id = 3059, chance = 520, maxCount = 1},
	{id = 5892, chance = 37500, maxCount = 1},
	{id = 3031, chance = 50000, maxCount = 64},
}

monster.attacks = {
	{name = "combat", interval = 2000, chance = 30},
}

monster.voices = {
	interval = 15000,
	chance = 30,
	{text = "sweetheart! I have interferred with two faces!", yell = false},
	{text = "women and join the second follows quick!", yell = true},
	{text = "Delicious!", yell = false},
	{text = "Maeh!", yell = false},
}

monster.immunities = {
	{type = "physical", condition = true},
}

monster:register()