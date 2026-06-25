-- Script auxiliar
local function calcularBonus(nivel)
    return nivel + 5
end

local xp = calcularBonus(10)
print("XP calculado: " .. xp)