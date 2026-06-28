-- Itens do Sistema: O Legado Perdido de Eridanus
-- Criado pelo MCR CRU (factory default)

-- Itens de Quest
local mapa = Item(30001, "Mapa do Legado")
mapa:setType("quest")
mapa:setDescription("Um mapa antigo mostrando a localizacao dos tres artefatos perdidos de Eridanus.")

local olho = Item(30010, "Olho de Eridanus")
olho:setType("quest")
olho:setDescription("Uma joia azul que brilha com luz propria. Dizem que ve tudo o que acontece na cidade.")

local chama = Item(30011, "Chama Eterna")
chama:setType("quest")
chama:setDescription("Uma chama que nunca se apaga, mesmo submersa. Aquecida pelo espirito dos fundadores.")

local selo = Item(30012, "Selo do Fundador")
selo:setType("quest")
selo:setDescription("Um selo de pedra com o simbolo dos tres fundadores de Eridanus.")

-- Recompensas
local amuleto = Item(30020, "Amuleto do Fundador")
amuleto:setType("armor")
amuleto:setDescription("Um amuleto que pertenceu ao fundador de Eridanus. Concede protecao especial.")
amuleto:setDefense(15)
amuleto:setWeight(5)

print("Itens do Legado Perdido carregados.")
