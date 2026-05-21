--[[
    Projeto MCR ? constantes.lua (v4.0)
    Centraliza todas as constantes do SPA.
    Carregar antes de qualquer outro módulo SPA.
--]]

-- ============================================================
-- DOMÍNIOS PRIMÁRIOS
-- ============================================================
DOMINIO_COMBATE   = 1
DOMINIO_MAGIA     = 2
DOMINIO_OFICIOS   = 3
DOMINIO_NATUREZA  = 4

-- ============================================================
-- DOMÍNIOS SECUNDÁRIOS
-- ============================================================
DOMINIO_LAMINAS    = 10
DOMINIO_MACHADOS   = 11
DOMINIO_CLAVAS     = 12
DOMINIO_PRECISAO   = 13
DOMINIO_DESARMADO  = 14
DOMINIO_ESCUDO     = 15
DOMINIO_ELEMENTOS  = 20
DOMINIO_ESPECTRO   = 21
DOMINIO_RUNOLOGIA  = 22

-- ============================================================
-- ESPECIALIDADES DE ARMA
-- ============================================================
DOMINIO_ESPADAS_LEVES     = 100
DOMINIO_ESPADAS_PESADAS   = 101
DOMINIO_MACHADOS_LEVES    = 110
DOMINIO_MACHADOS_PESADOS  = 111
DOMINIO_CLAVAS_LEVES      = 112
DOMINIO_CLAVAS_PESADAS    = 113
DOMINIO_ARCOS             = 120
DOMINIO_ARREMESSO         = 121

-- ============================================================
-- ESPECIALIDADES DE DESARMADO (SPA v4.0)
-- ============================================================
DOMINIO_DESARMADO_PURO     = 130
DOMINIO_DESARMADO_ESCUDO   = 131
DOMINIO_ARMAS_PUNHO        = 132
DOMINIO_BASTOES_ARCANOS    = 133

-- Compatibilidade com código antigo
DOMINIO_DESARMADO_LEVE    = 130
DOMINIO_DESARMADO_PESADO  = 131

-- ============================================================
-- DOMÍNIOS ELEMENTAIS E MÁGICOS
-- ============================================================
DOMINIO_FOGO_AR       = 23
DOMINIO_AGUA_GELO     = 24
DOMINIO_TERRA_VENENO  = 25
DOMINIO_SAGRADO_MORTE = 200

DOMINIO_WANDS = 210
DOMINIO_RODS  = 211
DOMINIO_RUNAS = 212

-- ============================================================
-- OUTROS
-- ============================================================
DOMINIO_SOBREVIVENCIA = 400

-- ============================================================
-- WEAPON TYPES REAIS DO CANARY
-- ============================================================
WEAPON_NONE    = 0
WEAPON_SWORD   = 1
WEAPON_CLUB    = 2
WEAPON_AXE     = 3
WEAPON_SHIELD  = 4
WEAPON_DISTANCE = 5
WEAPON_WAND    = 6
WEAPON_AMMO    = 7
WEAPON_MISSILE = 8
WEAPON_FIST    = 9

-- ============================================================
-- HIERARQUIA DE DOMÍNIOS (DOMAIN_TREE)
-- ============================================================
DOMAIN_TREE = {
    [100] = { secondary = 10, primary = 1 },
    [101] = { secondary = 10, primary = 1 },
    [110] = { secondary = 11, primary = 1 },
    [111] = { secondary = 11, primary = 1 },
    [112] = { secondary = 12, primary = 1 },
    [113] = { secondary = 12, primary = 1 },
    [120] = { secondary = 13, primary = 1 },
    [121] = { secondary = 13, primary = 1 },
    [130] = { secondary = 14, primary = 1 },
    [131] = { secondary = 14, primary = 1 },
    [132] = { secondary = 14, primary = 1 },
    [133] = { secondary = 14, primary = 1 },
    [23]  = { secondary = 20, primary = 2 },
    [24]  = { secondary = 20, primary = 2 },
    [25]  = { secondary = 20, primary = 2 },
    [200] = { secondary = 21, primary = 2 },
    [210] = { secondary = 22, primary = 2 },
    [211] = { secondary = 22, primary = 2 },
    [212] = { secondary = 22, primary = 2 },
    [10] = { primary = 1 },
    [11] = { primary = 1 },
    [12] = { primary = 1 },
    [13] = { primary = 1 },
    [14] = { primary = 1 },
    [15] = { primary = 1 },
    [20] = { primary = 2 },
    [21] = { primary = 2 },
    [22] = { primary = 2 },
    [1] = {},
    [2] = {},
    [3] = {},
    [4] = {},
}

-- Tabelas preenchidas pela buildDomainHierarchy
domainHierarchy = {}
secondaryParent = {}
ALL_DOMINIOS = {}

local function buildDomainHierarchy()
    domainHierarchy = {}
    secondaryParent = {}
    ALL_DOMINIOS = {}
    for id, data in pairs(DOMAIN_TREE) do
        table.insert(ALL_DOMINIOS, id)
        if data.secondary then
            domainHierarchy[id] = data.secondary
            secondaryParent[data.secondary] = data.primary
        end
    end
end
buildDomainHierarchy()

-- ============================================================
-- CURVA DE PROGRESSÃO
-- ============================================================
NIVEL_PONTOS = {
    50, 120, 300, 740, 1800,
    2500, 3450, 4750, 6550, 9000,
    12900, 18400, 26300, 37600, 54000,
    69000, 87000, 110000, 140000, 180000
}

