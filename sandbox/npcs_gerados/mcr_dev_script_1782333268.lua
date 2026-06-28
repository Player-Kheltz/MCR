```lua
-- sandbox\mcr_dev_script_1782333205.lua

local file = io.open("magic_items.txt", "w")

if file then
    file:write("Lista de Itens Mágicos:\n")
    file:write("- Um Anel da Sabedoria\n")
    file:write("- Um Livro Encantado\n")
    file:write("- Uma Espada Mágica\n")
    file:close()
    print("Arquivo 'magic_items.txt' criado com sucesso.")
else
    print("Erro ao criar o arquivo.")
end
```