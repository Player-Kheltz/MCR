--[[
    Projeto MCR ? postura.lua (v11.3)
    Aplicação de posturas, bónus de Desarmado, knockback, furtividade e think.
    Life Leech e Mana Leech aplicados diretamente no evento PosturaDmg.
    Mensagem "Postura ajustada" apenas ao mudar manualmente.
--]]

local STEALTH_STORAGE = STORAGE.STEALTH_BREAK_TIME
local ultimaArma = {}

function aplicarPostura(player, mode)
    local wt = getWeaponType(player)
    local temEscudo = hasShield(player)
    local weapon = player:getSlotItem(CONST_SLOT_LEFT) or player:getSlotItem(CONST_SLOT_RIGHT)

    local baseReg = POSTURA_BASE[wt] or POSTURA_BASE.default
    local cfg = baseReg[mode]
    if not cfg then return end

    -- Estilo de Combate (Arremesso 121) ? Atleta / Espartano
    if jogadorConheceHabilidade and jogadorConheceHabilidade(player, 12103) then
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(121))
        if hasShield(player) then
            local target = player:getTarget()
            if target then
                local dist = getCreatureDistance(player, target)
                if dist > 4 then
                    local slow = Condition(CONDITION_PARALYZE, CONDITIONID_COMBAT, 2000)
                    slow:setParameter(CONDITION_PARAM_SPEED, -30)
                    target:addCondition(slow)
                elseif dist <= 2 then
                    local chance = 15 + nivel
                    if math.random(100) <= chance then
                        local dir = Position(player:getPosition()):getDirectionTo(target:getPosition())
                        if dir then target:knockback(dir) end
                    end
                    player:setAttackSpeedModifier(1.2 + nivel * 0.01)
                end
            end
        else
            local lastDmg = player:getStorageValue(97811) or 0
            local now = os.time()
            if now - lastDmg >= 4 then
                player:setStorageValue(97812, math.floor(30 + nivel * 1.5))
                player:setStorageValue(97813, 1)
            else
                player:setStorageValue(97812, 0)
                player:setStorageValue(97813, 0)
            end
            local moveBonus = Condition(CONDITION_ATTRIBUTES, CONDITIONID_COMBAT, -1)
            moveBonus:setParameter(CONDITION_PARAM_SUBID, 200)
            moveBonus:setParameter(CONDITION_PARAM_SPEED, math.floor(player:getBaseSpeed() * 0.15))
            moveBonus:setParameter(CONDITION_PARAM_BUFF_SPELL, true)
            player:addCondition(moveBonus)
        end
    end

    local estiloCfg = {}
    if wt == WEAPON_WAND then
        estiloCfg = temEscudo and RUNOLOGIA_COM_ESCUDO or RUNOLOGIA_SEM_ESCUDO
    elseif wt == WEAPON_DISTANCE then
        estiloCfg = temEscudo and ARREMESSO_COM_ESCUDO or ARREMESSO_SEM_ESCUDO
    elseif wt == WEAPON_MISSILE then
        estiloCfg = temEscudo and ARREMESSO_COM_ESCUDO or ARREMESSO_SEM_ESCUDO
    elseif not temEscudo and weapon then
        if isWeaponTwoHanded(weapon) then
            estiloCfg = PESADA_AJUSTES[wt] or {}
        else
            estiloCfg = AGIL_AJUSTES[wt] or {}
        end
    end

    local shieldCfg = temEscudo and SHIELD_POSTURA[mode] or {}

    -- Leitura em lote das storages de bónus do SPA
    local storages = player:getStorages(
        STORAGE.SPEED_MOD, STORAGE.DAMAGE_MOD,
        STORAGE.MANA_REGEN_MOD, STORAGE.HEALTH_REGEN_MOD
    )
    local sSpd = (storages[STORAGE.SPEED_MOD] or 1000) / 1000
    local sDmg = (storages[STORAGE.DAMAGE_MOD] or 1000) / 1000
    local sManR = (storages[STORAGE.MANA_REGEN_MOD] or 1000) / 1000
    local sHpR = (storages[STORAGE.HEALTH_REGEN_MOD] or 1000) / 1000

    local baseSpd = (cfg.speedMod or 1.0) * (estiloCfg.speedMod or 1.0)
    local finalSpd = baseSpd * sSpd
    if finalSpd < 0.5 then finalSpd = 0.5 end

    local finalDmg = ((cfg.damageMod or 1.0) + (estiloCfg.damageModExtra or 0)) * sDmg
    local finalManR = (cfg.manaRegenMod or 1.0) * (estiloCfg.manaRegenMod or 1.0) * sManR
    local finalHpR = (cfg.healthRegenMod or 1.0) * (shieldCfg.healthRegenMod or 1.0) * sHpR
    local finalDef = math.min(cfg.damageTakenMod or 1.0, shieldCfg.damageTakenMod or 1.0, estiloCfg.damageTakenMod or 1.0)
    local push = shieldCfg.canPush or false
    local stealth = cfg.stealth or false
    local kb = estiloCfg.knockback or cfg.knockback or false
    local kbChance = estiloCfg.knockbackChance or cfg.knockbackChance or 0
    local ricochete = estiloCfg.ricocheteChance or 0

    -- Velocidade de ataque (só altera se não houver burst ativo)
    local now = os.time() * 1000
    local burstExpire = player:getStorageValue(STORAGE.BUFF_BASE + 2) or 0
    if not (burstExpire > 0 and now < burstExpire) then
        player:setAttackSpeedModifier(finalSpd)
    end

    player:setManaRegenModifier(finalManR)
    player:setHealthRegenModifier(finalHpR)
    if cfg.manaRegenTicksMod then player:setManaRegenTicksModifier(cfg.manaRegenTicksMod) end
    if cfg.healthRegenTicksMod then player:setHealthRegenTicksModifier(cfg.healthRegenTicksMod) end
    player:setRangeModifier(cfg.rangeMod or 0)

    -- Stealth seguro
    if stealth then
        player:setStealth(true)
    else
        player:setStealth(false)
    end

    player:setCanPushCreatures(push)
    if player.setDamageTakenModifier then player:setDamageTakenModifier(finalDef) end

    player:setStorageValue(90002, kb and 1 or 0)
    player:setStorageValue(90013, kbChance)
    player:setStorageValue(90003, cfg.stealthDelay or 0)
    player:setStorageValue(90011, cfg.effects and 1 or 0)
    player:setStorageValue(90014, ricochete)

    -- BÓNUS DE DESARMADO
        local left = player:getSlotItem(CONST_SLOT_LEFT)
    local right = player:getSlotItem(CONST_SLOT_RIGHT)
    local temArma = false
    if left and left:getType():getWeaponType() ~= WEAPON_SHIELD then
        temArma = true
    end
    if right and right:getType():getWeaponType() ~= WEAPON_SHIELD then
        temArma = true
    end

    if not temArma then
        local nivelDesarmado = getNivelPorAfinidade(player:getDominioAfinidade(14) or 0)
        local skillBonus = 0
        local dmgBonus = 0

        if nivelDesarmado >= 20 then
            skillBonus = 120; dmgBonus = 30
        elseif nivelDesarmado >= 16 then
            skillBonus = 90; dmgBonus = 20
        elseif nivelDesarmado >= 11 then
            skillBonus = 60; dmgBonus = 15
        elseif nivelDesarmado >= 6 then
            skillBonus = 30; dmgBonus = 10
        else
            skillBonus = 10; dmgBonus = 0
        end

        -- Remove condições anteriores para evitar acumulação
        player:removeCondition(CONDITION_ATTRIBUTES, CONDITIONID_COMBAT, 98)
        player:removeCondition(CONDITION_ATTRIBUTES, CONDITIONID_COMBAT, 99)

        -- Aplica nova condição de skill com duração de 1 hora (3600000 ms)
        local condSkill = Condition(CONDITION_ATTRIBUTES, CONDITIONID_COMBAT, 3600000)
        condSkill:setParameter(CONDITION_PARAM_SUBID, 98)
        condSkill:setParameter(CONDITION_PARAM_SKILL_FIST, skillBonus)
        condSkill:setParameter(CONDITION_PARAM_BUFF_SPELL, true)
        player:addCondition(condSkill)

        if dmgBonus > 0 then
            local condDmg = Condition(CONDITION_ATTRIBUTES, CONDITIONID_COMBAT, 3600000)
            condDmg:setParameter(CONDITION_PARAM_SUBID, 99)
            condDmg:setParameter(CONDITION_PARAM_BUFF_DAMAGEDEALT, dmgBonus)
            condDmg:setParameter(CONDITION_PARAM_BUFF_SPELL, true)
            player:addCondition(condDmg)
        end

        -- Atualiza a storage para o C++ ler
        player:setStorageValue(STORAGE.DESARMADO_LEVEL, nivelDesarmado)
    else
        -- Com arma equipada, remove os bónus desarmados e zera a storage
        player:removeCondition(CONDITION_ATTRIBUTES, CONDITIONID_COMBAT, 98)
        player:removeCondition(CONDITION_ATTRIBUTES, CONDITIONID_COMBAT, 99)
        player:setStorageValue(STORAGE.DESARMADO_LEVEL, 0)
    end
