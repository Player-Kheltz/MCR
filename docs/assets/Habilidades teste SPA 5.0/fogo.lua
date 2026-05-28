--[[
    Projeto MCR ? SPA ? Habilidades de Fogo (23)
    Perfil: Especialidade (36 habilidades + Traço Inerente)
    Arquitetura modular v4.6
--]]

-- ============================================================
-- TRAÇO INERENTE: Coração de Fogo
-- ============================================================
-- Nível 5: Ataques de fogo têm 10% de chance de incendiar o alvo (queimadura leve).
-- Nível 10: Inimigos em chamas explodem ao morrer, causando dano em área (raio 2).
-- Nível 15: Emite uma aura de calor que causa dano contínuo a inimigos próximos (raio 1).
-- Nível 20: A aura expande (raio 2) e concede imunidade a campos de fogo.
-- (A implementação dos efeitos é feita via passivas_ataque.lua e eventos de combate)

-- ============================================================
-- ÁRVORE I (nível 5): Passiva de Identidade
-- ============================================================
HABILIDADES[23001] = {
    nome = "Chama Interior",
    tipo = "passiva",
    dominio = {23},
    nivelMin = 5,
    descricaoEfeito = "Ataques de fogo têm 10% de chance de causar queimadura.",
    cor = COR.ELEM_FOGO,
    efeito = function(player)
        player:setCombatModifier("fire_burn_chance", 10)
    end
}

-- ============================================================
-- ÁRVORE II (nível 10): Passiva de Expansão
-- ============================================================
HABILIDADES[23002] = {
    nome = "Piromania",
    tipo = "passiva",
    dominio = {23},
    nivelMin = 10,
    descricaoEfeito = "Aumenta o dano de fogo em 12%.",
    cor = COR.ELEM_FOGO,
    efeito = function(player)
        player:setCombatModifier("fire_damage", 12)
    end
}

-- ============================================================
-- ÁRVORE III (nível 15): Gatilho de Assinatura ? Bola de Fogo
-- ============================================================
HABILIDADES[23003] = {
    nome = "Bola de Fogo",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 15,
    descricaoEfeito = "Explosão de fogo centrada no alvo, causando dano em área.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "area_target",
        percentual = 0.8,
        areaPercentual = 0.4,
        raio = 2,
        magicEffect = CONST_ME_FIREAREA
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 8,
    categoria = "aoe",
    condicaoFocoMin = 50,
    posturaMod = {
        [1] = { chanceMult = 1.4 },
        [2] = { chanceMult = 1.0 },
        [3] = { chanceMult = 0.7 }
    }
}

-- ============================================================
-- ÁRVORE IV (nível 20): Passiva de Maestria
-- ============================================================
HABILIDADES[23004] = {
    nome = "Inferno do Mestre",
    tipo = "passiva",
    dominio = {23},
    nivelMin = 20,
    descricaoEfeito = "Maestria em Fogo: dano de fogo ignora 20% da armadura e ensina Bola de Fogo a Água e Gelo.",
    cor = COR.ELEM_FOGO,
    efeito = function(player)
        player:setCombatModifier("fire_penetration", 20)
        if not jogadorConheceHabilidade(player, 24003) then
            aprenderHabilidade(player, 24003)
        end
    end
}

-- ============================================================
-- PASSIVAS DE ATRIBUTO (3 restantes)
-- ============================================================
HABILIDADES[23005] = {
    nome = "Passos Flamejantes",
    tipo = "passiva",
    dominio = {23},
    nivelMin = 3,
    descricaoEfeito = "Aumenta a velocidade de movimento em 1.5% por nível de Fogo.",
    cor = COR.ELEM_FOGO,
    efeito = function(player) end  -- gerido por recalcularVelocidade
}

HABILIDADES[23006] = {
    nome = "Fúria do Fogo",
    tipo = "passiva",
    dominio = {23},
    nivelMin = 8,
    descricaoEfeito = "Aumenta o dano de fogo em 1% por nível de Fogo.",
    cor = COR.ELEM_FOGO,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 23)
        player:setCombatModifier("fire_damage", 12 + nivel)
    end
}

