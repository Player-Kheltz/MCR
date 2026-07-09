-- Atualizações de efeitos visuais para Terra e Veneno (substituir as habilidades existentes)

-- Erupção Tóxica (25003)
HABILIDADES[25003] = {
    nome = "Erupção Tóxica",
    tipo = "gatilho",
    dominio = {25},
    nivelMin = 15,
    descricaoEfeito = "Explosão venenosa centrada no alvo, causando dano e envenenamento em área.",
    cor = COR.ELEM_VENENO,
    efeitoConfig = {
        tipo = "area_target",
        percentual = 0.7,
        areaPercentual = 0.4,
        raio = 2,
        magicEffect = CONST_ME_GREEN_RINGS,
        condicao = CONDITION_POISON,
        condDuration = 4000,
        periodicDamage = 12,
        conditionMagicEffect = CONST_ME_GREEN_RINGS
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 8,
    categoria = "aoe",
    condicaoFocoMin = 50,
    posturaMod = {
        [1] = { chanceMult = 1.3 },
        [2] = { chanceMult = 1.0 },
        [3] = { chanceMult = 0.8 }
    }
}

-- Nuvem Tóxica (25011)
HABILIDADES[25011] = {
    nome = "Nuvem Tóxica",
    tipo = "gatilho",
    dominio = {25},
    nivelMin = 9,
    descricaoEfeito = "Cria uma nuvem de veneno no chão que causa dano e envenenamento.",
    cor = COR.ELEM_VENENO,
    efeitoConfig = {
        tipo = "area_ground",
        centro = "alvo",
        raio = 2,
        percentual = 0.4,
        magicEffect = CONST_ME_GREEN_RINGS,
        condicao = CONDITION_POISON,
        condDuration = 4000,
        periodicDamage = 10,
        conditionMagicEffect = CONST_ME_GREEN_RINGS
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 7,
    categoria = "aoe",
    condicao = "cercadoAlvo",
    condicaoFocoMin = 50
}

-- Explosão de Esporos (25014)
HABILIDADES[25014] = {
    nome = "Explosão de Esporos",
    tipo = "gatilho",
    dominio = {25},
    nivelMin = 14,
    descricaoEfeito = "Liberta esporos venenosos que envenenam todos os inimigos ao redor.",
    cor = COR.ELEM_VENENO,
    efeitoConfig = {
        tipo = "area_ground",
        centro = "jogador",
        raio = 2,
        percentual = 0.3,
        magicEffect = CONST_ME_GREEN_RINGS,
        condicao = CONDITION_POISON,
        condDuration = 5000,
        periodicDamage = 15,
        conditionMagicEffect = CONST_ME_GREEN_RINGS
    },
    gatilho = "onAttack",
    cooldown = 20,
    prioridade = 8,
    categoria = "aoe",
    condicao = "cercado",
    condicaoFocoMin = 70
}

-- Veneno Corrosivo (25018)
HABILIDADES[25018] = {
    nome = "Veneno Corrosivo",
    tipo = "gatilho",
    dominio = {25},
    nivelMin = 15,
    descricaoEfeito = "Aplica um veneno devastador que causa dano massivo ao longo do tempo.",
    cor = COR.ELEM_VENENO,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_POISON,
        duration = 6000,
        periodicDamage = 20,
        comDano = true,
        percentual = 0.5,
        magicEffect = CONST_ME_GREEN_RINGS,
        conditionMagicEffect = CONST_ME_GREEN_RINGS
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 8,
    categoria = "debuff",
    condicaoFocoMin = 60
}

-- Erupção Ácida (25036)
HABILIDADES[25036] = {
    nome = "Erupção Ácida",
    tipo = "gatilho",
    dominio = {25},
    nivelMin = 17,
    descricaoEfeito = "Explosão de ácido que corrói a armadura do alvo e causa dano prolongado.",
    cor = COR.ELEM_VENENO,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_POISON,
        duration = 5000,
        periodicDamage = 18,
        comDano = true,
        percentual = 0.55,
        magicEffect = CONST_ME_GREEN_RINGS,
        conditionMagicEffect = CONST_ME_GREEN_RINGS
    },
    gatilho = "onAttack",
    cooldown = 22,
    prioridade = 8,
    categoria = "debuff",
    condicaoFocoMin = 75
}