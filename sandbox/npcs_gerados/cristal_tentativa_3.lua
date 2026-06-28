-- Tentativa 3
HABILIDADES = {}

HABILIDADES[27001] = {
    nome = "Lanca de Cristal",
    tipo = "gatilho",
    dominio = {27},
    cooldown = 4,
    categoria = "single",
    efeitoConfig = {
        tipo = "projectile",
        dano = 1.5,
        percentual = 0.5,
        elemento = COMBAT_ENERGYDAMAGE,
    },
    postura = {
        [1] = { efeitoConfig = { dano = 1.8 } },
        [3] = { efeitoConfig = { dano = 1.0 } },
    },
    niveis = {
        [5] = { { mod = "efeitoConfig", dano = "*1.15" } },
        [10] = { { mod = "efeitoConfig", distancia = "+1" } },
    },
}

print("OK")
