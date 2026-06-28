-- NPC: TestePosGeracao
local npc = NPC("TestePosGeracao")
npc:setSaudacao("Olá! Como posso te ajudar hoje?")
npc:addNPC(detector_de_objetos, 100)
print("NPC TestePosGeracao carregado.")