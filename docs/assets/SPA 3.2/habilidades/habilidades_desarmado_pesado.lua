--[[
    Projeto MCR ? Habilidades de Desarmado Pesado (v1.1)
    Especialidade: Desarmado Pesado (131)
    Temas: Chi (Harmony), Virtude da Justiça, Corpo como Arma, Brutalidade Imparável
    Corrigido: Virtue_t como tabela Lua, Harmony via storage
--]]

-- ============================================================
-- ÁRVORE I-IV: DESARMADO PESADO (131)
-- ============================================================

-- I (5) ? Passiva: Virtude da Justiça
HABILIDADES[13101] = {
    nome = "Virtude da Justiça",
    tipo = "passiva",
    dominio = {131},
    nivelMin = 5,
    efeito = function(player)
        player:setVirtue(Virtue_t.Justice)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(131))
        player:setStorageValue(97950, math.floor(nivel * 1.5)) -- % dano extra contra alvos com vida baixa
    end,
    descricaoEfeito = "causa mais dano a inimigos feridos",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="A justiça te guia.", [2]="Golpes precisos.", [3]="A balança pende a teu favor."}
}

-- II (10) ? Passiva: Corpo como Arma
HABILIDADES[13102] = {
    nome = "Corpo como Arma",
    tipo = "passiva",
    dominio = {131},
    nivelMin = 10,
    efeito = function(player)
        player:fillHarmony()
        player:setStorageValue(STORAGE.HARMONY, 5) -- Chi máximo
        player:setStorageValue(97951, 1) -- flag: bloqueios causam dano ao atacante
    end,
    descricaoEfeito = "bloquear um ataque causa dano ao inimigo",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Teu corpo é a arma.", [2]="Cada defesa é um ataque.", [3]="O inimigo que te toca sofre."}
}

-- III (15) ? Gatilho: Palma do Dragão (consome Chi)
HABILIDADES[13103] = {
    nome = "Palma do Dragão",
    tipo = "gatilho",
    dominio = {131},
    nivelMin = 15,
    gatilho = "onAttack",
    condicao = "5Golpes",
    chanceBase = 100,
    buffType = "custom",
    efeito = function(player, target, damage)
        local harmony = player:getStorageValue(STORAGE.HARMONY) or 0
        if harmony < 5 then return end
        -- Consome 5 pontos de Chi
        player:setStorageValue(STORAGE.HARMONY, 0)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(131))
        local bonusDmg = math.floor(damage * (1.0 + nivel * 0.1))
        doTargetCombatHealth(player, target, COMBAT_PHYSICALDAMAGE, bonusDmg, bonusDmg, CONST_ME_HITAREA)
        local dir = Position(player:getPosition()):getDirectionTo(target:getPosition())
        if dir then target:knockback(dir) end
    end,
    efeitoVisual = function(player, target) target:getPosition():sendMagicEffect(CONST_ME_HITAREA) end,
    descricaoEfeito = "gasta 5 Chi para um golpe massivo com knockback",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="A palma do dragão atinge o inimigo!", [2]="Impacto devastador.", [3]="O Chi explode."},
    posturaMod = {[1]={chanceMult=1.2}, [2]={}, [3]={chanceMult=0.8}}
}

-- IV (20) ? Passiva: Brutalidade Imparável
HABILIDADES[13104] = {
    nome = "Brutalidade Imparável",
    tipo = "passiva",
    dominio = {131},
    nivelMin = 20,
    efeito = function(player)
        player:setSerene(true)
        player:setStorageValue(97952, 1) -- flag: Chi máximo causa ataques em área
    end,
    descricaoEfeito = "Chi máximo ativa Serenidade e causa dano em área",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="És imparável!", [2]="Brutalidade pura.", [3]="Ninguém te detém."}
}

-- ============================================================
-- COMPLEMENTARES ? DESARMADO PESADO (131)
-- ============================================================

-- Gatilho 1: Impacto Brutal (nível 7)
HABILIDADES[13110] = {
    nome = "Impacto Brutal",
    tipo = "gatilho",
    dominio = {131},
    nivelMin = 7,
    gatilho = "onAttack",
    chanceBase = 12,
    chanceLampejo = 20,
    chanceVinculo = 28,
    buffType = "custom",
    efeito = function(player, target, damage)
        local dir = Position(player:getPosition()):getDirectionTo(target:getPosition())
        if dir then target:knockback(dir) end
    end,
    efeitoVisual = function(player, target) target:getPosition():sendMagicEffect(CONST_ME_HITAREA) end,
    descricaoEfeito = "empurra o inimigo com força bruta",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O impacto arranca o inimigo do chão!", [2]="Força bruta.", [3]="Nada resiste."},
    posturaMod = {[1]={chanceMult=1.4}, [2]={}, [3]={chanceMult=0.6}}
}

