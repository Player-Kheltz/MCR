--[[
    Projeto MCR ? SPA ? Habilidades de Combate (1)
    Perfil: Primário (35 habilidades + Traço Inerente)
    Arquitetura modular v4.6
--]]

-- ============================================================
-- TRAÇO INERENTE: Coração do Guerreiro
-- ============================================================
-- Nível 5: Ao matar um inimigo, recupera 2% da vida máxima.
-- Nível 10: O bónus sobe para 4% e também restaura 2% da mana máxima.
-- Nível 15: Ao matar um inimigo, ganha 10% de velocidade de ataque por 3s.
-- Nível 20: Síntese Superior ? "Mestre da Guerra": ao trocar de arma (especialidade), ganha 15% de dano e 10% de velocidade por 5s. Este efeito não acumula.

-- ============================================================
-- ÁRVORE I (nível 5): Passiva de Identidade
-- ============================================================
HABILIDADES[101] = {
    nome = "Veterano de Batalha",
    tipo = "passiva",
    dominio = {1},
    nivelMin = 5,
    descricaoEfeito = "Aumenta o dano físico em 1% por nível de Combate.",
    cor = COR.SISTEMA_INFO,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 1)
        player:setCombatModifier("physical_damage", nivel)
    end
}

-- ============================================================
-- ÁRVORE II (nível 10): Passiva de Expansão ? Sinergia com Filhos
-- ============================================================
HABILIDADES[102] = {
    nome = "Sinergia Marcial",
    tipo = "passiva",
    dominio = {1},
    nivelMin = 10,
    descricaoEfeito = "Concede bónus adicionais baseados nos domínios filhos.",
    cor = COR.SISTEMA_INFO,
    efeito = function(player)
        -- Lâminas (10): +velocidade de ataque
        if getNivelEfetivo(player, 10) >= 10 then
            player:setCombatModifier("combat_sword_speed", 0.05)
        end
        -- Machados (11): +dano
        if getNivelEfetivo(player, 11) >= 10 then
            player:setCombatModifier("combat_axe_damage", 8)
        end
        -- Clavas (12): +chance de atordoamento
        if getNivelEfetivo(player, 12) >= 10 then
            player:setCombatModifier("combat_club_stun", 10)
        end
        -- Precisão (13): +furtividade
        if getNivelEfetivo(player, 13) >= 10 then
            player:setCombatModifier("combat_precision_stealth", 1)
        end
        -- Artes Marciais (14): +regeneração
        if getNivelEfetivo(player, 14) >= 10 then
            player:setHealthRegenModifier(1.3)
        end
        -- Escudo (15): +defesa
        if getNivelEfetivo(player, 15) >= 10 then
            player:setCombatModifier("combat_shield_defense", 8)
        end
    end
}

-- ============================================================
-- ÁRVORE III (nível 15): Gatilho de Assinatura ? Golpe do General
-- ============================================================
HABILIDADES[103] = {
    nome = "Golpe do General",
    tipo = "gatilho",
    dominio = {1},
    nivelMin = 15,
    descricaoEfeito = "Golpe poderoso que causa dano massivo e aplica efeitos baseados nos filhos dominados.",
    cor = COR.SISTEMA_INFO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "dano_extra",
        percentual = 1.0,
        magicEffect = CONST_ME_HITAREA,
        nivelMinSecundario = 5
    },
    sinergiaDominios = {10, 11, 12, 13, 14, 15},
    efeitosSecundarios = {
        [10] = function(p, t, d) -- Lâminas: sangramento
            if getNivelEfetivo(p, 10) >= 5 then
                local cond = Condition(CONDITION_BLEEDING, CONDITIONID_COMBAT, 3000)
                cond:setParameter(CONDITION_PARAM_PERIODICDAMAGE, 15)
                cond:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
                t:addCondition(cond)
            end
        end,
        [11] = function(p, t, d) -- Machados: knockback
            if getNivelEfetivo(p, 11) >= 5 then
                empurrarAlvo(p, t)
            end
        end,
        [12] = function(p, t, d) -- Clavas: atordoamento
            if getNivelEfetivo(p, 12) >= 5 then
                local cond = Condition(CONDITION_DAZZLED, CONDITIONID_COMBAT, 2000)
                t:addCondition(cond)
            end
        end,
        [13] = function(p, t, d) -- Precisão: dano extra à distância
            if getNivelEfetivo(p, 13) >= 5 then
                local extra = math.floor(d * 0.2)
                doTargetCombatHealth(p, t, COMBAT_PHYSICALDAMAGE, -extra, -extra, CONST_ME_DRAWBLOOD)
            end
        end,
        [14] = function(p, t, d) -- Artes Marciais: roubo de vida
            if getNivelEfetivo(p, 14) >= 5 then
                p:addHealth(math.floor(d * 0.05))
            end
        end,
        [15] = function(p, t, d) -- Escudo: redução de dano por 2s
            if getNivelEfetivo(p, 15) >= 5 then
                p:setDamageTakenModifier(0.8)
                addEvent(function()
                    local pl = Player(p:getId())
                    if pl then pl:setDamageTakenModifier(1.0) end
                end, 2000)
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 20,
    prioridade = 9,
    categoria = "sinergia",
    condicaoFocoMin = 75,
    posturaMod = {
        [1] = { chanceMult = 1.4 },
        [2] = { chanceMult = 1.0 },
        [3] = { chanceMult = 0.7 }
    }
}

