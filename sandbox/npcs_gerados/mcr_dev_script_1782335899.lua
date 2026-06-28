```lua
-- sandbox\mcr_dev_script_1782333569.lua

local file = io.open("itens_magicos.txt", "w")

if file then
    file:write("Itens Mágicos:\n")
    file:write("- Espada de Fogo\n")
    file:write("- Escudo da Proteção\n")
    file:write("- Cinto do Velocidade\n")
    file:close()
    print("Arquivo 'itens_magicos.txt' criado com sucesso.")
else
    print("Erro ao criar o arquivo.")
end
```