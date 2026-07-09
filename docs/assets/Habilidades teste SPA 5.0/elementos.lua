--[[
    Projeto MCR ? SPA ? Habilidades de Elementos (20)
    Perfil: Secundário (34 habilidades + Traço Inerente)
    Arquitetura modular v4.6
--]]

-- ============================================================
-- TRAÇO INERENTE: Núcleo Elemental
-- ============================================================
-- Nível 5: Ataques elementais têm 5% de chance de aplicar um efeito secundário (queimadura, lentidão, envenenamento, paralisia leve) baseado no elemento.
-- Nível 10: A chance sobe para 10% e o efeito secundário é mais forte (maior dano/duração).
-- Nível 15: Concede resistência a todos os elementos igual a 3% por nível de Elementos.
-- Nível 20: Síntese Superior ? "Avatar Elemental": ao causar dano elemental, há 15% de chance de libertar uma onda do elemento oposto (fogo ? água, terra ? energia) causando 25% do dano original como dano extra do segundo elemento.

HABILIDADES[26999] = {
    nome = "Tempestade de Raios",
    tipo = "gatilho",
    dominio = {26},  -- Energia
    nivelMin = 15,
    descricaoEfeito = "Invoca uma tempestade que atinge um inimigo aleatório a cada 450ms por 3.6s.",
    cor = COR.ELEM_RAIO,
    efeitoConfig = {
        tipo = "storm",
        centro = "alvo",
        raio = 3,
        elemento = COMBAT_ENERGYDAMAGE,
        danoPorTick = 25,
        intervaloMs = 450,
        duracaoMs = 3600,
        magicEffect = CONST_ME_ENERGYHIT
    },
    gatilho = "onAttack",
    cooldown = 20,
    prioridade = 8,
    categoria = "aoe",
    condicaoFocoMin = 50
}


-- ============================================================
-- ÁRVORE I (nível 5): Passiva de Identidade
-- ============================================================
HABILIDADES[2001] = {
    nome = "Afinidade Elemental",
    tipo = "passiva",
    dominio = {20},
    nivelMin = 5,
    descricaoEfeito = "Aumenta o dano elemental em 5%.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        player:setCombatModifier("elemental_damage", 5)
    end
}

-- ============================================================
-- ÁRVORE II (nível 10): Passiva de Expansão ? Sinergia com Filhos
-- ============================================================
HABILIDADES[2002] = {
    nome = "Sinergia dos Elementos",
    tipo = "passiva",
    dominio = {20},
    nivelMin = 10,
    descricaoEfeito = "Concede bónus adicionais baseados nos domínios filhos.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        if getNivelEfetivo(player, 23) >= 10 then  -- Fogo
            player:setCombatModifier("fire_damage", (player:getCombatModifier("fire_damage") or 0) + 8)
        end
        if getNivelEfetivo(player, 24) >= 10 then  -- Água e Gelo
            player:setCombatModifier("ice_paralyze_duration", 500)
        end
        if getNivelEfetivo(player, 25) >= 10 then  -- Terra e Veneno
            player:setCombatModifier("earth_poison_damage", 5)
        end
        if getNivelEfetivo(player, 26) >= 10 then  -- Energia
            player:setCombatModifier("energy_chain_chance", 10)
        end
    end
}

