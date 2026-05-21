--[[
    Projeto MCR ? SPA v4.0 ? Login
--]]

local loginEvent = CreatureEvent("DominiosLogin")
loginEvent:onLogin(function(player)
    -- Garantir vocação de Aventureiro
    if player:getVocation():getId() ~= 0 then player:setVocation(0) end

    -- Primeiro login: teleporta para a praia inicial
    if player:getLastLoginSaved() == 0 and player:getStorageValue(90000) ~= 1 then
        player:setStorageValue(90000, 1)
        player:teleportTo(Position(1000, 1000, 7)) -- Praia do Náufrago
        enviarMsgColorida(player, "Você desperta nas areias de Eridanus.")
    end

    -- Limpar histórico de ações
    if player.clearActionHistory then player:clearActionHistory() end

    -- Inicializar storages de bónus
    player:setStorageValue(STORAGE.SPEED_MOD, 1000)
    player:setStorageValue(STORAGE.DAMAGE_MOD, 1000)
    player:setStorageValue(STORAGE.MANA_REGEN_MOD, 1000)
    player:setStorageValue(STORAGE.HEALTH_REGEN_MOD, 1000)
    player:setStorageValue(STORAGE.LIFE_LEECH, 0)
    player:setStorageValue(STORAGE.MANA_LEECH, 0)
    player:setStorageValue(STORAGE.SINTONIA_LAST_CHECK, 0)

    -- Carregar habilidades já aprendidas (da BD)
    carregarHabilidadesConhecidas(player)

    -- Aplicar passivas que não dependem de Vínculo
    if aplicarPassivasBasicas then aplicarPassivasBasicas(player) end

    -- Atualizar transformações baseadas nos estados de alma
    if atualizarTransformacoes then atualizarTransformacoes(player) end

    -- Garantir que stealth começa desligado
    player:setStealth(false)

    -- Aplicar postura inicial (Equilíbrio)
    aplicarPostura(player, FIGHTMODE_BALANCED)

    -- Registar eventos think
    player:registerEvent("BuffThink")
    player:registerEvent("PosturaThink")

    -- Limpar quaisquer locks residuais (precaução)
    for habId, hab in pairs(HABILIDADES) do
        if type(habId) == "number" and hab.tipo == "gatilho" then
            player:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 0)
        end
    end

    return true
end)
loginEvent:type("login"); loginEvent:register()

local logoutEvent = CreatureEvent("ProgressaoLogout")
logoutEvent:onLogout(function(player)
    if descarregarBuffer then descarregarBuffer(player) end
    return true
end)
logoutEvent:type("logout"); logoutEvent:register()

print("DEBUG: login.lua v4.0 carregado.")