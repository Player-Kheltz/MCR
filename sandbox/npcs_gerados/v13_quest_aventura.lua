-- Quest: Aventura
local quest = Quest("Aventura")
quest:setDescricao("Mate 10 ratos")
quest:addObjetivo("matar ratos")
quest:addRecompensa("xp", 500)
quest:addRecompensa("gold", 100)
print("Quest Aventura carregada.")