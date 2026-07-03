--[[
    Projeto MCR ? SPA ? Habilidades de Magia (2)
    Perfil: Primário (35 habilidades + Traço Inerente)
    Arquitetura modular v4.6
--]]

-- ============================================================
-- TRAÇO INERENTE: Centelha Arcana
-- ============================================================
-- Nível 5: Ataques mágicos têm 5% de chance de restaurar 1% da mana máxima.
-- Nível 10: A chance sobe para 10% e também reduz o cooldown global em 0.5s.
-- Nível 15: Concede um escudo arcano passivo que absorve 5% da vida máxima, recarregando fora de combate.
-- Nível 20: Síntese Superior ? "Avatar Arcano": ao lançar uma habilidade de gatilho, 15% de chance de ativar instantaneamente uma segunda habilidade de gatilho sem custo de cooldown.

-- ============================================================
-- ÁRVORE I (nível 5): Passiva de Identidade
-- ============================================================
HABILIDADES[201] = {
    nome = "Mente Arcana",
    tipo = "passiva",
    dominio = {2},
    nivelMin = 5,
    descricaoEfeito = "Aumenta o dano mágico em 1% por nível de Magia.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 2)
        player:setCombatModifier("magic_damage", nivel)
    end
}

-- ============================================================
-- ÁRVORE II (nível 10): Passiva de Expansão ? Sinergia com Filhos
-- ============================================================
HABILIDADES[202] = {
    nome = "Sinergia Arcana",
    tipo = "passiva",
    dominio = {2},
    nivelMin = 10,
    descricaoEfeito = "Concede bónus adicionais baseados nos domínios filhos.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        -- Elementos (20): +dano elemental
        if getNivelEfetivo(player, 20) >= 10 then
            player:setCombatModifier("elemental_damage", (player:getCombatModifier("elemental_damage") or 0) + 8)
        end
        -- Espectro (21): +chance de medo
        if getNivelEfetivo(player, 21) >= 10 then
            player:setCombatModifier("spectre_fear_chance", 10)
        end
        -- Runologia (22): +velocidade de ataque com runas
        if getNivelEfetivo(player, 22) >= 10 then
            player:setCombatModifier("runology_speed", 0.05)
        end
    end
}

