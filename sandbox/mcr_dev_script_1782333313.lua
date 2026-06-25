```lua
-- sandbox\mcr_dev_script_1782333268.lua

local items = {
    "Espada Mágica",
    "Cinto da Sabedoria",
    "Amuleto do Dragão"
}

local file = io.open("itens_magicos.txt", "w")

for _, item in ipairs(items) do
    file:write(item .. "\n")
end

file:close()
```