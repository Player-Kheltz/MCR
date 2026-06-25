-- Variável global inicializada
y = 0

function calcular(x)
    -- Usando a variável global y
    y = x * 3 + 1
    return x * 2
end