-- item: ArmaduraGelo
local item = Item("ArmaduraGelo")
item:setType("Armor")  -- Definindo o tipo como Armor

-- Configurando atributos da armadura de gelo
item:setAttribute("Defense", 20)
item:setAttribute("ColdResistance", 30)

-- Definindo a duração do item (em ticks, por exemplo, 1 dia = 24000 ticks)
item:setDuration(24000 * 7)  -- 1 semana

-- Atribuindo uma ação específica ao item
item:setActionId(12345)

print("item ArmaduraGelo carregado.")