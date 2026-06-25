Aqui está o código Lua que cria um arquivo .txt com uma lista de 3 itens mágicos para um jogo de RPG:

```lua
-- Nome do arquivo a ser criado
local filename = "sandbox\\mcr_dev_script_1782333368.lua"

-- Itens mágicos a serem adicionados ao arquivo
local magic_items = {
    "Espada Mágica",
    "Cinto de Proteção",
    "Amuleto da Sabedoria"
}

-- Abre o arquivo para escrita
local file = io.open(filename, "w")

-- Verifica se o arquivo foi aberto com sucesso
if file then
    -- Escreve os itens mágicos no arquivo
    for _, item in ipairs(magic_items) do
        file:write(item .. "\n")
    end

    -- Fecha o arquivo
    file:close()

    print("Arquivo criado com sucesso!")
else
    print("Erro ao criar o arquivo.")
end
```

Este código cria um arquivo chamado "mcr_dev_script_1782333368.lua" na pasta "sandbox". O conteúdo do arquivo será:

```
Espada Mágica
Cinto de Proteção
Amuleto da Sabedoria
```

Certifique-se de que a pasta "sandbox" existe no mesmo diretório onde o script está sendo executado. Se não existir, você precisará criar a pasta manualmente ou ajustar o caminho do arquivo conforme necessário.