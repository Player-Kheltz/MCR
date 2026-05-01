#!/usr/bin/env python3
"""
corretor.py – Restaura strings técnicas, aplica correções manuais e,
se necessário, reverte automaticamente strings cujos placeholders
foram corrompidos ou que pareçam caminhos de ficheiro / SQL.
"""
import sys
import os
import re

# ---------- Conjuntos de chaves a restaurar manualmente ----------
RESTAURAR = {
    "E:\\Projeto MCR\\Canary\\src\\canary_server.cpp": {
        "332_73", "369_65", "369_107", "396_68",
    },
    "E:\\Projeto MCR\\Canary\\src\\account\\account_repository_db.cpp": {
        "20_26", "21_28", "200_57",
    },
    "E:\\Projeto MCR\\Canary\\src\\creatures\\creature.cpp": {
        "154_7", "322_3", "614_6", "615_6", "616_6", "617_6",
        "618_6", "619_6", "1338_143",
    },
    "E:\\Projeto MCR\\Canary\\src\\database\\database.cpp": {
        "57_34", "138_62",
    },
    "E:\\Projeto MCR\\Canary\\src\\database\\databasemanager.cpp": {
        "33_152", "43_11", "62_152", "62_208",
    },
    "E:\\Projeto MCR\\Canary\\src\\game\\game.cpp": {
        # Apenas as strings que NÃO devem ser alteradas pelas correções manuais
        # (deixar vazio se quiseres que o CORRECOES controle tudo)
    },
    "E:\\Projeto MCR\\Canary\\src\\io\\ioguild.cpp": {
        "42_16", "62_89", "62_121"
    },
    "E:\\Projeto MCR\\Canary\\src\\io\\iomarket.cpp": {
        "70_199", "70_233", "103_131", "127_138", "265_236", "265_288", "350_2"
    },
    "E:\\Projeto MCR\\Canary\\src\\io\\ioprey.cpp": {
        "313_26", "424_26", "424_131", "484_25", "484_130",
    },
    "E:\\Projeto MCR\\Canary\\src\\io\\io_wheel.cpp": {
        "33_2", "34_2", "35_2", "36_2", "43_94", "53_14", "55_21", "63_20",
        "100_19", "172_19", "174_19", "220_18", "235_41", "239_41", "243_41",
        "247_41", "251_41", "257_42", "265_42", "269_42", "273_42", "283_43",
        "287_43", "292_43", "296_43", "302_44", "305_44", "309_44", "313_44",
        "318_44", "326_40", "331_40", "336_40", "341_40", "346_40",
        "526_66", "539_67", "544_66", "563_76", "565_76", "570_76", "572_76",
        "609_73", "612_73", "616_74", "618_74", "622_73", "644_75", "648_76",
        "650_76", "655_76", "657_76", "705_65", "707_65", "709_65", "711_65",
        "713_65", "768_66", "779_67", "783_66", "829_74", "833_73", "837_74",
        "839_74", "863_74", "865_74", "868_75", "870_75", "873_74", "901_77",
        "903_77", "907_76", "911_77", "913_77", "936_67", "940_67", "945_68",
        "947_68", "952_67"
    },
    # ========== FICHEIROS CRÍTICOS (Lua) ==========
    "E:\\Projeto MCR\\Canary\\src\\lua\\functions\\lua_functions_loader.cpp": {
        "35_21", "51_10", "53_10", "55_10", "57_10", "59_10", "61_10", "63_10", "65_10",
        "67_10", "69_10", "71_10", "73_10", "75_10", "77_10", "79_10", "81_10", "83_10",
        "85_10", "87_10", "89_10", "91_10", "117_11", "118_11", "122_13", "125_13", "128_13",
        "134_11", "138_13", "142_11", "151_19", "387_19", "394_19", "395_30", "443_55",
        "547_17", "559_17", "655_21", "658_21", "661_21", "667_21", "673_21", "679_21",
        "738_13", "909_18"
    },
    "E:\\Projeto MCR\\Canary\\src\\lua\\functions\\events\\events_scheduler_functions.cpp": {
        "16_23"
    },
}

