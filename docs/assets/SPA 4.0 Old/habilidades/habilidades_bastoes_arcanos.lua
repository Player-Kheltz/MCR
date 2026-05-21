--[[
    Projeto MCR ? SPA v4.0 ? Habilidades de Bastões Arcanos (133)
    Estilo: Mago de Combate com bastões elementais (two?handed). Sinergia com domínios elementais.
    Recursos: Chi (Harmony), Virtude da Sustentação, afinidade elemental obrigatória.
--]]

-- ============================================================
-- ÁRVORE I-IV: BASTÕES ARCANOS (133)
-- ============================================================

-- I (5) ? Passiva: Sintonia Arcana
HABILIDADES[13301] = {
    nome = "Sintonia Arcana",
    tipo = "passiva",
    dominio = {133},
    nivelMin = 5,
    efeito = function(player)
        player:setVirtue(Virtue_t.Sustain)
        local weapon = player:getSlotItem(CONST_SLOT_LEFT) or player:getSlotItem(CONST_SLOT_RIGHT)
        if weapon then
            local elemento = weapon:getElementalBond() or ELEMENTAL_BOND[weapon:getId()]
            if elemento then
                local dominioElemental = elemento == COMBAT_FIREDAMAGE and 23 or (elemento == COMBAT_ICEDAMAGE and 24 or (elemento == COMBAT_EARTHDAMAGE and 25 or (elemento == COMBAT_ENERGYDAMAGE and 23 or 0)))
                player:setCombatModifier("bastao_elemento", elemento)
                player:setCombatModifier("bastao_dominio", dominioElemental)
            end
        end
    end,
    descricaoEfeito = function(player)
        local weapon = player:getSlotItem(CONST_SLOT_LEFT) or player:getSlotItem(CONST_SLOT_RIGHT)
        if weapon then
            local elemento = weapon:getElementalBond() or ELEMENTAL_BOND[weapon:getId()]
            if elemento then
                return "dano elemental escala com domínio elemental da arma"
            end
        end
        return "sem bastão: sem efeito"
    end,
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    mensagem = {[1]="O bastão vibra com poder arcano.", [2]="Sintonia estabelecida.", [3]="Elemento canalizado."}
}

-- II (10) ? Passiva: Fluxo de Chi
HABILIDADES[13302] = {
    nome = "Fluxo de Chi",
    tipo = "passiva",
    dominio = {133},
    nivelMin = 10,
    efeito = function(player)
        player:fillHarmony()
        player:setStorageValue(STORAGE.HARMONY, 5)
        player:setCombatModifier("chi_geracao", 1.0)
    end,
    descricaoEfeito = "acumula Chi máximo",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    mensagem = {[1]="O Chi flui em ti.", [2]="Energia interior.", [3]="Poder acumulado."}
}

-- III (15) ? Gatilho: Explosão Arcana (consome Chi)
HABILIDADES[13303] = {
    nome = "Explosão Arcana",
    tipo = "gatilho",
    dominio = {133},
    nivelMin = 15,
    gatilho = "onAttack",
    chanceBase = 100,
    condicao = "5Golpes",
    buffType = "custom",
    efeito = function(player, target, damage)
        local harmony = player:getStorageValue(STORAGE.HARMONY) or 0
        if harmony < 5 then return end
        player:setStorageValue(STORAGE.HARMONY, harmony - 5)
        local elemento = player:getCombatModifier("bastao_elemento")
        if not elemento or elemento == 0 then return end
        local dominio = player:getCombatModifier("bastao_dominio")
        local nivelElemental = dominio > 0 and getNivelPorAfinidade(player:getDominioAfinidade(dominio)) or 0
        local bonus = 1.0 + nivelElemental * 0.1
        local dmg = math.floor(damage * 0.5 * bonus)
        local pos = target:getPosition()
        for _, c in ipairs(getCreaturesInArea(pos, 3, 3)) do
            if c:isMonster() then
                doTargetCombatHealth(player, c, elemento, dmg, dmg, CONST_ME_FIREAREA)
            end
        end
    end,
    efeitoVisual = function(player, target) target:getPosition():sendMagicEffect(CONST_ME_FIREAREA) end,
    descricaoEfeito = "gasta 5 Chi, explosão elemental em área escalando com domínio elemental",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    mensagem = {[1]="Explosão arcana!", [2]="O bastão libera poder.", [3]="Ninguém resiste."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.7}}
}

