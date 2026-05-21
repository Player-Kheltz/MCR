--[[
    Projeto MCR ? SPA v4.0 ? Habilidades de Armas de Punho (132)
--]]

-- ============================================================
-- ÁRVORE I-IV: ARMAS DE PUNHO (132)
-- ============================================================

HABILIDADES[13201] = {
    nome = "Punhos Cortantes", tipo = "passiva", dominio = {132, 14}, nivelMin = 5,
    efeito = function(player)
        player:setVirtue(Virtue_t.Harmony)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(132))
        player:setCombatModifier("punho_crit_chance", nivel * 0.5)
    end,
    descricaoEfeito = "+0.5% chance de crítico por nível",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Tuas lâminas são teus punhos.", [2]="Corte preciso.", [3]="Afiado."}
}

HABILIDADES[13202] = {
    nome = "Fluxo de Chi", tipo = "passiva", dominio = {132, 14}, nivelMin = 10,
    efeito = function(player)
        player:fillHarmony()
        player:setStorageValue(STORAGE.HARMONY, 5)
        player:setCombatModifier("chi_geracao", 1.0)
    end,
    descricaoEfeito = "acumula Chi máximo",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O Chi flui em ti.", [2]="Energia interior.", [3]="Poder acumulado."}
}

HABILIDADES[13203] = {
    nome = "Dança das Lâminas", tipo = "gatilho", dominio = {132}, nivelMin = 15,
    gatilho = "onAttack", chanceBase = 100, condicao = "5Golpes",
    buffType = "custom",
    efeito = function(player, target, damage)
        local harmony = player:getStorageValue(STORAGE.HARMONY) or 0
        if harmony < 4 then return end
        player:setStorageValue(STORAGE.HARMONY, harmony - 4)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(132))
        local hits = (nivel >= 18) and 4 or 3
        local dmg = math.floor(damage * 0.5)
        local pid, tid = player:getId(), target:getId()
        for i = 1, hits do
            addEvent(function()
                local pl, ta = Player(pid), Creature(tid)
                if pl and ta then
                    doTargetCombatHealth(pl, ta, COMBAT_PHYSICALDAMAGE, dmg, dmg, CONST_ME_DRAWBLOOD)
                end
            end, i * 100)
        end
    end,
    efeitoVisual = function(player, target) target:getPosition():sendMagicEffect(CONST_ME_DRAWBLOOD) end,
    descricaoEfeito = "gasta 4 Chi para múltiplos cortes rápidos",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Dança das lâminas!", [2]="Cortes infinitos.", [3]="O inimigo sangra."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.7}}
}

HABILIDADES[13204] = {
    nome = "Serenidade", tipo = "passiva", dominio = {132, 14}, nivelMin = 20,
    efeito = function(player) player:setSerene(true) end,
    descricaoEfeito = "Chi máximo ativa Serenidade",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="A serenidade te envolve.", [2]="Paz interior.", [3]="O Chi é infinito."}
}

-- ============================================================
-- COMPLEMENTARES ? ARMAS DE PUNHO (132) ? 7G, 5P, 3T
-- ============================================================

-- Gatilho 1: Corte Duplo (nível 7)
HABILIDADES[13210] = {
    nome = "Corte Duplo", tipo = "gatilho", dominio = {132}, nivelMin = 7,
    gatilho = "onAttack", chanceBase = 15, chanceLampejo = 25, chanceVinculo = 35,
    async = true, buffType = "custom",
    efeito = function(player, target, damage)
        local habId = 13210
        player:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 1)
        local pid, tid = player:getId(), target:getId()
        local dmg = math.floor(damage * 0.6)
        addEvent(function()
            local pl, ta = Player(pid), Creature(tid)
            if pl and ta then
                doTargetCombatHealth(pl, ta, COMBAT_PHYSICALDAMAGE, dmg, dmg, CONST_ME_DRAWBLOOD)
            end
            if pl then pl:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 0) end
        end, 100)
    end,
    descricaoEfeito = "um segundo corte rápido",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Corte duplo!", [2]="Duas lâminas.", [3]="Rápido e preciso."},
    posturaMod = {[1]={chanceMult=1.4}, [2]={}, [3]={chanceMult=0.6}}
}