end

-- ============================================================
-- EVENTOS
-- ============================================================

local changeEvent = CreatureEvent("PosturaChange")
changeEvent:onFightModeChange(function(player, oldMode, newMode)
    aplicarPostura(player, newMode)

    local nomePostura = ({[1]="Ímpeto", [2]="Equilíbrio", [3]="Guarda"})[newMode] or ""
    local corPostura = COR.POSTURA_EQUILIBRIO
    if newMode == FIGHTMODE_ATTACK then corPostura = COR.POSTURA_IMPETO
    elseif newMode == FIGHTMODE_DEFENSE then corPostura = COR.POSTURA_GUARDA end
    enviarMsgColorida(player, "Postura ajustada: " .. c(nomePostura, corPostura) .. ".")
end)
changeEvent:type("fightmodechange"); changeEvent:register()

local dmgEvent = CreatureEvent("PosturaDmg")
dmgEvent:onDealtDamage(function(player, target, damage, primary, secondary)
    if not player or not target or damage <= 0 then return damage, primary, secondary end

    local armaAtual = getWeaponId(player)
    local pid = player:getId()
    if ultimaArma[pid] and ultimaArma[pid] ~= armaAtual then
        aplicarPostura(player, player:getFightMode())
    end
    ultimaArma[pid] = armaAtual

    -- knockback gerido pelo passivas_ataque.lua

    if player:isStealth() then
        player:setStealth(false)
        player:setStorageValue(STEALTH_STORAGE, os.time())
    end

    if checkCombos then checkCombos(player, target) end

    applyPendingCondition(player, target)
    processBuffs(player)

    -- ============================================================
    -- LIFE LEECH E MANA LEECH (SPA)
    -- ============================================================
    local lifeLeech = player:getStorageValue(STORAGE.LIFE_LEECH) or 0
    if lifeLeech > 0 then
        local healAmount = math.floor(damage * lifeLeech / 100)
        if healAmount > 0 then
            player:addHealth(healAmount)
            -- Feedback silencioso (pode ser removido se poluir)
            -- enviarMsgColorida(player, c("[Life Leech] Você drena " .. healAmount .. " de vida.", COR.SUCESSO_CURA))
        end
    end

    local manaLeech = player:getStorageValue(STORAGE.MANA_LEECH) or 0
    if manaLeech > 0 then
        local manaAmount = math.floor(damage * manaLeech / 100)
        if manaAmount > 0 then
            player:addMana(manaAmount)
        end
    end

    return damage, primary, secondary
end)
dmgEvent:type("dealtDamage"); dmgEvent:register()

