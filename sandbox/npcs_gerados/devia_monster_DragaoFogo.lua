-- monster: DragaoFogo
local monster = Monster("DragaoFogo")

-- Configurações básicas
monster:setOutfit({lookType = 620})  -- Exemplo de outfit para dragão de fogo
monster:setSpeed(100)               -- Velocidade do dragão
monster:setMaxHealth(500)           -- Saúde máxima do dragão
monster:addHealth(500)              -- Adiciona saúde inicial

-- Definir o nome personalizado
monster:setCustomName("Dragão Ardente")

-- Configurar comportamento como um pet
monster:setPetBehavior(true)

-- Definir quem é o mestre do dragão (ID do jogador)
monster:setMaster(12345)  -- Substitua '12345' pelo ID real do jogador

-- Definir loot drop
monster:setDropLoot({
    {id = 266, chance = 100},  -- Exemplo de item: pocao de cura
    {id = 276, chance = 50}   -- Exemplo de item: pedra mágica
})

print("monster DragãoFogo carregado.")

### Explicação:
- **setOutfit**: Define a aparência do dragão (exemplo com lookType 620).
- **setSpeed**: Configura a velocidade do dragão.
- **setMaxHealth** e **addHealth**: Define e adiciona a saúde máxima do dragão.
- **setCustomName**: Define um nome personalizado para o dragão.
- **setPetBehavior**: Configura o comportamento como um pet.
- **setMaster**: Define quem é o mestre do dragão (substitua `12345` pelo ID real do jogador).
- **setDropLoot**: Define os itens que o dragão pode dropar ao morrer.

Este arquivo Lua cria e configura um monstro chamado "DragãoFogo" com as funções confirmadas fornecidas.