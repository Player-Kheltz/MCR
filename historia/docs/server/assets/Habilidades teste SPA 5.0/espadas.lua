--[[
    Projeto MCR ? SPA ? Habilidades de Lâminas (10)
    Perfil: Secundário (34 habilidades + Traço Inerente)
    Arquitetura modular v4.6
--]]

-- ============================================================
-- TRAÇO INERENTE: Afinidade com o Aço
-- ============================================================
-- Nível 5: Ataques com espadas têm 5% de chance de ignorar 10% da armadura.
-- Nível 10: A chance sobe para 10% e a ignoração para 15%.
-- Nível 15: Golpes consecutivos com a mesma arma aumentam o dano em 2% (máx 10%).
-- Nível 20: Todos os ataques com lâminas causam sangramento acumulativo (stacka até 3x).

-- ============================================================
-- ÁRVORE I (nível 5): Passiva de Identidade
-- ============================================================
HABILIDADES[1001] = {
    nome = "Mestre das Lâminas",
    tipo = "passiva",
    dominio = {10},
    nivelMin = 5,
    descricaoEfeito = "Aumenta o dano de todas as espadas em 5%.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        player:setCombatModifier("sword_damage", 5)
    end
}

-- ============================================================
-- ÁRVORE II (nível 10): Passiva de Expansão ? Sinergia com Filhos
-- ============================================================
HABILIDADES[1002] = {
    nome = "Sinergia das Lâminas",
    tipo = "passiva",
    dominio = {10},
    nivelMin = 10,
    descricaoEfeito = "Concede bónus adicionais baseados nos domínios filhos.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        local nivelLeves = getNivelEfetivo(player, 100)
        local nivelPesadas = getNivelEfetivo(player, 101)
        if nivelLeves >= 10 then
            player:setCombatModifier("sword_speed", 0.05)
        end
        if nivelPesadas >= 10 then
            player:setCombatModifier("sword_knockback", 10)
        end
    end
}

-- ============================================================
-- ÁRVORE III (nível 15): Gatilho de Assinatura ? Dança das Lâminas
-- ============================================================
HABILIDADES[1003] = {
    nome = "Dança das Lâminas",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 15,
    descricaoEfeito = "Desfere 3 golpes em sequência, cada um causando 40% do dano. Bónus adicionais conforme filhos.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "rajada",
        percentual = 0.4,
        numProjeteis = 3,
        intervaloMs = 300,
        nivelMinSecundario = 5
    },
    sinergiaDominios = {100, 101},
    efeitosSecundarios = {
        [100] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 100)
            if nivel >= 5 then
                local extra = math.floor(d * 0.1)
                golpeCorpoACorpo(p, t, extra, CONST_ME_DRAWBLOOD)
            end
        end,
        [101] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 101)
            if nivel >= 5 then
                empurrarAlvo(p, t)
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 8,
    categoria = "sinergia",
    condicaoFocoMin = 50,
    posturaMod = {
        [1] = { chanceMult = 1.3 },
        [2] = { chanceMult = 1.0 },
        [3] = { chanceMult = 0.7 }
    }
}

-- ============================================================
-- ÁRVORE IV (nível 20): Passiva de Maestria
-- ============================================================
HABILIDADES[1004] = {
    nome = "Maestria em Lâminas",
    tipo = "passiva",
    dominio = {10},
    nivelMin = 20,
    descricaoEfeito = "Maestria: todas as lâminas ganham 15% de dano extra e chance de sangramento acumulativo.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        player:setCombatModifier("sword_damage", (player:getCombatModifier("sword_damage") or 0) + 15)
        player:setCombatModifier("sword_accumulating_bleed", 1)
    end
}

-- ============================================================
-- PASSIVAS DE ATRIBUTO (5 restantes)
-- ============================================================
HABILIDADES[1005] = {
    nome = "Esgrima Natural",
    tipo = "passiva",
    dominio = {10},
    nivelMin = 2,
    descricaoEfeito = "Aumenta a velocidade de ataque em 0.5% por nível de Lâminas.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 10)
        player:setAttackSpeedModifier(1.0 - nivel * 0.005)
    end
}

