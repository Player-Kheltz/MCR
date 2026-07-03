--[[
    Projeto MCR ? SPA ? Habilidades de Wands (210)
    Perfil: Especialidade (36 habilidades + Traço Inerente)
    Arquitetura modular v4.6
--]]

-- ============================================================
-- TRAÇO INERENTE: Centelha Arcana
-- ============================================================
-- Nível 5: Ataques com wand têm 5% de chance de disparar uma segunda rajada (50% do dano).
-- Nível 10: A segunda rajada pode ricochetear para um inimigo próximo (raio 2).
-- Nível 15: Rajadas consecutivas aumentam o dano elemental em 2% por acerto (máx 10%).
-- Nível 20: A cada 10 segundos, a próxima habilidade de wand não consome mana.

-- ============================================================
-- ÁRVORE I (nível 5): Passiva de Identidade
-- ============================================================
HABILIDADES[21001] = {
    nome = "Varinha Mágica",
    tipo = "passiva",
    dominio = {210},
    nivelMin = 5,
    descricaoEfeito = "Aumenta o dano com wands em 10%.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        player:setCombatModifier("wand_damage", 10)
    end
}

-- ============================================================
-- ÁRVORE II (nível 10): Passiva de Expansão
-- ============================================================
HABILIDADES[21002] = {
    nome = "Fluxo de Mana",
    tipo = "passiva",
    dominio = {210},
    nivelMin = 10,
    descricaoEfeito = "Reduz o custo de mana das habilidades de wand em 15%.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        player:setCombatModifier("wand_mana_cost", -15)
    end
}