-- Gatilho 2: Dreno de Chi (nível 9)
HABILIDADES[13111] = {
    nome = "Dreno de Chi",
    tipo = "gatilho",
    dominio = {131},
    nivelMin = 9,
    gatilho = "onAttack",
    chanceBase = 10,
    chanceLampejo = 18,
    chanceVinculo = 25,
    buffType = "lifeLeech",
    leechPercent = 10,
    durationSec = 4,
    descricaoEfeito = "roubo de vida por 4 segundos",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O Chi do inimigo flui para ti!", [2]="Energia drenada.", [3]="A vida se renova."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.7}}
}

-- Gatilho 3: Bloqueio Devastador (nível 11)
HABILIDADES[13112] = {
    nome = "Bloqueio Devastador",
    tipo = "gatilho",
    dominio = {131},
    nivelMin = 11,
    gatilho = "onBlock",
    chanceBase = 15,
    chanceLampejo = 25,
    chanceVinculo = 35,
    buffType = "custom",
    efeito = function(player, target)
        local dmg = math.floor(target:getMaxHealth() * 0.05)
        doTargetCombatHealth(player, target, COMBAT_PHYSICALDAMAGE, dmg, dmg, CONST_ME_HITAREA)
    end,
    efeitoVisual = function(player, target) target:getPosition():sendMagicEffect(CONST_ME_HITAREA) end,
    descricaoEfeito = "o bloqueio causa dano ao atacante",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O teu bloqueio fere o inimigo!", [2]="Defesa ofensiva.", [3]="Contra?ataque natural."},
    posturaMod = {[1]={chanceMult=0.7}, [2]={}, [3]={chanceMult=1.5}}
}

-- Gatilho 4: Terremoto (nível 14)
HABILIDADES[13113] = {
    nome = "Terremoto",
    tipo = "gatilho",
    dominio = {131},
    nivelMin = 14,
    gatilho = "onAttack",
    condicao = "cercado",
    chanceBase = 10,
    chanceLampejo = 18,
    chanceVinculo = 25,
    buffType = "custom",
    efeito = function(player, target, damage)
        local pos = player:getPosition()
        for _, c in ipairs(getCreaturesInArea(pos, 3, 3)) do
            if c:isMonster() and c ~= target then
                doTargetCombatHealth(player, c, COMBAT_PHYSICALDAMAGE, math.floor(damage * 0.5), math.floor(damage * 0.5), CONST_ME_HITAREA)
            end
        end
    end,
    efeitoVisual = function(player, target) player:getPosition():sendMagicEffect(CONST_ME_GROUNDSHAKER) end,
    descricaoEfeito = "causa dano em área ao redor",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O chão estremece com a tua força!", [2]="Terremoto.", [3]="Ninguém fica de pé."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.7}}
}

-- Gatilho 5: Executar (nível 16)
HABILIDADES[13114] = {
    nome = "Executar",
    tipo = "gatilho",
    dominio = {131},
    nivelMin = 16,
    gatilho = "onAttack",
    condicao = "vidaBaixa",
    chanceBase = 20,
    chanceLampejo = 30,
    chanceVinculo = 40,
    buffType = "custom",
    efeito = function(player, target, damage)
        local bonusDmg = math.floor(damage * 0.5)
        doTargetCombatHealth(player, target, COMBAT_PHYSICALDAMAGE, bonusDmg, bonusDmg, CONST_ME_HITAREA)
    end,
    efeitoVisual = function(player, target) target:getPosition():sendMagicEffect(CONST_ME_HITAREA) end,
    descricaoEfeito = "causa dano extra a alvos com pouca vida",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O golpe final!", [2]="Execução impiedosa.", [3]="A morte é certa."},
    posturaMod = {[1]={chanceMult=1.2}, [2]={}, [3]={chanceMult=0.8}}
}

-- Gatilho 6: Fúria do Dragão (nível 18)
HABILIDADES[13115] = {
    nome = "Fúria do Dragão",
    tipo = "gatilho",
    dominio = {131},
    nivelMin = 18,
    gatilho = "onAttack",
    chanceBase = 5,
    chanceLampejo = 10,
    chanceVinculo = 16,
    buffType = "damageBoost",
    percentExtra = 30,
    buffHits = 3,
    descricaoEfeito = "aumenta o dano em 30% por 3 ataques",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="A fúria do dragão te consome!", [2]="Poder incalculável.", [3]="Força ancestral."},
    posturaMod = {[1]={chanceMult=1.4}, [2]={}, [3]={chanceMult=0.4}}
}

-- Gatilho 7: Colisão de Chi (nível 19)
HABILIDADES[13116] = {
    nome = "Colisão de Chi",
    tipo = "gatilho",
    dominio = {131},
    nivelMin = 19,
    gatilho = "onAttack",
    chanceBase = 8,
    chanceLampejo = 14,
    chanceVinculo = 20,
    buffType = "custom",
    efeito = function(player, target, damage)
        local pos = target:getPosition()
        for _, c in ipairs(getCreaturesInArea(pos, 1, 1)) do
            if c:isMonster() and c ~= target then
                doTargetCombatHealth(player, c, COMBAT_PHYSICALDAMAGE, math.floor(damage * 0.4), math.floor(damage * 0.4), CONST_ME_HITAREA)
            end
        end
    end,
    efeitoVisual = function(player, target) target:getPosition():sendMagicEffect(CONST_ME_HITAREA) end,
    descricaoEfeito = "o impacto atinge inimigos próximos ao alvo",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O Chi colide e estilhaça!", [2]="Impacto em cadeia.", [3]="Ninguém escapa."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.6}}
}