HABILIDADES[1006] = {
    nome = "Fio Implacável",
    tipo = "passiva",
    dominio = {10},
    nivelMin = 6,
    descricaoEfeito = "Aumenta a chance de sangramento em 1% por nível de Lâminas.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 10)
        player:setCombatModifier("sword_bleed_chance", nivel)
    end
}

HABILIDADES[1007] = {
    nome = "Lâmina Precisa",
    tipo = "passiva",
    dominio = {10},
    nivelMin = 8,
    descricaoEfeito = "Aumenta o dano crítico em 1% por nível de Lâminas.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 10)
        player:setCombatModifier("sword_crit_power", nivel)
    end
}

HABILIDADES[1008] = {
    nome = "Reflexos do Aço",
    tipo = "passiva",
    dominio = {10},
    nivelMin = 4,
    descricaoEfeito = "Aumenta a defesa em 0.5% por nível de Lâminas.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        local nivel = getNivelEfetivo(player, 10)
        player:setDamageTakenModifier(1.0 - nivel * 0.005)
    end
}

HABILIDADES[1009] = {
    nome = "Dança da Lâmina",
    tipo = "passiva",
    dominio = {10},
    nivelMin = 12,
    descricaoEfeito = "Aumenta a velocidade de movimento em 1% por nível de Lâminas.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player) end  -- gerido por recalcularVelocidade
}

-- ============================================================
-- GATILHOS DE COMBATE (8)
-- ============================================================
HABILIDADES[1010] = {
    nome = "Corte Duplo",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 6,
    descricaoEfeito = "Desfere dois golpes rápidos.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "rajada",
        percentual = 0.35,
        numProjeteis = 2,
        intervaloMs = 300
    },
    gatilho = "onAttack",
    cooldown = 12,
    prioridade = 7,
    categoria = "single",
    condicaoFocoMin = 30
}

HABILIDADES[1011] = {
    nome = "Lâmina em Fúria",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 8,
    descricaoEfeito = "Acelera a velocidade de ataque por 1.5s.",
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

HABILIDADES[1012] = {
    nome = "Golpe em Arco",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 10,
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
    condicao = "cercado"
}

HABILIDADES[1013] = {
    nome = "Investida Cortante",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 12,
    descricaoEfeito = "Avança contra o alvo e causa dano extra.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "knockback",
        comDano = true,
        percentual = 0.4,
        magicEffect = CONST_ME_HITAREA
    },
    gatilho = "onAttack",
    cooldown = 14,
    prioridade = 7,
    categoria = "single",
    condicao = "distancia4"
}

HABILIDADES[1014] = {
    nome = "Chuva de Lâminas",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 14,
    descricaoEfeito = "Dispara três projéteis cortantes em sequência.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "rajada",
        percentual = 0.35,
        numProjeteis = 3,
        intervaloMs = 250
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 8,
    categoria = "single",
    condicaoFocoMin = 70
}

HABILIDADES[1015] = {
    nome = "Contra-Ataque com Lâmina",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 7,
    descricaoEfeito = "Ao bloquear, contra-ataca todos ao redor.",
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
    condicao = "inimigosProximos"
}

HABILIDADES[1016] = {
    nome = "Execução do Gladiador",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 16,
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

HABILIDADES[1017] = {
    nome = "Precisão do Mestre",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 9,
    descricaoEfeito = "Causa dano extra ignorando parte da armadura.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "dano_extra",
        percentual = 0.4,
        magicEffect = CONST_ME_DRAWBLOOD
    },
    gatilho = "onAttack",
    cooldown = 10,
    prioridade = 6,
    categoria = "single"
}

