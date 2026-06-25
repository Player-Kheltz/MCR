-- NPC: Ferreiro
local npc = NPC("Ferreiro")
npc:setSaudacao("Bem-vindo!")
npc:addItem(101, 50)
npc:addItem(102, 100)
npc:setQuest("ajude o ferreiro")
print("NPC Ferreiro carregado.")