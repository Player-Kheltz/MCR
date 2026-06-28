-- CRU: Quest Items
local item1 = Item(41001, "Selo do Guardiao")
item1:setType("quest")
item1:setWeight(2)

local item2 = Item(41002, "Chama da Sabedoria")
item2:setType("quest")
item2:setWeight(1)

local item3 = Item(41003, "Coracao da Terra")
item3:setType("quest")
item3:setWeight(5)

-- Rewards
local item4 = Item(41004, "Amuleto do Heroi")
item4:setType("armor")
item4:setDefense(25)
item4:setWeight(3)

local item5 = Item(40003, "Pocao de Experiencia")
item5:setType("consumable")
item5:setWeight(1)

print("Quest items carregados.")
