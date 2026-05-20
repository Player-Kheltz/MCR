--[[
    Projeto MCR ? Habilidades de Desarmado (v1.0)
    Domínio Secundário: Desarmado (14)
    Partilhado entre Desarmado Leve (130) e Desarmado Pesado (131)
    Temas: artes marciais, chi, golpes contundentes
--]]

-- Gatilho 1: Chute Giratório (nível 6)
HABILIDADES[1401] = {
    nome = "Chute Giratório",
    tipo = "gatilho",
    dominio = {14},
    nivelMin = 6,
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
    descricaoEfeito = "atinge inimigos próximos ao alvo com um chute circular",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Um chute giratório atinge tudo à volta!", [2]="Chute em área.", [3]="O ar é cortado."},
    posturaMod = {[1]={chanceMult=1.2}, [2]={}, [3]={chanceMult=0.8}}
}

-- Gatilho 2: Agarrão (nível 8)
HABILIDADES[1402] = {
    nome = "Agarrão",
    tipo = "gatilho",
    dominio = {14},
    nivelMin = 8,
    gatilho = "onAttack",
    chanceBase = 10,
    chanceLampejo = 18,
    chanceVinculo = 25,
    buffType = "nextAttackCondition",
    conditionType = CONDITION_PARALYZE,
    conditionDuration = 2000,
    descricaoEfeito = "próximo ataque enraíza o alvo",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Agarras o inimigo, impedindo?o de fugir!", [2]="Presa firme.", [3]="Ninguém se solta."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.7}}
}

-- Gatilho 3: Esquiva Reflexiva (nível 10)
HABILIDADES[1403] = {
    nome = "Esquiva Reflexiva",
    tipo = "gatilho",
    dominio = {14},
    nivelMin = 10,
    gatilho = "onReceiveDamage",
    chanceBase = 10,
    chanceLampejo = 18,
    chanceVinculo = 25,
    buffType = "custom",
    efeito = function(player, attacker, damage)
        -- Aplica bónus de velocidade no próximo ataque
        player:setStorageValue(91550, 20) -- +20% dano no próximo ataque (lido por executor)
    end,
    descricaoEfeito = "ao receber dano, o próximo ataque causa mais dano",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="A esquiva alimenta a tua fúria!", [2]="Reflexos felinos.", [3]="Contra?ataque preparado."},
    posturaMod = {[1]={chanceMult=0.8}, [2]={}, [3]={chanceMult=1.3}}
}

-- Gatilho 4: Contra?Ataque (nível 12)
HABILIDADES[1404] = {
    nome = "Contra?Ataque",
    tipo = "gatilho",
    dominio = {14},
    nivelMin = 12,
    gatilho = "onBlock",
    chanceBase = 15,
    chanceLampejo = 25,
    chanceVinculo = 35,
    buffType = "custom",
    efeito = function(player, attacker)
        local dmg = math.floor(attacker:getMaxHealth() * 0.05)
        doTargetCombatHealth(player, attacker, COMBAT_PHYSICALDAMAGE, dmg, dmg, CONST_ME_HITAREA)
    end,
    efeitoVisual = function(player, target) target:getPosition():sendMagicEffect(CONST_ME_HITAREA) end,
    descricaoEfeito = "bloquear um ataque causa dano ao agressor",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O bloqueio transforma?se em ataque!", [2]="Contra?ataque fulminante.", [3]="Devolves o golpe."},
    posturaMod = {[1]={chanceMult=0.7}, [2]={}, [3]={chanceMult=1.5}}
}

-- Gatilho 5: Fluxo de Chi (nível 14)
HABILIDADES[1405] = {
    nome = "Fluxo de Chi",
    tipo = "gatilho",
    dominio = {14},
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
    mensagem = {[1]="O Chi flui e cura as tuas feridas!", [2]="Energia vital absorvida.", [3]="A vida retorna a ti."},
    posturaMod = {[1]={chanceMult=1.2}, [2]={}, [3]={chanceMult=0.8}}
}

-- Gatilho 6: Punhos de Ferro (nível 16)
HABILIDADES[1406] = {
    nome = "Punhos de Ferro",
    tipo = "gatilho",
    dominio = {14},
    nivelMin = 16,
    gatilho = "onAttack",
    chanceBase = 10,
    chanceLampejo = 18,
    chanceVinculo = 25,
    buffType = "custom",
    efeito = function(player, target, damage)
        local extraDmg = math.floor(damage * 0.15)
        doTargetCombatHealth(player, target, COMBAT_PHYSICALDAMAGE, extraDmg, extraDmg, CONST_ME_HITAREA)
    end,
    efeitoVisual = function(player, target) target:getPosition():sendMagicEffect(CONST_ME_HITAREA) end,
    descricaoEfeito = "causa dano extra ignorando parte da armadura",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Teus punhos atravessam a defesa!", [2]="Impacto perfurante.", [3]="Nada os detém."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.7}}
}

