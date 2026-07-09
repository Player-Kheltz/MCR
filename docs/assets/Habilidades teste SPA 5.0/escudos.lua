--[[
    Projeto MCR ? SPA ? Habilidades de Escudo (15)
    Perfil: Secundário (34 habilidades + Traço Inerente)
    Arquitetura modular v4.6
--]]

-- ============================================================
-- TRAÇO INERENTE: Muralha Viva
-- ============================================================
-- Nível 5: Ao bloquear, recupera 1% da vida máxima.
-- Nível 10: O bloqueio agora também reduz o dano recebido em 10% por 2s.
-- Nível 15: Ao bloquear, tem 20% de chance de empurrar o atacante.
-- Nível 20: Todos os aliados num raio de 2 tiles recebem 15% de redução de dano passiva enquanto o escudeiro estiver vivo.

-- ============================================================
-- ÁRVORE I (nível 5): Passiva de Identidade
-- ============================================================
HABILIDADES[15001] = {
    nome = "Postura de Defesa",
    tipo = "passiva",
    dominio = {15},
    nivelMin = 5,
    descricaoEfeito = "Aumenta a chance de bloqueio em 10%.",
    cor = COR.DOM_ESCUDO,
    efeito = function(player)
        player:setCombatModifier("shield_block_chance", 10)
    end
}

-- ============================================================
-- ÁRVORE II (nível 10): Passiva de Expansão
-- ============================================================
HABILIDADES[15002] = {
    nome = "Absorção de Impacto",
    tipo = "passiva",
    dominio = {15},
    nivelMin = 10,
    descricaoEfeito = "Reduz o dano recebido em 8% ao bloquear.",
    cor = COR.DOM_ESCUDO,
    efeito = function(player)
        player:setCombatModifier("shield_damage_reduction", 8)
    end
}

-- ============================================================
-- ÁRVORE III (nível 15): Gatilho de Assinatura ? Investida com Escudo
-- ============================================================
HABILIDADES[15003] = {
    nome = "Investida com Escudo",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 15,
    descricaoEfeito = "Avança contra o alvo, causando dano e empurrando-o.",
    cor = COR.DOM_ESCUDO,
    efeitoConfig = {
        tipo = "knockback",
        comDano = true,
        percentual = 0.4,
        magicEffect = CONST_ME_HITAREA
    },
    gatilho = "onAttack",
    cooldown = 14,
    prioridade = 8,
    categoria = "single",
    condicaoFocoMin = 50,
    posturaMod = {
        [1] = { chanceMult = 1.0 },
        [2] = { chanceMult = 1.2 },
        [3] = { chanceMult = 1.5 }
    }
}

-- ============================================================
-- ÁRVORE IV (nível 20): Passiva de Maestria
-- ============================================================
HABILIDADES[15004] = {
    nome = "Bastião Inquebrável",
    tipo = "passiva",
    dominio = {15},
    nivelMin = 20,
    descricaoEfeito = "Maestria em Escudo: regenera 2% da vida máxima a cada bloqueio e ensina Investida a Arremesso de Escudo.",
    cor = COR.DOM_ESCUDO,
    efeito = function(player)
        player:setCombatModifier("shield_regen_on_block", 2)
        if not jogadorConheceHabilidade(player, 14003) then
            aprenderHabilidade(player, 14003)
        end
    end
}

-- ============================================================
-- PASSIVAS DE ATRIBUTO (4 restantes)
-- ============================================================
HABILIDADES[15005] = {
    nome = "Treino com Peso",
    tipo = "passiva",
    dominio = {15},
    nivelMin = 3,
    descricaoEfeito = "Aumenta a vida máxima em 2% por nível de Escudo.",
    cor = COR.DOM_ESCUDO,
    efeito = function(player) end  -- gerido por recalcularVidaMana
}

HABILIDADES[15006] = {
    nome = "Reflexos de Aço",
    tipo = "passiva",
    dominio = {15},
    nivelMin = 8,
    descricaoEfeito = "Aumenta a defesa geral em 1% por nível de Escudo.",
    cor = COR.DOM_ESCUDO,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 15)
        player:setCombatModifier("shield_defense", nivel)
    end
}