HABILIDADES[23007] = {
    nome = "Pele de Fogo",
    tipo = "passiva",
    dominio = {23},
    nivelMin = 6,
    descricaoEfeito = "Aumenta a resistência a fogo em 1% por nível de Fogo.",
    cor = COR.ELEM_FOGO,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 23)
        player:setCombatModifier("fire_resistance", nivel)
    end
}

-- ============================================================
-- GATILHOS DE COMBATE (14)
-- ============================================================
HABILIDADES[23010] = {
    nome = "Lança-Chamas",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 6,
    descricaoEfeito = "Dispara uma rajada de fogo que causa queimadura.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_FIRE,
        duration = 4000,
        periodicDamage = 12,
        comDano = true,
        percentual = 0.35,
        magicEffect = CONST_ME_FIREATTACK
    },
    gatilho = "onAttack",
    cooldown = 10,
    prioridade = 7,
    categoria = "debuff",
    condicaoFocoMin = 25
}

HABILIDADES[23011] = {
    nome = "Explosão Incendiária",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 9,
    descricaoEfeito = "Explosão no chão que causa dano e queimadura em área.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "area_ground",
        centro = "alvo",
        raio = 2,
        percentual = 0.5,
        magicEffect = CONST_ME_FIREAREA,
        condicao = CONDITION_FIRE,
        condDuration = 3000,
        periodicDamage = 10
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 8,
    categoria = "aoe",
    condicao = "cercadoAlvo",
    condicaoFocoMin = 50
}

HABILIDADES[23012] = {
    nome = "Chuva de Fogo",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 12,
    descricaoEfeito = "Dispara três projéteis de fogo em sequência.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "rajada",
        percentual = 0.35,
        numProjeteis = 3,
        intervaloMs = 250
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 8,
    categoria = "single",
    condicaoFocoMin = 50
}

HABILIDADES[23013] = {
    nome = "Onda de Calor",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 8,
    descricaoEfeito = "Acelera a velocidade de ataque por 1.5 segundos.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "buff_speed",
        multiplier = 0.5,
        durationMs = 1500
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 5,
    categoria = "buff",
    condicaoFocoMin = 30
}

HABILIDADES[23014] = {
    nome = "Incêndio",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 14,
    descricaoEfeito = "Cria um campo de fogo no chão que causa dano contínuo.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "field",
        centro = "alvo",
        elemento = COMBAT_FIREDAMAGE,
        danoPorTick = 15,
        duracaoMs = 6000,
        intervaloMs = 1000,
        magicEffect = CONST_ME_FIREAREA,
        raio = 5 
    },
    gatilho = "onAttack",
    cooldown = 22,
    prioridade = 8,
    categoria = "aoe",
    condicaoFocoMin = 70
}

HABILIDADES[23015] = {
    nome = "Erupção",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 11,
    descricaoEfeito = "Explosão no chão ao redor do jogador, empurrando inimigos.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "area_ground",
        centro = "jogador",
        raio = 2,
        percentual = 0.4,
        magicEffect = CONST_ME_FIREAREA,
        knockback = true
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 7,
    categoria = "aoe",
    condicao = "cercado",
    condicaoFocoMin = 60
}

HABILIDADES[23016] = {
    nome = "Labareda",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 7,
    descricaoEfeito = "Dispara um projétil de fogo que causa dano extra.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "dano_extra",
        percentual = 0.3,
        tipo = "distancia",
        magicEffect = CONST_ME_FIREATTACK
    },
    gatilho = "onAttack",
    cooldown = 8,
    prioridade = 6,
    categoria = "single"
}

HABILIDADES[23017] = {
    nome = "Nova Solar",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 16,
    descricaoEfeito = "Explosão massiva centrada no jogador, causando dano e queimadura.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "area_ground",
        centro = "jogador",
        raio = 3,
        percentual = 0.6,
        magicEffect = CONST_ME_FIREAREA,
        condicao = CONDITION_FIRE,
        condDuration = 4000,
        periodicDamage = 15
    },
    gatilho = "onAttack",
    cooldown = 24,
    prioridade = 9,
    categoria = "aoe",
    condicao = "cercado",
    condicaoFocoMin = 85
}