-- IV (20) ? Passiva: Avatar Elemental
HABILIDADES[13304] = {
    nome = "Avatar Elemental",
    tipo = "passiva",
    dominio = {133},
    nivelMin = 20,
    efeito = function(player)
        player:setSerene(true)
        player:setCombatModifier("avatar_elemental", 1)
    end,
    descricaoEfeito = "Serenidade ativa, dano elemental máximo",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    mensagem = {[1]="És o avatar do elemento.", [2]="Poder absoluto.", [3]="O bastão é uma extensão de ti."}
}

-- ============================================================
-- COMPLEMENTARES ? BASTÕES ARCANOS (133) ? 7G, 5P, 3T
-- ============================================================

-- Gatilho 1: Rajada Elemental (nível 7)
HABILIDADES[13310] = {
    nome = "Rajada Elemental",
    tipo = "gatilho",
    dominio = {133},
    nivelMin = 7,
    gatilho = "onAttack",
    chanceBase = 12,
    chanceLampejo = 20,
    chanceVinculo = 28,
    buffType = "custom",
    efeito = function(player, target, damage)
        local elemento = player:getCombatModifier("bastao_elemento")
        if not elemento or elemento == 0 then return end
        local dmg = math.floor(damage * 0.3)
        doTargetCombatHealth(player, target, elemento, dmg, dmg, CONST_ME_ENERGYHIT)
    end,
    descricaoEfeito = "causa dano extra do elemento da arma",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    mensagem = {[1]="Rajada elemental!", [2]="O elemento golpeia.", [3]="Poder arcano."},
    posturaMod = {[1]={chanceMult=1.2}, [2]={}, [3]={chanceMult=0.8}}
}

-- Gatilho 2: Bastão Sísmico (nível 9)
HABILIDADES[13311] = {
    nome = "Bastão Sísmico",
    tipo = "gatilho",
    dominio = {133},
    nivelMin = 9,
    gatilho = "onAttack",
    chanceBase = 10,
    chanceLampejo = 18,
    chanceVinculo = 25,
    buffType = "custom",
    efeito = function(player, target, damage)
        local elemento = player:getCombatModifier("bastao_elemento") or COMBAT_PHYSICALDAMAGE
        local pos = target:getPosition()
        for _, c in ipairs(getCreaturesInArea(pos, 1, 1)) do
            if c:isMonster() and c ~= target then
                doTargetCombatHealth(player, c, elemento, math.floor(damage * 0.3), math.floor(damage * 0.3), CONST_ME_GROUNDSHAKER)
            end
        end
    end,
    efeitoVisual = function(player, target) target:getPosition():sendMagicEffect(CONST_ME_GROUNDSHAKER) end,
    descricaoEfeito = "impacto elemental em área pequena",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    mensagem = {[1]="O chão treme!", [2]="Impacto sísmico.", [3]="Ninguém foge."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.7}}
}

-- Gatilho 3: Dreno Arcano (nível 11)
HABILIDADES[13312] = {
    nome = "Dreno Arcano",
    tipo = "gatilho",
    dominio = {133},
    nivelMin = 11,
    gatilho = "onAttack",
    chanceBase = 8,
    chanceLampejo = 14,
    chanceVinculo = 20,
    buffType = "lifeLeech",
    leechPercent = 10,
    durationSec = 4,
    descricaoEfeito = "roubo de vida por 4 segundos",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    mensagem = {[1]="O bastão drena vida.", [2]="Energia vital roubada.", [3]="Poder sombrio."},
    posturaMod = {[1]={chanceMult=1.2}, [2]={}, [3]={chanceMult=0.8}}
}

-- Gatilho 4: Escudo Arcano (nível 14)
HABILIDADES[13313] = {
    nome = "Escudo Arcano",
    tipo = "gatilho",
    dominio = {133},
    nivelMin = 14,
    gatilho = "onReceiveDamage",
    chanceBase = 10,
    chanceLampejo = 18,
    chanceVinculo = 25,
    buffType = "custom",
    efeito = function(player, attacker, damage)
        local elemento = player:getCombatModifier("bastao_elemento") or COMBAT_ENERGYDAMAGE
        -- Devolve 20% do dano como dano elemental ao atacante
        local reflect = math.floor(damage * 0.2)
        doTargetCombatHealth(player, attacker, elemento, reflect, reflect, CONST_ME_ENERGYHIT)
    end,
    descricaoEfeito = "devolve 20% do dano recebido como dano elemental",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    mensagem = {[1]="Escudo arcano!", [2]="O dano é refletido.", [3]="Proteção elemental."},
    posturaMod = {[1]={chanceMult=0.8}, [2]={}, [3]={chanceMult=1.5}}
}