-- ============================================================
-- ÁRVORE III (nível 15): Gatilho de Assinatura ? Erupção Arcana
-- ============================================================
HABILIDADES[203] = {
    nome = "Erupção Arcana",
    tipo = "gatilho",
    dominio = {2},
    nivelMin = 15,
    descricaoEfeito = "Explosão mágica massiva que causa dano baseado nos filhos dominados.",
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
    sinergiaDominios = {20, 21, 22},
    efeitosSecundarios = {
        [20] = function(p, t, d) -- Elementos: adiciona efeito do elemento dominante
            local elementos = {23, 24, 25, 26}
            local melhor = 23
            local melhorNivel = 0
            for _, elemId in ipairs(elementos) do
                local nv = getNivelEfetivo(p, elemId)
                if nv > melhorNivel then
                    melhorNivel = nv
                    melhor = elemId
                end
            end
            if melhorNivel >= 10 then
                if melhor == 23 then
                    local cond = Condition(CONDITION_FIRE, CONDITIONID_COMBAT, 3000)
                    cond:setParameter(CONDITION_PARAM_PERIODICDAMAGE, 15)
                    cond:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
                    t:addCondition(cond)
                elseif melhor == 24 then
                    local cond = Condition(CONDITION_PARALYZE, CONDITIONID_COMBAT, 2000)
                    t:addCondition(cond)
                elseif melhor == 25 then
                    local cond = Condition(CONDITION_POISON, CONDITIONID_COMBAT, 4000)
                    cond:setParameter(CONDITION_PARAM_PERIODICDAMAGE, 12)
                    cond:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
                    t:addCondition(cond)
                elseif melhor == 26 then
                    if math.random(100) <= 40 then
                        local extra = math.floor(d * 0.3)
                        doTargetCombatHealth(p, t, COMBAT_ENERGYDAMAGE, -extra, -extra, CONST_ME_ENERGYHIT)
                    end
                end
            end
        end,
        [21] = function(p, t, d) -- Espectro: causa medo em área
            if getNivelEfetivo(p, 21) >= 10 then
                local criaturas = getCreaturesInArea(t:getPosition(), 2, 2)
                for _, c in ipairs(criaturas) do
                    if c:isMonster() and c:getId() ~= t:getId() then
                        local cond = Condition(CONDITION_CURSED, CONDITIONID_COMBAT, 2000)
                        c:addCondition(cond)
                    end
                end
            end
        end,
        [22] = function(p, t, d) -- Runologia: dispara runas adicionais
            if getNivelEfetivo(p, 22) >= 10 then
                local criaturas = getCreaturesInArea(t:getPosition(), 3, 3)
                for _, c in ipairs(criaturas) do
                    if c:isMonster() and c:getId() ~= t:getId() then
                        doTargetCombatHealth(p, c, COMBAT_ENERGYDAMAGE, -math.floor(d * 0.15), -math.floor(d * 0.15), CONST_ME_ENERGYHIT)
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
-- ÁRVORE IV (nível 20): Passiva de Maestria ? Avatar Arcano
-- ============================================================
HABILIDADES[204] = {
    nome = "Avatar Arcano",
    tipo = "passiva",
    dominio = {2},
    nivelMin = 20,
    descricaoEfeito = "Síntese Superior: escudo arcano passivo (5% da vida máxima) e chance de ativar habilidades duplas. Ensina Erupção Arcana a todos os secundários.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        player:setCombatModifier("magic_avatar", 1)
        -- Ensina a habilidade III aos secundários
        local filhos = {20, 21, 22}
        for _, filhoId in ipairs(filhos) do
            local habIrma = filhoId * 100 + 3  -- convenção: [domId]03
            if HABILIDADES[habIrma] and not jogadorConheceHabilidade(player, habIrma) then
                aprenderHabilidade(player, habIrma)
            end
        end
    end
}

-- ============================================================
-- PASSIVAS DE ATRIBUTO (6 restantes)
-- ============================================================
HABILIDADES[205] = {
    nome = "Reservatório Arcano",
    tipo = "passiva",
    dominio = {2},
    nivelMin = 3,
    descricaoEfeito = "Aumenta a mana máxima em 2% por nível de Magia.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player) end  -- gerido por recalcularVidaMana
}

HABILIDADES[206] = {
    nome = "Ligeireza Arcana",
    tipo = "passiva",
    dominio = {2},
    nivelMin = 5,
    descricaoEfeito = "Aumenta a velocidade de movimento em 1% por nível de Magia.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player) end  -- gerido por recalcularVelocidade
}

HABILIDADES[207] = {
    nome = "Foco Arcano",
    tipo = "passiva",
    dominio = {2},
    nivelMin = 7,
    descricaoEfeito = "Reduz o cooldown global em 0.3% por nível de Magia.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 2)
        player:setCombatModifier("magic_cdr", nivel * 0.3)
    end
}

HABILIDADES[208] = {
    nome = "Potência Mística",
    tipo = "passiva",
    dominio = {2},
    nivelMin = 9,
    descricaoEfeito = "Aumenta o dano crítico mágico em 1.5% por nível de Magia.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 2)
        player:setCombatModifier("magic_crit_power", nivel * 1.5)
    end
}

HABILIDADES[209] = {
    nome = "Absorção Arcana",
    tipo = "passiva",
    dominio = {2},
    nivelMin = 11,
    descricaoEfeito = "Reduz o dano mágico recebido em 0.5% por nível de Magia.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 2)
        player:setCombatModifier("magic_absorb", nivel * 0.5)
    end
}

HABILIDADES[210] = {
    nome = "Mente Cristalina",
    tipo = "passiva",
    dominio = {2},
    nivelMin = 13,
    descricaoEfeito = "Aumenta a regeneração de mana em 1% por nível de Magia.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 2)
        player:setManaRegenModifier(1.0 + nivel * 0.01)
    end
}

-- ============================================================
-- GATILHOS DE COMBATE (4)
-- ============================================================
HABILIDADES[211] = {
    nome = "Míssil Arcano",
    tipo = "gatilho",
    dominio = {2},
    nivelMin = 10,
    descricaoEfeito = "Dispara um projétil de energia pura que causa dano extra.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "dano_extra",
        percentual = 0.4,
        magicEffect = CONST_ME_ENERGYHIT
    },
    gatilho = "onAttack",
    cooldown = 8,
    prioridade = 6,
    categoria = "single"
}

HABILIDADES[212] = {
    nome = "Nova Arcana",
    tipo = "gatilho",
    dominio = {2},
    nivelMin = 14,
    descricaoEfeito = "Explosão ao redor do jogador que causa dano em área.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "area_ground",
        centro = "jogador",
        raio = 2,
        percentual = 0.5,
        magicEffect = CONST_ME_ENERGYAREA
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 7,
    categoria = "aoe",
    condicao = "cercado",
    condicaoFocoMin = 50
}

HABILIDADES[213] = {
    nome = "Rajada Arcana",
    tipo = "gatilho",
    dominio = {2},
    nivelMin = 12,
    descricaoEfeito = "Dispara três projéteis arcanos em sequência.",
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

HABILIDADES[214] = {
    nome = "Pulso de Mana",
    tipo = "gatilho",
    dominio = {2},
    nivelMin = 8,
    descricaoEfeito = "Acelera a velocidade de ataque por 2s.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "buff_speed",
        multiplier = 0.6,
        durationMs = 2000
    },
    gatilho = "onAttack",
    cooldown = 20,
    prioridade = 5,
    categoria = "buff",
    condicaoFocoMin = 30
}

-- ============================================================
-- GATILHOS DE CONDIÇÃO/DEFESA (2)
-- ============================================================
HABILIDADES[215] = {
    nome = "Barreira Mística",
    tipo = "gatilho",
    dominio = {2},
    nivelMin = 15,
    descricaoEfeito = "Reduz o dano recebido em 60% por 3s e reflete 20% do dano ao atacante.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "defesa_barreira",
        factor = 0.4,
        durationMs = 3000
    },
    gatilho = "onReceiveDamage",
    cooldown = 25,
    prioridade = 6,
    categoria = "defense"
}