CORRECOES = {
    # ========== canary_server.cpp ==========
    "E:\\Projeto MCR\\Canary\\src\\canary_server.cpp": {
        "332_73": "data-otservbr-global",
        "369_65": "/items/appearances.dat",
        "357_17": "Conexão com o banco de dados estabelecida!",
        "396_68": "json/eventscheduler/events.json",
    },
    # ========== account_repository_db.cpp ==========
    "E:\\Projeto MCR\\Canary\\src\\account\\account_repository_db.cpp": {
        "20_26": "coins_tournament",
        "21_28": "coins_transferable",
        "200_57": "premdays_purchased",
    },
    # ========== configmanager.cpp ==========
    "E:\\Projeto MCR\\Canary\\src\\config\\configmanager.cpp": {
        "44_42": "disableLegacyRaids",
        "45_34": "allowOldProtocol",
        "47_42": "randomMonsterSpawn",
        "49_42": "toggleMaintainMode",
        "61_40": "premiumDepotLimit",
        "66_41": "houseRentPeriod",
        "68_45": "maintainModeMessage",
        "80_42": "hotkeyAimbotEnabled",
        "81_39": "allowChangeOutfit",
        "86_41": "classicAttackSpeed",
        "87_43": "cleanProtectionZones",
        "88_43": "convertUnsafeScripts",
        "89_42": "disableMonsterArmor",
        "93_42": "enableSupportOutfit",
        "94_44": "experienceByKillingPlayers",
        "100_43": "houseOwnedByAccount",
        "101_47": "housePurchasedShowPrice",
        "102_35": "inventoryGlowOnFiveBless",
        "105_43": "metricsEnableOstream",
        "106_46": "metricsEnablePrometheus",
        "108_41": "onlyPremiumAccount",
        "109_48": "partyAutoShareExperience",
        "110_44": "partyShareLootBoosts",
        "115_49": "refundBeginningWeaponMana",
        "116_49": "removeBeginningWeaponAmmunition",
        "117_42": "removeChargesFromPotions",
        "118_40": "removeChargesFromRunes",
        "120_42": "removeWeaponCharges",
        "121_42": "replaceKickOnLogin",
        "122_49": "rewardChestCollectEnabled",
        "124_43": "showLootsInBestiary",
        "126_40": "sortLootByChance",
        "132_41": "taskHuntingSystemEnabled",
        "133_49": "taskHuntingFreeThirdSlot",
        "135_37": "teleportSummons",
        "137_40": "toggleDownloadMap",
        "138_38": "toggleFreeQuest",
        "139_53": "toggleGoldPouchAllowAnything",
        "140_53": "toggleGoldPouchQuickLootOnly",
        "141_40": "toggleHazardSystem",
        "142_60": "toggleHouseTransferOnRestart",
        "145_39": "toggleMountInProtectionZone",
        "146_42": "toggleReceiveReward",
        "147_38": "toggleSaveAsync",
        "148_51": "toggleSaveIntervalCleanMap",
        "149_41": "toggleSaveInterval",
        "151_40": "toggleTravelsFree",
        "152_39": "wheelSystemEnabled",
        "158_40": "warnUnsafeScripts",
        "159_36": "experienceDisplayRates",
        "160_45": "toggleCyclopediaHouseAuction",
        "161_41": "leavePartyOnDeath",
        "163_52": "bestiaryRateCharmShopPrice",
        "168_45": "forgeAmountMultiplier",
        "169_49": "hazardExpBonusMultiplier",
        "170_57": "loyaltyBonusPercentageMultiplier",
        "171_47": "momentumChanceFormulaA",
        "172_47": "momentumChanceFormulaB",
        "173_47": "momentumChanceFormulaC",
        "174_48": "onslaughtChanceFormulaA",
        "175_48": "onslaughtChanceFormulaB",
        "176_48": "onslaughtChanceFormulaC",
        "177_64": "partyShareLootBoostsDimishingFactor",
        "180_39": "rateAttackSpeed",
        "182_39": "rateBossDefense",
        "184_50": "rateExerciseTrainingSpeed",
        "185_45": "rateHealthRegenSpeed",
        "186_39": "rateHealthRegen",
        "187_43": "rateManaRegenSpeed",
        "189_41": "rateMonsterAttack",
        "190_42": "rateMonsterDefense",
        "191_41": "rateMonsterHealth",
        "193_49": "rateOfflineTrainingSpeed",
        "194_43": "rateSoulRegenSpeed",
        "196_41": "rateSpellCooldown",
        "207_62": "animusMasteryMaxMonsterXpMultiplier",
        "208_58": "animusMasteryMonsterXpMultiplier",
        "209_59": "animusMasteryMonstersXpMultiplier",
        "212_45": "adventurersBlessingLevel",
        "213_44": "bestiaryKillMultiplier",
        "220_39": "buyAolCommandFee",
        "221_41": "buyBlessCommandFee",
        "223_38": "combatChainDelay",
        "224_40": "combatChainTargets",
        "225_37": "packetCompressionLevel",
        "228_38": "deathLosePercent",
        "229_40": "defaultRespawnTime",
        "237_43": "forgeBaseSuccessRate",
        "238_44": "forgeBonusSuccessRate",
        "239_54": "forgeConvergenceFusionDustCost",
        "240_56": "forgeConvergenceTransferCost",
        "242_41": "forgeCostOneSliver",
        "243_50": "forgeFiendishLimit",
        "244_42": "forgeFusionDustCost",
        "245_52": "forgeInfluencedLimit",
        "247_39": "forgeMaxItemTier",
        "248_37": "forgeMaxSlivers",
        "249_37": "forgeMinSlivers",
        "250_39": "forgeSliverAmount",
        "251_45": "forgeTierLossReduction",
        "252_44": "forgeTransferDustCost",
        "256_42": "hazardCriticalChance",
        "257_44": "hazardCriticalInterval",
        "258_46": "hazardCriticalMultiplier",
        "259_44": "hazardDamageMultiplier",
        "260_45": "hazardDefenseMultiplier",
        "261_43": "hazardDodgeMultiplier",
        "262_48": "hazardLootBonusMultiplier",
        "263_38": "hazardPodsDamage",
        "264_47": "hazardPodsDropMultiplier",
        "265_46": "hazardPodsTimeToDamage",
        "266_45": "hazardPodsTimeToSpawn",
        "267_51": "hazardSpawnPlunderMultiplier",
        "270_47": "houseLoseAfterInactivity",
        "273_38": "lootPouchMaxLimit",
        "275_51": "loyaltyPointsPerCreationDay",
        "276_60": "loyaltyPointsPerPremiumDayPurchased",
        "277_56": "loyaltyPointsPerPremiumDaySpent",
        "284_44": "maxElementalResistance",
        "291_44": "metricsOstreamInterval",
        "293_44": "minElementalResistance",
        "295_38": "monthKillsToRedSkull",
        "296_41": "orangeSkullDuration",
        "299_43": "partyListMaxDistance",
        "300_43": "preyBonusRerollPrice",
        "302_41": "preyFreeRerollTime",
        "303_43": "preyRerollPricePerLevel",
        "305_36": "protectionLevel",
        "308_44": "pvpMaxLevelDifference",
        "311_54": "rateKillingInTheNameOfPoints",
        "317_50": "rewardChestMaxCollectItems",
        "318_38": "saveIntervalTime",
        "319_34": "stairJumpExhaustion",
        "320_39": "staminaGreenDelay",
        "321_40": "staminaOrangeDelay",
        "323_41": "staminaTrainerDelay",
        "324_40": "staminaTrainerGain",
        "325_50": "partyShareRangeMultiplier",
        "331_51": "taskHuntingBonusRerollPrice",
        "332_49": "taskHuntingFreeRerollTime",
        "334_51": "taskHuntingRerollPricePerLevel",
        "335_53": "taskHuntingSelectListPrice",
        "336_50": "tibiadromeConcoctionCooldown",
        "337_50": "tibiadromeConcoctionDuration",
        "338_49": "transcendenceAvatarDuration",
        "343_37": "weekKillsToRedSkull",
        "344_53": "wheelAtelierRevealGreaterCost",
        "345_52": "wheelAtelierRevealLesserCost",
        "346_53": "wheelAtelierRevealRegularCost",
        "347_53": "wheelAtelierRotateGreaterCost",
        "348_52": "wheelAtelierRotateLesserCost",
        "349_53": "wheelAtelierRotateRegularCost",
        "352_52": "augmentIncreasedDamagePercent",
        "353_51": "augmentPowerfulImpactPercent",
        "354_49": "augmentStrongImpactPercent",
        "358_37": "dataPackDirectory",
        "358_58": "data-otservbr-global",
        "359_39": "defaultPriority",
        "361_51": "forgeFiendishIntervalTime",
        "362_51": "forgeFiendishIntervalType",
        "366_49": "metricsPrometheusAddress",
        "373_54": "tibiadromeConcoctionTickType",
    },
    # ========== database.cpp ==========
    "E:\\Projeto MCR\\Canary\\src\\database\\database.cpp": {
        "57_34": "SHOW VARIABLES LIKE 'max_allowed_packet'",
        "138_62": "database_backup",
    },
    # ========== databasemanager.cpp ==========
    "E:\\Projeto MCR\\Canary\\src\\database\\databasemanager.cpp": {
        "33_152": " AND `DATA_FREE` > 0",
        "43_11": "OPTIMIZE TABLE `",
        "62_152": " AND `TABLE_NAME` = ",
        "62_208": " LIMIT 1",
    },
    # ========== game.cpp ==========
    "E:\\Projeto MCR\\Canary\\src\\game\\game.cpp": {
        "232_24": "Rookie Hero",
        "233_24": "Veteran Hero",
        "234_24": "Senior Hero",
        "235_24": "Ancient Hero",
        "236_24": "Exalted Hero",
        "265_19": "Beaststrider (Grade 1)",
        "266_19": "Beaststrider (Grade 2)",
        "267_19": "Beaststrider (Grade 3)",
        "268_19": "Beaststrider (Grade 4)",
        "269_19": "Beaststrider (Grade 5)",
        "271_20": "Topmodel of Tibia (Grade 1)",
        "272_21": "Topmodel of Tibia (Grade 2)",
        "273_21": "Topmodel of Tibia (Grade 3)",
        "274_21": "Topmodel of Tibia (Grade 4)",
        "275_21": "Topmodel of Tibia (Grade 5)",
        "277_35": "Reached level 50.",
        "278_36": "Reached level 100.",
        "279_35": "Reached level 200.",
        "280_32": "Reached level 300.",
        "281_33": "Reached level 400.",
        "282_31": "Reached level 500.",
        "283_30": "Reached level 1000.",
        "285_24": "Apex Predator",
        "286_24": "Big Boss",
        "287_24": "Jack of All Pests",
        "288_24": "Legend of Fishing",
        "289_24": "Legend of Magic",
        "290_24": "Legend of Marksmanship",
        "291_24": "Legend of the Axe",
        "292_24": "Legend of the Club",
        "293_24": "Legend of the Fist",
        "294_24": "Legend of the Shield",
        "295_24": "Legend of the Sword",
        "296_24": "Prince Charming",
        "297_24": "Current Drome Champion",
        "299_84": "Unlocked all Humanoid Bestiary entries.",
        "300_69": "Blood Moon Hunter",
        "300_100": "Blood Moon Huntress",
        "301_85": "Unlocked all Amphibian Bestiary entries.",
        "302_86": "Unlocked all Bird Bestiary entries.",
        "303_80": "Unlocked all Demon Bestiary entries.",
        "304_84": "Unlocked all Dragon Bestiary entries.",
        "305_87": "Unlocked all Elemental Bestiary entries.",
        "306_84": "Unlocked all Vermin Bestiary entries.",
        "307_79": "Unlocked all Fey Bestiary entries.",
        "308_96": "Unlocked all Undead Bestiary entries.",
        "309_93": "Unlocked all Construct Bestiary entries.",
        "310_88": "Unlocked all Mammal Bestiary entries.",
        "311_75": "Interdimensional Destroyer",
        "312_91": "Unlocked all Human Bestiary entries.",
        "313_65": "Master of Illusion",
        "314_63": "Blue Ooze",
        "315_65": "Sea Curse",
        "316_65": "Snake Charmer",
        "317_78": "Unlocked all Giant Bestiary entries.",
        "318_81": "Unlocked all Plant Bestiary entries.",
        "319_44": "Unlocked all Bestiary entries.",
        "321_81": "Boss Annihilator",
        "322_81": "Boss Destroyer",
        "323_81": "Boss Devastator",
        "324_81": "Boss Eraser",
        "325_26": "Boss Executioner",
        "326_78": "Boss Hunter",
        "327_81": "Boss Obliterator",
        "328_78": "Boss Slayer",
        "329_81": "Boss Smiter",
        "330_78": "Boss Veteran",
        "332_26": "Creature of Habit (Grade 1)",
        "333_26": "Creature of Habit (Grade 2)",
        "334_26": "Creature of Habit (Grade 3)",
        "335_26": "Creature of Habit (Grade 4)",
        "336_26": "Creature of Habit (Grade 5)",
        "338_18": "Aspirant Hunter",
        "339_18": "Competent Beast Slayer",
        "340_18": "Feared Bounty Hunter",
        "342_17": "Dedicated Entrepreneur",
        "343_33": "Explored all map areas.",
        "345_20": "Guild Leader",
        "346_20": "Proconsul of Iksupan",
        "347_20": "Admirer of the Crown",
        "348_20": "Big Spender",
        "349_20": "Challenger of the Iks",
        "350_20": "Royal Bounacean Advisor",
        "351_32": "Aeternal",
        "352_20": "Robinson Crusoe",
        "353_36": "Chompmeister",
        "354_20": "Bringer of Rain",
        "355_31": "Beastly",
        "356_20": "Midnight Hunter",
        "357_33": "Ratinator",
        "358_20": "Doomsday Nemesis",
        "359_20": "Hero of Bounac",
        "360_20": "King of Demon",
        "361_34": "Planegazer",
        "362_20": "Time Traveller",
        "363_20": "Truly Boss",
        "367_40": "Achievement Points",
        "368_40": "Axe Fighting",
        "369_39": "Boss Points",
        "370_34": "Charm Points",
        "371_41": "Club Fighting",
        "372_45": "Distance Fighting",
        "373_33": "Drome Score",
        "374_38": "Experience Points",
        "376_41": "Fist Fighting",
        "377_35": "Goshnar's Taint",
        "378_42": "Loyalty Points",
        "379_39": "Magic Level",
        "8882_2": "@curRank := IF(@prevRank = `{}`, @curRank, IF(@prevRank := `{}`, @curRank + 1, @curRank + 1)) AS `rank`",
        "8883_2": "(@row:= @row + 1) AS `rn`",
        "8888_23": ", @ourRow := IF(`id` = {}, @row - 1, @ourRow) AS `rw`",
        "8906_3": "`rn` > (@ourRow DIV {0}) * {0}) AND `rn` <= (((@ourRow DIV {0}) * {0}) + {0})",
        "8910_23": "`rn` > {} AND `rn` <= {}",
        "8928_17": " OR `vocation` = ",
        "3215_26": "balance_increase",
        "401_54": "instant-rewards",
        "506_4": "`date` = '",
        "509_4": "`lookfeet` = ",
        "511_4": "`lookhead` = ",
    },
    # ========== iologindata_save_player.cpp ==========
    "E:\\Projeto MCR\\Canary\\src\\io\\functions\\iologindata_save_player.cpp": {
        "183_78": ", `lastip` = ",
        "190_10": "`name` = ",
        "191_10": "`level` = ",
        "192_10": "`group_id` = ",
        "193_10": "`vocation` = ",
        "194_10": "`health` = ",
        "195_10": "`healthmax` = ",
        "196_10": "`experience` = ",
        "197_10": "`lookbody` = ",
        "198_10": "`lookfeet` = ",
        "199_10": "`lookhead` = ",
        "200_10": "`looklegs` = ",
        "201_10": "`looktype` = ",
        "202_10": "`lookaddons` = ",
        "203_10": "`lookmountbody` = ",
        "204_10": "`lookmountfeet` = ",
        "205_10": "`lookmounthead` = ",
        "206_10": "`lookmountlegs` = ",
        "207_10": "`lookfamiliarstype` = ",
        "208_10": "`isreward` = ",
        "209_10": "`maglevel` = ",
        "210_10": "`mana` = ",
        "211_10": "`manamax` = ",
        "212_10": "`manaspent` = ",
        "213_10": "`soul` = ",
        "215_11": "`town_id` = ",
        "219_10": "`posx` = ",
        "220_10": "`posy` = ",
        "221_10": "`posz` = ",
        "223_10": "`prey_wildcard` = ",
        "224_10": "`task_points` = ",
        "225_10": "`boss_points` = ",
        "226_10": "`forge_dusts` = ",
        "227_10": "`forge_dust_level` = ",
        "228_10": "`randomize_mount` = ",
        "230_10": "`cap` = ",
        "231_10": "`sex` = ",
        "234_11": "`lastlogin` = ",
        "238_11": "`lastip` = ",
        "253_10": "`conditions` = ",
        "261_10": "`animus_mastery` = ",
        "271_11": "`skulltime` = ",
        "279_11": "`skull` = ",
        "282_10": "`lastlogout` = ",
        "283_10": "`balance` = ",
        "284_10": "`offlinetraining_time` = ",
        "285_10": "`offlinetraining_skill` = ",
        "286_10": "`stamina` = ",
        "287_10": "`skill_fist` = ",
        "288_10": "`skill_fist_tries` = ",
        "289_10": "`skill_club` = ",
        "290_10": "`skill_club_tries` = ",
        "291_10": "`skill_sword` = ",
        "292_10": "`skill_sword_tries` = ",
        "293_10": "`skill_axe` = ",
        "294_10": "`skill_axe_tries` = ",
        "295_10": "`skill_dist` = ",
        "296_10": "`skill_dist_tries` = ",
        "297_10": "`skill_shielding` = ",
        "298_10": "`skill_shielding_tries` = ",
        "299_10": "`skill_fishing` = ",
        "300_10": "`skill_fishing_tries` = ",
        "301_10": "`skill_critical_hit_chance` = ",
        "302_10": "`skill_critical_hit_chance_tries` = ",
        "303_10": "`skill_critical_hit_damage` = ",
        "304_10": "`skill_critical_hit_damage_tries` = ",
        "305_10": "`skill_life_leech_chance` = ",
        "306_10": "`skill_life_leech_chance_tries` = ",
        "307_10": "`skill_life_leech_amount` = ",
        "308_10": "`skill_life_leech_amount_tries` = ",
        "309_10": "`skill_mana_leech_chance` = ",
        "310_10": "`skill_mana_leech_chance_tries` = ",
        "311_10": "`skill_mana_leech_amount` = ",
        "312_10": "`skill_mana_leech_amount_tries` = ",
        "313_10": "`manashield` = ",
        "314_10": "`max_manashield` = ",
        "315_10": "`xpboost_value` = ",
        "316_10": "`xpboost_stamina` = ",
        "317_10": "`quickloot_fallback` = ",
        "322_11": "`onlinetime` = `onlinetime` + ",
        "445_10": "`charm_points` = ",
        "446_10": "`minor_charm_echoes` = ",
        "447_10": "`max_charm_points` = ",
        "448_10": "`max_minor_charm_echoes` = ",
        "449_10": "`charm_expansion` = ",
        "450_10": "`UsedRunesBit` = ",
        "451_10": "`UnlockedRunesBit` = ",
        "462_10": " `charms` = ",
        "470_10": " `tracker list` = ",
    },
    # ========== iologindata_load_player.cpp ==========
    "E:\\Projeto MCR\\Canary\\src\\io\\functions\\iologindata_load_player.cpp": {
        "148_68": "quickloot_fallback",
        "173_55": "forge_dust_level",
        "174_73": "randomize_mount",
        "178_58": "offlinetraining_time",
        "179_58": "offlinetraining_skill",
        "213_52": "xpboost_stamina",
        "218_54": "marriage_spouse",
        "311_71": "lookfamiliarstype",
        "354_163": "skill_critical_hit_chance",
        "354_192": "skill_critical_hit_damage",
        "354_221": "skill_life_leech_chance",
        "354_248": "skill_life_leech_amount",
        "354_275": "skill_mana_leech_chance",
        "354_302": "skill_mana_leech_amount",
        "355_61": "skill_fist_tries",
        "355_81": "skill_club_tries",
        "355_101": "skill_sword_tries",
        "355_122": "skill_axe_tries",
        "355_141": "skill_dist_tries",
        "355_161": "skill_shielding_tries",
        "355_186": "skill_fishing_tries",
        "355_209": "skill_critical_hit_chance_tries",
        "355_244": "skill_critical_hit_damage_tries",
        "355_279": "skill_life_leech_chance_tries",
        "355_312": "skill_life_leech_amount_tries",
        "355_345": "skill_mana_leech_chance_tries",
        "355_378": "skill_mana_leech_amount_tries",
        "482_57": "minor_charm_echoes",
        "483_55": "max_charm_points",
        "484_60": "max_minor_charm_echoes",
        "485_51": "charm_expansion",
        "487_56": "UnlockedRunesBit",
        "508_43": "tracker list",
        "834_56": "bonus_percentage",
    },
    # ========== bank.cpp ==========
    "E:\\Projeto MCR\\Canary\\src\\game\\bank\\bank.cpp": {
        "136_25": "balance_decrease",
        "150_24": "balance_decrease",
        "182_24": "balance_decrease",
        "132_25": "balance_increase",
    },
    # ========== player.cpp ==========
    "E:\\Projeto MCR\\Canary\\src\\creatures\\players\\player.cpp": {
        "2519_24": "balance_decrease",
        "2519_99": "apply_imbuement",
        "2591_24": "balance_decrease",
        "2591_119": "clear_imbuement",
        "10471_25": "balance_decrease",
        "10471_99": "forge_convergence_fuse",
        "10525_27": "balance_decrease",
        "10598_26": "balance_decrease",
        "10734_24": "balance_decrease",
        "3357_25": "player_experience_actual",
        "3359_25": "player_experience_bonus_raw",
        "3360_25": "player_experience_bonus_actual",
    },
    # ========== ioguild.cpp ==========
    "E:\\Projeto MCR\\Canary\\src\\io\\ioguild.cpp": {
        "42_16": "`balance` = ",
        "62_89": " OR `guild2` = ",
        "62_121": ") AND `status` = 1",
    },
    # ========== iomarket.cpp ==========
    "E:\\Projeto MCR\\Canary\\src\\io\\iomarket.cpp": {
        "70_199": " AND `itemtype` = ",
        "70_233": " AND `tier` = ",
        "103_131": " AND `sale` = ",
        "127_138": " AND `sale` = ",
        "265_236": " AND ((`id` ^ 0xABCDEF) & 65535) = ",
        "265_288": " LIMIT 1",
        "350_2": "GROUP BY itemtype, sale, tier",
    },
    # ========== ioprey.cpp ==========
    "E:\\Projeto MCR\\Canary\\src\\io\\ioprey.cpp": {
        "313_26": "balance_decrease",
        "424_26": "balance_decrease",
        "424_131": "hunting_task_reroll",
        "484_25": "balance_decrease",
        "484_130": "hunting_task_cancel",
    },
    # ========== house.cpp ==========
    "E:\\Projeto MCR\\Canary\\src\\map\\house\\house.cpp": {
        "98_55": ", `new_owner` = -1, `paid` = 0, `bidder` = 0, `bidder_name` = '', `highest_bid` = 0, `internal_bid` = 0, `bid_end_date` = 0, `state` = ",
        "1000_26": "balance_decrease",
        "1050_100": " << house->getName() << ",
    },
    # ========== webhook.cpp ==========
    "E:\\Projeto MCR\\Canary\\src\\server\\network\\webhook\\webhook.cpp": {
        "24_38": "content-type: application/json",
        "25_38": "accept: application/json",
        "127_27": " << title << ",
        "129_34": " << message << ",
        "132_39": " << footer_text.str() << ",
        "139_31": " << (!message.empty() ? message : title) << ",
    },
    # ========== spells.cpp ==========
    "E:\\Projeto MCR\\Canary\\src\\creatures\\combat\\spells.cpp": {
        "132_16": " + param + ",
        "203_16": "Mystic Repulse",
        "203_44": "Forceful Uppercut",
        "203_75": "Focus Harmony",
    },
    # ========== player_wheel.cpp ==========
    "E:\\Projeto MCR\\Canary\\src\\creatures\\players\\components\\wheel\\player_wheel.cpp": {
        "985_4": "Terra Burst",
        "985_19": "Ice Burst",
        "986_4": "Ice Burst",
        "986_17": "Terra Burst",
        "1004_4": "Great Death Beam",
        "1004_24": "Great Energy Beam",
        "1005_4": "Great Energy Beam",
        "1005_25": "Great Death Beam",
        "1030_30": "wheel-of-destiny",
        "2116_17": "Battle Instinct",
        "2117_17": "Battle Healing",
        "2118_17": "Positional Tactics",
        "2119_17": "Ballistic Mastery",
        "2120_17": "Healing Link",
        "2121_17": "Runic Mastery",
        "2122_17": "Focus Mastery",
        "2124_17": "Guiding Presence",
        "2129_19": "Combat Mastery",
        "2132_18": "Combat Mastery",
        "2137_19": "Gift of Life",
        "2140_18": "Gift of Life",
        "2145_19": "Blessing of the Grove",
        "2148_18": "Blessing of the Grove",
        "2153_19": "Divine Empowerment",
        "2159_17": "Divine Empowerment",
        "2162_17": "Divine Empowerment",
        "2165_18": "Divine Empowerment",
        "2170_19": "Divine Grenade",
        "2175_17": "Divine Grenade",
        "2180_17": "Divine Grenade",
        "2183_18": "Divine Grenade",
        "2188_19": "Drain Body",
        "2191_18": "Drain Body",
        "2194_30": "Energy Beam",
        "2195_30": "Great Death Beam",
        "2196_30": "Great Energy Beam",
        "2198_19": "Beam Mastery",
        "2204_17": "Great Death Beam",
        "2207_17": "Great Death Beam",
        "2210_18": "Beam Mastery",
        "2215_19": "Twin Burst",
        "2221_17": "Ice Burst",
        "2222_17": "Terra Burst",
        "2225_17": "Ice Burst",
        "2226_17": "Terra Burst",
        "2229_18": "Twin Burst",
        "2234_19": "Executioner's Throw",
        "2239_17": "Executioner's Throw",
        "2242_17": "Executioner's Throw",
        "2245_18": "Executioner's Throw",
        "2251_19": "Avatar of Light",
        "2257_17": "Avatar of Light",
        "2260_17": "Avatar of Light",
        "2263_18": "Avatar of Light",
        "2268_19": "Avatar of Nature",
        "2274_17": "Avatar of Nature",
        "2277_17": "Avatar of Nature",
        "2280_18": "Avatar of Nature",
        "2285_19": "Avatar of Steel",
        "2290_17": "Avatar of Steel",
        "2293_17": "Avatar of Steel",
        "2296_18": "Avatar of Steel",
        "2301_19": "Avatar of Storm",
        "2306_17": "Avatar of Storm",
        "2309_17": "Avatar of Storm",
        "2312_18": "Avatar of Storm",
        "2317_19": "Avatar of Balance",
        "2322_17": "Avatar of Balance",
        "2325_17": "Avatar of Balance",
        "2328_18": "Avatar of Balance",
        "2333_19": "Spiritual Outburst",
        "2338_17": "Spiritual Outburst",
        "2341_17": "Spiritual Outburst",
        "2344_18": "Spiritual Outburst",
        "2350_19": "Combat Mastery",
        "2353_18": "Combat Mastery",
        "2652_20": "Executioner's Throw",
        "2657_20": "Great Death Beam",
        "2662_20": "Divine Grenade",
        "2667_20": "Spiritual Outburst",
        "2676_20": "Avatar of Steel",
        "2681_20": "Avatar of Light",
        "2686_20": "Avatar of Nature",
        "2691_20": "Avatar of Storm",
        "2696_20": "Avatar of Balance",
        "2707_20": "Drain_Body_Spells",
        "2712_20": "Divine Empowerment",
        "2717_20": "Terra Burst",
        "2718_20": "Ice Burst",
        "2818_16": "Battle Instinct",
        "2821_16": "Positional Tactics",
        "2824_16": "Ballistic Mastery",
        "3053_49": "That was close! Fortunately, your were saved by the Gift of Life.",
        "3201_17": "Avatar of Light",
        "3203_24": "Avatar of Steel",
        "3205_24": "Avatar of Nature",
        "3207_24": "Avatar of Storm",
        "3209_24": "Avatar of Balance",
        "3255_32": "Ballistic Mastery",
        "3257_32": "Ballistic Mastery",
        "3266_42": "Gift of Life",
        "3269_108": "Battle Instinct",
        "3269_142": "Positional Tactics",
        "3269_179": "Ballistic Mastery",
        "3269_215": "Gift of Life",
        "3269_246": "Combat Mastery",
        "3269_279": "Divine Empowerment",
        "3291_16": "Battle Instinct",
        "3295_16": "Positional Tactics",
        "3299_16": "Ballistic Mastery",
        "3303_16": "Combat Mastery",
        "3307_16": "Divine Empowerment",
        "3408_67": "Focus Mastery",
        "3510_20": "Spiritual Outburst",
        "3518_20": "Guiding Presence",
        "3520_20": "Battle Instinct",
        "3526_20": "Battle Healing",
        "3528_20": "Positional Tactics",
        "3534_20": "Ballistic Mastery",
        "3541_20": "Healing Link",
        "3543_20": "Runic Mastery",
        "3545_20": "Focus Mastery",
        "3550_20": "Beam Mastery",
        "3556_20": "Combat Mastery",
        "3562_20": "Gift of Life",
        "3568_20": "Blessing of the Grove",
        "3574_20": "Drain Body",
        "3580_20": "Divine Empowerment",
        "3586_20": "Divine Grenade",
        "3592_20": "Twin Burst",
        "3598_20": "Executioner's Throw",
        "3604_20": "Avatar of Light",
        "3610_20": "Avatar of Nature",
        "3616_20": "Avatar of Steel",
        "3622_20": "Avatar of Storm",
        "3628_20": "Avatar of Balance",
        "3665_4": "Battle Instinct",
        "3666_4": "Battle Healing",
        "3667_4": "Positional Tactics",
        "3668_4": "Ballistic Mastery",
        "3669_4": "Healing Link",
        "3670_4": "Runic Mastery",
        "3671_4": "Focus Mastery",
        "3673_4": "Guiding Presence",
        "3678_4": "Beam Mastery",
        "3679_4": "Combat Mastery",
        "3680_4": "Gift of Life",
        "3681_4": "Blessing of the Grove",
        "3682_4": "Drain Body",
        "3683_4": "Divine Empowerment",
        "3684_4": "Divine Grenade",
        "3685_4": "Twin Burst",
        "3686_4": "Executioner's Throw",
        "3687_4": "Avatar of Light",
        "3688_4": "Avatar of Nature",
        "3689_4": "Avatar of Steel",
        "3690_4": "Avatar of Storm",
        "3692_4": "Avatar of Balance",
        "3693_4": "Spiritual Outburst",
        "3770_17": "Healing Link",
        "3773_14": "Nature's Embrace",
        "3773_45": "Heal Friend",
        "3799_4": "Battle Instinct",
        "3800_4": "Battle Healing",
        "3801_4": "Positional Tactics",
        "3802_4": "Ballistic Mastery",
        "3803_4": "Healing Link",
        "3804_4": "Runic Mastery",
        "3805_4": "Focus Mastery",
        "3807_4": "Guiding Presence",
        "3811_4": "Beam Mastery",
        "3812_4": "Combat Mastery",
        "3813_4": "Gift of Life",
        "3814_4": "Blessing of the Grove",
        "3815_4": "Drain Body",
        "3816_4": "Divine Empowerment",
        "3817_4": "Divine Grenade",
        "3818_4": "Twin Burst",
        "3819_4": "Executioner's Throw",
        "3820_4": "Avatar of Light",
        "3821_4": "Avatar of Nature",
        "3822_4": "Avatar of Steel",
        "3823_4": "Avatar of Storm",
        "3824_4": "Avatar of Balance",
        "3932_76": "Beam Mastery",
        "3948_16": "Battle Healing",
        "3998_43": "Combat Mastery",
        "4055_4": "supremeModifier",
        "4071_45": "supremeModifier",
    },
    # ========== wheel_gems.cpp ==========
    "E:\\Projeto MCR\\Canary\\src\\creatures\\players\\components\\wheel\\wheel_gems.cpp": {
        "224_20": "WheelModifierContext::setStrategy: Invalid basic modifier: {}",
        "261_86": "Ultimate Healing",
        "332_86": "Avatar of Steel",
        "337_86": "Executioner's Throw",
        "341_86": "Executioner's Throw",
        "345_86": "Executioner's Throw",
        "349_86": "Fierce Berserk",
        "353_86": "Fierce Berserk",
        "365_86": "Front Sweep",
        "369_86": "Front Sweep",
        "389_86": "Fair Wound Cleansing",
        "395_86": "Avatar of Light",
        "400_86": "Divine Dazzle",
        "404_86": "Divine Grenade",
        "408_86": "Divine Grenade",
        "412_86": "Divine Caldera",
        "416_86": "Divine Caldera",
        "420_86": "Divine Missile",
        "424_86": "Divine Missile",
        "428_86": "Ethereal Spear",
        "432_86": "Ethereal Spear",
        "436_86": "Strong Ethereal Spear",
        "440_86": "Strong Ethereal Spear",
        "445_86": "Divine Empowerment",
        "450_86": "Divine Grenade",
        "460_86": "Avatar of Storm",
        "465_86": "Energy Wave",
        "469_86": "Great Death Beam",
        "473_86": "Great Death Beam",
        "477_86": "Hell's Core",
        "481_86": "Hell's Core",
        "485_86": "Energy Wave",
        "489_86": "Energy Wave",
        "493_86": "Great Fire Wave",
        "497_86": "Great Fire Wave",
        "501_86": "Rage of the Skies",
        "505_86": "Rage of the Skies",
        "509_86": "Great Energy Beam",
        "513_86": "Great Energy Beam",
        "519_86": "Avatar of Nature",
        "524_86": "Nature's Embrace",
        "528_86": "Terra Burst",
        "532_86": "Terra Burst",
        "536_86": "Ice Burst",
        "540_86": "Ice Burst",
        "544_86": "Eternal Winter",
        "548_86": "Eternal Winter",
        "552_86": "Terra Wave",
        "556_86": "Terra Wave",
        "560_86": "Strong Ice Wave",
        "564_86": "Strong Ice Wave",
        "568_86": "Heal Friend",
        "572_86": "Mass Healing",
        "580_86": "Avatar of Balance",
        "588_86": "Spirit Mend",
        "596_86": "Spiritual Outburst",
        "604_86": "Spiritual Outburst",
        "612_86": "Forceful Uppercut",
        "620_86": "Forceful Uppercut",
        "629_86": "Flurry of Blows",
        "638_86": "Flurry of Blows",
        "646_86": "Greater Flurry of Blows",
        "654_86": "Greater Flurry of Blows",
        "662_86": "Sweeping Takedown",
        "670_86": "Sweeping Takedown",
        "679_86": "Focus Serenity",
        "688_86": "Focus Harmony",
        "696_86": "Mass Spirit Mend",
        "700_20": "WheelModifierContext::setStrategy: Invalid supreme modifier: {}",
    },
    # ========== player_title.cpp ==========
    "E:\\Projeto MCR\\Canary\\src\\creatures\\players\\components\\player_title.cpp": {
        "250_21": "Boss Executioner",
        "277_13": "Guild Leader",
        "280_20": "Proconsul of Iksupan",
        "282_20": "Admirer of the Crown",
        "285_20": "Big Spender",
        "288_20": "Challenger of the Iks",
        "291_20": "Royal Bounacean Advisor",
        "297_20": "Robinson Crusoe",
        "301_20": "Bringer of Rain",
        "306_20": "Midnight Hunter",
        "313_20": "Doomsday Nemesis",
        "316_20": "Hero of Bounac",
        "318_20": "King of Demon",
        "323_20": "Time Traveller",
        "325_20": "Truly Boss",
    },
    # ========== NOVAS ADIÇÕES ==========
    "E:\\Projeto MCR\\Canary\\src\\game\\scheduling\\events_scheduler.cpp": {
        "60_41": "double-bestiary",
        "61_41": "double-bosstiary",
        "151_52": "doublebosstiary",
        "196_52": "double-bestiary",
        "200_52": "double-bosstiary",
        "232_40": "double-bestiary",
        "235_40": "double-bosstiary",
    },
    "E:\\Projeto MCR\\Canary\\src\\utils\\tools.cpp": {
        "970_10": "fist fighting",
        "973_10": "club fighting",
        "976_10": "sword fighting",
        "979_10": "axe fighting",
        "982_10": "distance fighting",
        "991_10": "critical hit chance",
        "994_10": "critical extra damage",
        "997_10": "life leech chance",
        "1000_10": "life leech",
        "1003_10": "mana leech chance",
        "1006_10": "mana leech",
        "1009_10": "magic level",
        "874_3": "elemental damage",
        "875_3": "life leech",
        "876_3": "mana leech",
        "877_3": "critical hit",
        "878_3": "elemental protection death",
        "879_3": "elemental protection earth",
        "880_3": "elemental protection fire",
        "881_3": "elemental protection ice",
        "882_3": "elemental protection energy",
        "883_3": "elemental protection holy",
        "884_3": "increase speed",
        "885_3": "skillboost fist",
        "886_3": "skillboost axe",
        "887_3": "skillboost sword",
        "888_3": "skillboost club",
        "889_3": "skillboost shielding",
        "890_3": "skillboost distance",
        "891_3": "skillboost magic level",
        "892_3": "increase capacity",
        "649_3": "blueenergyspark",
        "654_3": "confettihorizontal",
        "655_3": "confettivertical",
        "676_3": "greenenergyspark",
        "686_3": "mirrorhorizontal",
        "691_3": "orangeenergyspark",
        "692_3": "orangefireworks",
        "705_3": "pinkenergyspark",
        "712_3": "ragiazbonecapsule",
        "718_3": "skullhorizontal",
        "720_3": "stepshorizontal",
        "737_3": "yellowenergyspark",
        "741_3": "whiteenergyspark",
        "760_3": "crystallinearrow",
        "1132_4": "additemitemtile",
        "1133_4": "removeitemitemtile",
        "1598_15": "ultimatestrikes",
        "1275_12": "lootmessagesuffix",
    },
    "E:\\Projeto MCR\\Canary\\src\\items\\functions\\item\\item_parse.cpp": {
        "123_28": "magicshieldpotion",
        "138_19": "loot pouch",
        "217_20": "blockprojectile",
        "223_20": "allowpickupable",
        "266_27": "writeonceitemid",
        "380_20": "transformequipto",
        "390_27": "transformdeequipto",
        "479_20": "criticalhitchance",
        "481_27": "criticalhitdamage",
        "487_20": "lifeleechchance",
        "489_27": "lifeleechamount",
        "491_27": "manaleechchance",
        "493_27": "manaleechamount",
        "501_27": "maxhitpointspercent",
        "505_27": "maxmanapointspercent",
        "511_20": "magiclevelpoints",
        "513_27": "magiclevelpointspercent",
        "519_20": "fieldabsorbpercentenergy",
        "521_27": "fieldabsorbpercentfire",
        "523_27": "fieldabsorbpercentpoison",
        "529_20": "absorbpercentall",
        "535_27": "absorbpercentelements",
        "542_27": "absorbpercentmagic",
        "551_27": "absorbpercentenergy",
        "553_27": "absorbpercentfire",
        "555_27": "absorbpercentpoison",
        "555_67": "absorbpercentearth",
        "557_27": "absorbpercentice",
        "559_27": "absorbpercentholy",
        "561_27": "absorbpercentdeath",
        "563_27": "absorbpercentlifedrain",
        "565_27": "absorbpercentmanadrain",
        "567_27": "absorbpercentdrown",
        "569_27": "absorbpercentphysical",
        "571_27": "absorbpercenthealing",
        "589_28": "suppressphysical",
        "725_20": "partnerdirection",
        "729_20": "maletransformto",
        "740_27": "femaletransformto",
        "992_20": "usedbyhouseguests",
        "915_20": "deathmagiclevelpoints",
        "918_27": "energymagiclevelpoints",
        "921_27": "earthmagiclevelpoints",
        "924_27": "firemagiclevelpoints",
        "927_27": "healingmagiclevelpoints",
        "930_27": "holymagiclevelpoints",
        "933_27": "icemagiclevelpoints",
        "936_27": "physicalmagiclevelpoints",
        "944_20": "magicshieldcapacitypercent",
        "946_27": "magicshieldcapacityflat",
        "953_20": "perfectshotdamage",
        "955_27": "perfectshotrange",
        "971_27": "reflectpercentall",
    },
    "E:\\Projeto MCR\\Canary\\src\\items\\items.cpp": {
        "58_3": "creatureproduct",
    },
    "E:\\Projeto MCR\\Canary\\src\\creatures\\combat\\combat.cpp": {
        "40_32": "Runic Mastery",
        "1806_42": "Runic Mastery",
    },
    "E:\\Projeto MCR\\Canary\\src\\creatures\\monsters\\monster.cpp": {
        "909_43": "Ballistic Mastery",
    },
    "E:\\Projeto MCR\\Canary\\src\\creatures\\monsters\\monsters.cpp": {
        "195_25": "soulwars fear",
    },
    "E:\\Projeto MCR\\Canary\\src\\items\\weapons\\weapons.cpp": {
        "302_22": "cleave damage",
        "347_88": "wand of vortex",
        "347_127": "snakebite rod",
    },
    "E:\\Projeto MCR\\Canary\\src\\game\\zones\\zone.cpp": {
        "126_22": "goshnars-hatred-damage",
        "127_22": "goshnars-hatred-damage",
    },
    "E:\\Projeto MCR\\Canary\\src\\creatures\\appearance\\attached_effects\\attached_effects.cpp": {
        "34_32": "attachedeffects",
        "41_34": "attachedeffects",
        "48_34": "attachedeffects",
        "55_32": "attachedeffects",
    },
    "E:\\Projeto MCR\\Canary\\src\\io\\iomapserialize.cpp": {
        "319_48": "transfer_status",
        "408_175": "transfer_status",
    },
    "E:\\Projeto MCR\\Canary\\src\\creatures\\players\\vocations\\vocation.cpp": {
        "157_71": "secondaryShield",
        "182_74": "damageReceivedMultiplier",
        "187_71": "damageDealtMultiplier",
    },
    "E:\\Projeto MCR\\Canary\\src\\creatures\\players\\imbuements\\imbuements.cpp": {
        "62_44": "protectionPrice",
    },
    "E:\\Projeto MCR\\Canary\\src\\creatures\\players\\components\\player_cyclopedia.cpp": {
        "121_36": "mostdamage_unjustified",
    },
}