-- Passiva 1: Força do Gigante (nível 6)
HABILIDADES[13120] = {
    nome = "Força do Gigante",
    tipo = "passiva",
    dominio = {131},
    nivelMin = 6,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(131))
        player:setStorageValue(97960, math.floor(nivel * 0.5)) -- +% dano
    end,
    descricaoEfeito = "aumenta o dano desarmado",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Sentes a força do gigante.", [2]="Teus golpes são mais pesados.", [3]="Força bruta."}
}

-- Passiva 2: Resistência Imparável (nível 8)
HABILIDADES[13121] = {
    nome = "Resistência Imparável",
    tipo = "passiva",
    dominio = {131},
    nivelMin = 8,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(131))
        player:setStorageValue(97961, math.floor(nivel * 0.4)) -- redução de dano
    end,
    descricaoEfeito = "reduz o dano recebido",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Nada te fere.", [2]="Resistência inabalável.", [3]="Corpo de aço."}
}

-- Passiva 3: Presença Intimidadora (nível 12)
HABILIDADES[13122] = {
    nome = "Presença Intimidadora",
    tipo = "passiva",
    dominio = {131},
    nivelMin = 12,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(131))
        player:setStorageValue(97962, math.floor(nivel * 0.3)) -- % chance de medo ao ser atacado
    end,
    descricaoEfeito = "chance de causar medo em quem te ataca",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Tua presença intimida.", [2]="Os inimigos hesitam.", [3]="Aura de poder."}
}

-- Passiva 4: Vitalidade do Dragão (nível 15)
HABILIDADES[13123] = {
    nome = "Vitalidade do Dragão",
    tipo = "passiva",
    dominio = {131},
    nivelMin = 15,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(131))
        if nivel >= 15 then
            player:setStorageValue(97963, 1) -- +% vida máxima
        end
    end,
    descricaoEfeito = "aumenta a vida máxima",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="A vitalidade do dragão te preenche.", [2]="Vida longa.", [3]="Saúde inesgotável."}
}

-- Passiva 5: Maestria do Chi (nível 17)
HABILIDADES[13124] = {
    nome = "Maestria do Chi",
    tipo = "passiva",
    dominio = {131},
    nivelMin = 17,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(131))
        if nivel >= 17 then
            player:setStorageValue(97964, 1) -- Chi não decai
        end
    end,
    descricaoEfeito = "o Chi acumulado nunca diminui",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O Chi é eterno em ti.", [2]="Maestria do Chi.", [3]="Energia perpétua."}
}

-- Transformação 1: Postura do Dragão (nível 10)
HABILIDADES[13130] = {
    nome = "Postura do Dragão",
    tipo = "transformacao",
    dominio = {131},
    nivelMin = 10,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(131))
        if nivel >= 10 then
            local cond = Condition(CONDITION_ATTRIBUTES, CONDITIONID_COMBAT, -1)
            cond:setParameter(CONDITION_PARAM_SUBID, 203)
            cond:setParameter(CONDITION_PARAM_STAT_MAXHITPOINTSPERCENT, 110 + nivel * 0.5)
            cond:setParameter(CONDITION_PARAM_BUFF_SPELL, true)
            player:addCondition(cond)
        end
    end,
    descricaoEfeito = "aumenta a vida máxima",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="A postura do dragão te fortalece.", [2]="Poder ancestral.", [3]="Força interior."}
}

-- Transformação 2: Escudo de Chi (nível 16)
HABILIDADES[13131] = {
    nome = "Escudo de Chi",
    tipo = "transformacao",
    dominio = {131},
    nivelMin = 16,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(131))
        if nivel >= 16 then
            player:setStorageValue(97970, 1) -- flag: absorve % do dano como Chi
        end
    end,
    descricaoEfeito = "parte do dano recebido é convertido em Chi",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O Chi te protege.", [2]="Escudo espiritual.", [3]="A dor se torna poder."}
}

-- Transformação 3: Avatar do Dragão (nível 20)
HABILIDADES[13132] = {
    nome = "Avatar do Dragão",
    tipo = "transformacao",
    dominio = {131},
    nivelMin = 20,
    efeito = function(player)
        player:setSerene(true)
    end,
    descricaoEfeito = "ativa permanentemente a Serenidade",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="És o avatar do dragão!", [2]="Poder absoluto.", [3]="O Chi é a tua alma."}
}

print("DEBUG: habilidades_desarmado_pesado.lua (v1.1) carregado.")