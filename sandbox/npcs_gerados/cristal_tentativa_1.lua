-- Tentativa 1
HABILIDADES = {}


HABILIDADES[27001] = {
    nome = "Cristal Brilhante",
    tipo = "gatilho",
    dominio = {27},
    cooldown = 4,
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

HABILIDADES[27002] = {
    nome = "Cristal Explodente",
    tipo = "gatilho",
    dominio = {27},
    cooldown = 6,
    categoria = "single",
    efeitoConfig = {
        tipo = "projectile",
        dano = 1.5,
        percentual = 0.7,
        elemento = COMBAT_ENERGYDAMAGE,
    },
    postura = {
        [1] = { efeitoConfig = { dano = 2.0 } },
    },
    niveis = {
        [10] = { { mod = "efeitoConfig", dano = "*1.3" } },
    },
    sinergias = {
        [24] = { descricao = "Gelo + Cristal", nivelMin = 1, efeitoConfig = { elemento = COMBAT_ICEDAMAGE } },
    },
    estados = {
        vinculo = { efeitoConfig = { dano = 1.8 } },
    },
    condicoes = {
        cercado = { efeitoConfig = { raio = 7, dano = 1.5 } },
    },
}

HABILIDADES[27003] = {
    nome = "Cristal Absorvente",
    tipo = "gatilho",
    dominio = {27},
    cooldown = 8,
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
        [15] = { { mod = "efeitoConfig", dano = "*1.2" } },
    },
    sinergias = {
        [25] = { descricao = "Veneno + Cristal", nivelMin = 1, efeitoConfig = { elemento = COMBAT_EARTHDAMAGE } },
    },
    estados = {
        vinculo = { efeitoConfig = { dano = 1.4 } },
    },
    condicoes = {
        cercado = { efeitoConfig = { raio = 6, dano = 1.3 } },
    },
}


print("OK")