-- ============================================================
-- ÁRVORE IV (nível 20): Passiva de Maestria ? Mestre da Guerra
-- ============================================================
HABILIDADES[104] = {
    nome = "Mestre da Guerra",
    tipo = "passiva",
    dominio = {1},
    nivelMin = 20,
    descricaoEfeito = "Síntese Superior: ao trocar de arma, ganha 15% de dano e 10% de velocidade por 5s. Ensina Golpe do General a todos os secundários.",
    cor = COR.SISTEMA_INFO,
    efeito = function(player)
        player:setCombatModifier("combat_mastery", 1)
        -- Ensina a habilidade III aos secundários (se existirem)
        local filhos = {10, 11, 12, 13, 14, 15}
        for _, filhoId in ipairs(filhos) do
            local habIrma = filhoId * 100 + 3  -- convenção de ID: [domId]03
            if HABILIDADES[habIrma] and not jogadorConheceHabilidade(player, habIrma) then
                aprenderHabilidade(player, habIrma)
            end
        end
    end
}

-- ============================================================
-- PASSIVAS DE ATRIBUTO (6 restantes)
-- ============================================================
HABILIDADES[105] = {
    nome = "Constituição de Aço",
    tipo = "passiva",
    dominio = {1},
    nivelMin = 2,
    descricaoEfeito = "Aumenta a vida máxima em 1.5% por nível de Combate.",
    cor = COR.SISTEMA_INFO,
    efeito = function(player) end  -- gerido por recalcularVidaMana
}

HABILIDADES[106] = {
    nome = "Força Bruta",
    tipo = "passiva",
    dominio = {1},
    nivelMin = 4,
    descricaoEfeito = "Aumenta o dano corpo a corpo em 0.5% por nível de Combate.",
    cor = COR.SISTEMA_INFO,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 1)
        player:setCombatModifier("melee_damage", nivel * 0.5)
    end
}

HABILIDADES[107] = {
    nome = "Resiliência",
    tipo = "passiva",
    dominio = {1},
    nivelMin = 6,
    descricaoEfeito = "Reduz o dano recebido em 0.3% por nível de Combate.",
    cor = COR.SISTEMA_INFO,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 1)
        player:setDamageTakenModifier(1.0 - nivel * 0.003)
    end
}

HABILIDADES[108] = {
    nome = "Ímpeto Guerreiro",
    tipo = "passiva",
    dominio = {1},
    nivelMin = 8,
    descricaoEfeito = "Aumenta a velocidade de ataque em 0.3% por nível de Combate.",
    cor = COR.SISTEMA_INFO,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 1)
        player:setAttackSpeedModifier(1.0 - nivel * 0.003)
    end
}

HABILIDADES[109] = {
    nome = "Sede de Batalha",
    tipo = "passiva",
    dominio = {1},
    nivelMin = 10,
    descricaoEfeito = "Aumenta o roubo de vida em 0.2% por nível de Combate.",
    cor = COR.SISTEMA_INFO,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 1)
        player:setCombatModifier("combat_life_leech", nivel * 0.2)
    end
}

HABILIDADES[110] = {
    nome = "Presença Ameaçadora",
    tipo = "passiva",
    dominio = {1},
    nivelMin = 12,
    descricaoEfeito = "Inimigos num raio de 2 tiles têm 5% de chance de ficar atordoados ao atacar você.",
    cor = COR.SISTEMA_INFO,
    efeito = function(player)
        player:setCombatModifier("combat_intimidation", 5)
    end
}