HABILIDADES[15007] = {
    nome = "Fôlego de Combate",
    tipo = "passiva",
    dominio = {15},
    nivelMin = 6,
    descricaoEfeito = "Aumenta a regeneração de vida em 1% por nível de Escudo.",
    cor = COR.DOM_ESCUDO,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 15)
        player:setHealthRegenModifier(1.0 + nivel * 0.01)
    end
}

HABILIDADES[15008] = {
    nome = "Presença Imponente",
    tipo = "passiva",
    dominio = {15},
    nivelMin = 12,
    descricaoEfeito = "Inimigos no raio de 2 tiles têm 5% de chance de ficar atordoados ao atacar o escudeiro.",
    cor = COR.DOM_ESCUDO,
    efeito = function(player)
        player:setCombatModifier("shield_intimidation", 5)
    end
}

-- ============================================================
-- GATILHOS DE COMBATE (8)
-- ============================================================
HABILIDADES[15010] = {
    nome = "Golpe com Escudo",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 6,
    descricaoEfeito = "Golpe brusco com o escudo que causa dano extra.",
    cor = COR.DOM_ESCUDO,
    efeitoConfig = {
        tipo = "dano_extra",
        percentual = 0.3,
        magicEffect = CONST_ME_HITAREA
    },
    gatilho = "onAttack",
    cooldown = 8,
    prioridade = 6,
    categoria = "single"
}

HABILIDADES[15011] = {
    nome = "Impacto Sísmico",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 9,
    descricaoEfeito = "Bate o escudo no chão, causando dano em área e atordoamento.",
    cor = COR.DOM_ESCUDO,
    efeitoConfig = {
        tipo = "area_ground",
        centro = "jogador",
        raio = 1,
        percentual = 0.35,
        magicEffect = CONST_ME_GROUNDSHAKER,
        condicao = CONDITION_DAZZLED,
        condDuration = 1500
    },
    gatilho = "onAttack",
    cooldown = 14,
    prioridade = 7,
    categoria = "aoe",
    condicao = "cercado",
    condicaoFocoMin = 40
}