# ---------- funções auxiliares ----------
def carregar_extraido(caminho):
    dados = {}
    arquivo_atual = None
    with open(caminho, 'r', encoding='utf-8') as f:
        for linha in f:
            linha = linha.strip('\n')
            if linha.startswith('[') and linha.endswith(']'):
                arquivo_atual = linha[1:-1]
                dados[arquivo_atual] = {}
            elif '=' in linha and arquivo_atual:
                chave, valor = linha.split('=', 1)
                dados[arquivo_atual][chave] = valor
    return dados

def placeholders_diferentes(original, traduzido):
    """Retorna True se os placeholders {} ou «N» foram alterados."""
    orig_ph = re.findall(r'\{[^\}]*\}|\«\d+»', original)
    trad_ph = re.findall(r'\{[^\}]*\}|\«\d+»', traduzido)
    return orig_ph != trad_ph

def parece_caminho_ou_sql(texto):
    """Retorna True se a string parece ser um caminho de arquivo ou SQL."""
    if re.search(r'\.(json|dat|xml|otbm|png|ogg)$', texto, re.IGNORECASE):
        return True
    if re.search(r'\b(SELECT|UPDATE|SET|WHERE|INSERT|DELETE|FROM|VALUES|ORDER BY)\b', texto, re.IGNORECASE):
        return True
    return False

