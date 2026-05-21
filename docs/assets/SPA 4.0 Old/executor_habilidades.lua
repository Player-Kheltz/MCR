--[[
    Projeto MCR ? executor_habilidades.lua (v15.0)
    Locks removidos para habilidades assíncronas.
    Apenas o limite de 2 habilidades assíncronas por evento previne spam.
--]]

local _domainHierarchy = domainHierarchy or {}
local _secondaryParent = secondaryParent or {}

function carregarHabilidadesConhecidas(player)
    if player.getHabilidades then
        local lista = player:getHabilidades()
        for _, habId in ipairs(lista) do player:setStorageValue(STORAGE.HABILIDADE_BASE + habId, 1) end
        return lista
    end
    return {}
end

function jogadorConheceHabilidade(player, habId)
    return (player:getStorageValue(STORAGE.HABILIDADE_BASE + habId) or 0) == 1
end

function aprenderHabilidade(player, habId)
    if player.learnHabilidade then player:learnHabilidade(habId) end
    player:setStorageValue(STORAGE.HABILIDADE_BASE + habId, 1)
end

local function armaCompativeis(player, dominioIds)
    local weapon = player:getSlotItem(CONST_SLOT_LEFT) or player:getSlotItem(CONST_SLOT_RIGHT)
    if not weapon then
        for _, domId in ipairs(dominioIds) do
            if domId == 14 or domId == 130 or domId == 131 then return true end
        end
        return false
    end
    local especialidade = getWeaponEspecialidade(player, weapon)
    if not especialidade then return false end

    local secundarioEspecialidade = _domainHierarchy[especialidade]

    for _, domId in ipairs(dominioIds) do
        if domId == especialidade then return true end
        if secundarioEspecialidade and secundarioEspecialidade == domId then return true end
        if secundarioEspecialidade then
            local primarioEspecialidade = _secondaryParent[secundarioEspecialidade]
            if primarioEspecialidade and primarioEspecialidade == domId then return true end
        end
    end
    return false
end

function calcularChanceFinal(habilidade, player)
    local chance = habilidade.chanceBase or 0
    local postura = player:getFightMode()
    local mod = habilidade.posturaMod and habilidade.posturaMod[postura]
    local multChance = (mod and mod.chanceMult) or 1.0
    for _, domId in ipairs(habilidade.dominio) do
        local st = player:getDominioState(domId) or 0
        if st == 2 then
            local cv = habilidade.chanceVinculo or habilidade.chanceBase
            multChance = multChance * (1.0 + (cv - chance) / 100)
            break
        elseif st == 1 then
            local cl = habilidade.chanceLampejo or habilidade.chanceBase
            multChance = multChance * (1.0 + (cl - chance) / 100)
            break
        end
    end
    chance = chance * multChance
    if chance > 100 then chance = 100 end
    return chance
end

local function atualizarContadorAtaques(player)
    local weapon = player:getSlotItem(CONST_SLOT_LEFT) or player:getSlotItem(CONST_SLOT_RIGHT)
    local especialidadeAtual = weapon and getWeaponEspecialidade(player, weapon) or 0
    local ultimaEspecialidade = player:getStorageValue(91580) or 0
    local contador = player:getStorageValue(91581) or 0
    if especialidadeAtual == ultimaEspecialidade then contador = contador + 1 else contador = 1 end
    player:setStorageValue(91580, especialidadeAtual)
    player:setStorageValue(91581, contador)
    return contador
end

