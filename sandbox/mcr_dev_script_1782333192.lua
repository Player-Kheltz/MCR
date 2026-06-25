Aqui está o código para criar um arquivo .txt com uma lista de 5 itens de ouro em Tibia:

```lua
-- Função para criar o arquivo e escrever a lista de itens
function createOuroList()
    -- Nome do arquivo que será criado
    local filename = "ouro_list.txt"
    
    -- Lista de itens de ouro em Tibia
    local ouroItems = {
        "Cristal de ouro",
        "Medaillon de ouro",
        "Anel de ouro",
        "Broche de ouro",
        "Pulseira de ouro"
    }
    
    -- Abrir o arquivo para escrita
    local file = io.open(filename, "w")
    
    -- Verificar se o arquivo foi aberto com sucesso
    if file then
        -- Escrever cada item da lista no arquivo
        for _, item in ipairs(ouroItems) do
            file:write(item .. "\n")
        end
        
        -- Fechar o arquivo
        file:close()
        
        print("Arquivo " .. filename .. " criado com sucesso!")
    else
        print("Erro ao criar o arquivo.")
    end
end

-- Chamar a função para criar o arquivo
createOuroList()
```

Este código cria um arquivo chamado `ouro_list.txt` no diretório onde o script está sendo executado. O arquivo contém uma lista de 5 itens de ouro em Tibia, cada item em uma linha separada.

Para usar este código:

1. Copie e cole-o em um editor de texto.
2. Salve o arquivo com a extensão `.lua`.
3. Execute o script no seu ambiente Lua (por exemplo, no console do TFS).

Após a execução, você encontrará o arquivo `ouro_list.txt` no mesmo diretório onde salvou o script, contendo a lista de itens de ouro.