HABILIDADES[15012] = {
    nome = "Repelir",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 11,
    descricaoEfeito = "Empurra todos os inimigos ao redor com uma onda de choque.",
    cor = COR.DOM_ESCUDO,
    efeitoConfig = {
        tipo = "area_ground",
        centro = "jogador",
        raio = 2,
        percentual = 0.2,
        magicEffect = CONST_ME_HITAREA,
        knockback = true
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 7,
    categoria = "aoe",
    condicao = "cercado",
    condicaoFocoMin = 60
}

HABILIDADES[15013] = {
    nome = "Carga de Escudo",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 13,
    descricaoEfeito = "Avança contra o alvo, atordoando-o e causando dano.",
    cor = COR.DOM_ESCUDO,
    efeitoConfig = {
        tipo = "knockback",
        comDano = true,
        percentual = 0.45,
        magicEffect = CONST_ME_HITAREA
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 8,
    categoria = "single",
    condicao = "distancia4",
    condicaoFocoMin = 70
}

HABILIDADES[15014] = {
    nome = "Muralha de Escudos",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 15,
    descricaoEfeito = "Concede redução de dano a aliados próximos por 3 segundos.",
    cor = COR.DOM_ESCUDO,
    efeitoConfig = {
        tipo = "defesa_barreira",
        factor = 0.5,
        durationMs = 3000
    },
    gatilho = "onBlock",
    cooldown = 20,
    prioridade = 6,
    categoria = "defense"
}

HABILIDADES[15015] = {
    nome = "Contra-ataque em Área",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 8,
    descricaoEfeito = "Ao bloquear, causa dano a todos os inimigos ao redor.",
    cor = COR.DOM_ESCUDO,
    efeitoConfig = {
        tipo = "defesa_contra_ataque",
        percentual = 0.35,
        magicEffect = CONST_ME_HITAREA
    },
    gatilho = "onBlock",
    cooldown = 12,
    prioridade = 6,
    categoria = "defense",
    condicao = "inimigosProximos"
}

HABILIDADES[15016] = {
    nome = "Investida Brutal",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 14,
    descricaoEfeito = "Causa dano massivo e empurra o alvo se ele estiver isolado.",
    cor = COR.DOM_ESCUDO,
    efeitoConfig = {
        tipo = "knockback",
        comDano = true,
        percentual = 0.6,
        magicEffect = CONST_ME_HITAREA
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 8,
    categoria = "single",
    condicao = "alvoIsolado",
    condicaoFocoMin = 80
}

HABILIDADES[15017] = {
    nome = "Golpe de Oportunidade",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 10,
    descricaoEfeito = "Causa dano extra se o alvo estiver atordoado.",
    cor = COR.DOM_ESCUDO,
    efeitoConfig = {
        tipo = "dano_extra",
        percentual = 0.5,
        magicEffect = CONST_ME_HITAREA
    },
    gatilho = "onAttack",
    cooldown = 12,
    prioridade = 6,
    categoria = "single"
}

-- ============================================================
-- GATILHOS DE CONDIÇÃO/DEFESA (5)
-- ============================================================
HABILIDADES[15030] = {
    nome = "Atordoar",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 7,
    descricaoEfeito = "Golpe com escudo que atordoa o alvo.",
    cor = COR.DOM_ESCUDO,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_DAZZLED,
        duration = 2000,
        comDano = true,
        percentual = 0.2,
        magicEffect = CONST_ME_STUN
    },
    gatilho = "onAttack",
    cooldown = 14,
    prioridade = 6,
    categoria = "debuff",
    condicaoFocoMin = 30
}

HABILIDADES[15031] = {
    nome = "Quebrar Postura",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 12,
    descricaoEfeito = "Reduz a velocidade de ataque do alvo por 3 segundos.",
    cor = COR.DOM_ESCUDO,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_PARALYZE,
        duration = 3000,
        comDano = true,
        percentual = 0.3,
        magicEffect = CONST_ME_HITAREA
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 6,
    categoria = "debuff",
    condicaoFocoMin = 40
}

HABILIDADES[15032] = {
    nome = "Defesa Inabalável",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 5,
    descricaoEfeito = "Ao receber dano, reduz o próximo dano em 50% por 2s.",
    cor = COR.DOM_ESCUDO,
    efeitoConfig = {
        tipo = "defesa_barreira",
        factor = 0.5,
        durationMs = 2000
    },
    gatilho = "onReceiveDamage",
    cooldown = 18,
    prioridade = 5,
    categoria = "defense"
}

HABILIDADES[15033] = {
    nome = "Revide",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 9,
    descricaoEfeito = "Ao bloquear, recupera vida e causa dano ao atacante.",
    cor = COR.DOM_ESCUDO,
    efeitoConfig = {
        tipo = "defesa_cura",
        percentual = 0.05,
        reflect = true,
        reflectPercentual = 0.3
    },
    gatilho = "onBlock",
    cooldown = 15,
    prioridade = 6,
    categoria = "defense"
}

HABILIDADES[15034] = {
    nome = "Grito de Guerra",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 16,
    descricaoEfeito = "Amedronta todos os inimigos num raio de 3 tiles.",
    cor = COR.DOM_ESCUDO,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_CURSED,
        duration = 3000,
        comDano = false,
        magicEffect = CONST_ME_SOUND_RED
    },
    gatilho = "onAttack",
    cooldown = 22,
    prioridade = 7,
    categoria = "debuff",
    condicao = "cercado",
    condicaoFocoMin = 70
}

-- ============================================================
-- GATILHOS DE SINERGIA (8)
-- ============================================================
HABILIDADES[15040] = {
    nome = "Escudo e Espada",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 10,
    descricaoEfeito = "Aumenta o dano do próximo ataque com espada em 20%. Requer Espadas.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "dano_extra",
        percentual = 0.5,
        magicEffect = CONST_ME_HITAREA,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {10, 100, 101},
    efeitosSecundarios = {
        [10] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 10)
            if nivel >= 10 then
                applyDamageBoost(p, 20, 1)  -- próximo ataque +20%
            end
        end
    },
    gatilho = "onBlock",
    cooldown = 16,
    prioridade = 7,
    categoria = "sinergia",
    condicaoFocoMin = 40
}

