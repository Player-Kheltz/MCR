function buscarItem(player, id)
    local item = player:getItem(id)
    if item then 
        return item 
    end
    return nil -- Retorno padrão para casos em que não é encontrado o item
end