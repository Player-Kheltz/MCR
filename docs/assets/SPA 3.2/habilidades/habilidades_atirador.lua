--[[
    Projeto MCR ? Habilidades de Atirador / Arcos (v1.2)
    Especialidade: Arcos (120)
    Animações corrigidas.
--]]

-- ============================================================
-- ÁRVORE I-IV: ARCOS (120)
-- ============================================================

HABILIDADES[12001] = {
    nome = "Arco Tenso", tipo = "passiva", dominio = {120}, nivelMin = 5,
    efeito = function(p) p:setStorageValue(97401, math.floor(getNivelPorAfinidade(p:getDominioAfinidade(120)) * 0.8)) end,
    descricaoEfeito = "+0.8% dano por nível com Arcos", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="A corda está tensa.", [2]="O arco pede para disparar.", [3]="Potência máxima."}
}
HABILIDADES[12002] = {
    nome = "Mira Focada", tipo = "passiva", dominio = {120}, nivelMin = 10,
    efeito = function(p) p:setStorageValue(97402, math.min(5 + getNivelPorAfinidade(p:getDominioAfinidade(120)) * 0.5, 25)) end,
    descricaoEfeito = "chance de ignorar armadura com Arcos", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Vês o ponto fraco.", [2]="A mira não falha.", [3]="Foco absoluto."}
}
HABILIDADES[12003] = {
    nome = "Paciência do Atirador", tipo = "transformacao", dominio = {120}, nivelMin = 15,
    efeito = function(p)
        if getNivelPorAfinidade(p:getDominioAfinidade(120)) >= 15 then p:setStorageValue(97410, 1) end
    end,
    descricaoEfeito = "quanto mais esperas entre ataques, mais dano causas", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Cada segundo conta.", [2]="A paciência é uma virtude.", [3]="Esperas o momento certo."}
}
HABILIDADES[12004] = {
    nome = "Tiro da Morte", tipo = "passiva", dominio = {120}, nivelMin = 20,
    efeito = function(p) p:setStorageValue(97403, 1) end,
    descricaoEfeito = "aprimora a Paciência do Atirador e ensina-a ao Arremesso", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="És a morte silenciosa.", [2]="Nenhum alvo sobrevive.", [3]="Maestria do arco."}
}

-- ============================================================
-- COMPLEMENTARES ? ARCOS (120)
-- ============================================================

