--[[
    Projeto MCR ? Habilidades de Desarmado Leve (v1.1)
    Especialidade: Desarmado Leve (130)
    Temas: Chi (Harmony), Virtude da Harmonia, Serenidade, Rajada de Golpes
    Corrigido: Virtue_t como tabela Lua, Harmony via storage
--]]

-- ============================================================
-- ÁRVORE I-IV: DESARMADO LEVE (130)
-- ============================================================

-- I (5) ? Passiva: Virtude da Harmonia
HABILIDADES[13001] = {
    nome = "Virtude da Harmonia",
    tipo = "passiva",
    dominio = {130},
    nivelMin = 5,
    efeito = function(player)
        player:setVirtue(Virtue_t.Harmony)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(130))
        player:setStorageValue(97850, math.floor(nivel * 1.5)) -- % de cura ao causar dano
    end,
    descricaoEfeito = "parte do dano causado recupera a tua vida",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="A harmonia flui em ti.", [2]="Tua energia vital se renova.", [3]="O Chi te cura."}
}

-- II (10) ? Passiva: Fluxo de Chi
HABILIDADES[13002] = {
    nome = "Fluxo de Chi",
    tipo = "passiva",
    dominio = {130},
    nivelMin = 10,
    efeito = function(player)
        player:fillHarmony()  -- enche a barra nativa (se disponível) ou podemos usar storage
        player:setStorageValue(STORAGE.HARMONY, 5) -- Chi máximo
        player:setStorageValue(97851, 1) -- flag para acumular Chi em ataques
    end,
    descricaoEfeito = "acumula Chi (Harmony) a cada ataque",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O Chi começa a fluir.", [2]="Sentes a energia acumular.", [3]="Teu espírito se fortalece."}
}

-- III (15) ? Gatilho: Rajada de Golpes (consome Chi)
HABILIDADES[13003] = {
    nome = "Rajada de Golpes",
    tipo = "gatilho",
    dominio = {130},
    nivelMin = 15,
    gatilho = "onAttack",
    chanceBase = 100, -- sempre que tiver Chi >= 3
    buffType = "custom",
    efeito = function(player, target, damage)
        local harmony = player:getStorageValue(STORAGE.HARMONY) or 0
        if harmony < 3 then return end
        -- Consome 3 pontos de Chi
        player:setStorageValue(STORAGE.HARMONY, harmony - 3)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(130))
        local extraHits = (nivel >= 18) and 3 or 2
        local dmg = math.floor(damage * 0.6)
        local pid, tid = player:getId(), target:getId()
        for i = 1, extraHits do
            addEvent(function()
                local pl, ta = Player(pid), Creature(tid)
                if pl and ta then
                    doTargetCombatHealth(pl, ta, COMBAT_PHYSICALDAMAGE, dmg, dmg, CONST_ME_HITAREA)
                end
            end, i * 120)
        end
    end,
    efeitoVisual = function(player, target) target:getPosition():sendMagicEffect(CONST_ME_HITAREA) end,
    descricaoEfeito = "gasta 3 Chi para desferir golpes rápidos",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Uma rajada de golpes!", [2]="Teus punhos são uma névoa.", [3]="Chi liberado."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.7}}
}

-- IV (20) ? Passiva: Serenidade
HABILIDADES[13004] = {
    nome = "Serenidade",
    tipo = "passiva",
    dominio = {130},
    nivelMin = 20,
    efeito = function(player)
        player:setSerene(true)
        player:setStorageValue(97852, 1) -- flag de maestria
    end,
    descricaoEfeito = "Chi máximo ativa Serenidade, aumentando dano e cura",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="A serenidade te envolve.", [2]="Corpo e mente em paz.", [3]="O Chi é infinito."}
}

-- ============================================================
-- COMPLEMENTARES ? DESARMADO LEVE (130)
-- ============================================================

-- Gatilho 1: Punhos Velozes (nível 7)
HABILIDADES[13010] = {
    nome = "Punhos Velozes",
    tipo = "gatilho",
    dominio = {130},
    nivelMin = 7,
    gatilho = "onAttack",
    chanceBase = 15,
    chanceLampejo = 25,
    chanceVinculo = 35,
    buffType = "speedBurst",
    buffMultiplier = 0.1,
    buffDurationMs = 400,
    descricaoEfeito = "aumenta a velocidade de ataque brevemente",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Teus punhos são rápidos como o vento!", [2]="Velocidade desarmada.", [3]="Golpes acelerados."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.7}}
}

