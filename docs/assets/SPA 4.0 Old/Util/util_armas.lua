--[[
    Projeto MCR ? util_armas.lua (v3.0)
    Funções utilitárias para armas, escudos e nomes de domínios.
    Inclui mapeamento de estilos de armas de Monk (FIST_STYLE).
--]]

local bit = require("bit")

DOMINIO_NOMES = {
    [1]="Combate", [2]="Magia", [3]="Ofícios", [4]="Natureza",
    [10]="Lâminas", [11]="Machados", [12]="Clavas", [13]="Precisão", [14]="Desarmado", [15]="Escudo",
    [20]="Elementos", [21]="Espectro", [22]="Runologia",
    [23]="Fogo e Ar", [24]="Água e Gelo", [25]="Terra e Veneno",
    [30]="Ofícios Gerais", [40]="Natureza Geral",
    [100]="Espadas Leves", [101]="Espadas Pesadas",
    [110]="Machados Leves", [111]="Machados Pesados",
    [112]="Clavas Leves", [113]="Clavas Pesadas",
    [120]="Arcos", [121]="Arremesso",
    [130]="Desarmado Puro", [131]="Desarmado com Escudo",
    [132]="Armas de Punho", [133]="Bastões Arcanos",
    [200]="Sagrado e Morte",
    [210]="Wands", [211]="Rods", [212]="Runas",
}

function getNomeDominio(id)
    return DOMINIO_NOMES[id] or "Desconhecido"
end

function hasShield(p)
    local l = p:getSlotItem(CONST_SLOT_LEFT)
    local r = p:getSlotItem(CONST_SLOT_RIGHT)
    return (l and l:getType():getWeaponType()==WEAPON_SHIELD) or
           (r and r:getType():getWeaponType()==WEAPON_SHIELD)
end

function getWeaponType(p)
    local left = p:getSlotItem(CONST_SLOT_LEFT)
    local right = p:getSlotItem(CONST_SLOT_RIGHT)
    local weapon = nil
    if left and left:getType():getWeaponType() ~= WEAPON_SHIELD and left:getType():getWeaponType() ~= 0 then
        weapon = left
    elseif right and right:getType():getWeaponType() ~= WEAPON_SHIELD and right:getType():getWeaponType() ~= 0 then
        weapon = right
    end
    return weapon and weapon:getType():getWeaponType() or WEAPON_FIST
end

function getWeaponId(p)
    local left = p:getSlotItem(CONST_SLOT_LEFT)
    local right = p:getSlotItem(CONST_SLOT_RIGHT)
    local weapon = nil
    if left and left:getType():getWeaponType() ~= WEAPON_SHIELD then
        weapon = left
    elseif right and right:getType():getWeaponType() ~= WEAPON_SHIELD then
        weapon = right
    end
    return weapon and weapon:getId() or 0
end

function isWeaponTwoHanded(weapon)
    local itemType = weapon:getType()
    if not itemType then return false end
    if itemType.getSlotPosition then
        local ok, slotPos = pcall(itemType.getSlotPosition, itemType)
        if ok and type(slotPos) == "number" then
            return bit.band(slotPos, 2048) ~= 0
        end
    end
    if itemType.getSlotType then
        local ok, slotStr = pcall(itemType.getSlotType, itemType)
        if ok and type(slotStr) == "string" then
            return slotStr == "two-handed"
        end
    end
    return false
end

-- Tabela de estilos das armas de Monk (fist)
FIST_STYLE = {
    -- Bastões Arcanos (two-handed)
    [50166] = "bastao",  -- Luz Jo Pessoal
    [50167] = "bastao",  -- Cobra Bo
    [50168] = "bastao",  -- Nunchaku da Destruição
    [50169] = "bastao",  -- Pá de Lua Crescente Sobrenatural
    [50170] = "bastao",  -- Pá Dourada de Lua Crescente Sobrenatural
    [50171] = "bastao",  -- Pessoal Jo
    [50182] = "bastao",  -- Nunchaku
    [50270] = "bastao",  -- Bambu Jo
    [50272] = "bastao",  -- Sai da Iluminação
    [50273] = "bastao",  -- Nunchaku da Iluminação
    [51308] = "bastao",  -- Transcendente Bo
    -- Armas de Punho (dualwielding)
    [50157] = "punho",   -- Garras Sanguíneas
    [50158] = "punho",   -- Grandes Garras Sanguíneas
    [50159] = "punho",   -- Soulkamas
    [50160] = "punho",   -- Naga Katar
    [50161] = "punho",   -- Falcão Sai
    [50162] = "punho",   -- Garras de Leão
    [50163] = "punho",   -- Katar Umbral Bruto
    [50164] = "punho",   -- Katar Umbral
    [50165] = "punho",   -- Mestre Umbral Katar
    [50176] = "punho",   -- Garras de Profundidade
    [50181] = "punho",   -- Par de Punhos de Monge
    [50183] = "punho",   -- Sai
    [50239] = "punho",   -- Âmbar Kusarigama
    [50250] = "punho",   -- Garras Inferniarcas
    [50251] = "punho",   -- Rasgando as Garras do Inferniarca
    [50252] = "punho",   -- Drenando as Garras do Inferniarca
    [50253] = "punho",   -- Sugando Garras Inferniarcas
    [10389] = "punho",   -- Sai Tradicional
    [10391] = "punho",   -- Drachaku
}

