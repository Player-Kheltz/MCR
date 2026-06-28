--[[
    Projeto MCR — SPA — CLAVAS LEVES (112)
    Perfil: Especialidade (Clavas 12 -> Combate 1)
    SHC: 5 camadas contextuais
    IDs: 11201-11220
--]]
-- Traco: "Toque Rapido" — Nv5: velocidade+5% | Nv10: atordoamento+5% | Nv15: combo | Nv20: mestre do ritmo

HABILIDADES[11201] = {
    nome = "Toque Rapido",
    tipo = "gatilho",
    dominio = {112},
    cooldown = 2,
    categoria = "single",
    descricao = "Golpe rapido que atordoa.",
    efeitoConfig = {
        tipo = "melee",
        dano = 0.7,
        percentual = 0.25,
        elemento = COMBAT_PHYSICALDAMAGE,
    },
    postura = {
        [1] = { efeitoConfig = { dano = 0.9 } },
        [3] = { efeitoConfig = { dano = 0.4 } },
    },
    niveis = {
        [5] = { { mod = "efeitoConfig", dano = "*1.15" } },
        [10] = { { mod = "efeitoConfig", dano = "*1.2" } },
    },
}
HABILIDADES[11202] = {
    nome = "Ritmo de Batalha",
    tipo = "passiva",
    dominio = {112},
    cooldown = 0,
    categoria = "passiva",
    descricao = "Aumenta velocidade de ataque.",
    efeitoConfig = {
        tipo = "passive_scaling",
        velocidadeAtaque = 0.01,
    },
    niveis = {
        [5] = { { mod = "efeitoConfig", velocidadeAtaque = 0.01 } },
        [10] = { { mod = "efeitoConfig", velocidadeAtaque = 0.01 } },
    },
}
HABILIDADES[11203] = {
    nome = "Golpe Rapido",
    tipo = "gatilho",
    dominio = {112},
    cooldown = 2,
    categoria = "single",
    descricao = "Soco rapido que atordoa levemente.",
    efeitoConfig = {
        tipo = "melee",
        dano = 1.0,
        percentual = 0.35,
        elemento = COMBAT_PHYSICALDAMAGE,
    },
    postura = {
        [1] = { efeitoConfig = { dano = 1.2 } },
        [3] = { efeitoConfig = { dano = 0.7 } },
    },
    niveis = {
        [5] = { { mod = "efeitoConfig", dano = "*1.15" } },
        [10] = { { mod = "efeitoConfig", dano = "*1.15" } },
    },
}
HABILIDADES[11204] = {
    estados = {
        vinculo = {
            efeitoConfig = { dano = 1.5, damageType = "absolute" },
        },
        lampejo = {
            efeitoConfig = { dano = 2.0, custoMana = 0 },
        },
    },
HABILIDADES[11205] = {
    sinergias = {
        [113] = {
            descricao = "Impacto Pesado: dano de impacto extra",
            nivelMin = 1,
            efeitoConfig = {
                dano = 1.0 + 0.2,
            },
        },
    },
HABILIDADES[11206] = {
    condicoes = {
        vidaBaixa = {
            efeitoConfig = { lifesteal = 0.3, dano = 1.4 },
        },
    },
HABILIDADES[11207] = {
    nome = "Golpe Atordoante",
    tipo = "gatilho",
    dominio = {112},
    cooldown = 5,
    categoria = "single",
    descricao = "Golpe que atordoa o alvo.",
    efeitoConfig = {
        tipo = "melee",
        dano = 1.3,
        percentual = 0.45,
        elemento = COMBAT_PHYSICALDAMAGE,
    },
    postura = {
        [1] = { efeitoConfig = { dano = 1.6 } },
        [3] = { efeitoConfig = { dano = 0.9 } },
    },
    niveis = {
        [5] = { { mod = "efeitoConfig", dano = "*1.15" } },
        [10] = { { mod = "efeitoConfig", dano = "*1.15" } },
    },
}
HABILIDADES[11208] = {
    estados = {
        vinculo = {
            efeitoConfig = { dano = 1.5, damageType = "absolute" },
        },
        lampejo = {
            efeitoConfig = { dano = 2.0, custoMana = 0 },
        },
    },
HABILIDADES[11209] = {
    nome = "Foco Total",
    tipo = "gatilho",
    dominio = {112},
    cooldown = 8,
    categoria = "buff",
    descricao = "Foco que aumenta acerto critico.",
    efeitoConfig = {
        tipo = "buff",
        dano = 0,
        percentual = 0,
        elemento = COMBAT_PHYSICALDAMAGE,
    },
    postura = {
        [1] = { efeitoConfig = { dano = 0 } },
        [3] = { efeitoConfig = { dano = 0 } },
    },
    niveis = {
        [5] = { { mod = "efeitoConfig", dano = "*1.15" } },
        [10] = { { mod = "efeitoConfig", duracao = 2 } },
    },
}
HABILIDADES[11210] = {
    sinergias = {
        [113] = {
            descricao = "Impacto Pesado: dano de impacto extra",
            nivelMin = 1,
            efeitoConfig = {
                dano = 1.0 + 0.2,
            },
        },
    },
    estados = {
        vinculo = {
            efeitoConfig = { dano = 1.5, damageType = "absolute" },
        },
        lampejo = {
            efeitoConfig = { dano = 2.0, custoMana = 0 },
        },
    },

print(">> SPA: habilidades/clavas_leves.lua carregado")