-- Gatilho 2: Golpe Duplo (nível 9)
HABILIDADES[13011] = {
    nome = "Golpe Duplo",
    tipo = "gatilho",
    dominio = {130},
    nivelMin = 9,
    gatilho = "onAttack",
    chanceBase = 12,
    chanceLampejo = 20,
    chanceVinculo = 28,
    async = true,
    buffType = "custom",
    efeito = function(player, target, damage)
        local habId = 13011
        player:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 1)
        local pid, tid = player:getId(), target:getId()
        local dmg = math.floor(damage * 0.5)
        addEvent(function()
            local pl, ta = Player(pid), Creature(tid)
            if pl and ta then
                doTargetCombatHealth(pl, ta, COMBAT_PHYSICALDAMAGE, dmg, dmg, CONST_ME_HITAREA)
            end
            if pl then pl:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 0) end
        end, 120)
    end,
    descricaoEfeito = "desfere um segundo golpe rápido",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Um dois! Golpe duplo.", [2]="Segundo golpe.", [3]="Apanhaste o ritmo."},
    posturaMod = {[1]={chanceMult=1.4}, [2]={}, [3]={chanceMult=0.6}}
}

-- Gatilho 3: Esquiva Fluida (nível 11)
HABILIDADES[13012] = {
    nome = "Esquiva Fluida",
    tipo = "gatilho",
    dominio = {130},
    nivelMin = 11,
    gatilho = "onBlock",
    chanceBase = 15,
    chanceLampejo = 25,
    chanceVinculo = 35,
    buffType = "custom",
    efeito = function(player, target)
        local bonus = getNivelPorAfinidade(player:getDominioAfinidade(130)) * 2
        player:setStorageValue(91550, bonus) -- bónus para o próximo ataque
    end,
    descricaoEfeito = "o próximo ataque causa dano extra após um bloqueio",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Esquivaste e preparaste o contra?ataque!", [2]="Fluidez defensiva.", [3]="O Chi te guia."},
    posturaMod = {[1]={chanceMult=0.7}, [2]={}, [3]={chanceMult=1.4}}
}

-- Gatilho 4: Dança do Chi (nível 14)
HABILIDADES[13013] = {
    nome = "Dança do Chi",
    tipo = "gatilho",
    dominio = {130},
    nivelMin = 14,
    gatilho = "onAttack",
    chanceBase = 8,
    chanceLampejo = 14,
    chanceVinculo = 22,
    buffType = "lifeLeech",
    leechPercent = 8,
    durationSec = 3,
    descricaoEfeito = "roubo de vida por 3 segundos",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O Chi drena a vida do inimigo!", [2]="Energia vital roubada.", [3]="A vida flui para ti."},
    posturaMod = {[1]={chanceMult=1.2}, [2]={}, [3]={chanceMult=0.8}}
}

-- Gatilho 5: Palma Atordoante (nível 16)
HABILIDADES[13014] = {
    nome = "Palma Atordoante",
    tipo = "gatilho",
    dominio = {130},
    nivelMin = 16,
    gatilho = "onAttack",
    chanceBase = 10,
    chanceLampejo = 18,
    chanceVinculo = 25,
    buffType = "nextAttackCondition",
    conditionType = CONDITION_DAZZLED,
    conditionDuration = 2000,
    descricaoEfeito = "próximo ataque atordoa o alvo",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="A palma atordoa o inimigo!", [2]="Impacto no Chi.", [3]="O alvo cambaleia."},
    posturaMod = {[1]={chanceMult=1.2}, [2]={}, [3]={chanceMult=0.8}}
}

-- Gatilho 6: Onda de Chi (nível 18)
HABILIDADES[13015] = {
    nome = "Onda de Chi",
    tipo = "gatilho",
    dominio = {130},
    nivelMin = 18,
    gatilho = "onAttack",
    condicao = "cercado",
    chanceBase = 12,
    chanceLampejo = 20,
    chanceVinculo = 30,
    buffType = "custom",
    efeito = function(player, target, damage)
        local pos = player:getPosition()
        for _, c in ipairs(getCreaturesInArea(pos, 2, 2)) do
            if c:isMonster() and c ~= target then
                doTargetCombatHealth(player, c, COMBAT_PHYSICALDAMAGE, math.floor(damage * 0.4), math.floor(damage * 0.4), CONST_ME_HITAREA)
            end
        end
    end,
    efeitoVisual = function(player, target) player:getPosition():sendMagicEffect(CONST_ME_HITAREA) end,
    descricaoEfeito = "libera Chi em área ao redor",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O Chi explode à tua volta!", [2]="Onda de energia.", [3]="Ninguém se aproxima."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.7}}
}

-- Gatilho 7: Triplo Impacto (nível 19)
HABILIDADES[13016] = {
    nome = "Triplo Impacto",
    tipo = "gatilho",
    dominio = {130},
    nivelMin = 19,
    gatilho = "onAttack",
    chanceBase = 5,
    chanceLampejo = 10,
    chanceVinculo = 16,
    async = true,
    buffType = "custom",
    efeito = function(player, target, damage)
        local habId = 13016
        player:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 1)
        local pid, tid = player:getId(), target:getId()
        local dmg = math.floor(damage * 0.5)
        for i = 1, 2 do
            addEvent(function()
                local pl, ta = Player(pid), Creature(tid)
                if pl and ta then
                    doTargetCombatHealth(pl, ta, COMBAT_PHYSICALDAMAGE, dmg, dmg, CONST_ME_HITAREA)
                end
                if i == 2 and pl then pl:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 0) end
            end, i * 150)
        end
    end,
    descricaoEfeito = "três golpes consecutivos",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Três golpes num piscar de olhos!", [2]="Impacto triplo.", [3]="Ninguém resiste."},
    posturaMod = {[1]={chanceMult=1.5}, [2]={}, [3]={chanceMult=0.3}}
}

