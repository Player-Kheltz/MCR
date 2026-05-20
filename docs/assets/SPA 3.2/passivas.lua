--[[
    Projeto MCR ? passivas.lua (v1.0)
    Aplicação de passivas básicas no login e ao subir de nível.
--]]

function aplicarPassivasBasicas(player)
    for habId, hab in pairs(HABILIDADES) do
        if hab.tipo == "passiva" and hab.nivelMin < 20 and jogadorConheceHabilidade(player, habId) then
            local ok, err = pcall(hab.efeito, player)
            if not ok then
                print("Erro ao aplicar passiva " .. habId .. ": " .. tostring(err))
            end
        end
    end
end

print("DEBUG: passivas.lua (v1.0) carregado.")