--[[
    Projeto MCR ? util_criaturas.lua (v1.0)
    Funções auxiliares para manipulação de criaturas.
--]]

function getCreaturesInArea(centerPos, rangeX, rangeY)
    local creatures = {}
    for x = centerPos.x - rangeX, centerPos.x + rangeX do
        for y = centerPos.y - rangeY, centerPos.y + rangeY do
            local tile = Tile(Position(x, y, centerPos.z))
            if tile then
                local top = tile:getTopCreature()
                if top and top:isMonster() then
                    creatures[#creatures + 1] = top
                end
            end
        end
    end
    return creatures
end

function getCreatureDistance(creature1, creature2)
    return creature1:getPosition():getDistance(creature2:getPosition())
end

print("DEBUG: util_criaturas.lua (v1.0) carregado.")