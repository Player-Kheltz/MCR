--[[
    Projeto MCR ? SPA v4.0 ? Eventos de Progressão, Treino de Skills e Event Bus
    Inclui gatilho onBlock e onReceiveDamage para habilidades de escudo
--]]

local dmgEvent = CreatureEvent("ProgDano")
dmgEvent:onDealtDamage(function(player, target, damage, primary, secondary)
    if not player or damage <= 0 then return end
    local pontos = math.max(1, math.floor(damage / 30))
    local dominio = damageDomains[primary]
    if dominio then
        adicionarAfinidade(player, dominio, pontos)
        onDominioAction(player, dominio)
    elseif primary == COMBAT_PHYSICALDAMAGE then
        local weapon = player:getSlotItem(CONST_SLOT_LEFT)
        if weapon and (weapon:getType():getWeaponType() == WEAPON_SHIELD or weapon:getType():getWeaponType() == 0) then
            weapon = player:getSlotItem(CONST_SLOT_RIGHT)
        end
        if weapon and weapon:getType():getWeaponType() ~= WEAPON_SHIELD and weapon:getType():getWeaponType() ~= 0 then
            local dom = getWeaponEspecialidade(player, weapon)
            adicionarAfinidade(player, dom, pontos)
            onDominioAction(player, dom)
        else
            local dom = hasShield(player) and DOMINIO_DESARMADO_ESCUDO or DOMINIO_DESARMADO_PURO
            adicionarAfinidade(player, dom, pontos)
            onDominioAction(player, dom)
        end
        if hasShield(player) then
            adicionarAfinidade(player, DOMINIO_ESCUDO, 1)
            onDominioAction(player, DOMINIO_ESCUDO)
        end
    end

    local weapon = player:getSlotItem(CONST_SLOT_LEFT)
    if weapon and (weapon:getType():getWeaponType() == WEAPON_SHIELD or weapon:getType():getWeaponType() == 0) then
        weapon = player:getSlotItem(CONST_SLOT_RIGHT)
    end
    if weapon then
        local wt = weapon:getType():getWeaponType()
        if wt == WEAPON_FIST then player:addSkillTries(SKILL_FIST, 1)
        elseif wt == WEAPON_SWORD then player:addSkillTries(SKILL_SWORD, 1)
        elseif wt == WEAPON_AXE then player:addSkillTries(SKILL_AXE, 1)
        elseif wt == WEAPON_CLUB then player:addSkillTries(SKILL_CLUB, 1)
        elseif wt == WEAPON_DISTANCE or wt == WEAPON_MISSILE then player:addSkillTries(SKILL_DISTANCE, 1) end
    else
        player:addSkillTries(SKILL_FIST, 1)
    end

    if executarHabilidades then executarHabilidades(player, "onAttack", target, damage, primary) end
    aplicarPassivasAtaque(player, target, damage, primary)
    SPA.dispatchEvent("onPlayerDealtDamage", player, target, damage, primary, secondary)
end)
dmgEvent:type("dealtDamage"); dmgEvent:register()

local killEvent = CreatureEvent("ProgKill")
killEvent:onKill(function(player, target, lastHit)
    if not player or not target:isMonster() then return true end
    local weapon = player:getSlotItem(CONST_SLOT_LEFT)
    if weapon and (weapon:getType():getWeaponType() == WEAPON_SHIELD or weapon:getType():getWeaponType() == 0) then
        weapon = player:getSlotItem(CONST_SLOT_RIGHT)
    end
    if weapon then
        local dom = getWeaponEspecialidade(player, weapon)
        adicionarAfinidade(player, dom, 5)
        onDominioAction(player, dom)
    end
    if executarHabilidades then executarHabilidades(player, "onKill", target, nil) end
    SPA.dispatchEvent("onPlayerKill", player, target)
    return true
end)
killEvent:type("kill"); killEvent:register()

local itemEvent = CreatureEvent("ProgItem")
itemEvent:onUseItem(function(player, item)
    local dom = toolDomains[item:getId()]
    if dom then adicionarAfinidade(player, dom, 1); onDominioAction(player, dom) end
    return true
end)
itemEvent:type("itemUse"); itemEvent:register()

local defEvent = CreatureEvent("ProgDefesa")
defEvent:onHealthChange(function(player, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType, origin)
    if not player or primaryDamage <= 0 then
        return primaryDamage, primaryType, secondaryDamage, secondaryType
    end
    local pontos = math.max(1, math.floor(primaryDamage / 100))
    adicionarAfinidade(player, DOMINIO_SOBREVIVENCIA, pontos)
    onDominioAction(player, DOMINIO_SOBREVIVENCIA)
    if hasShield(player) then
        adicionarAfinidade(player, DOMINIO_ESCUDO, 1)
        onDominioAction(player, DOMINIO_ESCUDO)
        -- Gatilho onBlock para habilidades de escudo
        if executarHabilidades then executarHabilidades(player, "onBlock", attacker, primaryDamage) end
    end
    -- Gatilho onReceiveDamage para habilidades que reagem a dano
    if executarHabilidades then executarHabilidades(player, "onReceiveDamage", attacker, primaryDamage) end
    return primaryDamage, primaryType, secondaryDamage, secondaryType
end)
defEvent:type("healthChange"); defEvent:register()

print("DEBUG: eventos.lua v4.0 carregado.")