-- ============================================================
-- ÁRVORE III (nível 15): Gatilho de Assinatura ? Explosão Arcana
-- ============================================================
HABILIDADES[21003] = {
    nome = "Explosão Arcana",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 15,
    descricaoEfeito = "Explosão centrada no alvo, causando dano em área.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "area_target",
        percentual = 0.8,
        areaPercentual = 0.4,
        raio = 2,
        magicEffect = CONST_ME_ENERGYAREA
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
HABILIDADES[21004] = {
    nome = "Maestria em Wands",
    tipo = "passiva",
    dominio = {210},
    nivelMin = 20,
    descricaoEfeito = "Aumenta o dano elemental em 20% e ensina Explosão Arcana a Rods.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        player:setCombatModifier("wand_damage", 20)
        if not jogadorConheceHabilidade(player, 21103) then
            aprenderHabilidade(player, 21103)
        end
    end
}

-- ============================================================
-- PASSIVAS DE ATRIBUTO (3 restantes)
-- ============================================================
HABILIDADES[21005] = {
    nome = "Ligeireza Arcana",
    tipo = "passiva",
    dominio = {210},
    nivelMin = 3,
    descricaoEfeito = "Aumenta a velocidade de movimento em 1.5% por nível de Wands.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player) end  -- gerido por recalcularVelocidade
}

HABILIDADES[21006] = {
    nome = "Potência Arcanista",
    tipo = "passiva",
    dominio = {210},
    nivelMin = 8,
    descricaoEfeito = "Aumenta o dano elemental em 1% por nível de Wands.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 210)
        player:setCombatModifier("wand_damage", 10 + nivel)
    end
}

HABILIDADES[21007] = {
    nome = "Reservatório de Mana",
    tipo = "passiva",
    dominio = {210},
    nivelMin = 6,
    descricaoEfeito = "Aumenta a mana máxima em 2% por nível de Wands.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player) end  -- gerido por recalcularVidaMana
}

-- ============================================================
-- GATILHOS DE COMBATE (14)
-- ============================================================
HABILIDADES[21010] = {
    nome = "Raio Arcano",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 6,
    descricaoEfeito = "Dispara um raio arcano que causa dano extra.",
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

HABILIDADES[21011] = {
    nome = "Rajada de Centelhas",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 9,
    descricaoEfeito = "Dispara três projéteis arcanos em sequência.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "rajada",
        percentual = 0.35,
        numProjeteis = 3,
        intervaloMs = 250
    },
    gatilho = "onAttack",
    cooldown = 14,
    prioridade = 7,
    categoria = "single",
    condicaoFocoMin = 40
}

HABILIDADES[21012] = {
    nome = "Nova Arcana",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 11,
    descricaoEfeito = "Explosão no chão ao redor do jogador, causando dano em área.",
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

HABILIDADES[21013] = {
    nome = "Runa Relâmpago",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 13,
    descricaoEfeito = "Lança um projétil que salta entre inimigos próximos.",
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

HABILIDADES[21014] = {
    nome = "Descarga Arcana",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 15,
    descricaoEfeito = "Liga dois inimigos com um arco de energia, causando dano ao secundário.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "corrente",
        percentual = 0.5,
        raio = 3,
        magicEffect = CONST_ME_ENERGYHIT
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 7,
    categoria = "aoe",
    condicao = "cercadoAlvo",
    condicaoFocoMin = 60
}

HABILIDADES[21015] = {
    nome = "Pulso de Mana",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 8,
    descricaoEfeito = "Aumenta a velocidade de ataque por 1.5 segundos.",
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

HABILIDADES[21016] = {
    nome = "Barragem Arcana",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 14,
    descricaoEfeito = "Dispara quatro projéteis em rápida sucessão.",
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

HABILIDADES[21017] = {
    nome = "Contra-Carga",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 10,
    descricaoEfeito = "Ao bloquear, contra-ataca todos os inimigos ao redor com energia.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "defesa_contra_ataque",
        percentual = 0.35,
        magicEffect = CONST_ME_ENERGYHIT
    },
    gatilho = "onBlock",
    cooldown = 14,
    prioridade = 6,
    categoria = "defense",
    condicao = "cercado"
}

HABILIDADES[21018] = {
    nome = "Explosão Contida",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 12,
    descricaoEfeito = "Explosão no alvo que causa dano extra e pode atordoar.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_DAZZLED,
        duration = 2000,
        comDano = true,
        percentual = 0.4,
        magicEffect = CONST_ME_ENERGYAREA
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 7,
    categoria = "debuff",
    condicaoFocoMin = 50
}

HABILIDADES[21019] = {
    nome = "Anel de Repulsão",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 16,
    descricaoEfeito = "Empurra todos os inimigos ao redor e causa dano.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "area_ground",
        centro = "jogador",
        raio = 2,
        percentual = 0.35,
        magicEffect = CONST_ME_ENERGYAREA,
        knockback = true
    },
    gatilho = "onAttack",
    cooldown = 20,
    prioridade = 7,
    categoria = "aoe",
    condicao = "cercado",
    condicaoFocoMin = 70
}

HABILIDADES[21020] = {
    nome = "Feixe de Mana",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 7,
    descricaoEfeito = "Dispara um projétil de mana pura que ignora parcialmente a armadura.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "dano_extra",
        percentual = 0.35,
        magicEffect = CONST_ME_ENERGYHIT
    },
    gatilho = "onAttack",
    cooldown = 10,
    prioridade = 6,
    categoria = "single"
}

HABILIDADES[21021] = {
    nome = "Onda de Choque Arcana",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 17,
    descricaoEfeito = "Cria uma onda de energia que avança em linha, causando dano e atordoamento.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "area_ground",
        centro = "jogador",
        raio = 3,
        percentual = 0.5,
        magicEffect = CONST_ME_ENERGYAREA,
        condicao = CONDITION_DAZZLED,
        condDuration = 1500
    },
    gatilho = "onAttack",
    cooldown = 22,
    prioridade = 8,
    categoria = "aoe",
    condicaoFocoMin = 80
}

HABILIDADES[21022] = {
    nome = "Toque da Ruína",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 18,
    descricaoEfeito = "Dano massivo contra alvos com vida baixa, com medo em área.",
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

HABILIDADES[21023] = {
    nome = "Recarga Rápida",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 5,
    descricaoEfeito = "Aumenta a velocidade de ataque brevemente.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
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

-- ============================================================
-- GATILHOS DE CONDIÇÃO/DEFESA (7)
-- ============================================================
HABILIDADES[21030] = {
    nome = "Paralisia Arcana",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 9,
    descricaoEfeito = "Causa paralisia no alvo.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_PARALYZE,
        duration = 2500,
        comDano = true,
        percentual = 0.3,
        magicEffect = CONST_ME_ENERGYHIT
    },
    gatilho = "onAttack",
    cooldown = 14,
    prioridade = 6,
    categoria = "debuff",
    condicaoFocoMin = 30
}

HABILIDADES[21031] = {
    nome = "Atordoamento Mágico",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 12,
    descricaoEfeito = "Atordoa o alvo com uma explosão de mana.",
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

HABILIDADES[21032] = {
    nome = "Barreira Mágica",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 8,
    descricaoEfeito = "Reduz o dano recebido por 2 segundos.",
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

HABILIDADES[21033] = {
    nome = "Roubo de Essência",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 10,
    descricaoEfeito = "Rouba mana do alvo ao causar dano.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "mana_leech",
        leechPercent = 10,
        durationSec = 4
    },
    gatilho = "onAttack",
    cooldown = 20,
    prioridade = 5,
    categoria = "buff",
    condicaoFocoMin = 30
}

HABILIDADES[21034] = {
    nome = "Escudo Arcano",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 14,
    descricaoEfeito = "Ao bloquear, recupera vida e causa dano ao atacante.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "defesa_cura",
        percentual = 0.06,
        reflect = true,
        reflectPercentual = 0.3
    },
    gatilho = "onBlock",
    cooldown = 16,
    prioridade = 6,
    categoria = "defense"
}

HABILIDADES[21035] = {
    nome = "Descarga Estática",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 15,
    descricaoEfeito = "Aplica um debuff que aumenta o dano recebido pelo alvo.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_CURSED,
        duration = 4000,
        comDano = true,
        percentual = 0.4,
        magicEffect = CONST_ME_MORTAREA
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 7,
    categoria = "debuff",
    condicaoFocoMin = 60
}

HABILIDADES[21036] = {
    nome = "Reflexo Arcano",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 6,
    descricaoEfeito = "Ao esquivar, ganha 20% de velocidade de movimento por 2 segundos.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "buff_speed",
        multiplier = 0.6,
        durationMs = 2000
    },
    gatilho = "onReceiveDamage",
    cooldown = 15,
    prioridade = 5,
    categoria = "buff",
    condicao = "aposEsquiva"
}

-- ============================================================
-- GATILHOS DE SINERGIA (4)
-- ============================================================
HABILIDADES[21040] = {
    nome = "Wand de Fogo",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 10,
    descricaoEfeito = "A wand incendeia o alvo. Requer afinidade com Fogo.",
    cor = COR.ELEM_FOGO,
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
    sinergiaDominios = {23},
    efeitosSecundarios = {
        [23] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 23)
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

HABILIDADES[21041] = {
    nome = "Wand de Gelo",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 12,
    descricaoEfeito = "A wand congela o alvo, reduzindo sua velocidade. Requer afinidade com Gelo.",
    cor = COR.ELEM_GELO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "condicao",
        conditionType = CONDITION_PARALYZE,
        duration = 2000,
        comDano = true,
        percentual = 0.35,
        magicEffect = CONST_ME_ICEAREA,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {24},
    efeitosSecundarios = {
        [24] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 24)
            if nivel >= 10 then
                local cond = Condition(CONDITION_PARALYZE, CONDITIONID_COMBAT, 2000 + nivel * 100)
                t:addCondition(cond)
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 7,
    categoria = "sinergia",
    condicaoFocoMin = 30
}

HABILIDADES[21042] = {
    nome = "Wand de Energia",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 16,
    descricaoEfeito = "A wand sobrecarrega o alvo com energia, causando paralisia. Requer afinidade com Energia.",
    cor = COR.ELEM_RAIO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "condicao",
        conditionType = CONDITION_PARALYZE,
        duration = 2500,
        comDano = true,
        percentual = 0.45,
        magicEffect = CONST_ME_ENERGYAREA,
        nivelMinSecundario = 12
    },
    sinergiaDominios = {26},
    efeitosSecundarios = {
        [26] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 26)
            if nivel >= 12 then
                -- Raio duplo: chance de repetir o dano
                if math.random(100) <= 20 then
                    local extra = math.floor(d * (0.5 + nivel * 0.02))
                    doTargetCombatHealth(p, t, COMBAT_ENERGYDAMAGE, -extra, -extra, CONST_ME_ENERGYHIT)
                end
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 20,
    prioridade = 8,
    categoria = "sinergia",
    condicaoFocoMin = 60
}

HABILIDADES[21043] = {
    nome = "Escudo e Varinha",
    tipo = "gatilho",
    dominio = {210},
    nivelMin = 14,
    descricaoEfeito = "Aumenta a defesa e contra-ataca com energia. Requer Escudo equipado.",
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
HABILIDADES[21050] = {
    nome = "Fagulha Arcana",
    tipo = "transformacao",
    dominio = {210},
    nivelMin = 10,
    descricaoEfeito = "Lampejo: a velocidade de ataque aumenta 15% e a mana regenera mais rápido.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        player:setAttackSpeedModifier(0.85)
        player:setManaRegenModifier(2.0)
    end,
    desfazer = function(player)
        aplicarPostura(player, player:getFightMode())
        player:setManaRegenModifier(1.0)
    end
}

HABILIDADES[21051] = {
    nome = "Sinfonia Arcana",
    tipo = "transformacao",
    dominio = {210},
    nivelMin = 15,
    descricaoEfeito = "Vínculo: o dano elemental aumenta 20% e pequenas esferas arcanas orbitam o conjurador.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local atual = player:getCombatModifier("wand_damage") or 0
        player:setCombatModifier("wand_damage", atual + 20)
    end,
    desfazer = function(player)
        local atual = player:getCombatModifier("wand_damage") or 20
        player:setCombatModifier("wand_damage", atual - 20)
    end
}

HABILIDADES[21052] = {
    nome = "Varinha Lendária",
    tipo = "transformacao",
    dominio = {210},
    nivelMin = 20,
    descricaoEfeito = "Maestria: o dano elemental ignora 10% da armadura e o Vínculo é permanente.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        player:setCombatModifier("wand_penetration", 10)
    end,
    desfazer = function(player)
        player:setCombatModifier("wand_penetration", 0)
    end
}

HABILIDADES[21053] = {
    nome = "Apoteose Arcana",
    tipo = "transformacao",
    dominio = {210},
    nivelMin = 18,
    descricaoEfeito = "Transformação especial: invoca uma tempestade arcana que causa dano massivo em área por 6 segundos.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeito = function(player)
        local pid = player:getId()
        local function tick(count)
            local pl = Player(pid)
            if not pl or count >= 6 then return end
            local pos = pl:getPosition()
            local criaturas = getCreaturesInArea(pos, 3, 3)
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

print("DEBUG: habilidades_wands.lua carregado.")