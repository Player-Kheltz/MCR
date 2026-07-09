--[[
    Projeto MCR ? SPA ? Habilidades de Runologia (22)
    Perfil: Secundário (34 habilidades + Traço Inerente)
    Arquitetura modular v4.6
--]]

-- ============================================================
-- TRAÇO INERENTE: Tinta Viva
-- ============================================================
-- Nível 5: Criar runas (usar wands/rods/runas) tem 10% de chance de não consumir carga da runa/varinha.
-- Nível 10: A chance sobe para 20% e também reduz o cooldown de habilidades de runologia em 0.5s.
-- Nível 15: Ao usar uma runa, 15% de chance de a runa ecoar, duplicando seu efeito (dano ou cura) com 50% de força.
-- Nível 20: Síntese Superior ? "Mestre Rúnico": todas as runas ganham um efeito adicional baseado nos filhos (Wands: +dano, Rods: +cura/durabilidade, Runas: +raio).

-- ============================================================
-- ÁRVORE I (nível 5): Passiva de Identidade
-- ============================================================
HABILIDADES[2201] = {
    nome = "Escrita Arcana",
    tipo = "passiva",
    dominio = {22},
    nivelMin = 5,
    descricaoEfeito = "Aumenta a eficácia de runas, wands e rods em 5%.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        player:setCombatModifier("runology_power", 5)
    end
}

-- ============================================================
-- ÁRVORE II (nível 10): Passiva de Expansão ? Sinergia com Filhos
-- ============================================================
HABILIDADES[2202] = {
    nome = "Sinergia Rúnica",
    tipo = "passiva",
    dominio = {22},
    nivelMin = 10,
    descricaoEfeito = "Concede bónus baseados nos domínios filhos.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        -- Wands (210): +velocidade de ataque
        if getNivelEfetivo(player, 210) >= 10 then
            player:setCombatModifier("wand_speed", 0.08)
        end
        -- Rods (211): +regeneração de mana
        if getNivelEfetivo(player, 211) >= 10 then
            player:setManaRegenModifier(1.5)
        end
        -- Runas (212): +chance de eco
        if getNivelEfetivo(player, 212) >= 10 then
            player:setCombatModifier("rune_echo_chance", 15)
        end
    end
}