HABILIDADES[23018] = {
    nome = "Tocha Viva",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 13,
    descricaoEfeito = "Causa queimadura prolongada no alvo.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_FIRE,
        duration = 5000,
        periodicDamage = 18,
        comDano = true,
        percentual = 0.4,
        magicEffect = CONST_ME_FIREAREA
    },
    gatilho = "onAttack",
    cooldown = 14,
    prioridade = 7,
    categoria = "debuff",
    condicaoFocoMin = 40
}

HABILIDADES[23019] = {
    nome = "Meteoro",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 18,
    descricaoEfeito = "Invoca um meteoro que causa dano massivo em área.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "area_target",
        percentual = 1.0,
        areaPercentual = 0.6,
        raio = 3,
        magicEffect = CONST_ME_FIREAREA,
        knockback = true
    },
    gatilho = "onAttack",
    cooldown = 26,
    prioridade = 9,
    categoria = "aoe",
    condicaoFocoMin = 90
}

HABILIDADES[23020] = {
    nome = "Estouro",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 10,
    descricaoEfeito = "Causa dano extra se o alvo estiver em chamas.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "dano_extra",
        percentual = 0.5,
        magicEffect = CONST_ME_FIREAREA
    },
    gatilho = "onAttack",
    cooldown = 12,
    prioridade = 6,
    categoria = "single"
}

HABILIDADES[23021] = {
    nome = "Rajada de Fogo",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 15,
    descricaoEfeito = "Dispara quatro projéteis de fogo em rápida sucessão.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "rajada",
        percentual = 0.3,
        numProjeteis = 4,
        intervaloMs = 200
    },
    gatilho = "onAttack",
    cooldown = 20,
    prioridade = 8,
    categoria = "single",
    condicaoFocoMin = 75
}

HABILIDADES[23022] = {
    nome = "Fogo Interior",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 5,
    descricaoEfeito = "Aumenta a velocidade de ataque brevemente.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "buff_speed",
        multiplier = 0.4,
        durationMs = 600
    },
    gatilho = "onAttack",
    cooldown = 12,
    prioridade = 4,
    categoria = "buff"
}

HABILIDADES[23023] = {
    nome = "Aniquilação Flamejante",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 17,
    descricaoEfeito = "Golpe final massivo contra alvos com vida baixa, com medo em área.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "finisher",
        percentual = 1.5,
        magicEffect = CONST_ME_FIREAREA,
        knockback = true,
        medoArea = true
    },
    gatilho = "onAttack",
    cooldown = 30,
    prioridade = 10,
    categoria = "finisher",
    condicao = "vidaBaixa",
    condicaoFocoMin = 90
}

-- ============================================================
-- GATILHOS DE CONDIÇÃO/DEFESA (7)
-- ============================================================
HABILIDADES[23030] = {
    nome = "Queimadura Leve",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 7,
    descricaoEfeito = "Causa queimadura no alvo.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_FIRE,
        duration = 3000,
        periodicDamage = 10,
        comDano = true,
        percentual = 0.3,
        magicEffect = CONST_ME_FIREATTACK
    },
    gatilho = "onAttack",
    cooldown = 10,
    prioridade = 6,
    categoria = "debuff",
    condicaoFocoMin = 20
}

HABILIDADES[23031] = {
    nome = "Explosão Cegante",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 12,
    descricaoEfeito = "Atordoa o alvo com um clarão de fogo.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_DAZZLED,
        duration = 2000,
        comDano = true,
        percentual = 0.35,
        magicEffect = CONST_ME_FIREAREA
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 6,
    categoria = "debuff",
    condicaoFocoMin = 40
}

HABILIDADES[23032] = {
    nome = "Parede de Fogo",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 9,
    descricaoEfeito = "Reduz o dano recebido e causa queimadura a atacantes.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "defesa_barreira",
        factor = 0.5,
        durationMs = 2000
    },
    gatilho = "onReceiveDamage",
    cooldown = 20,
    prioridade = 5,
    categoria = "defense"
}