-- ============================================================
-- ÁRVORE III (nível 15): Gatilho de Assinatura ? Tempestade Elemental
-- ============================================================
HABILIDADES[2003] = {
    nome = "Tempestade Elemental",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 15,
    descricaoEfeito = "Invoca uma tempestade que causa dano baseado nos elementos dominados.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "area_target",
        percentual = 0.6,
        areaPercentual = 0.4,
        raio = 3,
        magicEffect = CONST_ME_ENERGYAREA,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {23, 24, 25, 26},
    efeitosSecundarios = {
        [23] = function(p, t, d) -- Fogo: queimadura
            if getNivelEfetivo(p, 23) >= 10 then
                local cond = Condition(CONDITION_FIRE, CONDITIONID_COMBAT, 4000)
                cond:setParameter(CONDITION_PARAM_PERIODICDAMAGE, 15)
                cond:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
                t:addCondition(cond)
            end
        end,
        [24] = function(p, t, d) -- Gelo: lentidão
            if getNivelEfetivo(p, 24) >= 10 then
                local cond = Condition(CONDITION_PARALYZE, CONDITIONID_COMBAT, 2500)
                t:addCondition(cond)
            end
        end,
        [25] = function(p, t, d) -- Terra: knockdown
            if getNivelEfetivo(p, 25) >= 10 then
                empurrarAlvo(p, t)
                local cond = Condition(CONDITION_POISON, CONDITIONID_COMBAT, 3000)
                cond:setParameter(CONDITION_PARAM_PERIODICDAMAGE, 10)
                cond:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
                t:addCondition(cond)
            end
        end,
        [26] = function(p, t, d) -- Energia: raio em cadeia
            if getNivelEfetivo(p, 26) >= 10 then
                local pos = t:getPosition()
                local criaturas = getCreaturesInArea(pos, 2, 2)
                for _, c in ipairs(criaturas) do
                    if c:isMonster() and c:getId() ~= t:getId() then
                        doTargetCombatHealth(p, c, COMBAT_ENERGYDAMAGE, -math.floor(d * 0.2), -math.floor(d * 0.2), CONST_ME_ENERGYHIT)
                    end
                end
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 20,
    prioridade = 9,
    categoria = "sinergia",
    condicaoFocoMin = 75,
    posturaMod = {
        [1] = { chanceMult = 1.3 },
        [2] = { chanceMult = 1.0 },
        [3] = { chanceMult = 0.8 }
    }
}

-- ============================================================
-- ÁRVORE IV (nível 20): Passiva de Maestria
-- ============================================================
HABILIDADES[2004] = {
    nome = "Avatar Elemental",
    tipo = "passiva",
    dominio = {20},
    nivelMin = 20,
    descricaoEfeito = "Síntese Superior: ao causar dano elemental, 15% de chance de causar uma onda do elemento oposto. Ensina Tempestade Elemental a Espectro.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        player:setCombatModifier("elemental_avatar", 1)
        if not jogadorConheceHabilidade(player, 21003) then
            aprenderHabilidade(player, 21003)  -- Ensinar ao irmão Espectro (21)
        end
    end
}

-- ============================================================
-- PASSIVAS DE ATRIBUTO (5 restantes)
-- ============================================================
HABILIDADES[2005] = {
    nome = "Resistência Arcana",
    tipo = "passiva",
    dominio = {20},
    nivelMin = 3,
    descricaoEfeito = "Aumenta a resistência mágica em 0.5% por nível de Elementos.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 20)
        player:setCombatModifier("magic_resist", nivel * 0.5)
    end
}

HABILIDADES[2006] = {
    nome = "Potência Arcanista",
    tipo = "passiva",
    dominio = {20},
    nivelMin = 6,
    descricaoEfeito = "Aumenta o dano mágico geral em 0.5% por nível de Elementos.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 20)
        player:setCombatModifier("magic_damage", nivel * 0.5)
    end
}

HABILIDADES[2007] = {
    nome = "Mente Expandida",
    tipo = "passiva",
    dominio = {20},
    nivelMin = 8,
    descricaoEfeito = "Aumenta a mana máxima em 2% por nível de Elementos.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player) end  -- gerido por recalcularVidaMana
}

HABILIDADES[2008] = {
    nome = "Ligeireza Arcana",
    tipo = "passiva",
    dominio = {20},
    nivelMin = 5,
    descricaoEfeito = "Aumenta a velocidade de movimento em 1% por nível de Elementos.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player) end  -- gerido por recalcularVelocidade
}

HABILIDADES[2009] = {
    nome = "Fúria Elemental",
    tipo = "passiva",
    dominio = {20},
    nivelMin = 12,
    descricaoEfeito = "Aumenta a chance de acerto crítico com magias em 0.3% por nível de Elementos.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 20)
        player:setCombatModifier("magic_crit_chance", nivel * 0.3)
    end
}

-- ============================================================
-- GATILHOS DE COMBATE (8)
-- ============================================================
HABILIDADES[2010] = {
    nome = "Explosão Elemental",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 6,
    descricaoEfeito = "Explosão no alvo que causa dano do seu elemento dominante.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "area_target",
        percentual = 0.5,
        areaPercentual = 0.3,
        raio = 2,
        magicEffect = CONST_ME_ENERGYAREA
    },
    gatilho = "onAttack",
    cooldown = 14,
    prioridade = 7,
    categoria = "aoe",
    condicaoFocoMin = 40
}