-- ============================================================
-- ÁRVORE III (nível 15): Gatilho de Assinatura ? Detonação Rúnica
-- ============================================================
HABILIDADES[2203] = {
    nome = "Detonação Rúnica",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 15,
    descricaoEfeito = "Invoca uma explosão rúnica que combina os efeitos dos filhos dominados.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "area_target",
        percentual = 0.7,
        areaPercentual = 0.5,
        raio = 3,
        magicEffect = CONST_ME_ENERGYAREA,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {210, 211, 212},
    efeitosSecundarios = {
        [210] = function(p, t, d) -- Wands: rajada adicional
            if getNivelEfetivo(p, 210) >= 10 then
                local alvos = {}
                local criaturas = getCreaturesInArea(t:getPosition(), 3, 3)
                for _, c in ipairs(criaturas) do
                    if c:isMonster() and c:getId() ~= t:getId() then table.insert(alvos, c) end
                end
                for i = 1, math.min(3, #alvos) do
                    doTargetCombatHealth(p, alvos[i], COMBAT_ENERGYDAMAGE, -math.floor(d * 0.15), -math.floor(d * 0.15), CONST_ME_ENERGYHIT)
                end
            end
        end,
        [211] = function(p, t, d) -- Rods: cura aliados próximos
            if getNivelEfetivo(p, 211) >= 10 then
                local party = p:getParty()
                if party then
                    local members = party:getMembers()
                    for _, member in ipairs(members) do
                        if member:getPosition():getDistance(p:getPosition()) <= 3 then
                            member:addHealth(math.floor(p:getMaxHealth() * 0.05))
                        end
                    end
                end
            end
        end,
        [212] = function(p, t, d) -- Runas: eco (dano extra no alvo)
            if getNivelEfetivo(p, 212) >= 10 then
                local ecoDmg = math.floor(d * 0.25)
                doTargetCombatHealth(p, t, COMBAT_ENERGYDAMAGE, -ecoDmg, -ecoDmg, CONST_ME_ENERGYHIT)
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
-- ÁRVORE IV (nível 20): Passiva de Maestria ? Mestre Rúnico
-- ============================================================
HABILIDADES[2204] = {
    nome = "Mestre Rúnico",
    tipo = "passiva",
    dominio = {22},
    nivelMin = 20,
    descricaoEfeito = "Síntese Superior: todas as runas ganham efeito adicional (dano em área, cura ou eco). Ensina Detonação Rúnica a todos os filhos.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        player:setCombatModifier("runology_mastery", 1)
        local filhos = {210, 211, 212}
        for _, filhoId in ipairs(filhos) do
            local habIrma = filhoId * 100 + 3  -- convenção: [domId]03
            if HABILIDADES[habIrma] and not jogadorConheceHabilidade(player, habIrma) then
                aprenderHabilidade(player, habIrma)
            end
        end
    end
}

-- ============================================================
-- PASSIVAS DE ATRIBUTO (5 restantes)
-- ============================================================
HABILIDADES[2205] = {
    nome = "Tinteiro Profundo",
    tipo = "passiva",
    dominio = {22},
    nivelMin = 3,
    descricaoEfeito = "Aumenta a mana máxima em 2% por nível de Runologia.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player) end  -- gerido por recalcularVidaMana
}

HABILIDADES[2206] = {
    nome = "Mãos Rápidas",
    tipo = "passiva",
    dominio = {22},
    nivelMin = 5,
    descricaoEfeito = "Aumenta a velocidade de ataque com wands/rods/runas em 0.5% por nível.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 22)
        player:setAttackSpeedModifier(1.0 - nivel * 0.005)
    end
}

HABILIDADES[2207] = {
    nome = "Precisão Rúnica",
    tipo = "passiva",
    dominio = {22},
    nivelMin = 8,
    descricaoEfeito = "Aumenta o dano crítico com runas em 1% por nível de Runologia.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 22)
        player:setCombatModifier("rune_crit_power", nivel)
    end
}

HABILIDADES[2208] = {
    nome = "Resistência Arcana",
    tipo = "passiva",
    dominio = {22},
    nivelMin = 6,
    descricaoEfeito = "Aumenta a resistência mágica em 0.3% por nível de Runologia.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 22)
        player:setCombatModifier("rune_magic_resist", nivel * 0.3)
    end
}

HABILIDADES[2209] = {
    nome = "Economia de Tinta",
    tipo = "passiva",
    dominio = {22},
    nivelMin = 12,
    descricaoEfeito = "Reduz o custo de mana em 0.5% por nível de Runologia.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 22)
        player:setCombatModifier("rune_mana_cost_reduction", nivel * 0.5)
    end
}

-- ============================================================
-- GATILHOS DE COMBATE (8)
-- ============================================================
HABILIDADES[2210] = {
    nome = "Explosão Rúnica",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 6,
    descricaoEfeito = "Explosão mágica centrada no alvo.",
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

HABILIDADES[2211] = {
    nome = "Rajada de Runas",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 8,
    descricaoEfeito = "Dispara três projéteis rúnicos em sequência.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "rajada",
        percentual = 0.35,
        numProjeteis = 3,
        intervaloMs = 250
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 7,
    categoria = "single",
    condicaoFocoMin = 50
}

HABILIDADES[2212] = {
    nome = "Runa Ricochete",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 10,
    descricaoEfeito = "A runa salta entre inimigos próximos.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "ricochete",
        percentual = 0.4,
        raio = 2,
        saltos = 2,
        magicEffect = CONST_ME_ENERGYHIT
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 7,
    categoria = "aoe",
    condicaoFocoMin = 50
}

HABILIDADES[2213] = {
    nome = "Nova Rúnica",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 12,
    descricaoEfeito = "Explosão ao redor do jogador com runas.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "area_ground",
        centro = "jogador",
        raio = 2,
        percentual = 0.5,
        magicEffect = CONST_ME_ENERGYAREA
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 7,
    categoria = "aoe",
    condicao = "cercado",
    condicaoFocoMin = 60
}

HABILIDADES[2214] = {
    nome = "Aceleração Rúnica",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 7,
    descricaoEfeito = "Acelera a velocidade de ataque por 1.5s.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
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

HABILIDADES[2215] = {
    nome = "Tempestade de Runas",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 14,
    descricaoEfeito = "Dispara quatro projéteis rúnicos em rápida sucessão.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
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
    condicaoFocoMin = 70
}

HABILIDADES[2216] = {
    nome = "Barragem Rúnica",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 16,
    descricaoEfeito = "Dispara uma barragem de 5 projéteis que causam dano em linha.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "rajada",
        percentual = 0.25,
        numProjeteis = 5,
        intervaloMs = 180
    },
    gatilho = "onAttack",
    cooldown = 22,
    prioridade = 8,
    categoria = "single",
    condicaoFocoMin = 80
}

HABILIDADES[2217] = {
    nome = "Runa Aniquiladora",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 18,
    descricaoEfeito = "Golpe final massivo contra alvos com vida baixa.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "finisher",
        percentual = 1.5,
        magicEffect = CONST_ME_MORTAREA,
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
-- GATILHOS DE CONDIÇÃO/DEFESA (5)
-- ============================================================
HABILIDADES[2220] = {
    nome = "Runa Paralisante",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 9,
    descricaoEfeito = "Aplica paralisia no alvo.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
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
    condicaoFocoMin = 30
}

HABILIDADES[2221] = {
    nome = "Runa Atordoante",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 11,
    descricaoEfeito = "Atordoa o alvo com uma explosão rúnica.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_DAZZLED,
        duration = 2000,
        comDano = true,
        percentual = 0.35,
        magicEffect = CONST_ME_STUN
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 6,
    categoria = "debuff",
    condicaoFocoMin = 40
}

HABILIDADES[2222] = {
    nome = "Barreira Rúnica",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 8,
    descricaoEfeito = "Reduz o dano recebido por 2s com um escudo rúnico.",
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

HABILIDADES[2223] = {
    nome = "Contra-ataque Rúnico",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 13,
    descricaoEfeito = "Ao bloquear, contra-ataca todos ao redor com runas.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "defesa_contra_ataque",
        percentual = 0.4,
        magicEffect = CONST_ME_ENERGYAREA
    },
    gatilho = "onBlock",
    cooldown = 16,
    prioridade = 6,
    categoria = "defense",
    condicao = "inimigosProximos"
}

HABILIDADES[2224] = {
    nome = "Dreno Rúnico",
    tipo = "gatilho",
    dominio = {22},
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
HABILIDADES[2230] = {
    nome = "Sinergia com Wands",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 10,
    descricaoEfeito = "Potencializa o dano de wands e adiciona rajada extra. Requer Wands.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "dano_extra",
        percentual = 0.4,
        magicEffect = CONST_ME_ENERGYHIT,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {210},
    efeitosSecundarios = {
        [210] = function(p, t, d)
            if getNivelEfetivo(p, 210) >= 10 then
                -- dispara um projétil extra
                doTargetCombatHealth(p, t, COMBAT_ENERGYDAMAGE, -math.floor(d * 0.2), -math.floor(d * 0.2), CONST_ME_ENERGYHIT)
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 12,
    prioridade = 7,
    categoria = "sinergia",
    condicaoFocoMin = 30
}

HABILIDADES[2231] = {
    nome = "Sinergia com Rods",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 12,
    descricaoEfeito = "Causa dano extra e restaura vida com base no dano. Requer Rods.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "dano_extra",
        percentual = 0.4,
        magicEffect = CONST_ME_MAGIC_BLUE,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {211},
    efeitosSecundarios = {
        [211] = function(p, t, d)
            if getNivelEfetivo(p, 211) >= 10 then
                local heal = math.floor(d * 0.1)
                p:addHealth(heal)
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 14,
    prioridade = 7,
    categoria = "sinergia",
    condicaoFocoMin = 30
}

HABILIDADES[2232] = {
    nome = "Sinergia com Runas",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 14,
    descricaoEfeito = "A próxima runa ecoará, causando dano em área adicional. Requer Runas.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "area_target",
        percentual = 0.5,
        areaPercentual = 0.3,
        raio = 2,
        magicEffect = CONST_ME_ENERGYAREA,
        nivelMinSecundario = 12
    },
    sinergiaDominios = {212},
    efeitosSecundarios = {
        [212] = function(p, t, d)
            if getNivelEfetivo(p, 212) >= 12 then
                -- eco adicional no alvo
                local ecoDmg = math.floor(d * 0.2)
                doTargetCombatHealth(p, t, COMBAT_ENERGYDAMAGE, -ecoDmg, -ecoDmg, CONST_ME_ENERGYHIT)
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 8,
    categoria = "sinergia",
    condicaoFocoMin = 50
}

HABILIDADES[2233] = {
    nome = "Runa Flamejante",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 13,
    descricaoEfeito = "A runa incendeia o alvo. Requer Fogo.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "condicao",
        conditionType = CONDITION_FIRE,
        duration = 3000,
        periodicDamage = 12,
        comDano = true,
        percentual = 0.4,
        magicEffect = CONST_ME_FIREAREA,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {23},
    efeitosSecundarios = {
        [23] = function(p, t, d)
            if getNivelEfetivo(p, 23) >= 10 then
                local extra = math.floor(d * 0.1)
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

HABILIDADES[2234] = {
    nome = "Runa Gélida",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 15,
    descricaoEfeito = "A runa congela o alvo, reduzindo sua velocidade. Requer Gelo.",
    cor = COR.ELEM_GELO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "condicao",
        conditionType = CONDITION_PARALYZE,
        duration = 2500,
        comDano = true,
        percentual = 0.35,
        magicEffect = CONST_ME_ICEAREA,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {24},
    efeitosSecundarios = {
        [24] = function(p, t, d)
            if getNivelEfetivo(p, 24) >= 10 then
                local cond = Condition(CONDITION_PARALYZE, CONDITIONID_COMBAT, 2500)
                t:addCondition(cond)
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 7,
    categoria = "sinergia",
    condicaoFocoMin = 40
}

HABILIDADES[2235] = {
    nome = "Runa Energizada",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 17,
    descricaoEfeito = "A runa descarrega energia, causando paralisia. Requer Energia.",
    cor = COR.ELEM_RAIO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "condicao",
        conditionType = CONDITION_PARALYZE,
        duration = 2000,
        comDano = true,
        percentual = 0.45,
        magicEffect = CONST_ME_ENERGYHIT,
        nivelMinSecundario = 15
    },
    sinergiaDominios = {26},
    efeitosSecundarios = {
        [26] = function(p, t, d)
            if getNivelEfetivo(p, 26) >= 15 then
                if math.random(100) <= 35 then
                    local extra = math.floor(d * 0.4)
                    doTargetCombatHealth(p, t, COMBAT_ENERGYDAMAGE, -extra, -extra, CONST_ME_ENERGYHIT)
                end
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 20,
    prioridade = 8,
    categoria = "sinergia",
    condicaoFocoMin = 70
}

HABILIDADES[2236] = {
    nome = "Runa do Vazio",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 16,
    descricaoEfeito = "A runa suga a vitalidade do alvo, roubando vida e mana. Requer Espectro.",
    cor = COR.ELEM_SOMBRA,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "life_leech",
        leechPercent = 15,
        durationSec = 4,
        nivelMinSecundario = 12
    },
    sinergiaDominios = {21},
    efeitosSecundarios = {
        [21] = function(p, t, d)
            if getNivelEfetivo(p, 21) >= 12 then
                p:addMana(math.floor(d * 0.05))
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 7,
    categoria = "sinergia",
    condicaoFocoMin = 50
}

HABILIDADES[2237] = {
    nome = "Escudo e Varinha",
    tipo = "gatilho",
    dominio = {22},
    nivelMin = 14,
    descricaoEfeito = "Aumenta a defesa e contra-ataca com energia. Requer Escudo.",
    cor = COR.DOM_ESCUDO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "defesa_contra_ataque",
        percentual = 0.4,
        magicEffect = CONST_ME_ENERGYHIT,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {15},
    efeitosSecundarios = {
        [15] = function(p, t, d)
            if getNivelEfetivo(p, 15) >= 10 then
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
-- TRANSFORMAÇÕES (5)
-- ============================================================
HABILIDADES[2240] = {
    nome = "Lampejo Rúnico",
    tipo = "transformacao",
    dominio = {22},
    nivelMin = 8,
    descricaoEfeito = "Lampejo: a velocidade de ataque aumenta 15% e o custo de mana reduz 10%.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        player:setAttackSpeedModifier(0.85)
        player:setCombatModifier("rune_mana_cost_reduction", (player:getCombatModifier("rune_mana_cost_reduction") or 0) + 10)
    end,
    desfazer = function(player)
        aplicarPostura(player, player:getFightMode())
        player:setCombatModifier("rune_mana_cost_reduction", (player:getCombatModifier("rune_mana_cost_reduction") or 10) - 10)
    end
}

HABILIDADES[2241] = {
    nome = "Vínculo Rúnico",
    tipo = "transformacao",
    dominio = {22},
    nivelMin = 12,
    descricaoEfeito = "Vínculo: o dano com runas aumenta 20% e runas orbitam o conjurador.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local atual = player:getCombatModifier("runology_power") or 0
        player:setCombatModifier("runology_power", atual + 20)
    end,
    desfazer = function(player)
        local atual = player:getCombatModifier("runology_power") or 20
        player:setCombatModifier("runology_power", atual - 20)
    end
}

HABILIDADES[2242] = {
    nome = "Maestria Rúnica",
    tipo = "transformacao",
    dominio = {22},
    nivelMin = 16,
    descricaoEfeito = "Maestria: as runas têm 20% de chance de não consumir carga e o Vínculo é permanente.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        player:setCombatModifier("rune_no_consume_chance", 20)
    end,
    desfazer = function(player)
        player:setCombatModifier("rune_no_consume_chance", 0)
    end
}

HABILIDADES[2243] = {
    nome = "Apocalipse Rúnico",
    tipo = "transformacao",
    dominio = {22},
    nivelMin = 20,
    descricaoEfeito = "Transformação suprema: invoca uma chuva de runas explosivas por 8s, causando dano massivo em área.",
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
                    doTargetCombatHealth(pl, c, COMBAT_ENERGYDAMAGE, -dmg, -dmg, CONST_ME_ENERGYAREA)
                end
            end
            pos:sendMagicEffect(CONST_ME_BIGCLOUDS)
            addEvent(tick, 1000, count + 1)
        end
        tick(0)
    end,
    desfazer = function(player) end
}

HABILIDADES[2244] = {
    nome = "Recarga Rúnica",
    tipo = "transformacao",
    dominio = {22},
    nivelMin = 10,
    descricaoEfeito = "Ao ativar, recupera imediatamente as cargas de todas as runas equipadas.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        -- Isto requereria uma lógica específica para recarregar runas; para já um placeholder.
        player:addMana(math.floor(player:getMaxMana() * 0.1))
        player:getPosition():sendMagicEffect(CONST_ME_MAGIC_BLUE)
    end,
    desfazer = function(player) end
}

print("DEBUG: habilidades_runologia.lua carregado.")