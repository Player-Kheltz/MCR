--[[
    Projeto MCR ? Habilidades de Arremesso (v1.2)
    Especialidade: Arremesso (121)
    Comportamento dual: sem escudo (Atleta) / com escudo (Espartano)
    Descrições adaptativas e animações corrigidas.
--]]

-- ============================================================
-- ÁRVORE I-IV: ARREMESSO (121)
-- ============================================================

-- I (5) ? Passiva: Projétil Potente
HABILIDADES[12101] = {
    nome = "Projétil Potente", tipo = "passiva", dominio = {121}, nivelMin = 5,
    efeito = function(p) p:setStorageValue(97801, math.floor(getNivelPorAfinidade(p:getDominioAfinidade(121)) * 0.7)) end,
    descricaoEfeito = "+0.7% dano por nível com Arremesso", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="O projétil corta o ar.", [2]="Força no arremesso.", [3]="Precisão potente."}
}

-- II (10) ? Passiva: Reflexos de Combate
HABILIDADES[12102] = {
    nome = "Reflexos de Combate", tipo = "passiva", dominio = {121}, nivelMin = 10,
    efeito = function(p)
        local n = getNivelPorAfinidade(p:getDominioAfinidade(121))
        if hasShield(p) then p:setStorageValue(97802, math.min(5 + n * 0.5, 20))
        else p:setStorageValue(97803, math.min(5 + n * 0.5, 20)) end
    end,
    descricaoEfeito = "sem escudo: esquiva; com escudo: lentidão ao atacar", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Teus instintos são aguçados.", [2]="Reflexos felinos.", [3]="Nada te surpreende."}
}

-- III (15) ? Passiva: Estilo de Combate
HABILIDADES[12103] = {
    nome = "Estilo de Combate", tipo = "passiva", dominio = {121}, nivelMin = 15,
    efeito = function(p)
        p:setStorageValue(97800, 1) -- flag para postura.lua
    end,
    descricaoEfeito = function(p)
        if hasShield(p) then return "Espartano: lentidão longe, empurrão perto"
        else return "Atleta: +dano e sem consumo de munição após esquivar" end
    end,
    cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="O campo de batalha é teu!", [2]="Estilo adaptado.", [3]="Cada situação exige uma tática."}
}

-- IV (20) ? Passiva: Maestria em Arremesso
HABILIDADES[12104] = {
    nome = "Maestria em Arremesso", tipo = "passiva", dominio = {121}, nivelMin = 20,
    efeito = function(p) p:setStorageValue(97820, 1) end,
    descricaoEfeito = "aperfeiçoa o Estilo de Combate e ensina-o ao Atirador", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="És um mestre do arremesso!", [2]="Nenhum alvo está a salvo.", [3]="O projétil obedece-te."}
}

-- ============================================================
-- COMPLEMENTARES ? ARREMESSO (121)
-- ============================================================

-- Gatilho 1: Arremesso Duplo (nível 6)
HABILIDADES[12110] = {
    nome = "Arremesso Duplo", tipo = "gatilho", dominio = {121}, nivelMin = 6,
    gatilho = "onAttack", chanceBase = 8, chanceLampejo = 16, chanceVinculo = 24,
    async = true, buffType = "custom",
    efeito = function(p, t, d)
        local habId = 12110
        p:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 1)
        local pid, tid = p:getId(), t:getId()
        local dmg = math.floor(d * 0.6)
        addEvent(function()
            local pl, ta = Player(pid), Creature(tid)
            if pl and ta then
                doTargetCombatHealth(pl, ta, COMBAT_PHYSICALDAMAGE, dmg, dmg, CONST_ME_BLOCKHIT)
                local anim = getDistanceAnim(pl)
                if anim then sendDistanceEffect(pl, ta, anim, CONST_ME_BLOCKHIT)
                else ta:getPosition():sendMagicEffect(CONST_ME_BLOCKHIT) end
            end
            if pl then pl:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 0) end
        end, 150)
    end,
    descricaoEfeito = "dispara um segundo projétil rapidamente", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Duas lanças partem!", [2]="Arremesso duplo.", [3]="O segundo projétil segue."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.7}}
}

-- Gatilho 2: Ricochete (nível 9)
HABILIDADES[12111] = {
    nome = "Ricochete", tipo = "gatilho", dominio = {121}, nivelMin = 9,
    gatilho = "onAttack", chanceBase = 8, chanceLampejo = 14, chanceVinculo = 20,
    buffType = "custom",
    efeito = function(p, t, d)
        local pos = t:getPosition()
        for _, c in ipairs(getCreaturesInArea(pos, 2, 2)) do
            if c:isMonster() and c ~= t then
                doTargetCombatHealth(p, c, COMBAT_PHYSICALDAMAGE, math.floor(d * 0.4), math.floor(d * 0.4), CONST_ME_HITAREA)
                local anim = getDistanceAnim(p)
                if anim then sendDistanceEffect(p, c, anim, CONST_ME_HITAREA)
                else c:getPosition():sendMagicEffect(CONST_ME_HITAREA) end
                break
            end
        end
    end,
    descricaoEfeito = "o projétil atinge um inimigo próximo adicional", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="O projétil ressalta!", [2]="Ricochete certeiro.", [3]="Atinge outro alvo."},
    posturaMod = {[1]={chanceMult=1.2}, [2]={}, [3]={chanceMult=0.8}}
}