-- Gatilho 2: Sangramento Profundo (nível 9)
HABILIDADES[13211] = {
    nome = "Sangramento Profundo", tipo = "gatilho", dominio = {132}, nivelMin = 9,
    gatilho = "onAttack", chanceBase = 12, chanceLampejo = 20, chanceVinculo = 28,
    buffType = "nextAttackCondition", conditionType = CONDITION_BLEEDING,
    conditionDuration = 4000, conditionDamage = 20,
    descricaoEfeito = "próximo ataque causa sangramento",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O sangue jorra.", [2]="Ferida profunda.", [3]="Sangramento."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.7}}
}

-- Gatilho 3: Golpe Atordoante (nível 11)
HABILIDADES[13212] = {
    nome = "Golpe Atordoante", tipo = "gatilho", dominio = {132}, nivelMin = 11,
    gatilho = "onAttack", chanceBase = 8, chanceLampejo = 14, chanceVinculo = 20,
    buffType = "nextAttackCondition", conditionType = CONDITION_DAZZLED,
    conditionDuration = 2000,
    descricaoEfeito = "próximo ataque atordoa",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Golpe atordoante!", [2]="O alvo cambaleia.", [3]="Impacto preciso."},
    posturaMod = {[1]={chanceMult=1.2}, [2]={}, [3]={chanceMult=0.8}}
}

-- Gatilho 4: Dreno de Chi (nível 14)
HABILIDADES[13213] = {
    nome = "Dreno de Chi", tipo = "gatilho", dominio = {132}, nivelMin = 14,
    gatilho = "onAttack", chanceBase = 10, chanceLampejo = 18, chanceVinculo = 25,
    buffType = "lifeLeech", leechPercent = 8, durationSec = 3,
    descricaoEfeito = "roubo de vida por 3 segundos",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O Chi drena o inimigo.", [2]="Vida roubada.", [3]="Energia vital."},
    posturaMod = {[1]={chanceMult=1.2}, [2]={}, [3]={chanceMult=0.8}}
}

-- Gatilho 5: Golpe Elemental (nível 16)
HABILIDADES[13214] = {
    nome = "Golpe Elemental", tipo = "gatilho", dominio = {132}, nivelMin = 16,
    gatilho = "onAttack", chanceBase = 12, chanceLampejo = 20, chanceVinculo = 28,
    buffType = "custom",
    efeito = function(player, target, damage)
        local weapon = player:getSlotItem(CONST_SLOT_LEFT) or player:getSlotItem(CONST_SLOT_RIGHT)
        if not weapon then return end
        local elemento = weapon:getElementalBond() or ELEMENTAL_BOND[weapon:getId()]
        if not elemento or elemento == COMBAT_PHYSICALDAMAGE then return end
        local dmg = math.floor(damage * 0.3)
        doTargetCombatHealth(player, target, elemento, dmg, dmg, CONST_ME_ENERGYHIT)
    end,
    descricaoEfeito = "causa dano extra do elemento da arma",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O punho carrega o elemento!", [2]="Golpe elemental.", [3]="Energia liberada."},
    posturaMod = {[1]={chanceMult=1.2}, [2]={}, [3]={chanceMult=0.8}}
}

-- Gatilho 6: Furacão de Punhos (nível 18)
HABILIDADES[13215] = {
    nome = "Furacão de Punhos", tipo = "gatilho", dominio = {132}, nivelMin = 18,
    gatilho = "onAttack", condicao = "cercado", chanceBase = 12, chanceLampejo = 20, chanceVinculo = 30,
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
    descricaoEfeito = "golpes em área ao redor",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Furacão de punhos!", [2]="Ninguém escapa.", [3]="Área devastada."},
    posturaMod = {[1]={chanceMult=1.3}, [2]={}, [3]={chanceMult=0.7}}
}

-- Gatilho 7: Execução (nível 19)
HABILIDADES[13216] = {
    nome = "Execução", tipo = "gatilho", dominio = {132}, nivelMin = 19,
    gatilho = "onAttack", condicao = "vidaBaixa", chanceBase = 25, chanceLampejo = 35, chanceVinculo = 50,
    buffType = "custom",
    efeito = function(player, target, damage)
        local bonusDmg = math.floor(damage * 0.5)
        doTargetCombatHealth(player, target, COMBAT_PHYSICALDAMAGE, bonusDmg, bonusDmg, CONST_ME_HITAREA)
    end,
    descricaoEfeito = "causa dano extra a alvos com pouca vida",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Execução!", [2]="Golpe final.", [3]="Sem piedade."},
    posturaMod = {[1]={chanceMult=1.2}, [2]={}, [3]={chanceMult=0.8}}
}