-- Gatilho 7: Golpe Atordoante (nível 18)
HABILIDADES[1407] = {
    nome = "Golpe Atordoante",
    tipo = "gatilho",
    dominio = {14},
    nivelMin = 18,
    gatilho = "onAttack",
    chanceBase = 8,
    chanceLampejo = 14,
    chanceVinculo = 20,
    buffType = "nextAttackCondition",
    conditionType = CONDITION_DAZZLED,
    conditionDuration = 2000,
    descricaoEfeito = "próximo ataque atordoa o alvo",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O golpe deixa o inimigo atordoado!", [2]="Pancada no crânio.", [3]="O alvo vê estrelas."},
    posturaMod = {[1]={chanceMult=1.2}, [2]={}, [3]={chanceMult=0.8}}
}

-- Passiva 1: Punhos Calejados (nível 5)
HABILIDADES[1410] = {
    nome = "Punhos Calejados",
    tipo = "passiva",
    dominio = {14},
    nivelMin = 5,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(14))
        player:setStorageValue(97750, math.floor(nivel * 0.6)) -- +% dano desarmado
    end,
    descricaoEfeito = "aumenta o dano desarmado",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Os punhos já não sentem dor.", [2]="Cada golpe é mais forte.", [3]="Mãos de guerreiro."}
}

-- Passiva 2: Resistência Física (nível 7)
HABILIDADES[1411] = {
    nome = "Resistência Física",
    tipo = "passiva",
    dominio = {14},
    nivelMin = 7,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(14))
        player:setStorageValue(97751, math.floor(nivel * 0.3)) -- % redução de dano
    end,
    descricaoEfeito = "reduz o dano recebido",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O corpo torna?se uma fortaleza.", [2]="Pele endurecida.", [3]="Resistência marcial."}
}

-- Passiva 3: Passo do Vento (nível 9)
HABILIDADES[1412] = {
    nome = "Passo do Vento",
    tipo = "passiva",
    dominio = {14},
    nivelMin = 9,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(14))
        player:setStorageValue(97752, math.floor(nivel * 0.5)) -- +% velocidade movimento
    end,
    descricaoEfeito = "aumenta a velocidade de movimento",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Os pés mal tocam o chão.", [2]="Movimento fluido.", [3]="Ligeiro como a brisa."}
}

-- Passiva 4: Espírito Inquebrável (nível 11)
HABILIDADES[1413] = {
    nome = "Espírito Inquebrável",
    tipo = "passiva",
    dominio = {14},
    nivelMin = 11,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(14))
        if nivel >= 11 then
            player:setStorageValue(97753, 1) -- imunidade a medo/atordoamento
        end
    end,
    descricaoEfeito = "imune a medo e atordoamento",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Nada te abala.", [2]="Mente inabalável.", [3]="O espírito prevalece."}
}

-- Passiva 5: Mestre do Chi (nível 13)
HABILIDADES[1414] = {
    nome = "Mestre do Chi",
    tipo = "passiva",
    dominio = {14},
    nivelMin = 13,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(14))
        if nivel >= 13 then
            player:setStorageValue(97754, 1) -- gera Chi mais rápido (usado pelas especialidades)
        end
    end,
    descricaoEfeito = "gera Chi mais rapidamente",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O Chi flui sem esforço.", [2]="Energia interior despertada.", [3]="O fluxo é constante."}
}

-- Transformação 1: Corpo Leve (nível 8)
HABILIDADES[1420] = {
    nome = "Corpo Leve",
    tipo = "transformacao",
    dominio = {14},
    nivelMin = 8,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(14))
        if nivel >= 8 then
            local moveBonus = Condition(CONDITION_ATTRIBUTES, CONDITIONID_COMBAT, -1)
            moveBonus:setParameter(CONDITION_PARAM_SUBID, 210)
            moveBonus:setParameter(CONDITION_PARAM_SPEED, math.floor(player:getBaseSpeed() * 0.10))
            moveBonus:setParameter(CONDITION_PARAM_BUFF_SPELL, true)
            player:addCondition(moveBonus)
        end
    end,
    descricaoEfeito = "+10% velocidade de movimento",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O corpo fica leve como uma pluma.", [2]="Movimento ágil.", [3]="Deslizas sobre o chão."}
}

-- Transformação 2: Fúria Interior (nível 14)
HABILIDADES[1421] = {
    nome = "Fúria Interior",
    tipo = "transformacao",
    dominio = {14},
    nivelMin = 14,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(14))
        if nivel >= 14 then
            player:setStorageValue(97760, 1) -- flag: +dano quando vida < 50%
        end
    end,
    descricaoEfeito = "causa mais dano quando a vida está baixa",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="A fúria interior consome?te!", [2]="Força na adversidade.", [3]="Quanto mais ferido, mais perigoso."}
}

-- Transformação 3: Serenidade (nível 18)
HABILIDADES[1422] = {
    nome = "Serenidade",
    tipo = "transformacao",
    dominio = {14},
    nivelMin = 18,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(14))
        if nivel >= 18 then
            -- Aplica a condição Serene (se disponível) ou um buff equivalente
            if player.setSerene then
                player:setSerene(true)
            else
                player:setStorageValue(97761, 1) -- flag para postura.lua: dano e cura aumentados
            end
        end
    end,
    descricaoEfeito = "estado de serenidade que aumenta dano e cura",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="A serenidade envolve?te.", [2]="Paz interior.", [3]="Mente e corpo em harmonia."}
}

print("DEBUG: habilidades_desarmado.lua (v1.0) carregado.")