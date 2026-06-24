-- Tentativa 2
HABILIDADES = {}


HABILIDADES[2701] = {
    nome = "Lance de Cristal",
    tipo = "projectile",
    dominio = {27},
    cooldown = 6,
    categoria = "single",
    efeitoConfig = {
        tipo = "projectile",
        dano = 1.0,
        percentual = 0.5,
        elemento = COMBAT_ENERGYDAMAGE,
    },
    postura = {
        [1] = { efeitoConfig = { dano = 1.3 } },
    },
    niveis = {
        [5] = { { mod = "efeitoConfig", dano = "*1.15" } },
    },
    sinergias = {
        [23] = { descricao = "Fogo + Cristal", nivelMin = 1, efeitoConfig = { elemento = COMBAT_FIREDAMAGE } },
    },
    estados = {
        vinculo = { efeitoConfig = { dano = 1.5 } },
    },
    condicoes = {
        cercado = { efeitoConfig = { raio = 5, dano = 1.2 } },
    },
}

HABILIDADES[2702] = {
    nome = "Cubo de Cristal",
    tipo = "area_target",
    dominio = {27},
    cooldown = 8,
    categoria = "aoe",
    efeitoConfig = {
        tipo = "area_target",
        dano = 1.5,
        percentual = 0.3,
        elemento = COMBAT_ENERGYDAMAGE,
    },
    postura = {
        [1] = { efeitoConfig = { dano = 1.8 } },
    },
    niveis = {
        [5] = { { mod = "efeitoConfig", dano = "*1.2" } },
    },
    sinergias = {
        [23] = { descricao = "Fogo + Cristal", nivelMin = 1, efeitoConfig = { elemento = COMBAT_FIREDAMAGE } },
    },
    estados = {
        vinculo = { efeitoConfig = { dano = 1.7 } },
    },
    condicoes = {
        cercado = { efeitoConfig = { raio = 5, dano = 1.4 } },
    },
}


print("OK")