-- Gatilho 5: Vórtice de Energia (nível 16)
HABILIDADES[13314] = {
    nome = "Vórtice de Energia",
    tipo = "gatilho",
    dominio = {133},
    nivelMin = 16,
    gatilho = "onAttack",
    condicao = "cercado",
    chanceBase = 10,
    chanceLampejo = 18,
    chanceVinculo = 25,
    buffType = "custom",
    efeito = function(player, target, damage)
        local elemento = player:getCombatModifier("bastao_elemento") or COMBAT_ENERGYDAMAGE
        local pos = player:getPosition()
        for _, c in ipairs(getCreaturesInArea(pos, 3, 3)) do
            if c:isMonster() and c ~= target then
                doTargetCombatHealth(player, c, elemento, math.floor(damage * 0.4), math.floor(damage * 0.4), CONST_ME_ENERGYHIT)
            end
        end
    end,
    efeitoVisual = function(player, target) player:getPosition():sendMagicEffect(CONST_ME_ENERGYHIT) end,
    descricaoEfeito = "libera energia elemental em área ao redor",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    mensagem = {[1]="Vórtice de energia!", [2]="O poder irradia.", [3]="Ninguém se aproxima."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.7}}
}

-- Gatilho 6: Toque do Vazio (nível 18)
HABILIDADES[13315] = {
    nome = "Toque do Vazio",
    tipo = "gatilho",
    dominio = {133},
    nivelMin = 18,
    gatilho = "onAttack",
    chanceBase = 5,
    chanceLampejo = 10,
    chanceVinculo = 16,
    buffType = "custom",
    efeito = function(player, target, damage)
        local elemento = player:getCombatModifier("bastao_elemento") or COMBAT_DEATHDAMAGE
        local dmg = math.floor(damage * 1.5)
        doTargetCombatHealth(player, target, elemento, dmg, dmg, CONST_ME_MORTAREA)
    end,
    efeitoVisual = function(player, target) target:getPosition():sendMagicEffect(CONST_ME_MORTAREA) end,
    descricaoEfeito = "golpe massivo de energia sombria",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    mensagem = {[1]="O vazio te atende!", [2]="Toque sombrio.", [3]="Poder absoluto."},
    posturaMod = {[1]={chanceMult=1.5}, [2]={}, [3]={chanceMult=0.3}}
}

-- Gatilho 7: Combo Elemental (nível 19)
HABILIDADES[13316] = {
    nome = "Combo Elemental",
    tipo = "gatilho",
    dominio = {133},
    nivelMin = 19,
    gatilho = "onAttack",
    chanceBase = 4,
    chanceLampejo = 10,
    chanceVinculo = 18,
    async = true,
    buffType = "custom",
    efeito = function(player, target, damage)
        local elemento = player:getCombatModifier("bastao_elemento") or COMBAT_ENERGYDAMAGE
        local habId = 13316
        player:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 1)
        local pid, tid = player:getId(), target:getId()
        local dmg = math.floor(damage * 0.8)
        for i = 1, 3 do
            addEvent(function()
                local pl, ta = Player(pid), Creature(tid)
                if pl and ta then
                    doTargetCombatHealth(pl, ta, elemento, dmg, dmg, CONST_ME_ENERGYHIT)
                end
                if i == 3 and pl then pl:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 0) end
            end, i * 150)
        end
    end,
    descricaoEfeito = "três golpes elementais consecutivos",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    mensagem = {[1]="Combo elemental!", [2]="Três golpes arcanos.", [3]="Ninguém resiste."},
    posturaMod = {[1]={chanceMult=1.5}, [2]={}, [3]={chanceMult=0.3}}
}