-- ============================================================
-- GATILHOS DE CONDIÇÃO/DEFESA (5)
-- ============================================================
HABILIDADES[1020] = {
    nome = "Dilacerar",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 5,
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

HABILIDADES[1021] = {
    nome = "Corte no Tendão",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 10,
    descricaoEfeito = "Causa lentidão e sangramento.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_PARALYZE,
        duration = 2500,
        periodicDamage = 8,
        comDano = true,
        percentual = 0.35,
        magicEffect = CONST_ME_DRAWBLOOD
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 6,
    categoria = "debuff",
    condicao = "alvoIsolado",
    condicaoFocoMin = 40
}

HABILIDADES[1022] = {
    nome = "Barreira de Lâminas",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 8,
    descricaoEfeito = "Reduz o dano recebido por 2s.",
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

HABILIDADES[1023] = {
    nome = "Sede de Sangue",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 12,
    descricaoEfeito = "Roubo de vida por 4s.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "life_leech",
        leechPercent = 15,
        durationSec = 4
    },
    gatilho = "onAttack",
    cooldown = 20,
    prioridade = 5,
    categoria = "buff",
    condicaoFocoMin = 30
}

HABILIDADES[1024] = {
    nome = "Atordoar com Cabo",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 14,
    descricaoEfeito = "Atordoa o alvo com o cabo da espada.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeitoConfig = {
        tipo = "condicao",
        conditionType = CONDITION_DAZZLED,
        duration = 2000,
        comDano = true,
        percentual = 0.2,
        magicEffect = CONST_ME_STUN
    },
    gatilho = "onAttack",
    cooldown = 16,
    prioridade = 6,
    categoria = "debuff",
    condicaoFocoMin = 40
}

-- ============================================================
-- GATILHOS DE SINERGIA (8)
-- ============================================================
HABILIDADES[1030] = {
    nome = "Lâmina Flamejante",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 10,
    descricaoEfeito = "A lâmina incendeia o alvo. Requer Fogo.",
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

HABILIDADES[1031] = {
    nome = "Lâmina Gélida",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 12,
    descricaoEfeito = "A lâmina congela o alvo. Requer Gelo.",
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

HABILIDADES[1032] = {
    nome = "Lâmina Sombria",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 16,
    descricaoEfeito = "A lâmina amaldiçoa o alvo. Requer Espectro.",
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

HABILIDADES[1033] = {
    nome = "Escudo e Espada",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 14,
    descricaoEfeito = "Ao bloquear, o próximo ataque causa dano extra. Requer Escudo.",
    cor = COR.DOM_ESCUDO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "dano_extra",
        percentual = 0.5,
        magicEffect = CONST_ME_HITAREA,
        nivelMinSecundario = 10
    },
    sinergiaDominios = {15},
    efeitosSecundarios = {
        [15] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 15)
            if nivel >= 10 then
                applyDamageBoost(p, 20, 1)
            end
        end
    },
    gatilho = "onBlock",
    cooldown = 16,
    prioridade = 7,
    categoria = "sinergia",
    condicaoFocoMin = 40
}

HABILIDADES[1034] = {
    nome = "Lâmina Terrena",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 15,
    descricaoEfeito = "A lâmina causa knockdown. Requer Terra.",
    cor = COR.ELEM_TERRA,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "knockback",
        comDano = true,
        percentual = 0.45,
        magicEffect = CONST_ME_GROUNDSHAKER,
        nivelMinSecundario = 12
    },
    sinergiaDominios = {25},
    efeitosSecundarios = {
        [25] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 25)
            if nivel >= 12 then
                local cond = Condition(CONDITION_PARALYZE, CONDITIONID_COMBAT, 1500)
                t:addCondition(cond)
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 7,
    categoria = "sinergia",
    condicaoFocoMin = 50
}

HABILIDADES[1035] = {
    nome = "Lâmina Energizada",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 18,
    descricaoEfeito = "A lâmina descarrega energia, causando paralisia. Requer Energia.",
    cor = COR.ELEM_RAIO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "condicao",
        conditionType = CONDITION_PARALYZE,
        duration = 2500,
        comDano = true,
        percentual = 0.5,
        magicEffect = CONST_ME_ENERGYHIT,
        nivelMinSecundario = 15
    },
    sinergiaDominios = {26},
    efeitosSecundarios = {
        [26] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 26)
            if nivel >= 15 then
                if math.random(100) <= 25 then
                    local extra = math.floor(d * 0.5)
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