HABILIDADES[23033] = {
    nome = "Fúria do Fogo",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 10,
    descricaoEfeito = "Ao receber dano, sua velocidade de ataque aumenta por 2s.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "buff_speed",
        multiplier = 0.6,
        durationMs = 2000
    },
    gatilho = "onReceiveDamage",
    cooldown = 18,
    prioridade = 5,
    categoria = "buff"
}

HABILIDADES[23034] = {
    nome = "Chamas da Vida",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 14,
    descricaoEfeito = "Roubo de vida por 4 segundos.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "life_leech",
        leechPercent = 15,
        durationSec = 4
    },
    gatilho = "onAttack",
    cooldown = 22,
    prioridade = 5,
    categoria = "buff",
    condicaoFocoMin = 40
}

HABILIDADES[23035] = {
    nome = "Combustão Espontânea",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 16,
    descricaoEfeito = "Aplica uma queimadura prolongada e intensa no alvo.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_FIRE,
        duration = 6000,
        periodicDamage = 20,
        comDano = true,
        percentual = 0.45,
        magicEffect = CONST_ME_FIREAREA
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 8,
    categoria = "debuff",
    condicaoFocoMin = 60
}

HABILIDADES[23036] = {
    nome = "Contra-Explosão",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 8,
    descricaoEfeito = "Ao bloquear, contra-ataca com fogo todos os inimigos ao redor.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "defesa_contra_ataque",
        percentual = 0.35,
        magicEffect = CONST_ME_FIREAREA
    },
    gatilho = "onBlock",
    cooldown = 14,
    prioridade = 6,
    categoria = "defense",
    condicao = "inimigosProximos"
}

-- ============================================================
-- GATILHOS DE SINERGIA (4)
-- ============================================================
HABILIDADES[23040] = {
    nome = "Lâmina de Fogo",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 10,
    descricaoEfeito = "A lâmina causa dano de fogo extra. Requer Lâminas.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "condicao",
        conditionType = CONDITION_FIRE,
        duration = 3000,
        periodicDamage = 10,
        comDano = true,
        percentual = 0.4,
        magicEffect = CONST_ME_FIREAREA,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {10, 100, 101},
    efeitosSecundarios = {
        [10] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 10)
            if nivel >= 10 then
                local cond = Condition(CONDITION_FIRE, CONDITIONID_COMBAT, 3000)
                cond:setParameter(CONDITION_PARAM_PERIODICDAMAGE, 10 + nivel)
                cond:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
                t:addCondition(cond)
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 14,
    prioridade = 7,
    categoria = "sinergia",
    condicaoFocoMin = 30
}

HABILIDADES[23041] = {
    nome = "Magma Vivo",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 14,
    descricaoEfeito = "Combina fogo e terra, criando um campo de magma. Requer Terra.",
    cor = COR.ELEM_TERRA,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "field",
        centro = "alvo",
        elemento = COMBAT_FIREDAMAGE,
        danoPorTick = 20,
        duracaoMs = 5000,
        intervaloMs = 1000,
        magicEffect = CONST_ME_FIREAREA,
        nivelMinSecundario = 12
    },
    sinergiaDominios = {25},
    efeitosSecundarios = {
        [25] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 25)
            if nivel >= 12 then
                local cond = Condition(CONDITION_PARALYZE, CONDITIONID_COMBAT, 2000)
                t:addCondition(cond)  -- lentidão da terra
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 20,
    prioridade = 8,
    categoria = "sinergia",
    condicaoFocoMin = 60
}

HABILIDADES[23042] = {
    nome = "Tempestade de Fogo",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 16,
    descricaoEfeito = "Fogo e ar criam uma tempestade flamejante que causa dano e empurra. Requer Ar (Precisão).",
    cor = COR.DOM_COMBATE_PRECISAO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "area_ground",
        centro = "alvo",
        raio = 2,
        percentual = 0.5,
        magicEffect = CONST_ME_FIREAREA,
        knockback = true,
        nivelMinSecundario = 12
    },
    sinergiaDominios = {13, 120, 121},
    efeitosSecundarios = {
        [13] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 13)
            if nivel >= 12 then
                -- rajada de vento adicional
                local criaturas = getCreaturesInArea(t:getPosition(), 2, 2)
                for _, c in ipairs(criaturas) do
                    if c:isMonster() and c:getId() ~= t:getId() then
                        empurrarAlvo(p, c)
                    end
                end
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 22,
    prioridade = 9,
    categoria = "sinergia",
    condicaoFocoMin = 75
}

