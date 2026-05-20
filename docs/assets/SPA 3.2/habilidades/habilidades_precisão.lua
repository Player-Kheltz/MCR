--[[
    Projeto MCR ? Habilidades de Precisão (v1.2)
    Domínio Secundário: Precisão (13)
    Partilhado entre Arcos (120) e Arremesso (121)
    Animações corrigidas.
--]]

HABILIDADES[1301] = {
    nome = "Disparo Preciso", tipo = "gatilho", dominio = {13}, nivelMin = 6,
    gatilho = "onAttack", chanceBase = 10, chanceLampejo = 18, chanceVinculo = 25,
    buffType = "custom",
    efeito = function(p, t, d)
        local n = getNivelPorAfinidade(p:getDominioAfinidade(13))
        doTargetCombatHealth(p, t, COMBAT_PHYSICALDAMAGE, math.floor(d * (0.10 + n * 0.01)), math.floor(d * (0.10 + n * 0.01)), CONST_ME_DRAWBLOOD)
    end,
    efeitoVisual = function(p, t) t:getPosition():sendMagicEffect(CONST_ME_DRAWBLOOD) end,
    descricaoEfeito = "causa dano adicional preciso", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Um tiro perfeito!", [2]="A pontaria é impecável.", [3]="Disparo preciso."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.7}}
}
HABILIDADES[1302] = {
    nome = "Tiro em Movimento", tipo = "gatilho", dominio = {13}, nivelMin = 8,
    gatilho = "onAttack", chanceBase = 12, chanceLampejo = 20, chanceVinculo = 28,
    buffType = "speedBurst", buffMultiplier = 0.15, buffDurationMs = 500,
    descricaoEfeito = "aumenta a velocidade de ataque brevemente", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Atiras em movimento!", [2]="Rápido como o vento.", [3]="Velocidade de disparo."},
    posturaMod = {[1]={chanceMult=1.4}, [2]={}, [3]={chanceMult=0.6}}
}
HABILIDADES[1303] = {
    nome = "Tiro Debilitante", tipo = "gatilho", dominio = {13}, nivelMin = 10,
    gatilho = "onAttack", chanceBase = 10, chanceLampejo = 18, chanceVinculo = 24,
    buffType = "nextAttackCondition", conditionType = CONDITION_PARALYZE, conditionDuration = 2000,
    descricaoEfeito = "próximo ataque reduz a velocidade do alvo", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="O projétil prende o alvo!", [2]="Tiro debilitante.", [3]="Movimento reduzido."},
    posturaMod = {[1]={chanceMult=1.2}, [2]={}, [3]={chanceMult=0.8}}
}
HABILIDADES[1304] = {
    nome = "Rajada de Projéteis", tipo = "gatilho", dominio = {13}, nivelMin = 14,
    gatilho = "onAttack", chanceBase = 6, chanceLampejo = 12, chanceVinculo = 20,
    async = true, buffType = "custom",
    efeito = function(p, t, d)
        local habId = 1304
        p:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 1)
        local pid, tid = p:getId(), t:getId()
        local dmg = math.floor(d * 0.5)
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
    descricaoEfeito = "dispara dois projéteis adicionais em sucessão", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Rajada de projéteis!", [2]="Múltiplos disparos.", [3]="O ar enche-se de aço."},
    posturaMod = {[1]={chanceMult=1.5}, [2]={}, [3]={chanceMult=0.3}}
}
HABILIDADES[1305] = {
    nome = "Tiro de Precisão", tipo = "gatilho", dominio = {13}, nivelMin = 16,
    gatilho = "onAttack", chanceBase = 8, chanceLampejo = 14, chanceVinculo = 22,
    buffType = "damageBoost", percentExtra = 25, buffHits = 2,
    descricaoEfeito = "aumenta o dano dos próximos 2 ataques em 25%", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="O alvo está na mira!", [2]="Tiro de precisão.", [3]="Dano concentrado."},
    posturaMod = {[1]={chanceMult=1.2}, [2]={}, [3]={chanceMult=0.8}}
}
HABILIDADES[1306] = {
    nome = "Marca do Caçador", tipo = "gatilho", dominio = {13}, nivelMin = 12,
    gatilho = "onAttack", chanceBase = 10, chanceLampejo = 18, chanceVinculo = 25,
    buffType = "lifeLeech", leechPercent = 10, durationSec = 4,
    descricaoEfeito = "roubo de vida por 4 segundos", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="A presa sangra e fortalece-te.", [2]="Marca do caçador.", [3]="Vida drenada."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.6}}
}
HABILIDADES[1307] = {
    nome = "Disparo em Área", tipo = "gatilho", dominio = {13}, nivelMin = 18,
    gatilho = "onAttack", condicao = "cercado", chanceBase = 12, chanceLampejo = 20, chanceVinculo = 30,
    buffType = "custom",
    efeito = function(p, t, d)
        local pos = t:getPosition()
        for _, c in ipairs(getCreaturesInArea(pos, 2, 2)) do
            if c:isMonster() and c ~= t then
                doTargetCombatHealth(p, c, COMBAT_PHYSICALDAMAGE, math.floor(d * 0.4), math.floor(d * 0.4), CONST_ME_HITAREA)
            end
        end
    end,
    efeitoVisual = function(p, t) t:getPosition():sendMagicEffect(CONST_ME_HITAREA) end,
    descricaoEfeito = "atinge inimigos próximos ao alvo", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Disparo em área!", [2]="Ninguém escapa.", [3]="Projétil explosivo."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.6}}
}

