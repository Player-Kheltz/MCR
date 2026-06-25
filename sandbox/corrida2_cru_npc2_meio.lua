-- CRU: NPC Meio — Sabia Anciã
-- Criado manualmente
local npc = NPC("Sabia Ancia")

npc:setSaudacao("Ah, o Guardiao me enviou? Entao e serio. Sente-se, vamos conversar.")

npc:addDialog("quest_progress", {
    {"Onde estao os artefatos?", "O Selo do Guardiao esta na torre norte, guardado pelo Espectro da Torre. A Chama da Sabedoria esta na biblioteca, protegida pelos Golem de Pedra. O Coracao da Terra esta nas cavernas profundas, com o Guardiao Subterraneo."},
    {"Como derrota-los?", "O Espectro teme luz, o Golem teme magia de gelo, e o Guardiao Subterraneo... bem, voce vai precisar de coragem."},
    {"Obrigado!", "Que a sabedoria te acompanhe."},
})

npc:addItem(40002, 100) -- Pocoes de mana
print("NPC Sabia Ancia carregado.")