HABILIDADES[2011] = {
    nome = "Cone Elemental",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 8,
    descricaoEfeito = "Sopro elemental em cone que causa dano e efeito do elemento.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "area_ground",
        centro = "jogador",
        raio = 2,
        percentual = 0.4,
        magicEffect = CONST_ME_FIREAREA
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 7,
    categoria = "aoe",
    condicao = "cercado"
}

HABILIDADES[2012] = {
    nome = "Míssil Mágico",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 5,
    descricaoEfeito = "Dispara um projétil arcano que causa dano extra.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "dano_extra",
        percentual = 0.3,
        magicEffect = CONST_ME_ENERGYHIT
    },
    gatilho = "onAttack",
    cooldown = 8,
    prioridade = 6,
    categoria = "single"
}

HABILIDADES[2013] = {
    nome = "Erupção Elemental",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 10,
    descricaoEfeito = "Cria uma erupção no chão que causa dano e knockback.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "area_ground",
        centro = "alvo",
        raio = 2,
        percentual = 0.5,
        magicEffect = CONST_ME_GROUNDSHAKER,
        knockback = true
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 8,
    categoria = "aoe",
    condicaoFocoMin = 60
}

HABILIDADES[2014] = {
    nome = "Rajada de Fragmentos",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 12,
    descricaoEfeito = "Dispara três projéteis elementais em sequência.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
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

HABILIDADES[2015] = {
    nome = "Barreira Elemental",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 9,
    descricaoEfeito = "Reduz o dano recebido por 2s e reflete o elemento.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
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

HABILIDADES[2016] = {
    nome = "Contra-Ataque Elemental",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 14,
    descricaoEfeito = "Ao bloquear, contra-ataca todos os inimigos ao redor com dano elemental.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "defesa_contra_ataque",
        percentual = 0.4,
        magicEffect = CONST_ME_ENERGYAREA
    },
    gatilho = "onBlock",
    cooldown = 16,
    prioridade = 7,
    categoria = "defense",
    condicao = "cercado"
}

HABILIDADES[2017] = {
    nome = "Nova Elemental",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 16,
    descricaoEfeito = "Explosão massiva ao redor do jogador com efeitos de todos os elementos dominados.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "area_ground",
        centro = "jogador",
        raio = 3,
        percentual = 0.6,
        magicEffect = CONST_ME_FIREAREA
    },
    gatilho = "onAttack",
    cooldown = 22,
    prioridade = 9,
    categoria = "aoe",
    condicao = "cercado",
    condicaoFocoMin = 85
}

-- ============================================================
-- GATILHOS DE CONDIÇÃO/DEFESA (5)
-- ============================================================
HABILIDADES[2020] = {
    nome = "Chamas Ardentes",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 7,
    descricaoEfeito = "Aplica queimadura no alvo.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_FIRE,
        duration = 3000,
        periodicDamage = 12,
        comDano = true,
        percentual = 0.35,
        magicEffect = CONST_ME_FIREATTACK
    },
    gatilho = "onAttack",
    cooldown = 12,
    prioridade = 6,
    categoria = "debuff",
    condicaoFocoMin = 25
}

HABILIDADES[2021] = {
    nome = "Gelo Paralisante",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 9,
    descricaoEfeito = "Aplica lentidão/paralisia no alvo.",
    cor = COR.ELEM_GELO,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_PARALYZE,
        duration = 2000,
        comDano = true,
        percentual = 0.3,
        magicEffect = CONST_ME_ICEAREA
    },
    gatilho = "onAttack",
    cooldown = 14,
    prioridade = 6,
    categoria = "debuff",
    condicaoFocoMin = 25
}

HABILIDADES[2022] = {
    nome = "Veneno Corrosivo",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 11,
    descricaoEfeito = "Aplica veneno no alvo.",
    cor = COR.ELEM_VENENO,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_POISON,
        duration = 4000,
        periodicDamage = 15,
        comDano = true,
        percentual = 0.4,
        magicEffect = CONST_ME_MAGIC_GREEN
    },
    gatilho = "onAttack",
    cooldown = 14,
    prioridade = 6,
    categoria = "debuff",
    condicaoFocoMin = 30
}

