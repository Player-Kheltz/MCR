--[[
    Projeto MCR ? eventos.lua (v10.0)
    Eventos de progressão e disparo de habilidades.
    Optimizado com buffer de progressão e detecção correcta de armas.
--]]

-- ============================================================
-- DANO CAUSADO
-- ============================================================
local dmgEvent = CreatureEvent("ProgDano")
dmgEvent:onDealtDamage(function(player, target, damage, primary, secondary)
    if not player or damage <= 0 then return end
    local pontos = math.max(1, math.floor(damage / 30))
    local dominio = damageDomains[primary]
    if dominio then
        adicionarAfinidade(player, dominio, pontos)
        onDominioAction(player, dominio)
    elseif primary == COMBAT_PHYSICALDAMAGE then
        local left = player:getSlotItem(CONST_SLOT_LEFT)
        local right = player:getSlotItem(CONST_SLOT_RIGHT)
        local weapon = nil
        if left and left:getType():getWeaponType() ~= WEAPON_SHIELD and left:getType():getWeaponType() ~= 0 then
            weapon = left
        elseif right and right:getType():getWeaponType() ~= WEAPON_SHIELD and right:getType():getWeaponType() ~= 0 then
            weapon = right
        end

        if weapon then
            local dom = getWeaponEspecialidade(player, weapon)
            adicionarAfinidade(player, dom, pontos)
            onDominioAction(player, dom)
        else
            local domDesarmado = hasShield(player) and DOMINIO_DESARMADO_PESADO or DOMINIO_DESARMADO_LEVE
            adicionarAfinidade(player, domDesarmado, pontos)
            onDominioAction(player, domDesarmado)
        end

        if hasShield(player) then
            adicionarAfinidade(player, DOMINIO_ESCUDO, 1)
            onDominioAction(player, DOMINIO_ESCUDO)
        end
    end

    -- Executa habilidades de gatilho
    if executarHabilidades then
        executarHabilidades(player, "onAttack", target, damage, primary)
    end

    -- ?? Aplica passivas de auto?ataque baseadas no domínio
    aplicarPassivasAtaque(player, target, damage, primary)
end)
dmgEvent:type("dealtDamage"); dmgEvent:register()

-- ============================================================
-- MORTE DE CRIATURA
-- ============================================================
local killEvent = CreatureEvent("ProgKill")
killEvent:onKill(function(player, target, lastHit)
    if not player or not target:isMonster() then return true end
    local weapon = player:getSlotItem(CONST_SLOT_LEFT) or player:getSlotItem(CONST_SLOT_RIGHT)
    if weapon then
        local dom = getWeaponEspecialidade(player, weapon)
        adicionarAfinidade(player, dom, 5)
        onDominioAction(player, dom)
    end
    if executarHabilidades then
        executarHabilidades(player, "onKill", target, nil)
    end
    return true
end)
killEvent:type("kill"); killEvent:register()

-- ============================================================
-- USO DE ITEM (FERRAMENTAS)
-- ============================================================
local itemEvent = CreatureEvent("ProgItem")
itemEvent:onUseItem(function(player, item)
    local dom = toolDomains[item:getId()]
    if dom then
        adicionarAfinidade(player, dom, 1)
        onDominioAction(player, dom)
    end
    return true
end)
itemEvent:type("itemUse"); itemEvent:register()

-- ============================================================
-- LANÇAR MAGIA
-- ============================================================
local spellEvent = CreatureEvent("ProgSpell")
spellEvent:onSpellCast(function(player, spellName)
    local dom = spellDomain[spellName]
    if dom then
        adicionarAfinidade(player, dom, 1)
        adicionarAfinidade(player, DOMINIO_MAGIA, 1)
        onDominioAction(player, dom)
    end
    return true
end)
spellEvent:type("spell"); spellEvent:register()

-- ============================================================
-- RECEBER DANO (DEFESA)
-- ============================================================
local defEvent = CreatureEvent("ProgDefesa")
defEvent:onHealthChange(function(player, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType, origin)
    if not player or primaryDamage <= 0 then return primaryDamage, primaryType, secondaryDamage, secondaryType end
    local pontos = math.max(1, math.floor(primaryDamage / 100))
    adicionarAfinidade(player, DOMINIO_SOBREVIVENCIA, pontos)
    onDominioAction(player, DOMINIO_SOBREVIVENCIA)

    -- Bloquear com escudo: sobe Combate e Escudo, ativa habilidades de bloqueio
    if hasShield(player) then
        adicionarAfinidade(player, DOMINIO_COMBATE, 1)
        adicionarAfinidade(player, DOMINIO_ESCUDO, 1)
        onDominioAction(player, DOMINIO_COMBATE)
        onDominioAction(player, DOMINIO_ESCUDO)
        if executarHabilidades then
            executarHabilidades(player, "onBlock", attacker, primaryDamage)
        end
    end

    -- Habilidades ao receber dano
    if executarHabilidades then
        executarHabilidades(player, "onReceiveDamage", attacker, primaryDamage)
    end
    return primaryDamage, primaryType, secondaryDamage, secondaryType
end)
defEvent:type("healthChange"); defEvent:register()

print("DEBUG: eventos.lua (v10.0) carregado.")