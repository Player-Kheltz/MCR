-- NPC: Velho Sabio de Eridanus
-- Criado pelo MCR CRU (factory default)
-- Sistema: O Legado Perdido de Eridanus

local npc = NPC("Velho Sabio")

npc:setSaudacao("Ah, um aventureiro! Vejo que seus olhos brilham com curiosidade. Sente-se, vamos conversar.")
npc:setAdeus("Que os ventos te levem em seguranca, jovem.")

npc:addDialog("quest", {
    {"O que e o Legado Perdido?", "Ha muito tempo, quando Eridanus foi fundada, tres artefatos foram criados para proteger a cidade. Mas eles foram perdidos durante o Grande Incendio. Dizem que quem os recuperar sera digno de uma recompensa antiga."},
    {"Como posso ajudar?", "Preciso que encontre tres artefatos: o Olho de Eridanus na Mina Abandonada, a Chama Eterna nas Ruinas do Templo, e o Selo do Fundador na Biblioteca Antiga. Cada um guarda um segredo."},
    {"Aceito a missao!", "Entao va! Que a sabedoria dos antigos te guie. Lembre-se: cada artefato esta protegido por enigmas do passado."},
})

npc:addItem(30001, 1)  -- Mapa do Legado (item de quest)
npc:addItem(30002, 1)  -- Pocao do Sabio (recompensa)
npc:addItem(30003, 1)  -- Livro de Eridanus (lore)

print("NPC Velho Sabio carregado.")