-- Passiva 1: Mãos de Ferro (nível 6)
HABILIDADES[13020] = {
    nome = "Mãos de Ferro",
    tipo = "passiva",
    dominio = {130},
    nivelMin = 6,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(130))
        player:setStorageValue(97860, math.floor(nivel * 0.5)) -- ignora % armadura
    end,
    descricaoEfeito = "ignora parte da armadura do alvo",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Teus punhos são como aço.", [2]="Nada os detém.", [3]="Mãos de ferro."}
}

-- Passiva 2: Pele de Pedra (nível 8)
HABILIDADES[13021] = {
    nome = "Pele de Pedra",
    tipo = "passiva",
    dominio = {130},
    nivelMin = 8,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(130))
        player:setStorageValue(97861, math.floor(nivel * 0.4)) -- redução de dano
    end,
    descricaoEfeito = "reduz o dano recebido",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Tua pele endurece.", [2]="Resistência natural.", [3]="Pele de pedra."}
}

-- Passiva 3: Passo Leve (nível 12)
HABILIDADES[13022] = {
    nome = "Passo Leve",
    tipo = "passiva",
    dominio = {130},
    nivelMin = 12,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(130))
        player:setStorageValue(97862, math.floor(nivel * 0.6)) -- +velocidade movimento
    end,
    descricaoEfeito = "aumenta a velocidade de movimento",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Teus passos são silenciosos.", [2]="Movimento ágil.", [3]="Passo leve."}
}

-- Passiva 4: Espírito Inquebrável (nível 15)
HABILIDADES[13023] = {
    nome = "Espírito Inquebrável",
    tipo = "passiva",
    dominio = {130},
    nivelMin = 15,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(130))
        if nivel >= 15 then
            player:setStorageValue(97863, 1) -- imunidade a medo
        end
    end,
    descricaoEfeito = "imune a medo e efeitos de pânico",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Nada te abala.", [2]="Espírito forte.", [3]="Inquebrável."}
}

-- Passiva 5: Mestre do Chi (nível 17)
HABILIDADES[13024] = {
    nome = "Mestre do Chi",
    tipo = "passiva",
    dominio = {130},
    nivelMin = 17,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(130))
        if nivel >= 17 then
            player:setStorageValue(97864, 1) -- aumenta a geração de Chi
        end
    end,
    descricaoEfeito = "gera Chi mais rapidamente",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O Chi flui abundantemente.", [2]="Mestre do Chi.", [3]="Energia sem fim."}
}

-- Transformação 1: Corpo Leve (nível 10)
HABILIDADES[13030] = {
    nome = "Corpo Leve",
    tipo = "transformacao",
    dominio = {130},
    nivelMin = 10,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(130))
        if nivel >= 10 then
            local moveBonus = Condition(CONDITION_ATTRIBUTES, CONDITIONID_COMBAT, -1)
            moveBonus:setParameter(CONDITION_PARAM_SUBID, 202)
            moveBonus:setParameter(CONDITION_PARAM_SPEED, math.floor(player:getBaseSpeed() * 0.15))
            moveBonus:setParameter(CONDITION_PARAM_BUFF_SPELL, true)
            player:addCondition(moveBonus)
        end
    end,
    descricaoEfeito = "+15% velocidade de movimento",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Teu corpo fica leve como uma pena.", [2]="Movimento livre.", [3]="Corpo leve."}
}

-- Transformação 2: Fúria Interior (nível 16)
HABILIDADES[13031] = {
    nome = "Fúria Interior",
    tipo = "transformacao",
    dominio = {130},
    nivelMin = 16,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(130))
        if nivel >= 16 then
            player:setStorageValue(97870, 1) -- flag: dano aumentado quando vida < 50%
        end
    end,
    descricaoEfeito = "causa mais dano quando a vida está baixa",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="A fúria interior desperta!", [2]="Poder da sobrevivência.", [3]="Força na adversidade."}
}

-- Transformação 3: Serenidade Plena (nível 20)
HABILIDADES[13032] = {
    nome = "Serenidade Plena",
    tipo = "transformacao",
    dominio = {130},
    nivelMin = 20,
    efeito = function(player)
        player:setSerene(true)
    end,
    descricaoEfeito = "ativa permanentemente a Serenidade",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="A serenidade plena te envolve.", [2]="Paz interior.", [3]="O Chi é eterno."}
}

print("DEBUG: habilidades_desarmado_leve.lua (v1.1) carregado.")