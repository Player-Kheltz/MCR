-- TalkAction: cmd_ajuda
local talk = TalkAction("!ajuda")
function talk.onSay(player, words, param)
    player:sendTextMessage(27, "Comandos disponiveis: !ajuda")
    return false
end
talk:register()