-- ============================================================
-- LIMITES GLOBAIS
-- ============================================================
SPEED_MIN = 0.40
DAMAGE_MAX = 1.80

-- ============================================================
-- MAPEAMENTOS RÁPIDOS
-- ============================================================
weaponDomains = {
    [WEAPON_SWORD]    = 10,
    [WEAPON_AXE]      = 11,
    [WEAPON_CLUB]     = 12,
    [WEAPON_DISTANCE] = 13,
    [WEAPON_MISSILE]  = 13,
    [WEAPON_WAND]     = 22,
}

-- Mapeamento de ID de arma fist ? tipo de dano elemental (COMBAT_*)
ELEMENTAL_BOND = {
    -- Garras Sanguíneas (Bakragore) ? Earth
    [50157] = COMBAT_EARTHDAMAGE,
    [50158] = COMBAT_EARTHDAMAGE,

    -- Soulkamas ? Energy
    [50159] = COMBAT_ENERGYDAMAGE,

    -- Naga Katar (Timira) ? Earth
    [50160] = COMBAT_EARTHDAMAGE,

    -- Falcão Sai (Oberon) ? Physical
    [50161] = COMBAT_PHYSICALDAMAGE,

    -- Garras de Leão (Ancient Lion Knight) ? Energy
    [50162] = COMBAT_ENERGYDAMAGE,

    -- Katares Umbrais ? Physical
    [50163] = COMBAT_PHYSICALDAMAGE,
    [50164] = COMBAT_PHYSICALDAMAGE,
    [50165] = COMBAT_PHYSICALDAMAGE,

    -- Luz Jo Pessoal ? Energy
    [50166] = COMBAT_ENERGYDAMAGE,

    -- Cobra Bo (Scarlett) ? Earth
    [50167] = COMBAT_EARTHDAMAGE,

    -- Nunchaku da Destruição ? Physical
    [50168] = COMBAT_PHYSICALDAMAGE,

    -- Pá de Lua Crescente Sobrenatural (Brainstealer) ? Energy
    [50169] = COMBAT_ENERGYDAMAGE,
    [50170] = COMBAT_ENERGYDAMAGE,

    -- Pessoal Jo ? Energy
    [50171] = COMBAT_ENERGYDAMAGE,

    -- Garras de Profundidade (Ancient Spawn of Morgathla) ? Energy
    [50176] = COMBAT_ENERGYDAMAGE,

    -- Par de Punhos de Monge ? Physical
    [50181] = COMBAT_PHYSICALDAMAGE,

    -- Nunchaku ? Earth
    [50182] = COMBAT_EARTHDAMAGE,

    -- Sai ? Energy
    [50183] = COMBAT_ENERGYDAMAGE,

    -- Âmbar Kusarigama (Rootkraken) ? Physical
    [50239] = COMBAT_PHYSICALDAMAGE,

    -- Garras Inferniarcas (Arbaziloth) ? Energy
    [50250] = COMBAT_ENERGYDAMAGE,
    [50251] = COMBAT_ENERGYDAMAGE,
    [50252] = COMBAT_ENERGYDAMAGE,
    [50253] = COMBAT_ENERGYDAMAGE,

    -- Sai Tradicional ? Physical
    [10389] = COMBAT_PHYSICALDAMAGE,

    -- Drachaku (Dragonking Zyrtarch) ? Energy
    [10391] = COMBAT_ENERGYDAMAGE,

    -- Bambu Jo (Ratmiral) ? Earth
    [50270] = COMBAT_EARTHDAMAGE,

    -- Iluminação ? Physical (sem elemento explícito)
    [50271] = COMBAT_PHYSICALDAMAGE,
    [50272] = COMBAT_PHYSICALDAMAGE,
    [50273] = COMBAT_PHYSICALDAMAGE,

    -- Transcendente Bo ? Earth (provavelmente)
    [51308] = COMBAT_EARTHDAMAGE,
}

damageDomains = {
    [COMBAT_FIREDAMAGE]   = 23,
    [COMBAT_ICEDAMAGE]    = 24,
    [COMBAT_EARTHDAMAGE]  = 25,
    [COMBAT_ENERGYDAMAGE] = 23,
    [COMBAT_DEATHDAMAGE]  = 200,
    [COMBAT_HOLYDAMAGE]   = 200,
}

toolDomains = {
    [3456] = 31, [3483] = 32, [5710] = 43, [3458] = 30, [3308] = 30,
}

-- ============================================================
-- STORAGES DO SPA
-- ============================================================
STORAGE = {
    SPEED_MOD           = 90004,
    DAMAGE_MOD          = 90005,
    MANA_REGEN_MOD      = 90006,
    HEALTH_REGEN_MOD    = 90007,
    LIFE_LEECH          = 90008,
    MANA_LEECH          = 90009,

    STEALTH_BREAK_TIME  = 91001,

    HABILIDADE_BASE     = 91500,
    HABILIDADE_LOCK     = 91600,

    BUFF_BASE           = 96000,

    AFINIDADE_BUFFER    = 95001,
    SINTONIA_LAST_CHECK = 92020,
    LAMPEJO_EXPIRE      = 92001,

    DESARMADO_LEVEL     = 97000,
    HARMONY             = 97880,
    SKILLTREE_BASE      = 94000,
}

-- Virtudes do Monk (valores do enum Virtue_t no C++)
Virtue_t = {
    None = 0,
    Harmony = 1,
    Justice = 2,
    Sustain = 3
}

print("DEBUG: constantes.lua (v4.0) carregado.")