--[[
    Projeto MCR ? SPA v4.0 ? Sintonia (Lampejos, Vínculos, Maestria)
--]]

local LAMPEJO_DURATION = 8
local VINCULO_CARENCIA = 15

function onDominioAction(player, dominioId)
    local now = os.time()
    local history = player:getActionHistory(30)
    if not history or #history < 3 then return end

    local count5, total5 = 0, math.min(#history, 5)
    for i = 1, total5 do
        if history[#history - i + 1].dominioId == dominioId then count5 = count5 + 1 end
    end
    local lampejoAtivo = count5 >= 3

    local count30, total30 = 0, math.min(#history, 30)
    for i = 1, total30 do
        if history[#history - i + 1].dominioId == dominioId then count30 = count30 + 1 end
    end
    local vinculoAtivo = total30 >= 15 and (count30 / total30) > 0.5

    local currentState = player:getDominioState(dominioId) or 0

    if vinculoAtivo and currentState < 2 then
        player:setDominioState(dominioId, 2)
        enviarMsgColorida(player, "Você aprofunda um Vínculo com " .. c(getNomeDominio(dominioId), corDominio(dominioId)) .. ".")
    elseif not vinculoAtivo and currentState == 2 then
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(dominioId))
        if nivel < 20 then
            player:setDominioState(dominioId, 0)
            enviarMsgColorida(player, "Seu Vínculo com " .. c(getNomeDominio(dominioId), corDominio(dominioId)) .. " se desfez.")
        end
    end

    if lampejoAtivo and currentState < 1 then
        player:setDominioState(dominioId, 1)
        player:setStorageValue(STORAGE.LAMPEJO_EXPIRE + dominioId, now + LAMPEJO_DURATION)
    elseif lampejoAtivo and currentState == 1 then
        player:setStorageValue(STORAGE.LAMPEJO_EXPIRE + dominioId, now + LAMPEJO_DURATION)
    elseif not lampejoAtivo and currentState == 1 then
        player:setDominioState(dominioId, 0)
        player:setStorageValue(STORAGE.LAMPEJO_EXPIRE + dominioId, 0)
    end

    aplicarBonus(player)
end

function aplicarBonus(player)
    local states = player:getAllActiveStates()
    local speedBonus, damageBonus = 0, 0
    for domId, state in pairs(states) do
        local nv = getNivelPorAfinidade(player:getDominioAfinidade(domId))
        if state == 2 then
            speedBonus = speedBonus + nv * 0.04
            damageBonus = damageBonus + nv * 0.06
        elseif state == 1 then
            speedBonus = speedBonus + nv * 0.02
            damageBonus = damageBonus + nv * 0.03
        end
    end
    speedBonus = math.min(speedBonus, 0.60)
    damageBonus = math.min(damageBonus, 0.80)

    local finalSpeed = math.max(1.0 - speedBonus, SPEED_MIN)
    local finalDmg = math.min(1.0 + damageBonus, DAMAGE_MAX)

    local newSpeedVal = math.floor(finalSpeed * 1000 + 0.5)
    local newDmgVal = math.floor(finalDmg * 1000 + 0.5)

    local currentSpeed = player:getStorageValue(STORAGE.SPEED_MOD) or 1000
    local currentDmg = player:getStorageValue(STORAGE.DAMAGE_MOD) or 1000

    if newSpeedVal ~= currentSpeed or newDmgVal ~= currentDmg then
        player:setStorageValue(STORAGE.SPEED_MOD, newSpeedVal)
        player:setStorageValue(STORAGE.DAMAGE_MOD, newDmgVal)
        aplicarPostura(player, player:getFightMode())
    end

    if atualizarTransformacoes then atualizarTransformacoes(player) end
end

local thinkEvent = CreatureEvent("SintoniaThink")
thinkEvent:onThink(function(player, interval)
    local now = os.time()
    local lastCheck = player:getStorageValue(STORAGE.SINTONIA_LAST_CHECK) or 0
    if now - lastCheck < 2 then return true end
    player:setStorageValue(STORAGE.SINTONIA_LAST_CHECK, now)

    if descarregarBuffer then descarregarBuffer(player) end

    local states = player:getAllActiveStates()
    for domId, state in pairs(states) do
        if state == 1 then
            local expireTime = player:getStorageValue(STORAGE.LAMPEJO_EXPIRE + domId) or 0
            if now >= expireTime then
                player:setDominioState(domId, 0)
                player:setStorageValue(STORAGE.LAMPEJO_EXPIRE + domId, 0)
            end
        elseif state == 2 then
            local nivel = getNivelPorAfinidade(player:getDominioAfinidade(domId))
            if nivel < 20 then
                local history = player:getActionHistory(1)
                if history and #history > 0 then
                    if history[1].dominioId == domId and (now - history[1].timestamp) > VINCULO_CARENCIA then
                        player:setDominioState(domId, 0)
                        enviarMsgColorida(player, "Seu Vínculo com " .. c(getNomeDominio(domId), corDominio(domId)) .. " se dissipou.")
                    end
                end
            end
        end
    end
    aplicarBonus(player)
    if SPA and SPA.checkSkillTrees then SPA.checkSkillTrees(player) end
    return true
end)
thinkEvent:type("think"); thinkEvent:register()

print("DEBUG: sintonia.lua v4.0 carregado.")