HABILIDADES[12010] = {
    nome = "Disparo Duplo", tipo = "gatilho", dominio = {120}, nivelMin = 6,
    gatilho = "onAttack", chanceBase = 8, chanceLampejo = 16, chanceVinculo = 24,
    async = true, buffType = "custom",
    efeito = function(p, t, d)
        local habId = 12010
        p:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 1)
        local pid, tid = p:getId(), t:getId()
        local dmg = math.floor(d * 0.6)
        addEvent(function()
            local pl, ta = Player(pid), Creature(tid)
            if pl and ta then
                doTargetCombatHealth(pl, ta, COMBAT_PHYSICALDAMAGE, dmg, dmg, CONST_ME_DRAWBLOOD)
                local anim = getDistanceAnim(pl)
                if anim then sendDistanceEffect(pl, ta, anim, CONST_ME_DRAWBLOOD)
                else ta:getPosition():sendMagicEffect(CONST_ME_DRAWBLOOD) end
            end
            if pl then pl:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 0) end
        end, 200)
    end,
    descricaoEfeito = "dispara uma segunda flecha", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Duas flechas partem em uníssono!", [2]="Disparo veloz.", [3]="Uma segunda flecha segue."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.5}}
}
HABILIDADES[12011] = {
    nome = "Flecha Envenenada", tipo = "gatilho", dominio = {120}, nivelMin = 8,
    gatilho = "onAttack", chanceBase = 10, chanceLampejo = 18, chanceVinculo = 25,
    buffType = "nextAttackCondition", conditionType = CONDITION_POISON, conditionDuration = 4000, conditionDamage = 12,
    descricaoEfeito = "próximo ataque envenena o alvo", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="A flecha traz a morte lenta.", [2]="Veneno na ponta.", [3]="O alvo adoece."},
    posturaMod = {[1]={chanceMult=1.2}, [2]={}, [3]={chanceMult=0.8}}
}
HABILIDADES[12012] = {
    nome = "Flecha Atordoante", tipo = "gatilho", dominio = {120}, nivelMin = 11,
    gatilho = "onAttack", chanceBase = 8, chanceLampejo = 14, chanceVinculo = 20,
    buffType = "nextAttackCondition", conditionType = CONDITION_DAZZLED, conditionDuration = 2000,
    descricaoEfeito = "próximo ataque atordoa o alvo", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="A flecha atordoa o inimigo.", [2]="Impacto na cabeça.", [3]="O alvo cambaleia."},
    posturaMod = {[1]={chanceMult=1.2}, [2]={}, [3]={chanceMult=0.8}}
}
HABILIDADES[12013] = {
    nome = "Disparo Triplo", tipo = "gatilho", dominio = {120}, nivelMin = 14,
    gatilho = "onAttack", chanceBase = 4, chanceLampejo = 10, chanceVinculo = 18,
    async = true, buffType = "custom",
    efeito = function(p, t, d)
        local habId = 12013
        p:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 1)
        local pid, tid = p:getId(), t:getId()
        local dmg = math.floor(d * 0.5)
        for i = 1, 2 do
            addEvent(function()
                local pl, ta = Player(pid), Creature(tid)
                if pl and ta then
                    doTargetCombatHealth(pl, ta, COMBAT_PHYSICALDAMAGE, dmg, dmg, CONST_ME_DRAWBLOOD)
                    local anim = getDistanceAnim(pl)
                    if anim then sendDistanceEffect(pl, ta, anim, CONST_ME_DRAWBLOOD)
                    else ta:getPosition():sendMagicEffect(CONST_ME_DRAWBLOOD) end
                end
                if i == 2 and pl then pl:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 0) end
            end, i * 200)
        end
    end,
    descricaoEfeito = "três flechas em rápida sucessão", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Três flechas cruzam o ar!", [2]="Disparo triplo.", [3]="Mortalidade garantida."},
    posturaMod = {[1]={chanceMult=1.5}, [2]={}, [3]={chanceMult=0.3}}
}
HABILIDADES[12014] = {
    nome = "Tiro de Ricochete", tipo = "gatilho", dominio = {120}, nivelMin = 16,
    gatilho = "onAttack", chanceBase = 6, chanceLampejo = 12, chanceVinculo = 18,
    buffType = "custom",
    efeito = function(p, t, d)
        local pos = t:getPosition()
        for _, c in ipairs(getCreaturesInArea(pos, 3, 3)) do
            if c:isMonster() and c ~= t then
                doTargetCombatHealth(p, c, COMBAT_PHYSICALDAMAGE, math.floor(d * 0.4), math.floor(d * 0.4), CONST_ME_HITAREA)
                local anim = getDistanceAnim(p)
                if anim then sendDistanceEffect(p, c, anim, CONST_ME_HITAREA)
                else c:getPosition():sendMagicEffect(CONST_ME_HITAREA) end
                break
            end
        end
    end,
    descricaoEfeito = "a flecha ricocheteia para um inimigo próximo", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="A flecha ressalta!", [2]="Ricochete certeiro.", [3]="Atinge outro alvo."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.7}}
}
HABILIDADES[12015] = {
    nome = "Flecha Explosiva", tipo = "gatilho", dominio = {120}, nivelMin = 18,
    gatilho = "onAttack", chanceBase = 5, chanceLampejo = 10, chanceVinculo = 16,
    buffType = "custom",
    efeito = function(p, t, d)
        local pos = t:getPosition()
        for _, c in ipairs(getCreaturesInArea(pos, 2, 2)) do
            if c:isMonster() then
                doTargetCombatHealth(p, c, COMBAT_FIREDAMAGE, math.floor(d * 0.5), math.floor(d * 0.5), CONST_ME_FIREAREA)
            end
        end
    end,
    efeitoVisual = function(p, t) t:getPosition():sendMagicEffect(CONST_ME_FIREAREA) end,
    descricaoEfeito = "explosão em área com dano de fogo", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="A flecha explode em chamas!", [2]="Explosão em área.", [3]="Fogo à distância."},
    posturaMod = {[1]={chanceMult=1.4}, [2]={}, [3]={chanceMult=0.4}}
}
HABILIDADES[12016] = {
    nome = "Seta Fantasma", tipo = "gatilho", dominio = {120}, nivelMin = 12,
    gatilho = "onAttack", chanceBase = 7, chanceLampejo = 13, chanceVinculo = 20,
    buffType = "custom",
    efeito = function(p, t, d)
        doTargetCombatHealth(p, t, COMBAT_PHYSICALDAMAGE, d, d, CONST_ME_ENERGYHIT)
    end,
    efeitoVisual = function(p, t) t:getPosition():sendMagicEffect(CONST_ME_ENERGYHIT) end,
    descricaoEfeito = "atravessa a armadura do alvo", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="A seta fantasma atravessa tudo!", [2]="Nada a detém.", [3]="Armadura inútil."},
    posturaMod = {[1]={chanceMult=1.2}, [2]={}, [3]={chanceMult=0.8}}
}

