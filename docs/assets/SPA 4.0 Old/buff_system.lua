--[[
    Projeto MCR ? SPA v4.0 ? Sistema de Buffs
--]]

function applySpeedBurst(player, multiplier, durationMs)
    if (player:getStorageValue(STORAGE.BUFF_BASE + 2) or 0) > 0 then return end
    local current = player:getAttackSpeedModifier() or 1.0
    local burst = current * multiplier
    if burst < 0.1 then burst = 0.1 end
    player:setAttackSpeedModifier(burst)
    player:setStorageValue(STORAGE.BUFF_BASE + 1, current * 1000)
    player:setStorageValue(STORAGE.BUFF_BASE + 2, 1)
    enviarMsgColorida(player, c("[Velocidade] Ataque acelerado por " .. math.floor(durationMs/1000) .. "s!", COR.COMBO_AVISO))
    local pid = player:getId()
    addEvent(function()
        local p = Player(pid)
        if p then
            p:setAttackSpeedModifier(current)
            p:setStorageValue(STORAGE.BUFF_BASE + 1, 0)
            p:setStorageValue(STORAGE.BUFF_BASE + 2, 0)
            enviarMsgColorida(p, c("[Velocidade] Ataque voltou ao normal.", COR.SISTEMA_NEUTRO))
        end
    end, durationMs)
end

function applyNextAttackCondition(player, condType, duration, damage)
    player:setStorageValue(STORAGE.BUFF_BASE + 10, condType)
    player:setStorageValue(STORAGE.BUFF_BASE + 11, duration)
    player:setStorageValue(STORAGE.BUFF_BASE + 12, damage or 0)
    player:setStorageValue(STORAGE.BUFF_BASE + 13, 1)
end

function applyDamageBoost(player, percent, numHits)
    local current = (player:getStorageValue(STORAGE.DAMAGE_MOD) or 1000) / 1000
    local boosted = current * (1 + percent/100)
    local boostedVal = math.floor(boosted * 1000 + 0.5)
    player:setStorageValue(STORAGE.DAMAGE_MOD, boostedVal)
    player:setStorageValue(STORAGE.BUFF_BASE + 20, current * 1000)
    player:setStorageValue(STORAGE.BUFF_BASE + 21, numHits)
    enviarMsgColorida(player, c("[Dano] Aumentado em " .. percent .. "% por " .. numHits .. " ataque(s)!", COR.COMBO_AVISO))
end

function applyLifeLeech(player, leechPercent, durationSec)
    player:setStorageValue(STORAGE.LIFE_LEECH, leechPercent)
    player:setStorageValue(STORAGE.BUFF_BASE + 30, os.time() + durationSec)
    enviarMsgColorida(player, c("[Life Leech] Roubo de vida ativado! (" .. leechPercent .. "%)", COR.SUCESSO_CURA))
end

function applyManaLeech(player, leechPercent, durationSec)
    player:setStorageValue(STORAGE.MANA_LEECH, leechPercent)
    player:setStorageValue(STORAGE.BUFF_BASE + 31, os.time() + durationSec)
    enviarMsgColorida(player, c("[Mana Leech] Roubo de mana ativado! (" .. leechPercent .. "%)", COR.SISTEMA_INFO))
end

function processBuffs(player)
    -- Damage boost
    local dmgHits = player:getStorageValue(STORAGE.BUFF_BASE + 21) or 0
    if dmgHits > 0 then
        dmgHits = dmgHits - 1
        if dmgHits <= 0 then
            local originalVal = player:getStorageValue(STORAGE.BUFF_BASE + 20) or 1000
            player:setStorageValue(STORAGE.DAMAGE_MOD, originalVal)
            player:setStorageValue(STORAGE.BUFF_BASE + 20, 0)
            player:setStorageValue(STORAGE.BUFF_BASE + 21, 0)
            enviarMsgColorida(player, c("[Dano] Bonus de dano expirou.", COR.SISTEMA_NEUTRO))
        else
            player:setStorageValue(STORAGE.BUFF_BASE + 21, dmgHits)
        end
    end
    -- Life leech
    local leechExpire = player:getStorageValue(STORAGE.BUFF_BASE + 30) or 0
    if leechExpire > 0 and os.time() > leechExpire then
        player:setStorageValue(STORAGE.LIFE_LEECH, 0)
        player:setStorageValue(STORAGE.BUFF_BASE + 30, 0)
        enviarMsgColorida(player, c("[Life Leech] Roubo de vida terminou.", COR.SISTEMA_NEUTRO))
    end
    -- Mana leech
    local manaExpire = player:getStorageValue(STORAGE.BUFF_BASE + 31) or 0
    if manaExpire > 0 and os.time() > manaExpire then
        player:setStorageValue(STORAGE.MANA_LEECH, 0)
        player:setStorageValue(STORAGE.BUFF_BASE + 31, 0)
        enviarMsgColorida(player, c("[Mana Leech] Roubo de mana terminou.", COR.SISTEMA_NEUTRO))
    end
    -- Condition
    local condHits = player:getStorageValue(STORAGE.BUFF_BASE + 13) or 0
    if condHits <= 0 then
        player:setStorageValue(STORAGE.BUFF_BASE + 10, 0)
        player:setStorageValue(STORAGE.BUFF_BASE + 11, 0)
        player:setStorageValue(STORAGE.BUFF_BASE + 12, 0)
        player:setStorageValue(STORAGE.BUFF_BASE + 13, 0)
    end
end

function applyPendingCondition(player, target)
    local condType = player:getStorageValue(STORAGE.BUFF_BASE + 10) or 0
    if condType == 0 then return end
    local duration = player:getStorageValue(STORAGE.BUFF_BASE + 11) or 2000
    local damage = player:getStorageValue(STORAGE.BUFF_BASE + 12) or 0
    local condition = Condition(condType, CONDITIONID_COMBAT, duration)
    if damage > 0 and (condType == CONDITION_BLEEDING or condType == CONDITION_POISON) then
        condition:setParameter(CONDITION_PARAM_PERIODICDAMAGE, damage)
        condition:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
    end
    target:addCondition(condition)
    local hitsLeft = player:getStorageValue(STORAGE.BUFF_BASE + 13) or 0
    hitsLeft = hitsLeft - 1
    player:setStorageValue(STORAGE.BUFF_BASE + 13, hitsLeft)
end

local thinkBuff = CreatureEvent("BuffThink")
thinkBuff:type("think")
thinkBuff:onThink(function(player, interval)
    local now = os.time()
    local lastCheck = player:getStorageValue(STORAGE.SINTONIA_LAST_CHECK) or 0
    if now - lastCheck < 2 then return true end
    player:setStorageValue(STORAGE.SINTONIA_LAST_CHECK, now)
    processBuffs(player)
    return true
end)
thinkBuff:register()

print("DEBUG: buff_system.lua v4.0 carregado.")