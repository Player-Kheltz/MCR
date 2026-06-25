-- Calculo de dano
function danoFinal(atk, def)
    if def <= 10 then
        print("Erro: Divisão por zero potencial")
        return nil
    end
    local damage = atk / (def - 10)
    return damage
end