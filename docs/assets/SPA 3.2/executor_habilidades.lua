--[[
    Projeto MCR ? executor_habilidades.lua (v12.2)
    Executor de habilidades com:
      - limite de 2 gatilhos por evento
      - cooldown global de 200ms por ataque (evita spam multi?alvo)
      - sem emote nas buff conditions
--]]

function carregarHabilidadesConhecidas(player)
    if player.getHabilidades then
        local lista = player:getHabilidades()
        for _, habId in ipairs(lista) do
            player:setStorageValue(STORAGE.HABILIDADE_BASE + habId, 1)
        end
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

function desaprenderHabilidade(player, habId)
    player:setStorageValue(STORAGE.HABILIDADE_BASE + habId, 0)
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
    for _, domId in ipairs(dominioIds) do
        if domId == especialidade then return true end
        local secundario = domainHierarchy[especialidade]
        if secundario and secundario == domId then return true end
        if secundario then
            local primario = secondaryParent[secundario]
            if primario and primario == domId then return true end
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

    if especialidadeAtual == ultimaEspecialidade then
        contador = contador + 1
    else
        contador = 1
    end

    player:setStorageValue(91580, especialidadeAtual)
    player:setStorageValue(91581, contador)
    return contador
end

function executarHabilidades(player, gatilho, target, damage, extra)
    if not player or not target then return end

    -- Cooldown global de 200ms para evitar múltiplas execuções no mesmo ataque (multi?alvo)
    local lastExecution = player:getStorageValue(91599) or 0
    local now = os.time() * 1000
    if now - lastExecution < 200 then
        return
    end
    player:setStorageValue(91599, now)

    local contadorAtaques = 0
    if gatilho == "onAttack" then
        contadorAtaques = atualizarContadorAtaques(player)
    end

    local habilidadesAtivadas = 0
    local maxHabilidadesPorEvento = 2

    for habId, hab in pairs(HABILIDADES) do
        if hab.tipo ~= "gatilho" then
            goto continue
        end

        if hab.gatilho ~= gatilho or not jogadorConheceHabilidade(player, habId) then
            goto continue
        end

        if not armaCompativeis(player, hab.dominio) then
            goto continue
        end

        if player:getStorageValue(STORAGE.HABILIDADE_LOCK + habId) == 1 then
            goto continue
        end

        if hab.condicao then
            if hab.condicao == "cercado" then
                local count = #getCreaturesInArea(player:getPosition(), 3, 3) - 1
                if count < 3 then goto continue end
            elseif hab.condicao == "vidaBaixa" then
                if target:getHealth() > target:getMaxHealth() * 0.2 then goto continue end
            elseif hab.condicao == "distancia4" then
                if getCreatureDistance(player, target) < 4 then goto continue end
            elseif hab.condicao == "5Golpes" or hab.condicao == "5Disparos" then
                if contadorAtaques < 5 then
                    goto continue
                end
                player:setStorageValue(91581, 0)
            end
        end

        if habilidadesAtivadas >= maxHabilidadesPorEvento then
            break
        end

        local chance = calcularChanceFinal(hab, player)
        if math.random(100) <= chance then
            player:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 1)

            local postura = player:getFightMode()

            local ok, err = pcall(function()
                if hab.buffType == "speedBurst" then
                    applySpeedBurst(player, hab.buffMultiplier, hab.buffDurationMs or 500)
                elseif hab.buffType == "nextAttackCondition" then
                    applyNextAttackCondition(player, hab.conditionType, hab.conditionDuration, hab.conditionDamage)
                elseif hab.buffType == "damageBoost" then
                    applyDamageBoost(player, hab.percentExtra, hab.buffHits)
                elseif hab.buffType == "lifeLeech" then
                    applyLifeLeech(player, hab.leechPercent, hab.durationSec)
                elseif hab.buffType == "custom" then
                    if hab.efeito then
                        hab.efeito(player, target, damage)
                    end
                end

                if hab.efeitoVisual then
                    hab.efeitoVisual(player, target)
                end
            end)

            if not ok then
                print("Erro na habilidade " .. habId .. ": " .. tostring(err))
            end

            -- Apenas emote se não for nextAttackCondition
            if hab.buffType ~= "nextAttackCondition" then
                player:say(hab.nome, TALKTYPE_MONSTER_SAY)
            end

            local descricao = hab.descricaoEfeito
            if type(descricao) == "function" then
                descricao = descricao(player)
            end
            local logMsg = c("[" .. hab.nome .. "] ", hab.cor or COR.SISTEMA_INFO) ..
                        (hab.mensagem[postura] or hab.mensagem[2] or "") .. "! " ..
                        c(descricao, COR.COMBO_AVISO) .. "."
            enviarMsgColorida(player, logMsg)

            habilidadesAtivadas = habilidadesAtivadas + 1

            if not hab.async then
                player:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 0)
            end
        end

        ::continue::
    end

    if gatilho == "onAttack" then
        local bonus = player:getStorageValue(91550) or 0
        if bonus > 0 then
            player:setStorageValue(91550, 0)
            enviarMsgColorida(player, "O teu golpe é " .. c("mais forte", COR.SUCESSO_CURA) .. " após a esquiva!")
        end
    end
end

function atualizarTransformacoes(player)
    local states = player:getAllActiveStates()
    for habId, hab in pairs(HABILIDADES) do
        if hab.tipo == "transformacao" and jogadorConheceHabilidade(player, habId) then
            local ativo = false
            for _, domId in ipairs(hab.dominio) do
                if states[domId] and states[domId] > 0 then
                    ativo = true
                    break
                end
            end
            local estavaAtivo = player:getStorageValue(92050 + habId) == 1
            if ativo and not estavaAtivo then
                hab.efeito(player)
                player:setStorageValue(92050 + habId, 1)
            elseif not ativo and estavaAtivo then
                player:setStorageValue(92050 + habId, 0)
            end
        end
    end
end

print("DEBUG: executor_habilidades.lua (v12.2) carregado.")