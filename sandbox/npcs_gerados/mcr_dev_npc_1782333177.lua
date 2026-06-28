### Código Completo do NPC Thalor

```lua
local npcHandler = NPCHandler:new()

function onSay(cid, words)
    if isInArray(FOCUS_GREETWORDS, words) then
        selfSay("Bem-vindo à minha loja antiga! Que tal um pouco de nossa cultura tradição?", cid)
        return true
    end

    if isInArray(FOCUS_TRADE_MESSAGE, words) then
        selfSay("Claro! Vamos ver o que temos em estoque.", cid)
        npcHandler:addCallback(cid, "onSell")
        npcHandler:addCallback(cid, "onBuy")
        return true
    end

    return false
end

function onSell(cid)
    local items = {
        {id = 2160, name = "Espada de Fogo", price = 500},
        {id = 2497, name = "Arco e Flecha", price = 300},
        {id = 2818, name = "Pedra Preciosa", price = 1000}
    }

    selfSay("O que você deseja vender? Nós temos:", cid)
    for i, item in ipairs(items) do
        selfSay(item.name .. " - " .. item.price .. " gold", cid)
    end

    npcHandler:addCallback(cid, "onSellItem")
end

function onBuy(cid)
    local items = {
        {id = 2160, name = "Espada de Fogo", price = 500},
        {id = 2497, name = "Arco e Flecha", price = 300},
        {id = 2818, name = "Pedra Preciosa", price = 1000}
    }

    selfSay("O que você deseja comprar? Nós temos:", cid)
    for i, item in ipairs(items) do
        selfSay(item.name .. " - " .. item.price .. " gold", cid)
    end

    npcHandler:addCallback(cid, "onBuyItem")
end

function onSellNPC(cid, words)
    local items = {
        {id = 2160, name = "Espada de Fogo", price = 500},
        {id = 2497, name = "Arco e Flecha", price = 300},
        {id = 2818, name = "Pedra Preciosa", price = 1000}
    }

    for i, item in ipairs(items) do
        if string.lower(words) == item.name then
            local player = Player(cid)
            if player:getMoney() >= item.price then
                player:removeMoney(item.price)
                player:addNPC(item.id, 1)
                selfSay("Aqui está sua " .. item.name .. ", " .. cid .. "! Tenha um ótimo dia!", cid)
                return true
            else
                selfSay("Desculpe, mas você não tem dinheiro suficiente para comprar isso.", cid)
                return true
            end
        end
    end

    selfSay("Peço desculpas, mas não consigo encontrar esse item em nosso estoque.", cid)
    return true
end

function onBuyNPC(cid, words)
    local items = {
        {id = 2160, name = "Espada de Fogo", price = 500},
        {id = 2497, name = "Arco e Flecha", price = 300},
        {id = 2818, name = "Pedra Preciosa", price = 1000}
    }

    for i, item in ipairs(items) do
        if string.lower(words) == item.name then
            local player = Player(cid)
            if player:getItemCount(item.id) > 0 then
                player:removeNPC(item.id, 1)
                player:addMoney(item.price)
                selfSay("Aqui está o seu dinheiro por " .. item.name .. ", " .. cid .. "! Tenha um ótimo dia!", cid)
                return true
            else
                selfSay("Desculpe, mas você não tem esse item em sua mochila.", cid)
                return true
            end
        end
    end

    selfSay("Peço desculpas, mas não consigo encontrar esse item em sua mochila.", cid)
    return true
end

npcHandler:addCallback(cid, "onSay")
```

Espero que isso atenda às suas expectativas! Se houver mais alguma coisa que você precise, estou à disposição.