-- Passivas (5)
HABILIDADES[12020] = {
    nome = "Olho de Lince", tipo = "passiva", dominio = {120}, nivelMin = 7,
    efeito = function(p)
        if getNivelPorAfinidade(p:getDominioAfinidade(120)) >= 7 then p:setRangeModifier(1) end
    end,
    descricaoEfeito = "+1 tile de alcance com Arcos", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Vês o invisível.", [2]="Nenhum alvo está longe.", [3]="Olho de lince."}
}
HABILIDADES[12021] = {
    nome = "Flechas Perfurantes", tipo = "passiva", dominio = {120}, nivelMin = 9,
    efeito = function(p) p:setStorageValue(97420, math.min(5 + getNivelPorAfinidade(p:getDominioAfinidade(120)) * 0.4, 20)) end,
    descricaoEfeito = "chance de perfurar armadura do alvo", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="A flecha não encontra resistência.", [2]="Armadura atravessada.", [3]="Nada te bloqueia."}
}
HABILIDADES[12022] = {
    nome = "Ritmo do Arqueiro", tipo = "passiva", dominio = {120}, nivelMin = 13,
    efeito = function(p) p:setStorageValue(97421, math.floor(getNivelPorAfinidade(p:getDominioAfinidade(120)) * 0.5)) end,
    descricaoEfeito = "aumenta a velocidade de ataque com Arcos", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="O arco dança nas tuas mãos.", [2]="Ritmo acelerado.", [3]="Disparos mais rápidos."}
}
HABILIDADES[12023] = {
    nome = "Postura de Tiro", tipo = "passiva", dominio = {120}, nivelMin = 15,
    efeito = function(p)
        if getNivelPorAfinidade(p:getDominioAfinidade(120)) >= 15 then p:setStorageValue(97422, 1) end
    end,
    descricaoEfeito = "ficar parado aumenta o dano do próximo disparo", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="Fincas os pés e miras.", [2]="Postura de tiro.", [3]="A quietude traz precisão."}
}
HABILIDADES[12024] = {
    nome = "Mestre Arqueiro", tipo = "passiva", dominio = {120}, nivelMin = 17,
    efeito = function(p)
        if getNivelPorAfinidade(p:getDominioAfinidade(120)) >= 17 then p:setStorageValue(97423, 5) end
    end,
    descricaoEfeito = "+5% chance para todas as habilidades de Arcos", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="A maestria aproxima-se.", [2]="Cada flecha é uma sentença.", [3]="Mestre arqueiro."}
}

-- Transformações (3)
HABILIDADES[12030] = {
    nome = "Vento nas Costas", tipo = "transformacao", dominio = {120}, nivelMin = 10,
    efeito = function(p)
        if getNivelPorAfinidade(p:getDominioAfinidade(120)) >= 10 then p:setStorageValue(97430, 1) end
    end,
    descricaoEfeito = "ganha velocidade de movimento após matar", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="O vento impele-te.", [2]="Corres como uma rajada.", [3]="Vento nas costas."}
}
HABILIDADES[12031] = {
    nome = "Arqueiro Fantasma", tipo = "transformacao", dominio = {120}, nivelMin = 16,
    efeito = function(p)
        if getNivelPorAfinidade(p:getDominioAfinidade(120)) >= 16 then
            local lastDmg = p:getStorageValue(97811) or 0
            if os.time() - lastDmg >= 2 then p:setStealth(true) end
        end
    end,
    descricaoEfeito = "furtividade rápida quando não sofre dano", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="És uma sombra.", [2]="Arqueiro fantasma.", [3]="Ninguém te vê."}
}
HABILIDADES[12032] = {
    nome = "Chuva de Flechas", tipo = "transformacao", dominio = {120}, nivelMin = 19,
    efeito = function(p)
        if getNivelPorAfinidade(p:getDominioAfinidade(120)) >= 19 then p:setStorageValue(97431, 1) end
    end,
    descricaoEfeito = "aumenta o número de projéteis das habilidades de múltiplos disparos", cor = COR.DOM_COMBATE_PRECISAO,
    mensagem = {[1]="O céu enche-se de flechas!", [2]="Ninguém escapa.", [3]="Chuva de morte."}
}

print("DEBUG: habilidades_atirador.lua (v1.2) carregado.")