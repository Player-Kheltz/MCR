--[[
    Projeto MCR ? SPA v4.0 ? Callbacks do Event Bus
--]]

SPA.onEvent("onPlayerKill", function(player, target)
    if target:isMonster() and target.getRaceId then
        local race = target:getRaceId()
        if race == 6 then -- Dragão
            adicionarAfinidade(player, DOMINIO_COMBATE, 2)
        end
    end
end)

print("DEBUG: eventos_sistema.lua v4.0 carregado.")