--[[
    Projeto MCR ? sintonia.lua (v11.0)
    Lampejos, Vínculos, bónus aditivos e integração com o buffer de progressão.
--]]

local LAMPEJO_DURATION = 8
local VINCULO_CARENCIA = 15

-- ============================================================
-- AÇÃO DE DOMÍNIO (chamada a cada ataque via eventos.lua)
-- ============================================================
function onDominioAction(player, dominioId)
    local now = os.time()
    local history = player:getActionHistory(30)
    if not history or #history < 3 then return end

    -- Lampejo: 3 das últimas 5 ações são deste domínio
    local count5 = 0
    local total5 = math.min(#history, 5)
    for i = 1, total5 do
        if history[#history - i + 1].dominioId == dominioId then
            count5 = count5 + 1
        end
    end
    local lampejoAtivo = count5 >= 3

    -- Vínculo: >50% das últimas 30 ações são deste domínio
    local count30 = 0
    local total30 = math.min(#history, 30)
    for i = 1, total30 do
        if history[#history - i + 1].dominioId == dominioId then
            count30 = count30 + 1
        end
    end
    local vinculoAtivo = total30 >= 15 and (count30 / total30) > 0.5

    local currentState = player:getDominioState(dominioId) or 0

    -- Atualiza Vínculo
    if vinculoAtivo and currentState < 2 then
        player:setDominioState(dominioId, 2)
        local nome = getNomeDominio(dominioId)
        enviarMsgColorida(player, "Você aprofunda um Vínculo com " .. c(nome, corDominio(dominioId)) .. ".")
    elseif not vinculoAtivo and currentState == 2 then
        player:setDominioState(dominioId, 0)
        local nome = getNomeDominio(dominioId)
        enviarMsgColorida(player, "Seu Vínculo com " .. c(nome, corDominio(dominioId)) .. " se desfez.")
    end

    -- Atualiza Lampejo (com controlo de expiração)
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

-- ============================================================
-- APLICAR BÓNUS DE LAMPEJOS E VÍNCULOS
-- ============================================================
function aplicarBonus(player)
    local states = player:getAllActiveStates()
    local speedBonus = 0
    local damageBonus = 0

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

    if speedBonus > 0.60 then speedBonus = 0.60 end
    if damageBonus > 0.80 then damageBonus = 0.80 end

    local finalSpeed = 1.0 - speedBonus
    local finalDmg = 1.0 + damageBonus

    if finalSpeed < SPEED_MIN then finalSpeed = SPEED_MIN end
    if finalDmg > DAMAGE_MAX then finalDmg = DAMAGE_MAX end

    -- Converte para inteiro (multiplicador * 1000) para compatibilidade com storages
    local newSpeedVal = math.floor(finalSpeed * 1000 + 0.5)
    local newDmgVal   = math.floor(finalDmg   * 1000 + 0.5)

    local currentSpeed = player:getStorageValue(STORAGE.SPEED_MOD) or 1000
    local currentDmg   = player:getStorageValue(STORAGE.DAMAGE_MOD) or 1000

    -- Só aplica a postura se os valores realmente mudaram
    if newSpeedVal ~= currentSpeed or newDmgVal ~= currentDmg then
        player:setStorageValue(STORAGE.SPEED_MOD, newSpeedVal)
        player:setStorageValue(STORAGE.DAMAGE_MOD, newDmgVal)
        aplicarPostura(player, player:getFightMode())
    end

    if atualizarTransformacoes then
        atualizarTransformacoes(player)
    end
end

-- ============================================================
-- THINK PERIÓDICO (a cada 2 segundos)
-- ============================================================
local thinkEvent = CreatureEvent("SintoniaThink")
thinkEvent:onThink(function(player, interval)
    local now = os.time()
    local lastCheck = player:getStorageValue(STORAGE.SINTONIA_LAST_CHECK) or 0
    if now - lastCheck < 2 then return true end
    player:setStorageValue(STORAGE.SINTONIA_LAST_CHECK, now)

    -- Descarrega o buffer de progressão (afinidades acumuladas)
    if descarregarBuffer then
        descarregarBuffer(player)
    end

    -- Expira Lampejos cujo tempo acabou
    local states = player:getAllActiveStates()
    for domId, state in pairs(states) do
        if state == 1 then
            local expireTime = player:getStorageValue(STORAGE.LAMPEJO_EXPIRE + domId) or 0
            if now >= expireTime then
                player:setDominioState(domId, 0)
                player:setStorageValue(STORAGE.LAMPEJO_EXPIRE + domId, 0)
            end
        elseif state == 2 then
            -- Vínculo: para Maestria (nível 20), nunca expira
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
            -- Se nível >= 20, o Vínculo é permanente e nunca se dissipa
        end
    end
    aplicarBonus(player)
    return true
end)
thinkEvent:type("think")
thinkEvent:register()

print("DEBUG: sintonia.lua (v11.0) carregado.")