--[[
    Projeto MCR ? SPA v4.0 ? Habilidades de Desarmado Puro (130)
    Estilo: Monge tradicional, punhos e chutes.
    Recursos: Chi (Harmony), Virtude da Harmonia.
--]]

-- ============================================================
-- ÁRVORE I-IV: DESARMADO PURO (130)
-- ============================================================

-- I (5) ? Passiva: Punhos de Ferro
HABILIDADES[13001] = {
    nome = "Punhos de Ferro",
    tipo = "passiva",
    dominio = {130},
    nivelMin = 5,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(130))
        player:setCombatModifier("desarmado_dano_fisico", nivel * 0.8)
    end,
    descricaoEfeito = "+0.8% dano desarmado por nível",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Teus punhos são como aço.", [2]="Força bruta.", [3]="Mãos de guerreiro."}
}

-- II (10) ? Passiva: Fluxo de Chi
HABILIDADES[13002] = {
    nome = "Fluxo de Chi",
    tipo = "passiva",
    dominio = {130},
    nivelMin = 10,
    efeito = function(player)
        player:fillHarmony()
        player:setStorageValue(STORAGE.HARMONY, 5)
        player:setCombatModifier("chi_geracao", 1.0)
    end,
    descricaoEfeito = "acumula Chi máximo",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O Chi flui em ti.", [2]="Energia interior.", [3]="Poder acumulado."}
}

-- III (15) ? Gatilho: Rajada de Golpes (consome Chi)
HABILIDADES[13003] = {
    nome = "Rajada de Golpes",
    tipo = "gatilho",
    dominio = {130},
    nivelMin = 15,
    gatilho = "onAttack",
    chanceBase = 100,
    condicao = "5Golpes",
    buffType = "custom",
    efeito = function(player, target, damage)
        local harmony = player:getStorageValue(STORAGE.HARMONY) or 0
        if harmony < 3 then return end
        player:setStorageValue(STORAGE.HARMONY, harmony - 3)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(130))
        local hits = (nivel >= 18) and 3 or 2
        local dmg = math.floor(damage * 0.6)
        local pid, tid = player:getId(), target:getId()
        for i = 1, hits do
            addEvent(function()
                local pl, ta = Player(pid), Creature(tid)
                if pl and ta then
                    doTargetCombatHealth(pl, ta, COMBAT_PHYSICALDAMAGE, dmg, dmg, CONST_ME_HITAREA)
                end
            end, i * 120)
        end
    end,
    efeitoVisual = function(player, target) target:getPosition():sendMagicEffect(CONST_ME_HITAREA) end,
    descricaoEfeito = "gasta 3 Chi para golpes rápidos",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Rajada de golpes!", [2]="Teus punhos são uma névoa.", [3]="Chi liberado."},
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
    end,
    descricaoEfeito = "Chi máximo ativa Serenidade",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="A serenidade te envolve.", [2]="Paz interior.", [3]="O Chi é infinito."}
}

-- ============================================================
-- COMPLEMENTARES ? DESARMADO PURO (130) ? 7G, 5P, 3T
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
    descricaoEfeito = "aumenta velocidade de ataque",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Rápido como o vento!", [2]="Velocidade.", [3]="Acelerado."},
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
    descricaoEfeito = "um segundo golpe rápido",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Um dois!", [2]="Golpe duplo.", [3]="Apanhaste o ritmo."},
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
        player:setStorageValue(91550, bonus)
    end,
    descricaoEfeito = "próximo ataque com dano extra",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Esquiva perfeita!", [2]="Contra?ataque preparado.", [3]="Fluidez defensiva."},
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
    descricaoEfeito = "roubo de vida",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O Chi drena o inimigo!", [2]="Vida roubada.", [3]="Energia vital."},
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
    descricaoEfeito = "próximo ataque atordoa",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="A palma atordoa!", [2]="Impacto no Chi.", [3]="O alvo cambaleia."},
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
    descricaoEfeito = "Chi explode em área",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Onda de Chi!", [2]="Energia liberada.", [3]="Ninguém se aproxima."},
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
    mensagem = {[1]="Três golpes!", [2]="Impacto triplo.", [3]="Ninguém resiste."},
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
        player:setCombatModifier("ignorar_armadura", nivel * 0.5)
    end,
    descricaoEfeito = "ignora % da armadura do alvo",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Mãos de ferro.", [2]="Nada os detém.", [3]="Força."}
}