-- Passiva 1: Mente Arcana (nível 6)
HABILIDADES[13320] = {
    nome = "Mente Arcana",
    tipo = "passiva",
    dominio = {133},
    nivelMin = 6,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(133))
        player:setCombatModifier("custo_mana_reduzido", nivel * 0.5)
    end,
    descricaoEfeito = "reduz custo de mana em %",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    mensagem = {[1]="Mente arcana.", [2]="Mana preservada.", [3]="Economia mágica."}
}

-- Passiva 2: Pele Elemental (nível 8)
HABILIDADES[13321] = {
    nome = "Pele Elemental",
    tipo = "passiva",
    dominio = {133},
    nivelMin = 8,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(133))
        player:setCombatModifier("absorcao_elemental", nivel * 0.3)
    end,
    descricaoEfeito = "absorve % do dano elemental recebido",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    mensagem = {[1]="Pele elemental.", [2]="O elemento te protege.", [3]="Resistência arcana."}
}

-- Passiva 3: Aura do Mago (nível 12)
HABILIDADES[13322] = {
    nome = "Aura do Mago",
    tipo = "passiva",
    dominio = {133},
    nivelMin = 12,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(133))
        player:setCombatModifier("aura_dano_proximos", nivel * 0.2)
    end,
    descricaoEfeito = "inimigos próximos sofrem dano elemental passivo",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    mensagem = {[1]="Aura do mago.", [2]="O ar ao redor queima.", [3]="Presença arcana."}
}

-- Passiva 4: Concentração (nível 15)
HABILIDADES[13323] = {
    nome = "Concentração",
    tipo = "passiva",
    dominio = {133},
    nivelMin = 15,
    efeito = function(player)
        if getNivelPorAfinidade(player:getDominioAfinidade(133)) >= 15 then
            player:setCombatModifier("interrupcao_imune", 1)
        end
    end,
    descricaoEfeito = "imune a interrupção de magias",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    mensagem = {[1]="Concentração absoluta.", [2]="Nada te distrai.", [3]="Foco arcano."}
}

-- Passiva 5: Maestria Arcana (nível 17)
HABILIDADES[13324] = {
    nome = "Maestria Arcana",
    tipo = "passiva",
    dominio = {133},
    nivelMin = 17,
    efeito = function(player)
        if getNivelPorAfinidade(player:getDominioAfinidade(133)) >= 17 then
            player:setCombatModifier("dano_elemental_extra", 10)
        end
    end,
    descricaoEfeito = "+10% dano elemental",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    mensagem = {[1]="Maestria arcana.", [2]="Poder amplificado.", [3]="O elemento obedece."}
}

-- Transformação 1: Canalização (nível 10)
HABILIDADES[13330] = {
    nome = "Canalização",
    tipo = "transformacao",
    dominio = {133},
    nivelMin = 10,
    efeito = function(player)
        if getNivelPorAfinidade(player:getDominioAfinidade(133)) >= 10 then
            player:setCombatModifier("canalizacao_ativa", 1)
        end
    end,
    descricaoEfeito = "magias canalizadas causam mais dano",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    mensagem = {[1]="Canalização iniciada.", [2]="Poder concentrado.", [3]="Energia flui."}
}

-- Transformação 2: Forma Etérea (nível 16)
HABILIDADES[13331] = {
    nome = "Forma Etérea",
    tipo = "transformacao",
    dominio = {133},
    nivelMin = 16,
    efeito = function(player)
        if getNivelPorAfinidade(player:getDominioAfinidade(133)) >= 16 then
            player:setCombatModifier("etereo", 1)
            player:setStealth(true)
        end
    end,
    descricaoEfeito = "fica furtivo e ganha velocidade",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    mensagem = {[1]="Forma etérea.", [2]="Invisível.", [3]="O bastão some na névoa."}
}

-- Transformação 3: Avatar Elemental (nível 20)
HABILIDADES[13332] = {
    nome = "Avatar Elemental",
    tipo = "transformacao",
    dominio = {133},
    nivelMin = 20,
    efeito = function(player)
        player:setSerene(true)
        player:setCombatModifier("avatar_elemental", 1)
    end,
    descricaoEfeito = "converte 100% do dano para elemental e aumenta em 50%",
    cor = COR.DOM_MAGIA_RUNOLOGIA,
    mensagem = {[1]="Avatar elemental!", [2]="És o elemento.", [3]="Poder infinito."}
}

print("DEBUG: habilidades_bastoes_arcanos.lua v4.0 carregado.")