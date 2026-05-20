--[[
    Projeto MCR ? login.lua (v10.1)
    Inicialização do jogador, com supressão de spam de postura no login.
--]]
local PRAIA_NAUFRAGO = Position(1000, 1000, 7)

local loginEvent = CreatureEvent("DominiosLogin")
loginEvent:type("login")
loginEvent:onLogin(function(player)
    -- Garantir que o personagem é um Aventureiro (vocation = 0)
    if player:getVocation():getId() ~= 0 then player:setVocation(0) end

    -- Primeiro login: teleporta para a praia inicial
    if player:getLastLoginSaved() == 0 and player:getStorageValue(90000) ~= 1 then
        player:setStorageValue(90000, 1)
        player:teleportTo(PRAIA_NAUFRAGO)
        enviarMsgColorida(player, "Você desperta nas areias de Eridanus.")
    end

    -- Limpar histórico de ações
    if player.clearActionHistory then player:clearActionHistory() end

    -- Inicializar storages de bónus com valores inteiros (1000 = 1.0)
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
    aplicarPassivasBasicas(player)

    -- Aplicar transformações baseadas no estado actual dos Vínculos
    atualizarTransformacoes(player)

    -- Garantir que o Stealth começa desligado
    player:setStealth(false)

    -- Suprimir mensagens de postura durante o arranque (evita spam)
    player:setStorageValue(91000, 1)

    -- Aplicar a postura inicial (Equilíbrio)
    aplicarPostura(player, FIGHTMODE_BALANCED)

    -- Registar eventos think essenciais para o SPA
    player:registerEvent("BuffThink")
    player:registerEvent("PosturaThink")

    -- Remover a supressão de postura após 2 segundos
    local playerId = player:getId()
    addEvent(function()
        local p = Player(playerId)
        if p then p:setStorageValue(91000, 0) end
    end, 2000)

    return true
end)

-- Descarregar o buffer de progressão ao fazer logout
local logoutEvent = CreatureEvent("ProgressaoLogout")
logoutEvent:type("logout")
logoutEvent:onLogout(function(player)
    if descarregarBuffer then
        descarregarBuffer(player)
    end
    return true
end)
logoutEvent:register()

loginEvent:register()
print("DEBUG: login.lua (v10.1) carregado.")