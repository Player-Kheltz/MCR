--[[
    Projeto MCR ? SPA ? Habilidades de Espadas Leves (100)
    Perfil: Especialidade (36 habilidades + Traço Inerente)
    Arquitetura modular v4.6
--]]

-- ============================================================
-- TRAÇO INERENTE: Dança das Lâminas
-- ============================================================
-- Nível 5: Ataques consecutivos aumentam a velocidade de ataque em 2% por acerto (máx 10%).
-- Nível 10: Ao esquivar, ganha 20% de velocidade de movimento por 2s.
-- Nível 15: Cada golpe reduz o cooldown global em 0.1s.
-- Nível 20: 5 acertos consecutivos concedem "Dança da Lâmina" (próximo ataque +50% dano e sangramento).
-- (Implementado via passivas_ataque.lua e eventos de combate)

-- ============================================================
-- ÁRVORE I (nível 5): Passiva de Identidade
-- ============================================================
HABILIDADES[10001] = {
    nome = "Lâmina Ágil",
    tipo = "passiva",
    dominio = {100},
    nivelMin = 5,
    descricaoEfeito = "Aumenta a velocidade de ataque em 10% com espadas leves.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        player:setCombatModifier("light_sword_speed", 0.10)
    end
}

-- ============================================================
-- ÁRVORE II (nível 10): Passiva de Expansão
-- ============================================================
HABILIDADES[10002] = {
    nome = "Fio Afiado",
    tipo = "passiva",
    dominio = {100},
    nivelMin = 10,
    descricaoEfeito = "Ataques com espadas leves têm 10% de chance de causar sangramento.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        player:setCombatModifier("light_sword_bleed_chance", 10)
    end
}

-- ============================================================
-- ÁRVORE III (nível 15): Gatilho de Assinatura ? Dança das Lâminas
-- ============================================================
HABILIDADES[10003] = {
    nome = "Dança das Lâminas",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 15,
    descricaoEfeito = "Desfere uma sequência de 3 golpes rápidos, cada um com 40% do dano base.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "rajada",
        percentual = 0.4,
        numProjeteis = 3,
        intervaloMs = 300
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 8,
    categoria = "single",
    condicaoFocoMin = 50,
    posturaMod = {
        [1] = { chanceMult = 1.5 },
        [2] = { chanceMult = 1.0 },
        [3] = { chanceMult = 0.6 }
    }
}

-- ============================================================
-- ÁRVORE IV (nível 20): Passiva de Maestria
-- ============================================================
HABILIDADES[10004] = {
    nome = "Maestria em Espadas Leves",
    tipo = "passiva",
    dominio = {100},
    nivelMin = 20,
    descricaoEfeito = "Aumenta o dano crítico em 25% e ensina Dança das Lâminas a Espadas Pesadas.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        player:setCombatModifier("light_sword_crit_power", 0.25)
        if not jogadorConheceHabilidade(player, 10103) then
            aprenderHabilidade(player, 10103)
        end
    end
}

-- ============================================================
-- PASSIVAS DE ATRIBUTO (2)
-- ============================================================
HABILIDADES[10005] = {
    nome = "Esgrima Fluida",
    tipo = "passiva",
    dominio = {100},
    nivelMin = 3,
    descricaoEfeito = "Aumenta a velocidade de movimento em 2% por nível de Espadas Leves.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player) end  -- gerido por recalcularVelocidade
}

HABILIDADES[10006] = {
    nome = "Golpes Precisos",
    tipo = "passiva",
    dominio = {100},
    nivelMin = 8,
    descricaoEfeito = "Aumenta o dano com espadas leves em 1.5% por nível.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 100)
        player:setCombatModifier("light_sword_damage", nivel * 1.5)
    end
}

-- ============================================================
-- PASSIVA DE SINERGIA (1)
-- ============================================================
HABILIDADES[10007] = {
    nome = "Lâmina Sanguinária",
    tipo = "passiva",
    dominio = {100},
    nivelMin = 18,
    descricaoEfeito = "Aumenta a chance de sangramento em 1% por nível de Espadas Leves.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 100)
        player:setCombatModifier("light_sword_bleed_chance", 10 + nivel)
    end
}