-- Passiva 2: Pele de Pedra (nível 8)
HABILIDADES[13021] = {
    nome = "Pele de Pedra",
    tipo = "passiva",
    dominio = {130},
    nivelMin = 8,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(130))
        player:setCombatModifier("reducao_dano", nivel * 0.4)
    end,
    descricaoEfeito = "reduz dano recebido",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Pele dura.", [2]="Resistência.", [3]="Pedra."}
}

-- Passiva 3: Passo Leve (nível 12)
HABILIDADES[13022] = {
    nome = "Passo Leve",
    tipo = "passiva",
    dominio = {130},
    nivelMin = 12,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(130))
        player:setCombatModifier("velocidade_movimento", nivel * 0.6)
    end,
    descricaoEfeito = "+velocidade movimento",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Passo leve.", [2]="Ágil.", [3]="Silencioso."}
}

-- Passiva 4: Espírito Inquebrável (nível 15)
HABILIDADES[13023] = {
    nome = "Espírito Inquebrável",
    tipo = "passiva",
    dominio = {130},
    nivelMin = 15,
    efeito = function(player)
        if getNivelPorAfinidade(player:getDominioAfinidade(130)) >= 15 then
            player:setCombatModifier("imune_medo", 1)
        end
    end,
    descricaoEfeito = "imune a medo",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Inquebrável.", [2]="Espírito forte.", [3]="Nada te abala."}
}

-- Passiva 5: Mestre do Chi (nível 17)
HABILIDADES[13024] = {
    nome = "Mestre do Chi",
    tipo = "passiva",
    dominio = {130},
    nivelMin = 17,
    efeito = function(player)
        if getNivelPorAfinidade(player:getDominioAfinidade(130)) >= 17 then
            player:setCombatModifier("chi_geracao", 1.5)
        end
    end,
    descricaoEfeito = "Chi não decai",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Chi eterno.", [2]="Mestre.", [3]="Energia infinita."}
}

-- Transformação 1: Corpo Leve (nível 10)
HABILIDADES[13030] = {
    nome = "Corpo Leve",
    tipo = "transformacao",
    dominio = {130},
    nivelMin = 10,
    efeito = function(player)
        if getNivelPorAfinidade(player:getDominioAfinidade(130)) >= 10 then
            local c = Condition(CONDITION_ATTRIBUTES, CONDITIONID_COMBAT, -1)
            c:setParameter(CONDITION_PARAM_SUBID, 202)
            c:setParameter(CONDITION_PARAM_SPEED, math.floor(player:getBaseSpeed() * 0.15))
            c:setParameter(CONDITION_PARAM_BUFF_SPELL, true)
            player:addCondition(c)
        end
    end,
    descricaoEfeito = "+15% vel movimento",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Corpo leve.", [2]="Ágil.", [3]="Pluma."}
}

-- Transformação 2: Fúria Interior (nível 16)
HABILIDADES[13031] = {
    nome = "Fúria Interior",
    tipo = "transformacao",
    dominio = {130},
    nivelMin = 16,
    efeito = function(player)
        if getNivelPorAfinidade(player:getDominioAfinidade(130)) >= 16 then
            player:setCombatModifier("furia_interior", 1)
        end
    end,
    descricaoEfeito = "+dano com vida baixa",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Fúria!", [2]="Poder na adversidade.", [3]="Força."}
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
    descricaoEfeito = "Serenidade permanente",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Serenidade plena.", [2]="Paz.", [3]="Chi eterno."}
}

print("DEBUG: habilidades_desarmado_puro.lua v4.0 carregado.")