HABILIDADES[2023] = {
    nome = "Choque Elétrico",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 13,
    descricaoEfeito = "Aplica paralisia elétrica no alvo.",
    cor = COR.ELEM_RAIO,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_PARALYZE,
        duration = 1500,
        comDano = true,
        percentual = 0.35,
        magicEffect = CONST_ME_ENERGYHIT
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 7,
    categoria = "debuff",
    condicaoFocoMin = 40
}

HABILIDADES[2024] = {
    nome = "Roubo de Essência",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 15,
    descricaoEfeito = "Rouba mana do alvo ao causar dano.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "mana_leech",
        leechPercent = 12,
        durationSec = 4
    },
    gatilho = "onAttack",
    cooldown = 20,
    prioridade = 5,
    categoria = "buff",
    condicaoFocoMin = 30
}

-- ============================================================
-- GATILHOS DE SINERGIA (8)
-- ============================================================
HABILIDADES[2030] = {
    nome = "Fúria do Fogo",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 10,
    descricaoEfeito = "Potencializa o fogo com dano extra e queimadura. Requer Fogo.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "condicao",
        conditionType = CONDITION_FIRE,
        duration = 3500,
        periodicDamage = 18,
        comDano = true,
        percentual = 0.5,
        magicEffect = CONST_ME_FIREAREA,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {23},
    efeitosSecundarios = {
        [23] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 23)
            if nivel >= 10 then
                local extra = math.floor(d * nivel * 0.02)
                doTargetCombatHealth(p, t, COMBAT_FIREDAMAGE, -extra, -extra, CONST_ME_FIREAREA)
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 14,
    prioridade = 7,
    categoria = "sinergia",
    condicaoFocoMin = 30
}

HABILIDADES[2031] = {
    nome = "Muralha de Gelo",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 12,
    descricaoEfeito = "Cria uma barreira de gelo que reduz dano e causa lentidão. Requer Água e Gelo.",
    cor = COR.ELEM_GELO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "defesa_barreira",
        factor = 0.4,
        durationMs = 3000,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {24},
    efeitosSecundarios = {
        [24] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 24)
            if nivel >= 10 then
                local criaturas = getCreaturesInArea(p:getPosition(), 2, 2)
                for _, c in ipairs(criaturas) do
                    if c:isMonster() then
                        local cond = Condition(CONDITION_PARALYZE, CONDITIONID_COMBAT, 2000)
                        c:addCondition(cond)
                    end
                end
            end
        end
    },
    gatilho = "onBlock",
    cooldown = 18,
    prioridade = 7,
    categoria = "sinergia"
}

HABILIDADES[2032] = {
    nome = "Erupção Tóxica",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 14,
    descricaoEfeito = "Explosão venenosa que causa dano e envenenamento. Requer Terra e Veneno.",
    cor = COR.ELEM_VENENO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "area_ground",
        centro = "alvo",
        raio = 2,
        percentual = 0.5,
        magicEffect = CONST_ME_MAGIC_GREEN,
        condicao = CONDITION_POISON,
        condDuration = 4000,
        periodicDamage = 12,
        nivelMinSecundario = 12
    },
    sinergiaDominios = {25},
    efeitosSecundarios = {
        [25] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 25)
            if nivel >= 12 then
                local criaturas = getCreaturesInArea(t:getPosition(), 2, 2)
                for _, c in ipairs(criaturas) do
                    if c:isMonster() and c:getId() ~= t:getId() then
                        local cond = Condition(CONDITION_POISON, CONDITIONID_COMBAT, 3000)
                        cond:setParameter(CONDITION_PARAM_PERIODICDAMAGE, 8)
                        cond:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
                        c:addCondition(cond)
                    end
                end
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 8,
    categoria = "sinergia",
    condicaoFocoMin = 60
}

HABILIDADES[2033] = {
    nome = "Tempestade de Raios",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 16,
    descricaoEfeito = "Cadeia de raios que saltam entre inimigos. Requer Energia.",
    cor = COR.ELEM_RAIO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "corrente",
        percentual = 0.5,
        raio = 3,
        magicEffect = CONST_ME_ENERGYHIT,
        nivelMinSecundario = 15
    },
    sinergiaDominios = {26},
    efeitosSecundarios = {
        [26] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 26)
            if nivel >= 15 then
                if math.random(100) <= 30 then
                    local extra = math.floor(d * 0.5)
                    doTargetCombatHealth(p, t, COMBAT_ENERGYDAMAGE, -extra, -extra, CONST_ME_ENERGYHIT)
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