function executarHabilidades(player, gatilho, target, damage, extra)
    if not player or not target then return end

    local lastExecution = player:getStorageValue(91599) or 0
    local now = os.time() * 1000
    if now - lastExecution < 200 then return end
    player:setStorageValue(91599, now)

    local contadorAtaques = 0
    if gatilho == "onAttack" then contadorAtaques = atualizarContadorAtaques(player) end

    local habilidadesAtivadas = 0
    local maxHabilidadesPorEvento = 2
    local asyncCount = 0
    local maxAsync = 2
    local debugMode = player:getStorageValue(99999) == 1

    local espAtual = nil
    if debugMode then
        local weapon = player:getSlotItem(CONST_SLOT_LEFT) or player:getSlotItem(CONST_SLOT_RIGHT)
        espAtual = getWeaponEspecialidade(player, weapon)
    end

    for habId, hab in pairs(HABILIDADES) do
        if hab.tipo ~= "gatilho" then
            -- saltar
        elseif hab.gatilho ~= gatilho or not jogadorConheceHabilidade(player, habId) then
            if debugMode and hab.gatilho == gatilho and not jogadorConheceHabilidade(player, habId) then
                enviarMsgColorida(player, "DEBUG: " .. hab.nome .. " - NAO CONHECIDA")
            end
        elseif not armaCompativeis(player, hab.dominio) then
            if debugMode then
                local ids = table.concat(hab.dominio, ",")
                enviarMsgColorida(player, "DEBUG: " .. hab.nome .. " - FALHOU (esp=" .. tostring(espAtual) .. " doms=[" .. ids .. "])")
            end
        elseif hab.async and asyncCount >= maxAsync then
            if debugMode then
                enviarMsgColorida(player, "DEBUG: " .. hab.nome .. " - ASYNC LIMIT")
            end
        else
            local condOk = true
            if hab.condicao then
                if hab.condicao == "cercado" then
                    local count = #getCreaturesInArea(player:getPosition(), 3, 3) - 1
                    if count < 3 then condOk = false end
                elseif hab.condicao == "vidaBaixa" then
                    if target:getHealth() > target:getMaxHealth() * 0.2 then condOk = false end
                elseif hab.condicao == "distancia4" then
                    if getCreatureDistance(player, target) < 4 then condOk = false end
                elseif hab.condicao == "5Golpes" or hab.condicao == "5Disparos" then
                    if contadorAtaques < 5 then condOk = false else player:setStorageValue(91581, 0) end
                end
                if not condOk and debugMode then
                    enviarMsgColorida(player, "DEBUG: " .. hab.nome .. " - COND " .. hab.condicao)
                end
            end

            if condOk then
                if habilidadesAtivadas >= maxHabilidadesPorEvento then
                    if debugMode then enviarMsgColorida(player, "DEBUG: " .. hab.nome .. " - LIMITE ATINGIDO") end
                    break
                end

                local chance = calcularChanceFinal(hab, player)
                if debugMode then enviarMsgColorida(player, "DEBUG: " .. hab.nome .. " - OK " .. string.format("%.1f", chance) .. "%") end

                if math.random(100) <= chance then
                    if hab.async then asyncCount = asyncCount + 1 end
                    local postura = player:getFightMode()

                    local ok, err = pcall(function()
                        if hab.buffType == "speedBurst" then applySpeedBurst(player, hab.buffMultiplier, hab.buffDurationMs or 500)
                        elseif hab.buffType == "nextAttackCondition" then applyNextAttackCondition(player, hab.conditionType, hab.conditionDuration, hab.conditionDamage)
                        elseif hab.buffType == "damageBoost" then applyDamageBoost(player, hab.percentExtra, hab.buffHits)
                        elseif hab.buffType == "lifeLeech" then applyLifeLeech(player, hab.leechPercent, hab.durationSec)
                        elseif hab.buffType == "custom" and hab.efeito then hab.efeito(player, target, damage) end
                        if hab.efeitoVisual then hab.efeitoVisual(player, target) end
                    end)

                    if not ok then print("Erro na habilidade " .. habId .. ": " .. tostring(err)) end

                    if hab.buffType ~= "nextAttackCondition" then player:say(hab.nome, TALKTYPE_MONSTER_SAY) end

                    local descricao = hab.descricaoEfeito
                    if type(descricao) == "function" then descricao = descricao(player) end
                    local logMsg = c("[" .. hab.nome .. "] ", hab.cor or COR.SISTEMA_INFO) ..
                                (hab.mensagem[postura] or hab.mensagem[2] or "") .. "! " ..
                                c(descricao, COR.COMBO_AVISO) .. "."
                    enviarMsgColorida(player, logMsg)

                    habilidadesAtivadas = habilidadesAtivadas + 1
                end
            end
        end
    end

    if gatilho == "onAttack" then
        local bonus = player:getStorageValue(91550) or 0
        if bonus > 0 then player:setStorageValue(91550, 0) end
    end
end

function atualizarTransformacoes(player)
    local states = player:getAllActiveStates()
    for habId, hab in pairs(HABILIDADES) do
        if hab.tipo == "transformacao" and jogadorConheceHabilidade(player, habId) then
            local ativo = false
            for _, domId in ipairs(hab.dominio) do
                if states[domId] and states[domId] > 0 then ativo = true; break end
            end
            local estavaAtivo = player:getStorageValue(92050 + habId) == 1
            if ativo and not estavaAtivo then hab.efeito(player); player:setStorageValue(92050 + habId, 1)
            elseif not ativo and estavaAtivo then player:setStorageValue(92050 + habId, 0) end
        end
    end
end

print("DEBUG: executor_habilidades.lua (v15.0) carregado.")