-- Item: Espada Magica
local item = Item(3001, "Espada Magica")
item:setType("weapon")
item.setAttribute("attack", 50)     -- CORREÇÃO! MCR usa setAttribute
item.setAttribute("defense", 20)    -- CORREÇÃO! MCR usa setAttribute
item:setWeight(30)
print("Item Espada Magica carregado.")