HABILIDADES[15041] = {
    nome = "Escudo e Machado",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 12,
    descricaoEfeito = "Causa sangramento ao bloquear. Requer Machados.",
    cor = COR.DOM_COMBATE_IMPACTO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "condicao",
        conditionType = CONDITION_BLEEDING,
        duration = 4000,
        periodicDamage = 12,
        comDano = true,
        percentual = 0.4,
        magicEffect = CONST_ME_DRAWBLOOD,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {11, 110, 111},
    efeitosSecundarios = {
        [11] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 11)
            if nivel >= 10 then
                local bleed = 12 + nivel * 2
                local cond = Condition(CONDITION_BLEEDING, CONDITIONID_COMBAT, 4000)
                cond:setParameter(CONDITION_PARAM_PERIODICDAMAGE, bleed)
                cond:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
                t:addCondition(cond)
            end
        end
    },
    gatilho = "onBlock",
    cooldown = 16,
    prioridade = 7,
    categoria = "sinergia",
    condicaoFocoMin = 40
}

HABILIDADES[15042] = {
    nome = "Escudo e Precisão",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 14,
    descricaoEfeito = "Ao bloquear, ganha furtividade por 2s. Requer Precisão.",
    cor = COR.DOM_COMBATE_PRECISAO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "buff_speed",
        multiplier = 0.5,
        durationMs = 2000,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {13, 120, 121},
    efeitosSecundarios = {
        [13] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 13)
            if nivel >= 10 then
                p:setStealth(true)
                addEvent(function()
                    local pl = Player(p:getId())
                    if pl then pl:setStealth(false) end
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

HABILIDADES[15043] = {
    nome = "Escudo e Fogo",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 16,
    descricaoEfeito = "Ao bloquear, cria uma explosão de fogo. Requer Fogo.",
    cor = COR.ELEM_FOGO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "area_ground",
        centro = "jogador",
        raio = 1,
        percentual = 0.4,
        magicEffect = CONST_ME_FIREAREA,
        nivelMinSecundario = 12
    },
    sinergiaDominios = {23},
    efeitosSecundarios = {
        [23] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 23)
            if nivel >= 12 then
                local cond = Condition(CONDITION_FIRE, CONDITIONID_COMBAT, 3000)
                cond:setParameter(CONDITION_PARAM_PERIODICDAMAGE, 10 + nivel)
                cond:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
                t:addCondition(cond)
            end
        end
    },
    gatilho = "onBlock",
    cooldown = 18,
    prioridade = 8,
    categoria = "sinergia",
    condicaoFocoMin = 60
}

HABILIDADES[15044] = {
    nome = "Escudo e Gelo",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 18,
    descricaoEfeito = "Ao bloquear, congela o atacante. Requer Gelo.",
    cor = COR.ELEM_GELO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "condicao",
        conditionType = CONDITION_PARALYZE,
        duration = 2500,
        comDano = true,
        percentual = 0.3,
        magicEffect = CONST_ME_ICEAREA,
        nivelMinSecundario = 12
    },
    sinergiaDominios = {24},
    efeitosSecundarios = {
        [24] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 24)
            if nivel >= 12 then
                local cond = Condition(CONDITION_PARALYZE, CONDITIONID_COMBAT, 2500 + nivel * 100)
                t:addCondition(cond)
            end
        end
    },
    gatilho = "onBlock",
    cooldown = 20,
    prioridade = 8,
    categoria = "sinergia",
    condicaoFocoMin = 70
}

HABILIDADES[15045] = {
    nome = "Escudo e Energia",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 20,
    descricaoEfeito = "Ao bloquear, descarrega energia em cadeia. Requer Energia.",
    cor = COR.ELEM_RAIO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "corrente",
        percentual = 0.5,
        raio = 2,
        magicEffect = CONST_ME_ENERGYHIT,
        nivelMinSecundario = 15
    },
    sinergiaDominios = {26},
    efeitosSecundarios = {
        [26] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 26)
            if nivel >= 15 then
                -- Raio duplo: 30% de chance
                if math.random(100) <= 30 then
                    local extra = math.floor(d * (0.6 + nivel * 0.03))
                    doTargetCombatHealth(p, t, COMBAT_ENERGYDAMAGE, -extra, -extra, CONST_ME_ENERGYHIT)
                end
            end
        end
    },
    gatilho = "onBlock",
    cooldown = 22,
    prioridade = 9,
    categoria = "sinergia",
    condicaoFocoMin = 80
}