function getWeaponEspecialidade(p, weapon)
    if not weapon then
        return hasShield(p) and DOMINIO_DESARMADO_ESCUDO or DOMINIO_DESARMADO_PURO
    end
    local wt = weapon:getType():getWeaponType()
    local esc = hasShield(p)
    local twoHanded = isWeaponTwoHanded(weapon)

    if wt == WEAPON_SWORD then
        return twoHanded and DOMINIO_ESPADAS_PESADAS or DOMINIO_ESPADAS_LEVES
    elseif wt == WEAPON_AXE then
        return twoHanded and DOMINIO_MACHADOS_PESADOS or DOMINIO_MACHADOS_LEVES
    elseif wt == WEAPON_CLUB then
        return twoHanded and DOMINIO_CLAVAS_PESADAS or DOMINIO_CLAVAS_LEVES
    elseif wt == WEAPON_DISTANCE then
        return twoHanded and DOMINIO_ARCOS or DOMINIO_ARREMESSO
    elseif wt == WEAPON_MISSILE then
        return DOMINIO_ARREMESSO
    elseif wt == WEAPON_WAND then
        return DOMINIO_WANDS
    elseif wt == WEAPON_FIST then
        local style = FIST_STYLE[weapon:getId()]
        if style == "punho" then
            return DOMINIO_ARMAS_PUNHO
        elseif style == "bastao" then
            return DOMINIO_BASTOES_ARCANOS
        else
            return twoHanded and DOMINIO_BASTOES_ARCANOS or DOMINIO_ARMAS_PUNHO
        end
    else
        return esc and DOMINIO_DESARMADO_ESCUDO or DOMINIO_DESARMADO_PURO
    end
end

-- Mapeamento de shootType ? CONST_ANI
local SHOOT_TYPE_TO_ANI = {
    ["spear"] = CONST_ANI_SPEAR,
    ["bolt"] = CONST_ANI_BOLT,
    ["arrow"] = CONST_ANI_ARROW,
    ["fire"] = CONST_ANI_FIRE,
    ["energy"] = CONST_ANI_ENERGY,
    ["poisonarrow"] = CONST_ANI_POISONARROW,
    ["burstarrow"] = CONST_ANI_BURSTARROW,
    ["throwingstar"] = CONST_ANI_THROWINGSTAR,
    ["throwingknife"] = CONST_ANI_THROWINGKNIFE,
    ["smallstone"] = CONST_ANI_SMALLSTONE,
    ["death"] = CONST_ANI_DEATH,
    ["largerock"] = CONST_ANI_LARGEROCK,
    ["snowball"] = CONST_ANI_SNOWBALL,
    ["powerbolt"] = CONST_ANI_POWERBOLT,
    ["poison"] = CONST_ANI_POISON,
    ["infernalbolt"] = CONST_ANI_INFERNALBOLT,
    ["huntingspear"] = CONST_ANI_HUNTINGSPEAR,
    ["enchantedspear"] = CONST_ANI_ENCHANTEDSPEAR,
    ["redstar"] = CONST_ANI_REDSTAR,
    ["greenstar"] = CONST_ANI_GREENSTAR,
    ["royalspear"] = CONST_ANI_ROYALSPEAR,
    ["sniperarrow"] = CONST_ANI_SNIPERARROW,
    ["onyxarrow"] = CONST_ANI_ONYXARROW,
    ["piercingbolt"] = CONST_ANI_PIERCINGBOLT,
    ["whirlwindsword"] = CONST_ANI_WHIRLWINDSWORD,
    ["whirlwindaxe"] = CONST_ANI_WHIRLWINDAXE,
    ["whirlwindclub"] = CONST_ANI_WHIRLWINDCLUB,
    ["etherealspear"] = CONST_ANI_ETHEREALSPEAR,
    ["ice"] = CONST_ANI_ICE,
    ["earth"] = CONST_ANI_EARTH,
    ["holy"] = CONST_ANI_HOLY,
    ["suddendeath"] = CONST_ANI_SUDDENDEATH,
    ["flasharrow"] = CONST_ANI_FLASHARROW,
    ["flammingarrow"] = CONST_ANI_FLAMMINGARROW,
    ["flamingarrow"] = CONST_ANI_FLAMMINGARROW,
    ["shiverarrow"] = CONST_ANI_SHIVERARROW,
    ["energyball"] = CONST_ANI_ENERGYBALL,
    ["smallice"] = CONST_ANI_SMALLICE,
    ["smallholy"] = CONST_ANI_SMALLHOLY,
    ["smallearth"] = CONST_ANI_SMALLEARTH,
    ["eartharrow"] = CONST_ANI_EARTHARROW,
    ["explosion"] = CONST_ANI_EXPLOSION,
    ["cake"] = CONST_ANI_CAKE,
}

function getDistanceAnim(player)
    -- 1. Tenta pela munição
    local ammo = player:getSlotItem(CONST_SLOT_AMMO)
    if ammo then
        local ammoType = ammo:getType()
        if ammoType and ammoType.shootType then
            local ani = SHOOT_TYPE_TO_ANI[ammoType.shootType]
            if ani then return ani end
        end
    end

    -- 2. Tenta pela arma da mão
    local weapon = player:getSlotItem(CONST_SLOT_LEFT) or player:getSlotItem(CONST_SLOT_RIGHT)
    if weapon then
        local weaponType = weapon:getType()
        if weaponType and weaponType.shootType then
            local ani = SHOOT_TYPE_TO_ANI[weaponType.shootType]
            if ani then return ani end
        end
    end

    -- 3. Fallback
    return nil
end

print("DEBUG: util_armas.lua (v3.0) carregado.")