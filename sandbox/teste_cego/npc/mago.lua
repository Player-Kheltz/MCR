-- NPC: Mago
local npc = NPC("Mago")
npc:saudacao("Ola!")
npc:setMana(500)
npc:setMagia(20) -- Correção do método para definir o nível de magia
npc:addItem(102, 100)