-- ============================================================
-- GATILHOS DE COMBATE (14)
-- ============================================================
HABILIDADES[10010] = {
    nome = "Estocada Dupla",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 6,
    descricaoEfeito = "Desfere duas estocadas rápidas.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "rajada",
        percentual = 0.3,
        numProjeteis = 2,
        intervaloMs = 250
    },
    gatilho = "onAttack",
    cooldown = 10,
    prioridade = 7,
    categoria = "single"
}

HABILIDADES[10011] = {
    nome = "Golpe em Arco",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 9,
    descricaoEfeito = "Dano em área ao redor do jogador.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "area_ground",
        centro = "jogador",
        raio = 1,
        percentual = 0.4,
        magicEffect = CONST_ME_HITAREA
    },
    gatilho = "onAttack",
    cooldown = 14,
    prioridade = 7,
    categoria = "aoe",
    condicao = "cercado",
    posturaMod = {
        [1] = { chanceMult = 1.3 },
        [2] = { chanceMult = 1.0 },
        [3] = { chanceMult = 0.8 }
    }
}

HABILIDADES[10012] = {
    nome = "Investida Cortante",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 7,
    descricaoEfeito = "Avança rapidamente contra o alvo e desfere um golpe.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "knockback",
        comDano = true,
        percentual = 0.35,
        magicEffect = CONST_ME_HITAREA
    },
    gatilho = "onAttack",
    cooldown = 12,
    prioridade = 6,
    categoria = "single",
    condicao = "distancia4"
}

HABILIDADES[10013] = {
    nome = "Corte Rápido",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 8,
    descricaoEfeito = "Golpe rápido que causa dano extra.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "dano_extra",
        percentual = 0.3,
        magicEffect = CONST_ME_DRAWBLOOD
    },
    gatilho = "onAttack",
    cooldown = 8,
    prioridade = 6,
    categoria = "single"
}

HABILIDADES[10014] = {
    nome = "Lâmina em Fúria",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 12,
    descricaoEfeito = "Acelera a velocidade de ataque por 1.5 segundos.",
    cor = COR.DOM_COMBATE_LAMINAS,
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

HABILIDADES[10015] = {
    nome = "Retalhar",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 14,
    descricaoEfeito = "Dano extra e sangramento se o alvo estiver isolado.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_BLEEDING,
        duration = 4000,
        periodicDamage = 18,
        comDano = true,
        percentual = 0.5,
        magicEffect = CONST_ME_DRAWBLOOD
    },
    gatilho = "onAttack",
    cooldown = 13,
    prioridade = 8,
    categoria = "single",
    condicao = "alvoIsolado",
    condicaoFocoMin = 50
}

HABILIDADES[10016] = {
    nome = "Golpe de Oportunidade",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 16,
    descricaoEfeito = "Causa dano extra massivo se o alvo estiver com sangramento.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "dano_extra",
        percentual = 0.8,
        magicEffect = CONST_ME_DRAWBLOOD
    },
    gatilho = "onAttack",
    cooldown = 20,
    prioridade = 9,
    categoria = "single",
    condicaoFocoMin = 70
}

HABILIDADES[10017] = {
    nome = "Véu de Aço",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 10,
    descricaoEfeito = "Reduz o dano recebido e contra-ataca.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "defesa_contra_ataque",
        percentual = 0.3,
        magicEffect = CONST_ME_HITAREA
    },
    gatilho = "onBlock",
    cooldown = 15,
    prioridade = 6,
    categoria = "defense",
    condicao = "inimigosProximos"
}

HABILIDADES[10018] = {
    nome = "Corte Profundo",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 13,
    descricaoEfeito = "Causa sangramento prolongado no alvo.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_BLEEDING,
        duration = 5000,
        periodicDamage = 15,
        comDano = true,
        percentual = 0.4,
        magicEffect = CONST_ME_DRAWBLOOD
    },
    gatilho = "onAttack",
    cooldown = 14,
    prioridade = 7,
    categoria = "debuff",
    condicaoFocoMin = 40
}