HABILIDADES[23043] = {
    nome = "Escudo Térmico",
    tipo = "gatilho",
    dominio = {23},
    nivelMin = 12,
    descricaoEfeito = "Ao bloquear, emite uma onda de calor que causa dano e reduz dano recebido. Requer Escudo.",
    cor = COR.DOM_ESCUDO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "defesa_contra_ataque",
        percentual = 0.4,
        magicEffect = CONST_ME_FIREAREA,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {15},
    efeitosSecundarios = {
        [15] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 15)
            if nivel >= 10 then
                p:setDamageTakenModifier(0.8)
                addEvent(function()
                    local pl = Player(p:getId())
                    if pl then pl:setDamageTakenModifier(1.0) end
                end, 2000)
            end
        end
    },
    gatilho = "onBlock",
    cooldown = 18,
    prioridade = 7,
    categoria = "sinergia",
    condicaoFocoMin = 40
}

-- ============================================================
-- TRANSFORMAÇÕES (4)
-- ============================================================
HABILIDADES[23050] = {
    nome = "Fagulha",
    tipo = "transformacao",
    dominio = {23},
    nivelMin = 10,
    descricaoEfeito = "Lampejo: o dano de fogo aumenta 15% e você se move mais rápido.",
    cor = COR.ELEM_FOGO,
    efeito = function(player)
        player:setCombatModifier("fire_damage", (player:getCombatModifier("fire_damage") or 0) + 15)
    end,
    desfazer = function(player)
        player:setCombatModifier("fire_damage", (player:getCombatModifier("fire_damage") or 15) - 15)
    end
}

HABILIDADES[23051] = {
    nome = "Labareda Viva",
    tipo = "transformacao",
    dominio = {23},
    nivelMin = 15,
    descricaoEfeito = "Vínculo: o dano de fogo aumenta 25% e as chamas lambem seu corpo.",
    cor = COR.ELEM_FOGO,
    efeito = function(player)
        local atual = player:getCombatModifier("fire_damage") or 0
        player:setCombatModifier("fire_damage", atual + 25)
    end,
    desfazer = function(player)
        local atual = player:getCombatModifier("fire_damage") or 25
        player:setCombatModifier("fire_damage", atual - 25)
    end
}

HABILIDADES[23052] = {
    nome = "Fornalha Viva",
    tipo = "transformacao",
    dominio = {23},
    nivelMin = 20,
    descricaoEfeito = "Maestria: o dano de fogo ignora 20% da armadura e o Vínculo é permanente.",
    cor = COR.ELEM_FOGO,
    efeito = function(player)
        player:setCombatModifier("fire_penetration", 20)
    end,
    desfazer = function(player)
        player:setCombatModifier("fire_penetration", 0)
    end
}

HABILIDADES[23053] = {
    nome = "Apocalipse Flamejante",
    tipo = "transformacao",
    dominio = {23},
    nivelMin = 18,
    descricaoEfeito = "Transformação especial: invoca uma chuva de meteoros que causa dano massivo em área por 6 segundos.",
    cor = COR.ELEM_FOGO,
    efeito = function(player)
        local pid = player:getId()
        local function tick(count)
            local pl = Player(pid)
            if not pl or count >= 6 then return end
            local pos = pl:getPosition()
            local criaturas = getCreaturesInArea(pos, 4, 4)
            for _, c in ipairs(criaturas) do
                if c:isMonster() then
                    local dmg = math.floor((pl:getMagicLevel() * 3) * (1 + count * 0.25))
                    doTargetCombatHealth(pl, c, COMBAT_FIREDAMAGE, -dmg, -dmg, CONST_ME_FIREAREA)
                end
            end
            pos:sendMagicEffect(CONST_ME_FIREAREA)
            addEvent(tick, 1000, count + 1)
        end
        tick(0)
    end,
    desfazer = function(player) end
}

print("DEBUG: habilidades_fogo.lua carregado.")