local ultimaArmaThink = {}

local thinkEvent = CreatureEvent("PosturaThink")
thinkEvent:onThink(function(player, interval)
    local now = os.time()
    local lastCheck = player:getStorageValue(STORAGE.SINTONIA_LAST_CHECK) or 0
    if now - lastCheck < 2 then return true end
    player:setStorageValue(STORAGE.SINTONIA_LAST_CHECK, now)

    local pid = player:getId()
    local armaAtual = getWeaponId(player)

    if ultimaArmaThink[pid] and ultimaArmaThink[pid] ~= armaAtual then
        aplicarPostura(player, player:getFightMode())
    end
    ultimaArmaThink[pid] = armaAtual

    if not player:isStealth() then
        local lastBreak = player:getStorageValue(STEALTH_STORAGE) or 0
        local delay = player:getStorageValue(90003) or 1500
        if lastBreak > 0 and (os.time() - lastBreak) * 1000 >= delay then
            local cfg = (POSTURA_BASE[getWeaponType(player)] or POSTURA_BASE.default)[player:getFightMode()]
            if cfg and cfg.stealth then
                player:setStealth(true)
                player:setStorageValue(STEALTH_STORAGE, 0)
            end
        end
    end
    return true
end)
thinkEvent:type("think"); thinkEvent:register()

local logoutEvent = CreatureEvent("PosturaLogout")
logoutEvent:onLogout(function(player)
    player:setAttackSpeedModifier(1.0); player:setManaRegenModifier(1.0); player:setHealthRegenModifier(1.0)
    player:setManaRegenTicksModifier(1.0); player:setHealthRegenTicksModifier(1.0)
    player:setRangeModifier(0); player:setStealth(false); player:setCanPushCreatures(false)
    if player.setDamageTakenModifier then player:setDamageTakenModifier(1.0) end
    player:setStorageValue(90002,0); player:setStorageValue(90003,0); player:setStorageValue(90011,0)
    player:setStorageValue(90013,0); player:setStorageValue(90014,0); player:setStorageValue(STEALTH_STORAGE,0)
    player:setStorageValue(STORAGE.LIFE_LEECH, 0)
    player:setStorageValue(STORAGE.MANA_LEECH, 0)
    player:setStorageValue(STORAGE.BUFF_BASE + 30, 0)
    player:setStorageValue(STORAGE.BUFF_BASE + 31, 0)
    ultimaArma[player:getId()] = nil
    return true
end)
logoutEvent:type("logout"); logoutEvent:register()

print("DEBUG: postura.lua (v11.3) carregado.")