-- Passivas (5)
HABILIDADES[1310] = {
    nome = "Olho de Águia", tipo = "passiva", dominio = {13}, nivelMin = 5,
    efeito = function(p)
        if getNivelPorAfinidade(p:getDominioAfinidade(13)) >= 5 then p:setRangeModifier(1) end
    end,
    descricaoEfeito = "+1 tile de alcance com armas de distância", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="O horizonte aproxima-se.", [2]="Vês o alvo com nitidez.", [3]="Olho de águia."}
}
HABILIDADES[1311] = {
    nome = "Mãos Firmes", tipo = "passiva", dominio = {13}, nivelMin = 7,
    efeito = function(p) p:setStorageValue(97301, math.floor(getNivelPorAfinidade(p:getDominioAfinidade(13)) * 0.6)) end,
    descricaoEfeito = "aumenta a chance de ignorar armadura", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="O pulso não treme.", [2]="A flecha encontra a falha.", [3]="Mãos firmes."}
}
HABILIDADES[1312] = {
    nome = "Fôlego do Caçador", tipo = "passiva", dominio = {13}, nivelMin = 9,
    efeito = function(p) p:setStorageValue(97302, math.floor(getNivelPorAfinidade(p:getDominioAfinidade(13)) * 0.4)) end,
    descricaoEfeito = "aumenta a velocidade de movimento", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Corres como o vento.", [2]="Sempre em movimento.", [3]="Fôlego do caçador."}
}
HABILIDADES[1313] = {
    nome = "Reserva de Munição", tipo = "passiva", dominio = {13}, nivelMin = 11,
    efeito = function(p) p:setStorageValue(97303, math.min(10 + getNivelPorAfinidade(p:getDominioAfinidade(13)) * 0.5, 30)) end,
    descricaoEfeito = "chance de não consumir munição", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Encontras uma reserva.", [2]="A munição não acabou.", [3]="Sempre preparado."}
}
HABILIDADES[1314] = {
    nome = "Paciência do Caçador", tipo = "passiva", dominio = {13}, nivelMin = 13,
    efeito = function(p)
        if getNivelPorAfinidade(p:getDominioAfinidade(13)) >= 13 then p:setStorageValue(97304, 1) end
    end,
    descricaoEfeito = "ganha dano extra se esperar entre ataques", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="A espera recompensa.", [2]="Respiras e miras.", [3]="Paciência letal."}
}

-- Transformações (3)
HABILIDADES[1320] = {
    nome = "Furtividade do Caçador", tipo = "transformacao", dominio = {13}, nivelMin = 10,
    efeito = function(p)
        if getNivelPorAfinidade(p:getDominioAfinidade(13)) >= 10 then
            local lastDmg = p:getStorageValue(97811) or 0
            if os.time() - lastDmg >= 3 then p:setStealth(true) end
        end
    end,
    descricaoEfeito = "furtividade quando não sofre dano", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Desapareces nas sombras.", [2]="O caçador torna-se invisível.", [3]="Furtividade natural."}
}
HABILIDADES[1321] = {
    nome = "Chuva de Flechas", tipo = "transformacao", dominio = {13}, nivelMin = 15,
    efeito = function(p)
        if getNivelPorAfinidade(p:getDominioAfinidade(13)) >= 15 then p:setStorageValue(97310, 1) end
    end,
    descricaoEfeito = "habilidades de múltiplos disparos disparam um projétil extra", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="O céu escurece com as tuas flechas!", [2]="Mais projéteis.", [3]="Chuva de aço."}
}
HABILIDADES[1322] = {
    nome = "Sniper", tipo = "transformacao", dominio = {13}, nivelMin = 19,
    efeito = function(p)
        if getNivelPorAfinidade(p:getDominioAfinidade(13)) >= 19 then p:setStorageValue(97311, 1) end
    end,
    descricaoEfeito = "crítico garantido a longa distância", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Um tiro, uma morte.", [2]="O alvo está na mira.", [3]="Precisão absoluta."}
}

print("DEBUG: habilidades_precisao.lua (v1.2) carregado.")