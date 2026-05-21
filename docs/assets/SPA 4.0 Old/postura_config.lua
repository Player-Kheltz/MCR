--[[
    Projeto MCR ? SPA v4.0 ? Configuração de Posturas
--]]

POSTURA_BASE = {
    [WEAPON_SWORD] = {
        [1] = { speedMod=1.00, damageMod=1.15 },
        [2] = { speedMod=1.00, damageMod=1.00 },
        [3] = { speedMod=1.05, damageMod=0.75, damageTakenMod=0.85, healthRegenMod=1.2 }
    },
    [WEAPON_AXE] = {
        [1] = { speedMod=1.05, damageMod=1.20 },
        [2] = { speedMod=1.00, damageMod=1.00 },
        [3] = { speedMod=1.10, damageMod=0.65, damageTakenMod=0.80, healthRegenMod=1.4 }
    },
    [WEAPON_CLUB] = {
        [1] = { speedMod=1.05, damageMod=1.10 },
        [2] = { speedMod=1.00, damageMod=1.00 },
        [3] = { speedMod=1.10, damageMod=0.65, damageTakenMod=0.85, healthRegenMod=1.3 }
    },
    [WEAPON_DISTANCE] = {
        [1] = { speedMod=0.95, damageMod=1.10, rangeMod=1 },
        [2] = { speedMod=1.00, damageMod=1.00 },
        [3] = { speedMod=1.05, damageMod=0.70, damageTakenMod=0.85, stealth=true, stealthDelay=1500 }
    },
    [WEAPON_MISSILE] = {
        [1] = { speedMod=0.85, damageMod=1.05 },
        [2] = { speedMod=0.95, damageMod=1.00 },
        [3] = { speedMod=1.00, damageMod=0.70, stealth=true, stealthDelay=1500 }
    },
    [WEAPON_WAND] = {
        [1] = { speedMod=1.00, damageMod=1.00, manaRegenMod=0.8 },
        [2] = { speedMod=1.00, damageMod=1.00 },
        [3] = { speedMod=1.00, damageMod=0.60, manaRegenMod=1.5, manaLeech=8 }
    },
    [WEAPON_FIST] = {
        [1] = { speedMod=0.70, damageMod=1.05, stealth=true, stealthDelay=800 },
        [2] = { speedMod=0.85, damageMod=1.00 },
        [3] = { speedMod=0.95, damageMod=0.70, damageTakenMod=0.80, healthRegenMod=1.3, stealth=true, stealthDelay=1200 }
    },
    default = {
        [1] = { speedMod=1.00, damageMod=1.00 },
        [2] = { speedMod=1.00, damageMod=1.00 },
        [3] = { speedMod=1.00, damageMod=0.70 }
    }
}

AGIL_AJUSTES = {
    [WEAPON_SWORD] = { speedMod=0.85, damageModExtra=0.05 },
    [WEAPON_AXE]   = { speedMod=0.90, damageModExtra=0.05 },
    [WEAPON_CLUB]  = { speedMod=0.90, damageModExtra=0.05 },
    [WEAPON_FIST]  = { speedMod=0.80, damageModExtra=0.02 },
}

PESADA_AJUSTES = {
    [WEAPON_SWORD] = { speedMod=0.90, damageModExtra=0.10, knockback=true, knockbackChance=25 },
    [WEAPON_AXE]   = { speedMod=0.85, damageModExtra=0.15, knockback=true, knockbackChance=20 },
    [WEAPON_CLUB]  = { speedMod=0.85, damageModExtra=0.10, knockback=true, knockbackChance=30 },
    [WEAPON_FIST]  = { speedMod=0.90, damageModExtra=0.10 },
}

RUNOLOGIA_SEM_ESCUDO = { speedMod=0.60, manaRegenMod=0.7, damageTakenMod=1.10 }
RUNOLOGIA_COM_ESCUDO = { damageTakenMod=0.80, manaRegenMod=1.2 }
ARREMESSO_SEM_ESCUDO = { speedMod=0.80 }
ARREMESSO_COM_ESCUDO = { damageTakenMod=0.85, knockback=true, knockbackChance=15 }

SHIELD_POSTURA = {
    [1] = { damageTakenMod=0.95, canPush=false },
    [2] = { damageTakenMod=0.90, canPush=false },
    [3] = { damageTakenMod=0.75, healthRegenMod=1.5, canPush=true },
}

function corDominio(domId)
    local cores = {
        [1]=COR.SISTEMA_INFO, [2]=COR.DOM_MAGIA_RUNOLOGIA, [3]=COR.DOM_OFICIO_CRAFT, [4]=COR.DOM_NATUREZA_CULTIVO,
        [10]=COR.DOM_COMBATE_LAMINAS, [11]=COR.DOM_COMBATE_IMPACTO, [12]=COR.DOM_COMBATE_IMPACTO,
        [13]=COR.DOM_COMBATE_PRECISAO, [14]=COR.DOM_COMBATE_DESARMADO, [15]=COR.DOM_ESCUDO,
        [100]=COR.DOM_COMBATE_LAMINAS, [101]=COR.DOM_COMBATE_LAMINAS,
        [110]=COR.DOM_COMBATE_IMPACTO, [111]=COR.DOM_COMBATE_IMPACTO,
        [112]=COR.DOM_COMBATE_IMPACTO, [113]=COR.DOM_COMBATE_IMPACTO,
        [120]=COR.DOM_COMBATE_PRECISAO, [121]=COR.DOM_COMBATE_PRECISAO,
        [130]=COR.DOM_COMBATE_DESARMADO, [131]=COR.DOM_COMBATE_DESARMADO,
        [132]=COR.DOM_COMBATE_DESARMADO, [133]=COR.DOM_MAGIA_RUNOLOGIA,
        [20]=COR.DOM_MAGIA_RUNOLOGIA, [21]=COR.DOM_MAGIA_SAGRADO, [22]=COR.DOM_MAGIA_RUNOLOGIA,
        [23]=COR.ELEM_FOGO, [24]=COR.ELEM_GELO, [25]=COR.ELEM_VENENO,
        [200]=COR.ELEM_SAGRADO,
        [210]=COR.DOM_MAGIA_RUNOLOGIA, [211]=COR.DOM_MAGIA_RUNOLOGIA, [212]=COR.DOM_MAGIA_RUNOLOGIA,
        [400]=COR.DOM_NATUREZA_SOBREV,
    }
    return cores[domId] or COR.SISTEMA_INFO
end

print("DEBUG: postura_config.lua v4.0 carregado.")