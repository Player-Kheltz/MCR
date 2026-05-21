--[[
    Projeto MCR ? util_efeitos.lua (v1.0)
    Função auxiliar para envio de efeitos visuais (projécteis e magias).
--]]

function sendDistanceEffect(player, target, shootEffect, damageEffect)
    local playerPos = player:getPosition()
    local targetPos = target:getPosition()
    playerPos:sendDistanceEffect(targetPos, shootEffect or CONST_ANI_ARROW)
    targetPos:sendMagicEffect(damageEffect or CONST_ME_DRAWBLOOD)
end

print("DEBUG: util_efeitos.lua (v1.0) carregado.")