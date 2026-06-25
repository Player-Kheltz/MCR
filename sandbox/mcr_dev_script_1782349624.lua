Aqui está o código Lua que cria um arquivo .txt no diretório sandbox com uma lista de três itens mágicos para um jogo RPG:

```lua
-- Definindo a lista de itens mágicos
local itens_magicos = {
    "Espada Mágica",
    "Cinto da Fortuna",
    "Amuleto do Saber"
}

-- Nome do arquivo onde os itens serão salvos
local nome_arquivo = "sandbox\\itens_magicos.txt"

-- Abrindo o arquivo para escrita
local arquivo = io.open(nome_arquivo, "w")

-- Verificando se o arquivo foi aberto com sucesso
if arquivo then
    -- Escrevendo cada item na lista no arquivo
    for _, item in ipairs(itens_magicos) do
        arquivo:write(item .. "\n")
    end

    -- Fechando o arquivo
    arquivo:close()

    print("Arquivo criado com sucesso!")
else
    print("Erro ao criar o arquivo.")
end
```

Este script faz o seguinte:

1. Define uma tabela `itens_magicos` contendo três itens mágicos.

2. Especifica o nome do arquivo onde os itens serão salvos (`sandbox\\itens_magicos.txt`).

3. Abre o arquivo para escrita usando `io.open`.

4. Verifica se o arquivo foi aberto com sucesso.

5. Se sim, itera sobre a tabela de itens e escreve cada um no arquivo, seguido por uma nova linha.

6. Fecha o arquivo após a escrita.

7. Exibe uma mensagem indicando que o arquivo foi criado com sucesso ou um erro caso contrário.

Para executar este script, certifique-se de que ele está em um ambiente Lua compatível e tenha permissões para criar arquivos no diretório especificado (`sandbox`).