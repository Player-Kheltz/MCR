-- item: EspadaFlamejante
local item = Item("EspadaFlamejante")
item.setAttribute("damage", 50)
item.setDuration(3600) -- 1 hora em segundos
item.setActionId(2001)
item.setType("weapon")

print("item EspadaFlamejante carregado.")