-- Passiva 1: Lâminas Afiadas (nível 6)
HABILIDADES[13220] = {
    nome = "Lâminas Afiadas", tipo = "passiva", dominio = {132, 14}, nivelMin = 6,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(132))
        player:setCombatModifier("ignorar_armadura", nivel * 0.4)
    end,
    descricaoEfeito = "ignora % da armadura do alvo",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Lâminas afiadas.", [2]="Nada as detém.", [3]="Corte preciso."}
}

-- Passiva 2: Agilidade Felina (nível 8)
HABILIDADES[13221] = {
    nome = "Agilidade Felina", tipo = "passiva", dominio = {132, 14}, nivelMin = 8,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(132))
        player:setCombatModifier("velocidade_ataque", nivel * 0.3)
    end,
    descricaoEfeito = "+velocidade de ataque",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Ágil como um felino.", [2]="Velocidade.", [3]="Golpes rápidos."}
}

-- Passiva 3: Instinto de Caça (nível 12)
HABILIDADES[13222] = {
    nome = "Instinto de Caça", tipo = "passiva", dominio = {132, 14}, nivelMin = 12,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(132))
        player:setCombatModifier("dano_criaturas_feridas", nivel * 0.5)
    end,
    descricaoEfeito = "+dano contra alvos com <50% vida",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Instinto de caça.", [2]="Presas fáceis.", [3]="O sangue chama."}
}

-- Passiva 4: Reflexos Rápidos (nível 15)
HABILIDADES[13223] = {
    nome = "Reflexos Rápidos", tipo = "passiva", dominio = {132, 14}, nivelMin = 15,
    efeito = function(player)
        if getNivelPorAfinidade(player:getDominioAfinidade(132)) >= 15 then
            player:setCombatModifier("esquiva_extra", 5)
        end
    end,
    descricaoEfeito = "+5% chance de esquiva",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Reflexos rápidos.", [2]="Esquiva natural.", [3]="Intocado."}
}

-- Passiva 5: Mestre das Lâminas (nível 17)
HABILIDADES[13224] = {
    nome = "Mestre das Lâminas", tipo = "passiva", dominio = {132, 14}, nivelMin = 17,
    efeito = function(player)
        if getNivelPorAfinidade(player:getDominioAfinidade(132)) >= 17 then
            player:setCombatModifier("crit_damage_mult", 1.5)
        end
    end,
    descricaoEfeito = "dano crítico aumentado em 50%",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Mestre das lâminas.", [2]="Crítico devastador.", [3]="Letal."}
}

-- Transformação 1: Sede de Sangue (nível 10)
HABILIDADES[13230] = {
    nome = "Sede de Sangue", tipo = "transformacao", dominio = {132, 14}, nivelMin = 10,
    efeito = function(player)
        if getNivelPorAfinidade(player:getDominioAfinidade(132)) >= 10 then
            player:setCombatModifier("sede_sangue", 1)
        end
    end,
    descricaoEfeito = "roubo de vida aumentado quando há sangramento",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Sede de sangue!", [2]="A vida alimenta.", [3]="Voraz."}
}

-- Transformação 2: Fúria do Caçador (nível 16)
HABILIDADES[13231] = {
    nome = "Fúria do Caçador", tipo = "transformacao", dominio = {132, 14}, nivelMin = 16,
    efeito = function(player)
        if getNivelPorAfinidade(player:getDominioAfinidade(132)) >= 16 then
            player:setCombatModifier("furia_cacador", 1)
        end
    end,
    descricaoEfeito = "dano aumenta contra alvos sangrando",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Fúria do caçador!", [2]="A presa é tua.", [3]="Implacável."}
}

-- Transformação 3: Serenidade Plena (nível 20)
HABILIDADES[13232] = {
    nome = "Serenidade Plena", tipo = "transformacao", dominio = {132, 14}, nivelMin = 20,
    efeito = function(player) player:setSerene(true) end,
    descricaoEfeito = "Serenidade permanente",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Serenidade plena.", [2]="Paz.", [3]="Chi eterno."}
}

print("DEBUG: habilidades_armas_punho.lua v2.0 carregado.")