HABILIDADES[1036] = {
    nome = "Lâmina Sagrada",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 17,
    descricaoEfeito = "A lâmina causa dano sagrado extra. Requer Sagrado.",
    cor = COR.ELEM_SAGRADO,
    efeitoConfig = {
        tipo = "sinergia",
        efeitoBase = "dano_extra",
        percentual = 0.5,
        magicEffect = CONST_ME_HOLYAREA,
        nivelMinSecundario = 12
    },
    sinergiaDominios = {200},
    efeitosSecundarios = {
        [200] = function(p, t, d)
            local nivel = getNivelEfetivo(p, 200)
            if nivel >= 12 then
                p:addHealth(math.floor(d * 0.1))
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 7,
    categoria = "sinergia",
    condicaoFocoMin = 50
}

HABILIDADES[1037] = {
    nome = "Lâmina Rúnica",
    tipo = "gatilho",
    dominio = {10},
    nivelMin = 13,
    descricaoEfeito = "A lâmina ativa uma runa de dano. Requer Runologia.",
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
                local extra = math.floor(d * nivel * 0.02)
                doTargetCombatHealth(p, t, COMBAT_ENERGYDAMAGE, -extra, -extra, CONST_ME_ENERGYHIT)
            end
        end
    },
    gatilho = "onAttack",
    cooldown = 18,
    prioridade = 7,
    categoria = "sinergia",
    condicaoFocoMin = 40
}

-- ============================================================
-- TRANSFORMAÇÕES (5)
-- ============================================================
HABILIDADES[1040] = {
    nome = "Dança da Faísca",
    tipo = "transformacao",
    dominio = {10},
    nivelMin = 8,
    descricaoEfeito = "Lampejo: a velocidade de ataque aumenta 15%.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        player:setAttackSpeedModifier(0.85)
    end,
    desfazer = function(player)
        aplicarPostura(player, player:getFightMode())
    end
}

HABILIDADES[1041] = {
    nome = "Sinfonia de Aço",
    tipo = "transformacao",
    dominio = {10},
    nivelMin = 12,
    descricaoEfeito = "Vínculo: o dano com lâminas aumenta 20% e lâminas fantasmagóricas orbitam o conjurador.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        local atual = player:getCombatModifier("sword_damage") or 0
        player:setCombatModifier("sword_damage", atual + 20)
    end,
    desfazer = function(player)
        local atual = player:getCombatModifier("sword_damage") or 20
        player:setCombatModifier("sword_damage", atual - 20)
    end
}

HABILIDADES[1042] = {
    nome = "Lâmina Imortal",
    tipo = "transformacao",
    dominio = {10},
    nivelMin = 16,
    descricaoEfeito = "Maestria: o dano crítico aumenta 30% e o Vínculo é permanente.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        player:setCombatModifier("sword_crit_power", (player:getCombatModifier("sword_crit_power") or 0) + 30)
    end,
    desfazer = function(player)
        player:setCombatModifier("sword_crit_power", (player:getCombatModifier("sword_crit_power") or 30) - 30)
    end
}

HABILIDADES[1043] = {
    nome = "Forma de Aço",
    tipo = "transformacao",
    dominio = {10},
    nivelMin = 20,
    descricaoEfeito = "Transformação suprema: por 8s, todos os ataques causam sangramento e você reflete 20% do dano.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        player:setCombatModifier("sword_reflect", 20)
        player:setCombatModifier("sword_bleed_all", 1)
    end,
    desfazer = function(player)
        player:setCombatModifier("sword_reflect", 0)
        player:setCombatModifier("sword_bleed_all", 0)
    end
}

HABILIDADES[1044] = {
    nome = "Lâmina Vorpal",
    tipo = "transformacao",
    dominio = {10},
    nivelMin = 14,
    descricaoEfeito = "Seu próximo ataque ignora completamente a armadura do alvo.",
    cor = COR.DOM_COMBATE_LAMINAS,
    efeito = function(player)
        applyNextAttackCondition(player, CONDITION_BLEEDING, 3000, 0)
    end,
    desfazer = function(player) end
}

print("DEBUG: habilidades_laminas.lua carregado.")