-- Gatilho 3: Empurrão Tático (nível 12, com escudo)
HABILIDADES[12112] = {
    nome = "Empurrão Tático", tipo = "gatilho", dominio = {121}, nivelMin = 12,
    gatilho = "onAttack", chanceBase = 15, chanceLampejo = 25, chanceVinculo = 40,
    buffType = "custom",
    efeito = function(p, t)
        if not hasShield(p) then return end
        if getCreatureDistance(p, t) <= 2 then
            local dir = Position(p:getPosition()):getDirectionTo(t:getPosition())
            if dir then t:knockback(dir) end
        end
    end,
    efeitoVisual = function(p, t) t:getPosition():sendMagicEffect(CONST_ME_HITAREA) end,
    descricaoEfeito = "empurra o inimigo com o escudo", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="O escudo golpeia o inimigo!", [2]="Empurrão tático.", [3]="Manténs a distância."},
    posturaMod = {[1]={chanceMult=1.4}, [2]={}, [3]={chanceMult=0.6}}
}

-- Gatilho 4: Chuva de Projécteis (nível 16)
HABILIDADES[12113] = {
    nome = "Chuva de Projécteis", tipo = "gatilho", dominio = {121}, nivelMin = 16,
    gatilho = "onAttack", chanceBase = 5, chanceLampejo = 10, chanceVinculo = 18,
    async = true, buffType = "custom",
    efeito = function(p, t, d)
        local habId = 12113
        p:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 1)
        local pid, tid = p:getId(), t:getId()
        local dmg = math.floor(d * 0.5)
        for i = 1, 3 do
            addEvent(function()
                local pl, ta = Player(pid), Creature(tid)
                if pl and ta then
                    doTargetCombatHealth(pl, ta, COMBAT_PHYSICALDAMAGE, dmg, dmg, CONST_ME_DRAWBLOOD)
                    local anim = getDistanceAnim(pl)
                    if anim then sendDistanceEffect(pl, ta, anim, CONST_ME_DRAWBLOOD)
                    else ta:getPosition():sendMagicEffect(CONST_ME_DRAWBLOOD) end
                end
                if i == 3 and pl then pl:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 0) end
            end, i * 150)
        end
    end,
    descricaoEfeito = "dispara uma rajada de projéteis", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Uma chuva de projécteis!", [2]="Múltiplos disparos.", [3]="Ninguém escapa."},
    posturaMod = {[1]={chanceMult=1.5}, [2]={}, [3]={chanceMult=0.3}}
}

-- Gatilho 5: Tiro Paralisante (nível 14)
HABILIDADES[12114] = {
    nome = "Tiro Paralisante", tipo = "gatilho", dominio = {121}, nivelMin = 14,
    gatilho = "onAttack", chanceBase = 8, chanceLampejo = 14, chanceVinculo = 20,
    buffType = "nextAttackCondition", conditionType = CONDITION_PARALYZE, conditionDuration = 2000,
    descricaoEfeito = "próximo ataque enraíza o alvo", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="O projétil prende o alvo!", [2]="Tiro paralisante.", [3]="Ninguém foge."},
    posturaMod = {[1]={chanceMult=1.2}, [2]={}, [3]={chanceMult=0.8}}
}

-- Gatilho 6: Sangramento à Distância (nível 10)
HABILIDADES[12115] = {
    nome = "Sangramento à Distância", tipo = "gatilho", dominio = {121}, nivelMin = 10,
    gatilho = "onAttack", chanceBase = 10, chanceLampejo = 18, chanceVinculo = 25,
    buffType = "nextAttackCondition", conditionType = CONDITION_BLEEDING, conditionDuration = 4000, conditionDamage = 15,
    descricaoEfeito = "próximo ataque causa sangramento", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="O projétil dilacera a carne.", [2]="Sangramento à distância.", [3]="Ferida que não fecha."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.5}}
}

-- Gatilho 7: Disparo Múltiplo (nível 18)
HABILIDADES[12116] = {
    nome = "Disparo Múltiplo", tipo = "gatilho", dominio = {121}, nivelMin = 18,
    gatilho = "onAttack", chanceBase = 4, chanceLampejo = 10, chanceVinculo = 16,
    async = true, buffType = "custom",
    efeito = function(p, t, d)
        local habId = 12116
        p:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 1)
        local pid, tid = p:getId(), t:getId()
        local dmg = math.floor(d * 0.8)
        for i = 1, 2 do
            addEvent(function()
                local pl, ta = Player(pid), Creature(tid)
                if pl and ta then
                    doTargetCombatHealth(pl, ta, COMBAT_PHYSICALDAMAGE, dmg, dmg, CONST_ME_HITAREA)
                    local anim = getDistanceAnim(pl)
                    if anim then sendDistanceEffect(pl, ta, anim, CONST_ME_HITAREA)
                    else ta:getPosition():sendMagicEffect(CONST_ME_HITAREA) end
                end
                if i == 2 and pl then pl:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 0) end
            end, i * 200)
        end
    end,
    descricaoEfeito = "dispara dois projéteis adicionais", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Projéteis múltiplos!", [2]="Chuva de aço.", [3]="O ar fica cheio de lâminas."},
    posturaMod = {[1]={chanceMult=1.4}, [2]={}, [3]={chanceMult=0.4}}
}

