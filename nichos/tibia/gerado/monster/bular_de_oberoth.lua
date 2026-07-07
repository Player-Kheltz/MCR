local monster = Game.createMonsterType("bular de Oberoth")
monster:register()

monster.name = "bular de Oberoth"
monster.description = "a bular de Oberoth"
monster.experience = 61074
monster.outfit = {
	lookType = 1222,
	lookHead = 101,
	lookBody = 79,
	lookLegs = 0,
	lookFeet = 0,
	lookAddons = 2,
	lookMount = 0,
}
monster.health = 82713
monster.maxHealth = 75000
monster.race = "venom"
monster.raceId = 15
monster.corpse = 31599
monster.speed = 124
monster.manaCost = 0

monster.changeTarget = false
monster.strategies = {"patrol"}
monster.flags = {
	ignoreSpawnBlock = true,
	pushCreatures = false,
	clientAnimations = true,
	attackPlayers = true,
}

monster.defenses = {
	defense = 25,
	armor = 78,
	-- mitigation = 1.0
}

monster.loot = {
	{id = 3434, chance = 5230, maxCount = 1},
	{id = 7383, chance = 6964, maxCount = 1},
	{id = 31557, chance = 520, maxCount = 1},
	{id = 239, chance = 1210, maxCount = 1},
	{id = 3081, chance = 500, maxCount = 1},
	{id = 10390, chance = 100, maxCount = 1},
	{id = 3033, chance = 2580, maxCount = 3},
}

monster.attacks = {
	{name = "combat", interval = 2000, chance = 20},
	{name = "melee", interval = 2000, chance = 100},
}

monster.voices = {
	interval = 10000,
	chance = 30,
	{text = "You are no match for a master assassin!", yell = false},
	{text = "zzizz azzault when you are swift as I am the curse! Aww", yell = true},
	{text = "SMALL *** TIME OF ZHE POWER...", yell = true},
	{text = "Stop! I am the second follows you. Just Look at you. Be", yell = false},
	{text = "Uh, So you are mad to seven!", yell = true},
}

monster.immunities = {
	{type = "holy", condition = true},
}

monster:register()