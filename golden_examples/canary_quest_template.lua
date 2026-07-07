--- CANARY QUEST TEMPLATE — API 100% real do servidor
--- PROIBIDO usar classes como Quest(). Use Action(), KeywordHandler(), storage values.
--- REGRA: metodos SAO chamados com : (dois-pontos), NAO com . (ponto).
--- action:uid(1001) — CERTO  |  action.uid = 1001 — ERRADO

--- ARQUIVO: npc_example.lua ---
-- NPC que da a quest (KeywordHandler)
local internalNpcName = "NomeDoNpc"
local npcType = Game.createNpcType(internalNpcName)
local npcConfig = {}

npcConfig.name = internalNpcName
npcConfig.outfit = { lookType = 130 }

npcConfig.shop = {}

local keywordHandler = KeywordHandler:new()
npcType:register(keywordHandler)

function keywordHandler:onCreatureSay(player, words)
    if words == "quest" then
        if player:getStorageValue(50001) == -1 then
            player:sendTextMessage(MESSAGE_INFO_DESCR, "Inicie a quest aqui.")
        elseif player:getStorageValue(50001) == 0 then
            player:sendTextMessage(MESSAGE_INFO_DESCR, "Va ao local e volte.")
        elseif player:getStorageValue(50001) == 1 then
            player:setStorageValue(50001, 2)
            player:addItem(2160, 5)
            player:sendTextMessage(MESSAGE_INFO_DESCR, "Recompensa recebida!")
        end
    end
    return true
end

--- ARQUIVO: action_example.lua ---
-- Action para bau / item da quest
local action = Action()

function action.onUse(player, item, fromPosition, target, toPosition, isHotkey)
    if item:getId() == 1234 then
        player:setStorageValue(50001, 1)
        player:sendTextMessage(MESSAGE_INFO_DESCR, "Item encontrado!")
        item:remove()
    end
    return true
end

action:uid(1001)     -- <<< ATENCAO: use :uid(), NUNCA .uid =
action:register()    -- <<< ATENCAO: use :register(), NUNCA .register =
