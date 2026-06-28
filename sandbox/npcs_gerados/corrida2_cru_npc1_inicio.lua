-- CRU: NPC Iniciador — Guardiao das Profecias
-- Criado manualmente, sem scripts
local npc = NPC("Guardiao das Profecias")

npc:setSaudacao("A profecia se cumpre. Voce e o escolhido? O tempo e curto.")
npc:setAdeus("Que a luz de Eridanus te guie.")

npc:addDialog("quest", {
    {"O que esta acontecendo?", "Ha muito tempo, os tres pilares de Eridanus foram selados. Alguem esta tentando despertar um poder antigo. Se conseguir, a cidade sera destruida."},
    {"Como posso ajudar?", "Voce precisa encontrar tres artefatos: o Selo do Guardiao na torre norte, a Chama da Sabedoria na biblioteca, e o Coracao da Terra nas profundezas. Cada um protege um segredo."},
    {"Aceito a missao!", "Entao va! Procure a Sabia Anciã na biblioteca. Ela tem o mapa dos artefatos. Que os ventos te protejam."},
})

npc:addNPC(40001, 50) -- Pocoes de cura
print("NPC Guardiao das Profecias carregado.")