-- ============================================================
-- GATILHOS DE COMBATE (4)
-- ============================================================
HABILIDADES[111] = {
    nome = "Investida do Guerreiro",
    tipo = "gatilho",
    dominio = {1},
    nivelMin = 10,
    descricaoEfeito = "Avança contra o alvo, causando dano e empurrando.",
    cor = COR.SISTEMA_INFO,
    efeitoConfig = {
        tipo = "knockback",
        comDano = true,
        percentual = 0.5,
        magicEffect = CONST_ME_HITAREA
    },
    gatilho = "onAttack",
    cooldown = 14,
    prioridade = 7,
    categoria = "single",
    condicao = "distancia4"
}

HABILIDADES[112] = {
    nome = "Grito de Guerra",
    tipo = "gatilho",
    dominio = {1},
    nivelMin = 14,
    descricaoEfeito = "Amedronta todos os inimigos num raio de 3 tiles.",
    cor = COR.SISTEMA_INFO,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_CURSED,
        duration = 3000,
        magicEffect = CONST_ME_SOUND_RED
    },
    gatilho = "onAttack",
    cooldown = 22,
    prioridade = 7,
    categoria = "aoe",
    condicao = "cercado",
    condicaoFocoMin = 60
}

HABILIDADES[113] = {
    nome = "Fúria do Guerreiro",
    tipo = "gatilho",
    dominio = {1},
    nivelMin = 12,
    descricaoEfeito = "Acelera a velocidade de ataque por 2s.",
    cor = COR.SISTEMA_INFO,
    efeitoConfig = {
        tipo = "buff_speed",
        multiplier = 0.6,
        durationMs = 2000
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 6,
    categoria = "buff",
    condicaoFocoMin = 40
}

HABILIDADES[114] = {
    nome = "Execução do General",
    tipo = "gatilho",
    dominio = {1},
    nivelMin = 18,
    descricaoEfeito = "Golpe final massivo contra alvos com vida baixa, com medo em área.",
    cor = COR.SISTEMA_INFO,
    efeitoConfig = {
        tipo = "finisher",
        percentual = 1.5,
        magicEffect = CONST_ME_DRAWBLOOD,
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
-- GATILHOS DE CONDIÇÃO/DEFESA (2)
-- ============================================================
HABILIDADES[115] = {
    nome = "Contra-Ataque do General",
    tipo = "gatilho",
    dominio = {1},
    nivelMin = 15,
    descricaoEfeito = "Ao bloquear, contra-ataca todos os inimigos ao redor e recupera vida.",
    cor = COR.SISTEMA_INFO,
    efeitoConfig = {
        tipo = "defesa_cura",
        percentual = 0.05,
        reflect = true,
        reflectPercentual = 0.4
    },
    gatilho = "onBlock",
    cooldown = 16,
    prioridade = 7,
    categoria = "defense",
    condicao = "cercado"
}

HABILIDADES[116] = {
    nome = "Postura Inquebrável",
    tipo = "gatilho",
    dominio = {1},
    nivelMin = 16,
    descricaoEfeito = "Reduz o dano recebido em 50% por 3s.",
    cor = COR.SISTEMA_INFO,
    efeitoConfig = {
        tipo = "defesa_barreira",
        factor = 0.5,
        durationMs = 3000
    },
    gatilho = "onReceiveDamage",
    cooldown = 25,
    prioridade = 6,
    categoria = "defense"
}

-- ============================================================
-- GATILHOS DE SINERGIA (10)
-- ============================================================
HABILIDADES[120] = {
    nome = "Dança das Armas",
    tipo = "gatilho",
    dominio = {1},
    nivelMin = 10,
    descricaoEfeito = "Combina todas as armas dominadas num único ataque devastador.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "rajada",
        percentual = 0.4,
        numProjeteis = 3,
        intervaloMs = 300,
        nivelMinSecundario = 5
    },
    sinergiaDominios = {10, 11, 12},
    efeitosSecundarios = {
        [10] = function(p, t, d)
            if getNivelEfetivo(p, 10) >= 5 then
                local cond = Condition(CONDITION_BLEEDING, CONDITIONID_COMBAT, 3000)
                cond:setParameter(CONDITION_PARAM_PERIODICDAMAGE, 10)
                cond:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
                t:addCondition(cond)
            end
        end,
        [11] = function(p, t, d)
            if getNivelEfetivo(p, 11) >= 5 then
                empurrarAlvo(p, t)
            end
        end,
        [12] = function(p, t, d)
            if getNivelEfetivo(p, 12) >= 5 then
                local cond = Condition(CONDITION_DAZZLED, CONDITIONID_COMBAT, 1500)
                t:addCondition(cond)
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 8,
    categoria = "sinergia",
    condicaoFocoMin = 50
}

HABILIDADES[121] = {
    nome = "Precisão do Mestre",
    tipo = "gatilho",
    dominio = {1},
    nivelMin = 12,
    descricaoEfeito = "Dispara um projétil que ricocheteia. Requer Precisão.",
    cor = COR.DOM_COMBATE_PRECISAO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "ricochete",
        percentual = 0.4,
        raio = 2,
        saltos = 2,
        magicEffect = CONST_ME_DRAWBLOOD,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {13, 120, 121},
    efeitosSecundarios = {
        [13] = function(p, t, d)
            if getNivelEfetivo(p, 13) >= 10 then
                local extra = math.floor(d * 0.15)
                doTargetCombatHealth(p, t, COMBAT_PHYSICALDAMAGE, -extra, -extra, CONST_ME_DRAWBLOOD)
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 7,
    categoria = "sinergia",
    condicaoFocoMin = 40
}

HABILIDADES[122] = {
    nome = "Punho do Mestre",
    tipo = "gatilho",
    dominio = {1},
    nivelMin = 14,
    descricaoEfeito = "Golpe desarmado que ignora armadura. Requer Artes Marciais.",
    cor = COR.DOM_COMBATE_DESARMADO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "dano_extra",
        percentual = 0.6,
        magicEffect = CONST_ME_HITAREA,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {14, 130, 132, 133},
    efeitosSecundarios = {
        [14] = function(p, t, d)
            if getNivelEfetivo(p, 14) >= 10 then
                p:addHealth(math.floor(d * 0.08))
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 7,
    categoria = "sinergia",
    condicaoFocoMin = 40
}

HABILIDADES[123] = {
    nome = "Baluarte Vivo",
    tipo = "gatilho",
    dominio = {1},
    nivelMin = 15,
    descricaoEfeito = "Ao bloquear, concede redução de dano a aliados próximos. Requer Escudo.",
    cor = COR.DOM_ESCUDO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "defesa_barreira",
        factor = 0.5,
        durationMs = 3000,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {15},
    efeitosSecundarios = {
        [15] = function(p, t, d)
            if getNivelEfetivo(p, 15) >= 10 then
                local party = p:getParty()
                if party then
                    local members = party:getMembers()
                    for _, member in ipairs(members) do
                        if member:getPosition():getDistance(p:getPosition()) <= 3 then
                            member:setDamageTakenModifier(0.8)
                            addEvent(function()
                                local pl = Player(member:getId())
                                if pl then pl:setDamageTakenModifier(1.0) end
                            end, 3000)
                        end
                    end
                end
            end
        end
    },
    gatilho = "onBlock",
    cooldown = 20,
    prioridade = 7,
    categoria = "sinergia"
}

HABILIDADES[124] = {
    nome = "Lâmina Arcana",
    tipo = "gatilho",
    dominio = {1},
    nivelMin = 16,
    descricaoEfeito = "A arma é imbuída com energia mágica. Requer Magia.",
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
    sinergiaDominios = {2},
    efeitosSecundarios = {
        [2] = function(p, t, d)
            if getNivelEfetivo(p, 2) >= 10 then
                local extra = math.floor(d * getNivelEfetivo(p, 2) * 0.02)
                doTargetCombatHealth(p, t, COMBAT_ENERGYDAMAGE, -extra, -extra, CONST_ME_ENERGYHIT)
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 8,
    categoria = "sinergia",
    condicaoFocoMin = 50
}

HABILIDADES[125] = {
    nome = "Fúria Elemental",
    tipo = "gatilho",
    dominio = {1},
    nivelMin = 18,
    descricaoEfeito = "Descarrega uma torrente elemental que se intensifica com a tua maestria.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "dano_extra",
        percentual = 0.5,
        magicEffect = CONST_ME_FIREAREA,  -- será substituído pelo efeito mais forte
        nivelMinSecundario = 10
    },
    sinergiaDominios = {20, 23, 24, 25, 26},
    efeitosSecundarios = {
        [23] = function(p, t, d)  -- Fogo
            local nivel = getNivelEfetivo(p, 23)
            if nivel >= 10 then
                local dmg = math.floor(d * (0.1 + nivel * 0.02))
                local cond = Condition(CONDITION_FIRE, CONDITIONID_COMBAT, 2000 + nivel * 200)
                cond:setParameter(CONDITION_PARAM_PERIODICDAMAGE, 10 + nivel)
                cond:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
                t:addCondition(cond)
                doTargetCombatHealth(p, t, COMBAT_FIREDAMAGE, -dmg, -dmg, CONST_ME_FIREAREA)
            end
        end,
        [24] = function(p, t, d)  -- Gelo
            local nivel = getNivelEfetivo(p, 24)
            if nivel >= 10 then
                local duration = 1500 + nivel * 100
                local cond = Condition(CONDITION_PARALYZE, CONDITIONID_COMBAT, duration)
                t:addCondition(cond)
                if nivel >= 20 then
                    -- Congelamento profundo: dano extra e explosão em área
                    local dmg = math.floor(d * 0.3)
                    doTargetCombatHealth(p, t, COMBAT_ICEDAMAGE, -dmg, -dmg, CONST_ME_ICEAREA)
                    local pos = t:getPosition()
                    local criaturas = getCreaturesInArea(pos, 1, 1)
                    for _, c in ipairs(criaturas) do
                        if c:isMonster() and c:getId() ~= t:getId() then
                            doTargetCombatHealth(p, c, COMBAT_ICEDAMAGE, -dmg, -dmg, CONST_ME_NONE)
                        end
                    end
                end
            end
        end,
        [25] = function(p, t, d)  -- Terra
            local nivel = getNivelEfetivo(p, 25)
            if nivel >= 10 then
                empurrarAlvo(p, t)
                local dmg = math.floor(d * nivel * 0.03)
                if nivel >= 20 then dmg = dmg * 2 end
                doTargetCombatHealth(p, t, COMBAT_EARTHDAMAGE, -dmg, -dmg, CONST_ME_GROUNDSHAKER)
                -- Veneno adicional se maestria
                if nivel >= 20 then
                    local cond = Condition(CONDITION_POISON, CONDITIONID_COMBAT, 4000)
                    cond:setParameter(CONDITION_PARAM_PERIODICDAMAGE, 20)
                    cond:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
                    t:addCondition(cond)
                end
            end
        end,
        [26] = function(p, t, d)  -- Energia
            local nivel = getNivelEfetivo(p, 26)
            if nivel >= 10 then
                local chance = 20 + nivel
                if math.random(100) <= chance then
                    local extra = math.floor(d * (0.3 + nivel * 0.02))
                    doTargetCombatHealth(p, t, COMBAT_ENERGYDAMAGE, -extra, -extra, CONST_ME_ENERGYHIT)
                    -- Raio em cadeia se maestria
                    if nivel >= 20 then
                        local pos = t:getPosition()
                        local criaturas = getCreaturesInArea(pos, 2, 2)
                        for _, c in ipairs(criaturas) do
                            if c:isMonster() and c:getId() ~= t:getId() then
                                doTargetCombatHealth(p, c, COMBAT_ENERGYDAMAGE, -math.floor(extra * 0.5), -math.floor(extra * 0.5), CONST_ME_ENERGYHIT)
                            end
                        end
                    end
                end
            end
        end,
    },
    -- ?? Efeito Épico: quando TODOS os elementos estão em Maestria
    efeitoEpico = function(p, t, d)
        -- Invoca uma devastação elemental combinada
        local pos = t:getPosition()
        -- Explosão massiva de fogo
        local dmgFire = math.floor(d * 1.0)
        doTargetCombatHealth(p, t, COMBAT_FIREDAMAGE, -dmgFire, -dmgFire, CONST_ME_FIREAREA)
        -- Gelo em área
        local criaturas = getCreaturesInArea(pos, 3, 3)
        for _, c in ipairs(criaturas) do
            if c:isMonster() and c:getId() ~= t:getId() then
                doTargetCombatHealth(p, c, COMBAT_ICEDAMAGE, -math.floor(dmgFire * 0.6), -math.floor(dmgFire * 0.6), CONST_ME_ICEAREA)
                local cond = Condition(CONDITION_PARALYZE, CONDITIONID_COMBAT, 2000)
                c:addCondition(cond)
            end
        end
        -- Terremoto no alvo principal
        empurrarAlvo(p, t)
        doTargetCombatHealth(p, t, COMBAT_EARTHDAMAGE, -math.floor(dmgFire * 0.8), -math.floor(dmgFire * 0.8), CONST_ME_GROUNDSHAKER)
        -- Tempestade de raios sobre todos os inimigos na área
        for _, c in ipairs(criaturas) do
            if c:isMonster() then
                doTargetCombatHealth(p, c, COMBAT_ENERGYDAMAGE, -math.floor(dmgFire * 0.5), -math.floor(dmgFire * 0.5), CONST_ME_ENERGYHIT)
            end
        end
        -- Efeito visual épico
        pos:sendMagicEffect(CONST_ME_BIGCLOUDS)
    end,
    -- Verificador de maestria total
    condicaoEpica = function(p)
        return getNivelEfetivo(p, 23) >= 20 and getNivelEfetivo(p, 24) >= 20 and getNivelEfetivo(p, 25) >= 20 and getNivelEfetivo(p, 26) >= 20
    end,
    gatilho = "onAttack",
    cooldown = 30,
    prioridade = 10,
    categoria = "sinergia",
    condicaoFocoMin = 80,
    -- Adaptação do motor para lidar com o épico
    -- (ver abaixo)
}

HABILIDADES[126] = {
    nome = "Sopro do Dragão",
    tipo = "gatilho",
    dominio = {1},
    nivelMin = 13,
    descricaoEfeito = "Sopro elemental em cone que causa dano e efeitos variados. Requer Fogo ou Gelo.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "area_ground",
        centro = "jogador",
        raio = 2,
        percentual = 0.4,
        magicEffect = CONST_ME_FIREAREA,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {23, 24},
    efeitosSecundarios = {
        [23] = function(p, t, d)
            if getNivelEfetivo(p, 23) >= 10 then
                local cond = Condition(CONDITION_FIRE, CONDITIONID_COMBAT, 3000)
                cond:setParameter(CONDITION_PARAM_PERIODICDAMAGE, 12)
                cond:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
                t:addCondition(cond)
            end
        end,
        [24] = function(p, t, d)
            if getNivelEfetivo(p, 24) >= 10 then
                local cond = Condition(CONDITION_PARALYZE, CONDITIONID_COMBAT, 2000)
                t:addCondition(cond)
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 7,
    categoria = "sinergia",
    condicao = "cercado",
    condicaoFocoMin = 50
}

HABILIDADES[127] = {
    nome = "Passos do Vento",
    tipo = "gatilho",
    dominio = {1},
    nivelMin = 11,
    descricaoEfeito = "Ao esquivar, ganha 30% de velocidade de movimento por 2s. Requer Precisão.",
    cor = COR.DOM_COMBATE_PRECISAO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "buff_speed",
        multiplier = 0.5,
        durationMs = 2000,
        nivelMinSecundario = 8
    },
    sinergiaDominios = {13, 120, 121},
    efeitosSecundarios = {
        [13] = function(p, t, d)
            if getNivelEfetivo(p, 13) >= 8 then
                p:setStealth(true)
                addEvent(function()
                    local pl = Player(p:getId())
                    if pl then pl:setStealth(false) end
                end, 2000)
            end
        end
    },
    gatilho = "onReceiveDamage",
    cooldown = 16,
    prioridade = 6,
    categoria = "sinergia",
    condicao = "aposEsquiva"
}

HABILIDADES[128] = {
    nome = "Impacto Sísmico",
    tipo = "gatilho",
    dominio = {1},
    nivelMin = 17,
    descricaoEfeito = "Bate a arma no chão, causando dano em área e atordoamento. Requer Clavas.",
    cor = COR.DOM_COMBATE_IMPACTO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "area_ground",
        centro = "jogador",
        raio = 3,
        percentual = 0.5,
        magicEffect = CONST_ME_GROUNDSHAKER,
        condicao = CONDITION_DAZZLED,
        condDuration = 2000,
        nivelMinSecundario = 12
    },
    sinergiaDominios = {12, 112, 113},
    efeitosSecundarios = {
        [12] = function(p, t, d)
            if getNivelEfetivo(p, 12) >= 12 then
                local cond = Condition(CONDITION_DAZZLED, CONDITIONID_COMBAT, 2500)
                t:addCondition(cond)
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 20,
    prioridade = 8,
    categoria = "sinergia",
    condicao = "cercado",
    condicaoFocoMin = 70
}

HABILIDADES[129] = {
    nome = "Aura de Batalha",
    tipo = "gatilho",
    dominio = {1},
    nivelMin = 19,
    descricaoEfeito = "Emite uma aura que aumenta o dano de aliados próximos em 10% por 4s.",
    cor = COR.SISTEMA_INFO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "buff_damage",
        percentExtra = 10,
        buffHits = 10,
        nivelMinSecundario = 5
    },
    sinergiaDominios = {10, 11, 12, 13, 14, 15},
    efeitosSecundarios = {
        [10] = function(p, t, d) end,
        [11] = function(p, t, d) end,
        [12] = function(p, t, d) end,
        [13] = function(p, t, d) end,
        [14] = function(p, t, d) end,
        [15] = function(p, t, d) end
    },
    gatilho = "onAttack",
    cooldown = 25,
    prioridade = 7,
    categoria = "sinergia",
    condicaoFocoMin = 80
}

-- ============================================================
-- TRANSFORMAÇÕES (5)
-- ============================================================
HABILIDADES[130] = {
    nome = "Lampejo do Guerreiro",
    tipo = "transformacao",
    dominio = {1},
    nivelMin = 8,
    descricaoEfeito = "Lampejo: a velocidade de ataque aumenta 15% e a regeneração dobra.",
    cor = COR.SISTEMA_INFO,
    efeito = function(player)
        player:setAttackSpeedModifier(0.85)
        player:setHealthRegenModifier(2.0)
    end,
    desfazer = function(player)
        aplicarPostura(player, player:getFightMode())
        player:setHealthRegenModifier(1.0)
    end
}

HABILIDADES[131] = {
    nome = "Vínculo do Gladiador",
    tipo = "transformacao",
    dominio = {1},
    nivelMin = 12,
    descricaoEfeito = "Vínculo: o dano físico aumenta 20% e você emite uma aura intimidadora.",
    cor = COR.SISTEMA_INFO,
    efeito = function(player)
        local atual = player:getCombatModifier("physical_damage") or 0
        player:setCombatModifier("physical_damage", atual + 20)
    end,
    desfazer = function(player)
        local atual = player:getCombatModifier("physical_damage") or 20
        player:setCombatModifier("physical_damage", atual - 20)
    end
}

HABILIDADES[132] = {
    nome = "Maestria do Combate",
    tipo = "transformacao",
    dominio = {1},
    nivelMin = 16,
    descricaoEfeito = "Maestria: todos os ataques têm 10% de chance de causar sangramento e o Vínculo é permanente.",
    cor = COR.SISTEMA_INFO,
    efeito = function(player)
        player:setCombatModifier("combat_bleed_all", 10)
    end,
    desfazer = function(player)
        player:setCombatModifier("combat_bleed_all", 0)
    end
}

HABILIDADES[133] = {
    nome = "Avatar da Guerra",
    tipo = "transformacao",
    dominio = {1},
    nivelMin = 20,
    descricaoEfeito = "Transformação suprema: por 8s, você se torna imune a controlo de grupo e reflete 30% do dano recebido.",
    cor = COR.SISTEMA_INFO,
    efeito = function(player)
        player:setCombatModifier("combat_avatar", 1)
        player:setDamageTakenModifier(0.6)
    end,
    desfazer = function(player)
        player:setCombatModifier("combat_avatar", 0)
        player:setDamageTakenModifier(1.0)
    end
}

HABILIDADES[134] = {
    nome = "Segundo Fôlego",
    tipo = "transformacao",
    dominio = {1},
    nivelMin = 10,
    descricaoEfeito = "Ao ativar, recupera 30% da vida máxima instantaneamente.",
    cor = COR.SUCESSO_CURA,
    efeito = function(player)
        local heal = math.floor(player:getMaxHealth() * 0.3)
        player:addHealth(heal)
        player:getPosition():sendMagicEffect(CONST_ME_MAGIC_BLUE)
    end,
    desfazer = function(player) end
}

print("DEBUG: habilidades_combate.lua carregado.")