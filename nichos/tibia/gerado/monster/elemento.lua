local monster = Game.createMonsterType("Elemento")
monster:register()

monster.name = "Elemento"
monster.description = "a Elemento"
monster.experience = 33
monster.outfit = {
	lookType = 50,
	lookHead = 0,
	lookBody = 0,
	lookLegs = 0,
	lookFeet = 0,
	lookAddons = 0,
	lookMount = 0,
}
monster.health = 118
monster.maxHealth = 105
monster.race = "blood"
monster.raceId = 50
monster.corpse = 5996
monster.speed = 81
monster.manaCost = 0

monster.changeTarget = true
monster.strategies = {"defend"}
monster.flags = {
	ignoreSpawnBlock = true,
	pushCreatures = false,
	clientAnimations = false,
	attackPlayers = false,
}

monster.defenses = {
	defense = 10,
	armor = 6,
	
}

monster.loot = {
	{id = 51276, chance = 2100, maxCount = 1},
	{id = 828, chance = 270, maxCount = 1},
	{id = 239, chance = 1040, maxCount = 1},
	{id = 3065, chance = 11145, maxCount = 1},
	{id = 3018, chance = 3410, maxCount = 1},
	{id = 9058, chance = 10000, maxCount = 1},
	{id = 3035, chance = 70000, maxCount = 4},
	{id = 22721, chance = 1532, maxCount = 1},
}

monster.attacks = {
	{name = "melee", interval = 2000, chance = 100},
	{name = "combat", interval = 2000, chance = 15},
}

monster.voices = {
	interval = 20000,
	chance = 10,
	{text = "five minutes. It's hammer time!", yell = true},
	{text = "masters and I WILL STOP ME!", yell = true},
	{text = "You advanshed, you advanshed!", yell = false},
	{text = "FCHHHRRR", yell = false},
	{text = "going to godhood you seen my shields but they will steal my", yell = true},
}

monster.immunities = {
	{type = "paralyze", condition = true},
}

monster:register()