HABILIDADES[10019] = {
    nome = "Rajada de Estocadas",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 18,
    descricaoEfeito = "Dispara três projéteis perfurantes em sequência.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "rajada",
        percentual = 0.3,
        numProjeteis = 3,
        intervaloMs = 250
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 8,
    categoria = "single",
    condicaoFocoMin = 75
}

HABILIDADES[10020] = {
    nome = "Avanço Ligeiro",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 5,
    descricaoEfeito = "Acelera a velocidade de ataque brevemente.",
    cor = COR.DOM_COMBATE_LAMINAS,
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

HABILIDADES[10021] = {
    nome = "Lâmina Giratória",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 11,
    descricaoEfeito = "Gira a lâmina ao redor, causando dano em área.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "area_ground",
        centro = "jogador",
        raio = 2,
        percentual = 0.35,
        magicEffect = CONST_ME_GROUNDSHAKER
    },
    gatilho = "onAttack",
    cooldown = 15,
    prioridade = 7,
    categoria = "aoe",
    condicao = "cercado"
}

HABILIDADES[10022] = {
    nome = "Execução do Duelista",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 17,
    descricaoEfeito = "Golpe final massivo contra alvos com vida baixa.",
    cor = COR.DOM_COMBATE_LAMINAS,
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

HABILIDADES[10023] = {
    nome = "Precisão Cirúrgica",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 15,
    descricaoEfeito = "Golpe preciso que ignora parte da armadura do alvo.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "dano_extra",
        percentual = 0.5,
        magicEffect = CONST_ME_HITAREA
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 7,
    categoria = "single",
    condicaoFocoMin = 60
}

-- ============================================================
-- GATILHOS DE CONDIÇÃO/DEFESA (7)
-- ============================================================
HABILIDADES[10030] = {
    nome = "Dilacerar",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 8,
    descricaoEfeito = "Causa sangramento no alvo.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_BLEEDING,
        duration = 4000,
        periodicDamage = 12,
        comDano = true,
        percentual = 0.3,
        magicEffect = CONST_ME_DRAWBLOOD
    },
    gatilho = "onAttack",
    cooldown = 12,
    prioridade = 6,
    categoria = "debuff",
    condicaoFocoMin = 25
}

HABILIDADES[10031] = {
    nome = "Corte no Tendão",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 12,
    descricaoEfeito = "Causa lentidão e sangramento no alvo.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_PARALYZE,
        duration = 3000,
        periodicDamage = 8,
        comDano = true,
        percentual = 0.4,
        magicEffect = CONST_ME_DRAWBLOOD
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 7,
    categoria = "debuff",
    condicao = "alvoIsolado",
    condicaoFocoMin = 50
}

HABILIDADES[10032] = {
    nome = "Bloqueio com Lâmina",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 7,
    descricaoEfeito = "Reduz o dano recebido por 2 segundos.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "defesa_barreira",
        factor = 0.6,
        durationMs = 2000
    },
    gatilho = "onReceiveDamage",
    cooldown = 20,
    prioridade = 5,
    categoria = "defense"
}

HABILIDADES[10033] = {
    nome = "Contra-Ataque Ágil",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 10,
    descricaoEfeito = "Ao bloquear, contra-ataca todos os inimigos ao redor.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "defesa_contra_ataque",
        percentual = 0.35,
        magicEffect = CONST_ME_HITAREA
    },
    gatilho = "onBlock",
    cooldown = 14,
    prioridade = 6,
    categoria = "defense",
    condicao = "cercado"
}

HABILIDADES[10034] = {
    nome = "Sede de Sangue",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 14,
    descricaoEfeito = "Roubo de vida por 4 segundos.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "life_leech",
        leechPercent = 20,
        durationSec = 4
    },
    gatilho = "onAttack",
    cooldown = 22,
    prioridade = 5,
    categoria = "buff",
    condicaoFocoMin = 40
}

HABILIDADES[10035] = {
    nome = "Atordoar",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 15,
    descricaoEfeito = "Golpe com o cabo da espada que atordoa o alvo.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_DAZZLED,
        duration = 2500,
        comDano = true,
        percentual = 0.2,
        magicEffect = CONST_ME_STUN
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 6,
    categoria = "debuff",
    condicaoFocoMin = 50
}

