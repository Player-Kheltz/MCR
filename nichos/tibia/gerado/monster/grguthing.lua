local monster = Game.createMonsterType("Grguthing")
monster:register()

monster.name = "Grguthing"
monster.description = "a Grguthing"
monster.experience = 59745
monster.outfit = {
	lookType = 842,
	lookHead = 77,
	lookBody = 132,
	lookLegs = 21,
	lookFeet = 20,
	lookAddons = 0,
	lookMount = 0,
}
monster.health = 199024
monster.maxHealth = 220000
monster.race = "fire"
monster.raceId = 64
monster.corpse = 6068
monster.speed = 164
monster.manaCost = 0

monster.changeTarget = false
monster.strategies = {"attack"}
monster.flags = {
	ignoreSpawnBlock = true,
	pushCreatures = false,
	clientAnimations = true,
	attackPlayers = true,
}

monster.defenses = {
	defense = 65,
	armor = 55,
	-- mitigation = 1.0
}

monster.loot = {
	{id = 824, chance = 200, maxCount = 1},
	{id = 3031, chance = 10000, maxCount = 78},
	{id = 16120, chance = 7630, maxCount = 1},
}

monster.attacks = {
	{name = "combat", interval = 2000, chance = 5},
	{name = "melee", interval = 2000, chance = 100},
}

monster.voices = {
	interval = 30000,
	chance = 40,
	{text = "Snow will be still you know... you can!!", yell = false},
	{text = "finally consume you! *giggle*", yell = false},
	{text = "adventurer who we there are you have my feet!", yell = true},
	{text = "Creation must be undone! We will join the ultimate in the annihiliverse!", yell = true},
	{text = "in the power of the shadow under your life actually!", yell = false},
}

monster.immunities = {
	{type = "physical", condition = true},
}

monster:register()