HABILIDADES[216] = {
    nome = "Contra-Carga Arcana",
    tipo = "gatilho",
    dominio = {2},
    nivelMin = 16,
    descricaoEfeito = "Ao bloquear, contra-ataca todos os inimigos ao redor com energia e recupera mana.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "defesa_contra_ataque",
        percentual = 0.4,
        magicEffect = CONST_ME_ENERGYAREA
    },
    gatilho = "onBlock",
    cooldown = 18,
    prioridade = 7,
    categoria = "defense",
    condicao = "cercado"
}

-- ============================================================
-- GATILHOS DE SINERGIA (10)
-- ============================================================
HABILIDADES[220] = {
    nome = "Fúria Elemental",
    tipo = "gatilho",
    dominio = {2},
    nivelMin = 12,
    descricaoEfeito = "Potencializa o próximo ataque com o elemento dominante. Requer Elementos.",
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
    sinergiaDominios = {20, 23, 24, 25, 26},
    efeitosSecundarios = {
        [23] = function(p, t, d)
            if getNivelEfetivo(p, 23) >= 10 then
                local cond = Condition(CONDITION_FIRE, CONDITIONID_COMBAT, 4000)
                cond:setParameter(CONDITION_PARAM_PERIODICDAMAGE, 20)
                cond:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
                t:addCondition(cond)
            end
        end,
        [24] = function(p, t, d)
            if getNivelEfetivo(p, 24) >= 10 then
                local cond = Condition(CONDITION_PARALYZE, CONDITIONID_COMBAT, 2500)
                t:addCondition(cond)
            end
        end,
        [25] = function(p, t, d)
            if getNivelEfetivo(p, 25) >= 10 then
                local cond = Condition(CONDITION_POISON, CONDITIONID_COMBAT, 4000)
                cond:setParameter(CONDITION_PARAM_PERIODICDAMAGE, 15)
                cond:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
                t:addCondition(cond)
            end
        end,
        [26] = function(p, t, d)
            if getNivelEfetivo(p, 26) >= 10 then
                if math.random(100) <= 35 then
                    local extra = math.floor(d * 0.4)
                    doTargetCombatHealth(p, t, COMBAT_ENERGYDAMAGE, -extra, -extra, CONST_ME_ENERGYHIT)
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

HABILIDADES[221] = {
    nome = "Toque do Espectro",
    tipo = "gatilho",
    dominio = {2},
    nivelMin = 14,
    descricaoEfeito = "Aplica medo e maldição no alvo. Requer Espectro.",
    cor = COR.ELEM_SOMBRA,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "condicao",
        conditionType = CONDITION_CURSED,
        duration = 4000,
        comDano = true,
        percentual = 0.45,
        magicEffect = CONST_ME_MORTAREA,
        nivelMinSecundario = 12
    },
    sinergiaDominios = {21},
    efeitosSecundarios = {
        [21] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 21)
            if nivel >= 12 then
                -- medo em área
                local criaturas = getCreaturesInArea(t:getPosition(), 2, 2)
                for _, c in ipairs(criaturas) do
                    if c:isMonster() and c:getId() ~= t:getId() then
                        local cond = Condition(CONDITION_CURSED, CONDITIONID_COMBAT, 2000)
                        c:addCondition(cond)
                    end
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

HABILIDADES[222] = {
    nome = "Runa Instável",
    tipo = "gatilho",
    dominio = {2},
    nivelMin = 13,
    descricaoEfeito = "Ativa uma runa explosiva no alvo. Requer Runologia.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "area_target",
        percentual = 0.5,
        areaPercentual = 0.3,
        raio = 2,
        magicEffect = CONST_ME_ENERGYAREA,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {22},
    efeitosSecundarios = {
        [22] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 22)
            if nivel >= 10 then
                -- runa adicional em outro inimigo aleatório
                local criaturas = getCreaturesInArea(t:getPosition(), 3, 3)
                for _, c in ipairs(criaturas) do
                    if c:isMonster() and c:getId() ~= t:getId() then
                        doTargetCombatHealth(p, c, COMBAT_ENERGYDAMAGE, -math.floor(d * 0.2), -math.floor(d * 0.2), CONST_ME_ENERGYHIT)
                        break
                    end
                end
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 7,
    categoria = "sinergia",
    condicaoFocoMin = 50
}

HABILIDADES[223] = {
    nome = "Lâmina Arcana",
    tipo = "gatilho",
    dominio = {2},
    nivelMin = 11,
    descricaoEfeito = "A arma é envolta em energia mágica, causando dano extra. Requer Combate.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "dano_extra",
        percentual = 0.5,
        magicEffect = CONST_ME_ENERGYHIT,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {1},
    efeitosSecundarios = {
        [1] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 1)
            if nivel >= 10 then
                -- adiciona sangramento mágico
                local cond = Condition(CONDITION_BLEEDING, CONDITIONID_COMBAT, 3000)
                cond:setParameter(CONDITION_PARAM_PERIODICDAMAGE, 12)
                cond:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
                t:addCondition(cond)
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 14,
    prioridade = 7,
    categoria = "sinergia",
    condicaoFocoMin = 40
}

HABILIDADES[224] = {
    nome = "Escudo Arcano",
    tipo = "gatilho",
    dominio = {2},
    nivelMin = 15,
    descricaoEfeito = "Ao bloquear, ganha um escudo mágico que absorve dano. Requer Escudo.",
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
            local nivel = getNivelEfetivo(p, 15)
            if nivel >= 10 then
                p:setDamageTakenModifier(0.5)
                addEvent(function()
                    local pl = Player(p:getId())
                    if pl then pl:setDamageTakenModifier(1.0) end
                end, 4000)
            end
        end
    },
    gatilho = "onBlock",
    cooldown = 22,
    prioridade = 7,
    categoria = "sinergia"
}

HABILIDADES[225] = {
    nome = "Tempestade Arcana",
    tipo = "gatilho",
    dominio = {2},
    nivelMin = 17,
    descricaoEfeito = "Invoca uma tempestade mágica que combina todos os estilos arcanos. Requer múltiplos filhos.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "area_target",
        percentual = 0.6,
        areaPercentual = 0.4,
        raio = 3,
        magicEffect = CONST_ME_ENERGYAREA,
        nivelMinSecundario = 15
    },
    sinergiaDominios = {20, 21, 22},
    efeitosSecundarios = {
        [20] = function(p, t, d) -- elemental
            if getNivelEfetivo(p, 20) >= 15 then
                local criaturas = getCreaturesInArea(t:getPosition(), 3, 3)
                for _, c in ipairs(criaturas) do
                    if c:isMonster() and c:getId() ~= t:getId() then
                        doTargetCombatHealth(p, c, COMBAT_FIREDAMAGE, -math.floor(d * 0.15), -math.floor(d * 0.15), CONST_ME_FIREAREA)
                    end
                end
            end
        end,
        [21] = function(p, t, d) -- espectro
            if getNivelEfetivo(p, 21) >= 15 then
                local criaturas = getCreaturesInArea(t:getPosition(), 2, 2)
                for _, c in ipairs(criaturas) do
                    if c:isMonster() then
                        local cond = Condition(CONDITION_CURSED, CONDITIONID_COMBAT, 2500)
                        c:addCondition(cond)
                    end
                end
            end
        end,
        [22] = function(p, t, d) -- runologia
            if getNivelEfetivo(p, 22) >= 15 then
                -- rajada adicional
                local alvos = {}
                local criaturas = getCreaturesInArea(t:getPosition(), 3, 3)
                for _, c in ipairs(criaturas) do
                    if c:isMonster() then table.insert(alvos, c) end
                end
                for i = 1, math.min(3, #alvos) do
                    doTargetCombatHealth(p, alvos[i], COMBAT_ENERGYDAMAGE, -math.floor(d * 0.1), -math.floor(d * 0.1), CONST_ME_ENERGYHIT)
                end
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 24,
    prioridade = 9,
    categoria = "sinergia",
    condicaoFocoMin = 85
}

HABILIDADES[226] = {
    nome = "Dreno Arcano",
    tipo = "gatilho",
    dominio = {2},
    nivelMin = 10,
    descricaoEfeito = "Rouba vida e mana do alvo. Requer qualquer secundário.",
    cor = COR.SUCESSO_CURA,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "life_leech",
        leechPercent = 12,
        durationSec = 4,
        nivelMinSecundario = 8
    },
    sinergiaDominios = {20, 21, 22},
    efeitosSecundarios = {
        [20] = function(p, t, d)
            if getNivelEfetivo(p, 20) >= 8 then
                p:addMana(math.floor(d * 0.05))
            end
        end,
        [21] = function(p, t, d)
            if getNivelEfetivo(p, 21) >= 8 then
                local heal = math.floor(d * 0.03)
                p:addHealth(heal)
            end
        end,
        [22] = function(p, t, d)
            if getNivelEfetivo(p, 22) >= 8 then
                p:addMana(math.floor(d * 0.08))
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 6,
    categoria = "sinergia",
    condicaoFocoMin = 30
}

HABILIDADES[227] = {
    nome = "Onda de Choque Mágica",
    tipo = "gatilho",
    dominio = {2},
    nivelMin = 16,
    descricaoEfeito = "Empurra todos os inimigos ao redor e causa dano. Requer Escudo ou Elementos.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "area_ground",
        centro = "jogador",
        raio = 3,
        percentual = 0.4,
        magicEffect = CONST_ME_ENERGYAREA,
        knockback = true,
        nivelMinSecundario = 12
    },
    sinergiaDominios = {15, 20},
    efeitosSecundarios = {
        [15] = function(p, t, d) end,
        [20] = function(p, t, d) end
    },
    gatilho = "onAttack",
    cooldown = 20,
    prioridade = 7,
    categoria = "sinergia",
    condicao = "cercado",
    condicaoFocoMin = 70
}

HABILIDADES[228] = {
    nome = "Chama Arcana",
    tipo = "gatilho",
    dominio = {2},
    nivelMin = 9,
    descricaoEfeito = "Causa queimadura arcana que não pode ser apagada facilmente. Requer Fogo.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "condicao",
        conditionType = CONDITION_FIRE,
        duration = 5000,
        periodicDamage = 15,
        comDano = true,
        percentual = 0.4,
        magicEffect = CONST_ME_FIREAREA,
        nivelMinSecundario = 8
    },
    sinergiaDominios = {23},
    efeitosSecundarios = {
        [23] = function(p, t, d)
            if getNivelEfetivo(p, 23) >= 8 then
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

HABILIDADES[229] = {
    nome = "Sopro do Dragão Arcano",
    tipo = "gatilho",
    dominio = {2},
    nivelMin = 18,
    descricaoEfeito = "Sopro mágico que combina elementos. Requer Fogo e Gelo.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "area_ground",
        centro = "jogador",
        raio = 3,
        percentual = 0.5,
        magicEffect = CONST_ME_FIREAREA,
        nivelMinSecundario = 15
    },
    sinergiaDominios = {23, 24},
    efeitosSecundarios = {
        [23] = function(p, t, d)
            if getNivelEfetivo(p, 23) >= 15 then
                local cond = Condition(CONDITION_FIRE, CONDITIONID_COMBAT, 3000)
                cond:setParameter(CONDITION_PARAM_PERIODICDAMAGE, 20)
                cond:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
                t:addCondition(cond)
            end
        end,
        [24] = function(p, t, d)
            if getNivelEfetivo(p, 24) >= 15 then
                local cond = Condition(CONDITION_PARALYZE, CONDITIONID_COMBAT, 2500)
                t:addCondition(cond)
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 26,
    prioridade = 9,
    categoria = "sinergia",
    condicaoFocoMin = 90
}

-- ============================================================
-- TRANSFORMAÇÕES (5)
-- ============================================================
HABILIDADES[230] = {
    nome = "Lampejo Arcano",
    tipo = "transformacao",
    dominio = {2},
    nivelMin = 8,
    descricaoEfeito = "Lampejo: o dano mágico aumenta 15% e a regeneração de mana dobra.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local atual = player:getCombatModifier("magic_damage") or 0
        player:setCombatModifier("magic_damage", atual + 15)
        player:setManaRegenModifier(2.0)
    end,
    desfazer = function(player)
        local atual = player:getCombatModifier("magic_damage") or 15
        player:setCombatModifier("magic_damage", atual - 15)
        player:setManaRegenModifier(1.0)
    end
}

HABILIDADES[231] = {
    nome = "Vínculo Místico",
    tipo = "transformacao",
    dominio = {2},
    nivelMin = 12,
    descricaoEfeito = "Vínculo: o dano mágico aumenta 25% e runas flutuam ao seu redor.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local atual = player:getCombatModifier("magic_damage") or 0
        player:setCombatModifier("magic_damage", atual + 25)
    end,
    desfazer = function(player)
        local atual = player:getCombatModifier("magic_damage") or 25
        player:setCombatModifier("magic_damage", atual - 25)
    end
}

HABILIDADES[232] = {
    nome = "Maestria Arcana",
    tipo = "transformacao",
    dominio = {2},
    nivelMin = 16,
    descricaoEfeito = "Maestria: as habilidades mágicas ignoram 15% da armadura do alvo e o Vínculo é permanente.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        player:setCombatModifier("magic_penetration", 15)
    end,
    desfazer = function(player)
        player:setCombatModifier("magic_penetration", 0)
    end
}

HABILIDADES[233] = {
    nome = "Apoteose Arcana",
    tipo = "transformacao",
    dominio = {2},
    nivelMin = 20,
    descricaoEfeito = "Transformação suprema: invoca uma devastação arcana massiva por 8s, causando dano mágico puro em área.",
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
                    local dmg = math.floor((pl:getMagicLevel() * 4) * (1 + count * 0.2))
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

HABILIDADES[234] = {
    nome = "Recarga Arcana",
    tipo = "transformacao",
    dominio = {2},
    nivelMin = 10,
    descricaoEfeito = "Ao ativar, restaura 30% da mana máxima instantaneamente.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local mana = math.floor(player:getMaxMana() * 0.3)
        player:addMana(mana)
        player:getPosition():sendMagicEffect(CONST_ME_MAGIC_BLUE)
    end,
    desfazer = function(player) end
}

print("DEBUG: habilidades_magia.lua carregado.")