HABILIDADES[10036] = {
    nome = "Esquiva Reflexa",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 9,
    descricaoEfeito = "Ao esquivar, ganha 20% de velocidade de movimento por 2 segundos.",
    cor = COR.DOM_COMBATE_LAMINAS,
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
HABILIDADES[10040] = {
    nome = "Lâmina Incendiária",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 10,
    descricaoEfeito = "A lâmina incendeia o alvo. Requer afinidade com Fogo.",
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

HABILIDADES[10041] = {
    nome = "Lâmina Gélida",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 12,
    descricaoEfeito = "A lâmina gélida reduz a velocidade do alvo. Requer afinidade com Gelo.",
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

HABILIDADES[10042] = {
    nome = "Lâmina Sombria",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 16,
    descricaoEfeito = "A lâmina causa medo no alvo. Requer afinidade com Espectro.",
    cor = COR.ELEM_SOMBRA,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "condicao",
        conditionType = CONDITION_CURSED,
        duration = 3000,
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
                local cond = Condition(CONDITION_CURSED, CONDITIONID_COMBAT, 3000 + nivel * 200)
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

HABILIDADES[10043] = {
    nome = "Escudo e Espada",
    tipo = "gatilho",
    dominio = {100},
    nivelMin = 14,
    descricaoEfeito = "Aumenta a defesa e contra-ataca. Requer Escudo equipado.",
    cor = COR.DOM_ESCUDO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "defesa_contra_ataque",
        percentual = 0.4,
        magicEffect = CONST_ME_HITAREA,
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
HABILIDADES[10050] = {
    nome = "Dança da Faísca",
    tipo = "transformacao",
    dominio = {100},
    nivelMin = 10,
    descricaoEfeito = "Lampejo: a velocidade de ataque aumenta 15%.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        player:setAttackSpeedModifier(0.85)
    end,
    desfazer = function(player)
        aplicarPostura(player, player:getFightMode())
    end
}

HABILIDADES[10051] = {
    nome = "Sinfonia de Aço",
    tipo = "transformacao",
    dominio = {100},
    nivelMin = 15,
    descricaoEfeito = "Vínculo: o dano com espadas leves aumenta 20% e lâminas fantasmagóricas dançam ao redor.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        player:setCombatModifier("light_sword_damage", (player:getCombatModifier("light_sword_damage") or 0) + 20)
    end,
    desfazer = function(player)
        player:setCombatModifier("light_sword_damage", (player:getCombatModifier("light_sword_damage") or 20) - 20)
    end
}

HABILIDADES[10052] = {
    nome = "Lâmina Imortal",
    tipo = "transformacao",
    dominio = {100},
    nivelMin = 20,
    descricaoEfeito = "Maestria: o dano crítico aumenta 30% e o Vínculo é permanente.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        player:setCombatModifier("light_sword_crit_power", 0.30)
    end,
    desfazer = function(player)
        player:setCombatModifier("light_sword_crit_power", 0.0)
    end
}

HABILIDADES[10053] = {
    nome = "Tempestade de Lâminas",
    tipo = "transformacao",
    dominio = {100},
    nivelMin = 18,
    descricaoEfeito = "Transformação especial: invoca uma tempestade de lâminas que causa dano em área massivo por 6 segundos.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        local pid = player:getId()
        local function tick(count)
            local pl = Player(pid)
            if not pl or count >= 6 then return end
            local pos = pl:getPosition()
            local criaturas = getCreaturesInArea(pos, 3, 3)
            for _, c in ipairs(criaturas) do
                if c:isMonster() then
                    local dmg = math.floor((pl:getSkillLevel(SKILL_SWORD) * 2) * (1 + count * 0.2))
                    golpeCorpoACorpo(pl, c, dmg, CONST_ME_WHIRLWINDSWORD)
                end
            end
            pos:sendMagicEffect(CONST_ME_GROUNDSHAKER)
            addEvent(tick, 1000, count + 1)
        end
        tick(0)
    end,
    desfazer = function(player) end
}

print("DEBUG: habilidades_espadas_leves.lua carregado.")