-- Passivas (5)
HABILIDADES[12120] = {
    nome = "Velocidade do Arremessador", tipo = "passiva", dominio = {121}, nivelMin = 7,
    efeito = function(p) p:setStorageValue(97830, math.floor(getNivelPorAfinidade(p:getDominioAfinidade(121)) * 0.5)) end,
    descricaoEfeito = "aumenta a velocidade de ataque com arremesso", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Teus dedos são ágeis.", [2]="Arremessas mais rápido.", [3]="Velocidade mortal."}
}
HABILIDADES[12121] = {
    nome = "Alcance Ampliado", tipo = "passiva", dominio = {121}, nivelMin = 11,
    efeito = function(p)
        if getNivelPorAfinidade(p:getDominioAfinidade(121)) >= 11 then p:setRangeModifier(1) end
    end,
    descricaoEfeito = "+1 alcance com armas de arremesso", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Vês mais longe.", [2]="O alvo está ao teu alcance.", [3]="Nada escapa."}
}
HABILIDADES[12122] = {
    nome = "Munição de Reserva", tipo = "passiva", dominio = {121}, nivelMin = 13,
    efeito = function(p) p:setStorageValue(97831, math.min(10 + getNivelPorAfinidade(p:getDominioAfinidade(121)) * 0.4, 25)) end,
    descricaoEfeito = "chance de não consumir munição", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Encontras uma reserva.", [2]="A munição não acabou.", [3]="Sempre preparado."}
}
HABILIDADES[12123] = {
    nome = "Foco do Atleta", tipo = "passiva", dominio = {121}, nivelMin = 15,
    efeito = function(p)
        if getNivelPorAfinidade(p:getDominioAfinidade(121)) >= 15 and not hasShield(p) then
            local moveBonus = Condition(CONDITION_ATTRIBUTES, CONDITIONID_COMBAT, -1)
            moveBonus:setParameter(CONDITION_PARAM_SUBID, 201)
            moveBonus:setParameter(CONDITION_PARAM_SPEED, math.floor(p:getBaseSpeed() * 0.10))
            moveBonus:setParameter(CONDITION_PARAM_BUFF_SPELL, true)
            p:addCondition(moveBonus)
        end
    end,
    descricaoEfeito = "sem escudo: +10% velocidade de movimento", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Corres como o vento.", [2]="Nenhum campo é obstáculo.", [3]="Atleta nato."}
}
HABILIDADES[12124] = {
    nome = "Postura do Espartano", tipo = "passiva", dominio = {121}, nivelMin = 17,
    efeito = function(p)
        if hasShield(p) then
            p:setStorageValue(97832, math.floor(getNivelPorAfinidade(p:getDominioAfinidade(121)) * 0.3))
        end
    end,
    descricaoEfeito = "com escudo: reduz dano recebido", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="O escudo é a tua fortaleza.", [2]="Inquebrável.", [3]="Defesa espartana."}
}

-- Transformações (3)
HABILIDADES[12130] = {
    nome = "Sede de Batalha", tipo = "transformacao", dominio = {121}, nivelMin = 8,
    efeito = function(p)
        if getNivelPorAfinidade(p:getDominioAfinidade(121)) >= 8 then
            p:setStorageValue(97840, 1)
        end
    end,
    descricaoEfeito = "parte do dano causado recupera vida", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="O combate alimenta-te!", [2]="Sede de batalha.", [3]="Cada golpe fortalece."}
}
HABILIDADES[12131] = {
    nome = "Manto do Caçador", tipo = "transformacao", dominio = {121}, nivelMin = 14,
    efeito = function(p)
        if getNivelPorAfinidade(p:getDominioAfinidade(121)) >= 14 then
            local lastDmg = p:getStorageValue(97811) or 0
            if os.time() - lastDmg >= 3 then p:setStealth(true) end
        end
    end,
    descricaoEfeito = "furtividade quando não sofre dano", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Desapareces nas sombras.", [2]="O caçador torna-se a presa.", [3]="Invisível."}
}
HABILIDADES[12132] = {
    nome = "Fúria do Espartano", tipo = "transformacao", dominio = {121}, nivelMin = 19,
    efeito = function(p)
        if hasShield(p) and getNivelPorAfinidade(p:getDominioAfinidade(121)) >= 19 then
            p:setStorageValue(97841, 1)
        end
    end,
    descricaoEfeito = "com escudo: riposta em área ao bloquear", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="A fúria espartana desperta!", [2]="Cada bloqueio é um ataque.", [3]="O escudo é uma arma."}
}

print("DEBUG: habilidades_arremesso.lua (v1.2) carregado.")