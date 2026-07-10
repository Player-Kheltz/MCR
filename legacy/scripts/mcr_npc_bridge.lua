--[[
mcr_npc_bridge.lua — Bridge Lua entre NPCs do Canary e o MCR-DevIA NPC Server.
Envia dialogos do jogador para o servidor Python via socket TCP e recebe respostas.

Instalacao:
  1. Copie este arquivo para server/data/scripts/npc/ ou server/data/npclib/
  2. Importe nos NPCs que deseja tornar "vivos":
       dofile("data/scripts/npc/mcr_npc_bridge.lua")
  3. Inicie o servidor Python:
       python mcr/npc_server.py
  4. Nos NPCs, use:
       local resposta = mcr_falar("Kheltz", "Ola, tudo bem?")
       if resposta then player:sendTextMessage(MESSAGE_INFO_DESCR, resposta) end

Requisitos: luasocket (socket.http ou socket.core)
Timeout: 1 segundo — se o servidor Python estiver offline, retorna nil e usa fallback.
]]

-- Tenta carregar o socket
local _HAS_SOCKET = false
local _socket = nil

-- Tenta luasocket (presente no Canary)
pcall(function()
    _socket = require("socket")
    _HAS_SOCKET = true
end)

-- Fallback: tenta socket.http direto
if not _HAS_SOCKET then
    pcall(function()
        _socket = require("socket.http")
        _HAS_SOCKET = (_socket ~= nil)
    end)
end

-- Configuracao
local HOST = "127.0.0.1"
local PORT = 7777
local TIMEOUT = 1  -- segundos (se passar, retorna nil)


--- Envia uma mensagem para o servidor MCR e retorna a resposta.
--@param npc_id: Nome do NPC (ex: "Guarda Real", "Druida")
--@param player_id: Nome do jogador (ex: "Kheltz")
--@param message: Mensagem do jogador (ex: "Ola, tudo bem?")
--@return: string com a resposta ou nil se timeout/erro
function mcr_falar(npc_id, player_id, message)
    if not _HAS_SOCKET then
        return nil  -- luasocket nao disponivel, usa dialogo padrao
    end

    -- Monta JSON
    local request = '{"npc_id":"' .. npc_id .. '","player_id":"' .. player_id .. '","message":"' .. message .. '"}'

    -- Conexao TCP
    local client, err = _socket.tcp()
    if not client then
        return nil
    end

    client:settimeout(TIMEOUT)

    local ok, conn_err = client:connect(HOST, PORT)
    if not ok then
        client:close()
        return nil  -- Servidor offline, fallback
    end

    -- Envia
    local send_ok, send_err = client:send(request)
    if not send_ok then
        client:close()
        return nil
    end

    -- Recebe resposta
    local response, recv_err = client:receive("*a")
    client:close()

    if not response then
        return nil  -- Timeout ou erro
    end

    -- Parse JSON
    local ok, parsed = pcall(function()
        return json.decode(response)
    end)

    if not ok or not parsed or not parsed.response then
        return nil
    end

    return parsed.response
end


--[[
-- EXEMPLO DE USO EM UM NPC:
--
-- local internalNpcName = "Druida"
-- local npcType = Game.createNpcType(internalNpcName)
-- local npcConfig = {}
-- npcConfig.name = internalNpcName
--
-- local keywordHandler = KeywordHandler:new()
-- npcType:register(keywordHandler)
--
-- function keywordHandler:onCreatureSay(player, words)
--     if words == "ervas" or words == "natureza" then
--         local resposta = mcr_falar(internalNpcName, player:getName(), words)
--         if resposta then
--             player:sendTextMessage(MESSAGE_INFO_DESCR, resposta)
--         else
--             player:sendTextMessage(MESSAGE_INFO_DESCR, "A natureza guarda seus segredos...")
--         end
--     end
--     return true
-- end
]]

-- Retorna true para o servidor carregar
return true