def parece_log_tecnico(texto):
    """Retorna True se a string contém :: (ex.: Classe::metodo)."""
    return '::' in texto

def parece_caminho_script(texto):
    """Retorna True se a string é um caminho de script Lua."""
    return '/scripts/' in texto or (texto.startswith('/') and texto.endswith('/'))

def aplicar_restauracoes_automaticas(caminho, extraido):
    """Para cada chave, se a tradução corrompeu placeholders ou é caminho/SQL/log técnico, restaura o original."""
    if not os.path.exists(caminho):
        return 0

    with open(caminho, 'r', encoding='utf-8') as f:
        linhas = f.readlines()

    alteracoes = 0
    novas_linhas = []
    secao_atual = None

    for linha in linhas:
        linha_stripped = linha.rstrip('\n')
        if not linha_stripped.strip():
            continue
        if linha_stripped.startswith('[') and linha_stripped.endswith(']'):
            secao_atual = linha_stripped[1:-1]
            novas_linhas.append(linha)
            continue
        if secao_atual and '=' in linha_stripped:
            chave, traduzido = linha_stripped.split('=', 1)
            original = extraido.get(secao_atual, {}).get(chave)
            if original is not None and original != traduzido:
                if (placeholders_diferentes(original, traduzido)
                        or parece_caminho_ou_sql(original)
                        or parece_log_tecnico(original)
                        or parece_caminho_script(original)):
                    print(f"  ⚠️ {secao_atual} {chave} – string técnica/log, restaurando.")
                    linha = f"{chave}={original}\n"
                    alteracoes += 1
        novas_linhas.append(linha)

    if alteracoes > 0:
        with open(caminho, 'w', encoding='utf-8') as f:
            f.writelines(novas_linhas)
        print(f"✔ {caminho}: {alteracoes} strings restauradas automaticamente.")
    return alteracoes