HABILIDADES[15046] = {
    nome = "Defesa Arcana",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 15,
    descricaoEfeito = "Ao bloquear, ganha um escudo arcano que absorve dano. Requer Runologia.",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "defesa_barreira",
        factor = 0.4,
        durationMs = 3000,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {22},
    efeitosSecundarios = {
        [22] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 22)
            if nivel >= 10 then
                local shield = p:getMaxHealth() * 0.1 * nivel
                -- Aqui poderia usar um escudo de absorção, mas simplificamos com redução extra
                p:setDamageTakenModifier(0.5)
                addEvent(function()
                    local pl = Player(p:getId())
                    if pl then pl:setDamageTakenModifier(1.0) end
                end, 3000)
            end
        end
    },
    gatilho = "onBlock",
    cooldown = 20,
    prioridade = 8,
    categoria = "sinergia",
    condicaoFocoMin = 60
}

HABILIDADES[15047] = {
    nome = "Protetor dos Fracos",
    tipo = "gatilho",
    dominio = {15},
    nivelMin = 12,
    descricaoEfeito = "Aliados próximos recebem cura quando você bloqueia. Requer Artes Marciais.",
    cor = COR.DOM_COMBATE_DESARMADO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "defesa_cura",
        percentual = 0.03,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {14},
    efeitosSecundarios = {
        [14] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 14)
            if nivel >= 10 then
                local party = p:getParty()
                if party then
                    local members = party:getMembers()
                    for _, member in ipairs(members) do
                        if member:getPosition():getDistance(p:getPosition()) <= 3 then
                            member:addHealth(p:getMaxHealth() * 0.02)
                        end
                    end
                end
            end
        end
    },
    gatilho = "onBlock",
    cooldown = 18,
    prioridade = 6,
    categoria = "sinergia"
}

-- ============================================================
-- TRANSFORMAÇÕES (5)
-- ============================================================
HABILIDADES[15050] = {
    nome = "Escudo Protetor",
    tipo = "transformacao",
    dominio = {15},
    nivelMin = 8,
    descricaoEfeito = "Lampejo: o bloqueio reduz 15% a mais de dano.",
    cor = COR.DOM_ESCUDO,
    efeito = function(player)
        player:setCombatModifier("shield_block_power", 15)
    end,
    desfazer = function(player)
        player:setCombatModifier("shield_block_power", 0)
    end
}

HABILIDADES[15051] = {
    nome = "Muralha Sólida",
    tipo = "transformacao",
    dominio = {15},
    nivelMin = 12,
    descricaoEfeito = "Vínculo: regenera 1% da vida máxima por segundo e a defesa aumenta 20%.",
    cor = COR.DOM_ESCUDO,
    efeito = function(player)
        player:setHealthRegenModifier(2.0)
        player:setDamageTakenModifier(0.8)
    end,
    desfazer = function(player)
        aplicarPostura(player, player:getFightMode())
    end
}

HABILIDADES[15052] = {
    nome = "Bastião Eterno",
    tipo = "transformacao",
    dominio = {15},
    nivelMin = 16,
    descricaoEfeito = "Maestria: a cada 10s, ganha um escudo que absorve 15% da vida máxima.",
    cor = COR.DOM_ESCUDO,
    efeito = function(player)
        player:setCombatModifier("shield_absorption", 15)
        -- Lógica de escudo seria implementada via think ou evento
    end,
    desfazer = function(player)
        player:setCombatModifier("shield_absorption", 0)
    end
}

HABILIDADES[15053] = {
    nome = "Forma de Aço",
    tipo = "transformacao",
    dominio = {15},
    nivelMin = 20,
    descricaoEfeito = "Transformação suprema: por 8 segundos, toda a defesa é dobrada e você reflete 30% do dano recebido.",
    cor = COR.DOM_ESCUDO,
    efeito = function(player)
        player:setDamageTakenModifier(0.5)
        player:setCombatModifier("shield_reflect", 30)
    end,
    desfazer = function(player)
        player:setDamageTakenModifier(1.0)
        player:setCombatModifier("shield_reflect", 0)
    end
}

HABILIDADES[15054] = {
    nome = "Reflexo Protetor",
    tipo = "transformacao",
    dominio = {15},
    nivelMin = 14,
    descricaoEfeito = "Ao ativar, seu próximo bloqueio causa dano massivo ao atacante.",
    cor = COR.DOM_ESCUDO,
    efeito = function(player)
        applyNextAttackCondition(player, CONDITION_BLEEDING, 3000, 0)  -- placeholder, será tratado no PosturaDmg
    end,
    desfazer = function(player) end
}

print("DEBUG: habilidades_escudo.lua carregado.")