HABILIDADES[2034] = {
    nome = "Combustão Arcana",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 13,
    descricaoEfeito = "Combina fogo e energia para causar dano massivo e atordoamento. Requer Fogo e Energia.",
    cor = COR.ELEM_RAIO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "area_target",
        percentual = 0.6,
        areaPercentual = 0.4,
        raio = 2,
        magicEffect = CONST_ME_FIREAREA,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {23, 26},
    efeitosSecundarios = {
        [23] = function(p, t, d)
            if getNivelEfetivo(p, 23) >= 10 then
                local cond = Condition(CONDITION_FIRE, CONDITIONID_COMBAT, 3000)
                cond:setParameter(CONDITION_PARAM_PERIODICDAMAGE, 15)
                cond:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
                t:addCondition(cond)
            end
        end,
        [26] = function(p, t, d)
            if getNivelEfetivo(p, 26) >= 10 then
                local cond = Condition(CONDITION_DAZZLED, CONDITIONID_COMBAT, 2000)
                t:addCondition(cond)
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 20,
    prioridade = 8,
    categoria = "sinergia",
    condicaoFocoMin = 60
}

HABILIDADES[2035] = {
    nome = "Campo de Força Elemental",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 17,
    descricaoEfeito = "Cria um campo de força que reduz dano e reflete dano elemental. Requer Escudo.",
    cor = COR.DOM_ESCUDO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "defesa_barreira",
        factor = 0.3,
        durationMs = 4000,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {15},
    efeitosSecundarios = {
        [15] = function(p, t, d)
            if getNivelEfetivo(p, 15) >= 10 then
                p:setCombatModifier("elemental_reflect", 15)
                addEvent(function()
                    local pl = Player(p:getId())
                    if pl then pl:setCombatModifier("elemental_reflect", 0) end
                end, 4000)
            end
        end
    },
    gatilho = "onReceiveDamage",
    cooldown = 25,
    prioridade = 6,
    categoria = "sinergia"
}

HABILIDADES[2036] = {
    nome = "Lâmina Elemental",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 15,
    descricaoEfeito = "A arma é envolta em energia elemental, causando dano extra do elemento dominante. Requer Lâminas.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "dano_extra",
        percentual = 0.5,
        magicEffect = CONST_ME_ENERGYAREA,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {10},
    efeitosSecundarios = {
        [10] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 10)
            if nivel >= 10 then
                -- Adiciona um efeito aleatório baseado nos filhos de Elementos
                local elementos = {23, 24, 25, 26}
                local melhor = 0
                local melhorNivel = 0
                for _, elemId in ipairs(elementos) do
                    local nv = getNivelEfetivo(p, elemId)
                    if nv > melhorNivel then
                        melhorNivel = nv
                        melhor = elemId
                    end
                end
                if melhor == 23 then
                    local cond = Condition(CONDITION_FIRE, CONDITIONID_COMBAT, 2000)
                    cond:setParameter(CONDITION_PARAM_PERIODICDAMAGE, 10)
                    cond:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
                    t:addCondition(cond)
                elseif melhor == 24 then
                    local cond = Condition(CONDITION_PARALYZE, CONDITIONID_COMBAT, 1500)
                    t:addCondition(cond)
                elseif melhor == 25 then
                    local cond = Condition(CONDITION_POISON, CONDITIONID_COMBAT, 3000)
                    cond:setParameter(CONDITION_PARAM_PERIODICDAMAGE, 8)
                    cond:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
                    t:addCondition(cond)
                elseif melhor == 26 then
                    if math.random(100) <= 40 then
                        local extra = math.floor(d * 0.3)
                        doTargetCombatHealth(p, t, COMBAT_ENERGYDAMAGE, -extra, -extra, CONST_ME_ENERGYHIT)
                    end
                end
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 8,
    categoria = "sinergia",
    condicaoFocoMin = 50
}

HABILIDADES[2037] = {
    nome = "Aura dos Elementos",
    tipo = "gatilho",
    dominio = {20},
    nivelMin = 18,
    descricaoEfeito = "Emite uma aura que causa dano contínuo do seu elemento mais forte por 5s. Requer qualquer elemento.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "area_ground",
        centro = "jogador",
        raio = 2,
        percentual = 0.3,
        magicEffect = CONST_ME_FIREAREA,
        nivelMinSecundario = 15
    },
    sinergiaDominios = {23, 24, 25, 26},
    efeitosSecundarios = {
        [23] = function(p, t, d) end,
        [24] = function(p, t, d) end,
        [25] = function(p, t, d) end,
        [26] = function(p, t, d) end
    },
    gatilho = "onAttack",
    cooldown = 24,
    prioridade = 8,
    categoria = "sinergia",
    condicaoFocoMin = 80
}