def aplicar_restauracoes(caminho, extraido, restauracoes):
    if not os.path.exists(caminho):
        return 0
    with open(caminho, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
    alteracoes = 0
    novas_linhas = []
    secao_atual = None
    for linha in linhas:
        linha_stripped = linha.rstrip('\n')
        if not linha_stripped.strip():
            continue
        if linha_stripped.startswith('[') and linha_stripped.endswith(']'):
            secao_atual = linha_stripped[1:-1]
            novas_linhas.append(linha)
            continue
        if secao_atual and '=' in linha_stripped:
            chave, valor = linha_stripped.split('=', 1)
            if secao_atual in restauracoes and chave in restauracoes[secao_atual]:
                original = extraido.get(secao_atual, {}).get(chave)
                if original is not None and original != valor:
                    print(f"  🔄 {secao_atual} {chave}: '{valor}' -> '{original}'")
                    linha = f"{chave}={original}\n"
                    alteracoes += 1
        novas_linhas.append(linha)
    if alteracoes > 0:
        with open(caminho, 'w', encoding='utf-8') as f:
            f.writelines(novas_linhas)
        print(f"✔ {caminho}: {alteracoes} strings restauradas.")
    return alteracoes

def aplicar_correcoes(caminho, correcoes):
    if not os.path.exists(caminho):
        return 0
    with open(caminho, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
    alteracoes = 0
    novas_linhas = []
    secao_atual = None
    for linha in linhas:
        linha_stripped = linha.rstrip('\n')
        if not linha_stripped.strip():
            continue
        if linha_stripped.startswith('[') and linha_stripped.endswith(']'):
            secao_atual = linha_stripped[1:-1]
            novas_linhas.append(linha)
            continue
        if secao_atual and '=' in linha_stripped:
            chave, valor = linha_stripped.split('=', 1)
            if secao_atual in correcoes and chave in correcoes[secao_atual]:
                novo_valor = correcoes[secao_atual][chave]
                if novo_valor != valor:
                    print(f"  ✏️ {secao_atual} {chave}: '{valor}' -> '{novo_valor}'")
                    linha = f"{chave}={novo_valor}\n"
                    alteracoes += 1
        novas_linhas.append(linha)
    if alteracoes > 0:
        with open(caminho, 'w', encoding='utf-8') as f:
            f.writelines(novas_linhas)
        print(f"✔ {caminho}: {alteracoes} correções manuais.")
    return alteracoes

def main():
    if len(sys.argv) < 4:
        print("Uso: python corretor.py extraido.txt traduzido.txt reparado.txt")
        return
    arq_extraido = sys.argv[1]
    arq_traduzido = sys.argv[2]
    arq_reparado = sys.argv[3]
    extraido = carregar_extraido(arq_extraido)

    total = 0

    print("🔧 Passo 1 – Restaurar strings técnicas (via extraido.txt)")
    total += aplicar_restauracoes(arq_traduzido, extraido, RESTAURAR)
    total += aplicar_restauracoes(arq_reparado, extraido, RESTAURAR)

    print("🔧 Passo 2 – Aplicar correções manuais (CORRECOES)")
    total += aplicar_correcoes(arq_traduzido, CORRECOES)
    total += aplicar_correcoes(arq_reparado, CORRECOES)

    print("🔧 Passo 3 – Corrigir automaticamente placeholders e caminhos/SQL")
    total += aplicar_restauracoes_automaticas(arq_traduzido, extraido)
    total += aplicar_restauracoes_automaticas(arq_reparado, extraido)

    print(f"🎉 Total de alterações: {total}")

if __name__ == '__main__':
    main()