-- CRU: TalkAction — !profecia (verificar progresso da quest)
local talk = TalkAction("!profecia")
function talk.onSay(player, words, param)
    local quest = player:getQuest("O Despertar de Eridanus")
    if not quest then
        player:sendTextMessage(27, "Voce nao iniciou a profecia. Procure o Guardiao das Profecias.")
        return false
    end
    
    local etapa = quest:getEtapaAtual()
    if etapa == 0 then
        player:sendTextMessage(27, "Profecia: Encontre o Guardiao das Profecias para comecar.")
    elseif etapa == 1 then
        player:sendTextMessage(27, "Profecia: Derrote o Espectro da Torre e obtenha o Selo do Guardiao.")
    elseif etapa == 2 then
        player:sendTextMessage(27, "Profecia: Derrote o Golem de Pedra e obtenha a Chama da Sabedoria.")
    elseif etapa == 3 then
        player:sendTextMessage(27, "Profecia: Derrote o Guardiao Subterraneo e obtenha o Coracao da Terra.")
    elseif etapa == 4 then
        player:sendTextMessage(27, "Profecia: Retorne ao Guardiao das Profecias com os tres artefatos.")
    else
        player:sendTextMessage(27, "Profecia cumprida! A luz de Eridanus brilha novamente.")
    end
    
    return false
end
talk:register()
print("TalkAction !profecia carregado.")
