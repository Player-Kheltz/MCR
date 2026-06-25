-- NPC: GuardiaoDraconico — Completo
-- Gerado pelo Cloud
local npc = NPC("GuardiaoDraconico")

-- Configuracao basica
npc:setSaudacao("A chama ancestral queima dentro de voce.")
npc:setAdeus("Volte sempre, aventureiro.")
npc:setGender(1)
npc:setOutfit( Mention(20, 0, 0, 0, 0) )
npc:setSpeed(100)
npc:setHealth(1000)
npc:setMaxHealth(1000)

-- Dialogo em arvore
npc:addDialog("quest", {
    {"Sobre a quest", "Ha uma antiga profecia que precisa ser cumprida. Tres artefatos foram perdidos."},
    {"Aceito ajudar", "Entao va! Procure o Guardiao na torre norte. Ele tem o primeiro artefato."},
    {"Quem voce e?", "Sou o guardiao deste reino. Protejo Eridanus ha mais de 300 anos."},
})

-- Loja
npc:addItem(5001, 200)
npc:addItem(5002, 210)
npc:addItem(5003, 225)

-- Quest
npc:setQuest("")
npc:addQuestItem(5001, 1)
npc:addQuestItem(5002, 1)
npc:addQuestItem(5003, 1)
npc:setQuestReward("xp", 5000)
npc:setQuestReward("gold", 2000)
npc:setQuestReward("item", 6001)

print("NPC GuardiaoDraconico carregado.")