-- ============================================================
-- TRANSFORMAÇÕES (5)
-- ============================================================
HABILIDADES[2040] = {
    nome = "Lampejo Elemental",
    tipo = "transformacao",
    dominio = {20},
    nivelMin = 8,
    descricaoEfeito = "Lampejo: o dano elemental aumenta 15% e você se move mais rápido.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local atual = player:getCombatModifier("elemental_damage") or 0
        player:setCombatModifier("elemental_damage", atual + 15)
    end,
    desfazer = function(player)
        local atual = player:getCombatModifier("elemental_damage") or 15
        player:setCombatModifier("elemental_damage", atual - 15)
    end
}

HABILIDADES[2041] = {
    nome = "Vínculo Primordial",
    tipo = "transformacao",
    dominio = {20},
    nivelMin = 12,
    descricaoEfeito = "Vínculo: o dano elemental aumenta 25% e elementos orbitam ao seu redor.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local atual = player:getCombatModifier("elemental_damage") or 0
        player:setCombatModifier("elemental_damage", atual + 25)
    end,
    desfazer = function(player)
        local atual = player:getCombatModifier("elemental_damage") or 25
        player:setCombatModifier("elemental_damage", atual - 25)
    end
}

HABILIDADES[2042] = {
    nome = "Maestria Elemental",
    tipo = "transformacao",
    dominio = {20},
    nivelMin = 16,
    descricaoEfeito = "Maestria: os efeitos secundários dos elementos duram 50% mais e o Vínculo é permanente.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        player:setCombatModifier("elemental_duration", 50)
    end,
    desfazer = function(player)
        player:setCombatModifier("elemental_duration", 0)
    end
}

HABILIDADES[2043] = {
    nome = "Apocalipse Elemental",
    tipo = "transformacao",
    dominio = {20},
    nivelMin = 20,
    descricaoEfeito = "Transformação suprema: invoca uma devastação elemental massiva por 8s, causando dano de todos os elementos dominados.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local pid = player:getId()
        local function tick(count)
            local pl = Player(pid)
            if not pl or count >= 8 then return end
            local pos = pl:getPosition()
            local criaturas = getCreaturesInArea(pos, 4, 4)
            for _, c in ipairs(criaturas) do
                if c:isMonster() then
                    local dmg = math.floor((pl:getMagicLevel() * 3) * (1 + count * 0.2))
                    -- usa o elemento com maior afinidade
                    local elementos = {23, 24, 25, 26}
                    local melhor = 23
                    local melhorNivel = 0
                    for _, elemId in ipairs(elementos) do
                        local nv = getNivelEfetivo(pl, elemId)
                        if nv > melhorNivel then
                            melhorNivel = nv
                            melhor = elemId
                        end
                    end
                    local combatType = COMBAT_FIREDAMAGE
                    if melhor == 24 then combatType = COMBAT_ICEDAMAGE
                    elseif melhor == 25 then combatType = COMBAT_EARTHDAMAGE
                    elseif melhor == 26 then combatType = COMBAT_ENERGYDAMAGE
                    end
                    doTargetCombatHealth(pl, c, combatType, -dmg, -dmg, CONST_ME_FIREAREA)
                end
            end
            pos:sendMagicEffect(CONST_ME_FIREAREA)
            addEvent(tick, 1000, count + 1)
        end
        tick(0)
    end,
    desfazer = function(player) end
}

HABILIDADES[2044] = {
    nome = "Recarga Elemental",
    tipo = "transformacao",
    dominio = {20},
    nivelMin = 10,
    descricaoEfeito = "Ao ativar, restaura 20% da mana máxima instantaneamente.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local mana = math.floor(player:getMaxMana() * 0.2)
        player:addMana(mana)
        player:getPosition():sendMagicEffect(CONST_ME_MAGIC_BLUE)
    end,
    desfazer = function(player) end
}

print("DEBUG: habilidades_elementos.lua carregado.")