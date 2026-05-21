--[[
    Projeto MCR ? SPA v4.0 ? Habilidades de Desarmado com Escudo (131)
    Estilo: Tank Supremo. Sem arma, com escudo. Focado em defesa, contra?ataque e utilidade solo/coop.
    Recursos: Chi (Harmony), Virtude da Justiça, Serenidade.
--]]

-- ============================================================
-- ÁRVORE I-IV: DESARMADO COM ESCUDO (131)
-- ============================================================

-- I (5) ? Passiva: Postura de Defesa
HABILIDADES[13101] = {
    nome = "Postura de Defesa",
    tipo = "passiva",
    dominio = {131},
    nivelMin = 5,
    efeito = function(player)
        player:setVirtue(Virtue_t.Justice)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(131))
        player:setCombatModifier("escudo_reducao_dano", nivel * 0.6)
    end,
    descricaoEfeito = "+0.6% redução de dano por nível",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Tua defesa é sólida.", [2]="Inquebrável.", [3]="Parede humana."}
}

-- II (10) ? Passiva: Escudo Vivo
HABILIDADES[13102] = {
    nome = "Escudo Vivo",
    tipo = "passiva",
    dominio = {131},
    nivelMin = 10,
    efeito = function(player)
        player:fillHarmony()
        player:setStorageValue(STORAGE.HARMONY, 5)
        player:setCombatModifier("escudo_chi", 1.0)
    end,
    descricaoEfeito = "Chi máximo, bloqueios geram Chi",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O escudo é parte de ti.", [2]="Defesa e Chi unidos.", [3]="Escudo vivo."}
}

-- III (15) ? Gatilho: Contra?Ataque (consome Chi)
HABILIDADES[13103] = {
    nome = "Contra?Ataque",
    tipo = "gatilho",
    dominio = {131},
    nivelMin = 15,
    gatilho = "onBlock",
    chanceBase = 25,
    chanceLampejo = 35,
    chanceVinculo = 50,
    buffType = "custom",
    efeito = function(player, target)
        local harmony = player:getStorageValue(STORAGE.HARMONY) or 0
        if harmony < 3 then return end
        player:setStorageValue(STORAGE.HARMONY, harmony - 3)
        local dmg = math.floor(target:getMaxHealth() * 0.08)
        doTargetCombatHealth(player, target, COMBAT_PHYSICALDAMAGE, dmg, dmg, CONST_ME_HITAREA)
    end,
    efeitoVisual = function(player, target) target:getPosition():sendMagicEffect(CONST_ME_HITAREA) end,
    descricaoEfeito = "gasta 3 Chi, bloqueio causa 8% da vida do alvo como dano",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Contra?ataque!", [2]="O escudo fere.", [3]="Defesa ofensiva."},
    posturaMod = {[1]={chanceMult=0.5}, [2]={}, [3]={chanceMult=2.0}}
}

-- IV (20) ? Passiva: Muralha Impenetrável
HABILIDADES[13104] = {
    nome = "Muralha Impenetrável",
    tipo = "passiva",
    dominio = {131},
    nivelMin = 20,
    efeito = function(player)
        player:setSerene(true)
        player:setCombatModifier("muralha_ativa", 1)
    end,
    descricaoEfeito = "Serenidade ativa, dano recebido redução máxima",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="És uma muralha.", [2]="Impenetrável.", [3]="Defesa absoluta."}
}

-- ============================================================
-- COMPLEMENTARES ? DESARMADO COM ESCUDO (131) ? 7G, 5P, 3T
-- ============================================================

-- Gatilho 1: Empurrão de Escudo (nível 7)
HABILIDADES[13110] = {
    nome = "Empurrão de Escudo",
    tipo = "gatilho",
    dominio = {131},
    nivelMin = 7,
    gatilho = "onBlock",
    chanceBase = 15,
    chanceLampejo = 25,
    chanceVinculo = 35,
    buffType = "custom",
    efeito = function(player, target)
        local dir = Position(player:getPosition()):getDirectionTo(target:getPosition())
        if dir then target:knockback(dir) end
    end,
    descricaoEfeito = "empurra o atacante",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Empurrão!", [2]="Afasta o inimigo.", [3]="Espaço criado."},
    posturaMod = {[1]={chanceMult=0.5}, [2]={}, [3]={chanceMult=2.0}}
}

-- Gatilho 2: Regeneração de Chi (nível 9)
HABILIDADES[13111] = {
    nome = "Regeneração de Chi",
    tipo = "gatilho",
    dominio = {131},
    nivelMin = 9,
    gatilho = "onBlock",
    chanceBase = 12,
    chanceLampejo = 20,
    chanceVinculo = 30,
    buffType = "custom",
    efeito = function(player)
        local heal = math.floor(player:getMaxHealth() * 0.05)
        player:addHealth(heal)
    end,
    descricaoEfeito = "bloqueio recupera 5% da vida máxima",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O Chi te cura.", [2]="Vida restaurada.", [3]="Energia renovada."},
    posturaMod = {[1]={chanceMult=0.5}, [2]={}, [3]={chanceMult=2.0}}
}

-- Gatilho 3: Escudo Atordoante (nível 12)
HABILIDADES[13112] = {
    nome = "Escudo Atordoante",
    tipo = "gatilho",
    dominio = {131},
    nivelMin = 12,
    gatilho = "onBlock",
    chanceBase = 10,
    chanceLampejo = 18,
    chanceVinculo = 25,
    buffType = "nextAttackCondition",
    conditionType = CONDITION_DAZZLED,
    conditionDuration = 2000,
    descricaoEfeito = "próximo ataque atordoa o agressor",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O escudo atordoa!", [2]="Impacto defensivo.", [3]="O inimigo cambaleia."},
    posturaMod = {[1]={chanceMult=0.5}, [2]={}, [3]={chanceMult=2.0}}
}

-- Gatilho 4: Manto de Aço (nível 14)
HABILIDADES[13113] = {
    nome = "Manto de Aço",
    tipo = "gatilho",
    dominio = {131},
    nivelMin = 14,
    gatilho = "onReceiveDamage",
    chanceBase = 10,
    chanceLampejo = 18,
    chanceVinculo = 25,
    buffType = "custom",
    efeito = function(player, attacker, damage)
        local reducao = math.floor(damage * 0.3)
        player:addHealth(reducao) -- devolve 30% do dano como vida
    end,
    descricaoEfeito = "ao receber dano, recupera 30% do valor como vida",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O aço te protege.", [2]="Dano absorvido.", [3]="Resistência inabalável."},
    posturaMod = {[1]={chanceMult=0.8}, [2]={}, [3]={chanceMult=1.5}}
}

-- Gatilho 5: Guarda do Leão (nível 16)
HABILIDADES[13114] = {
    nome = "Guarda do Leão",
    tipo = "gatilho",
    dominio = {131},
    nivelMin = 16,
    gatilho = "onBlock",
    chanceBase = 8,
    chanceLampejo = 14,
    chanceVinculo = 20,
    buffType = "custom",
    efeito = function(player, target)
        -- Aplica medo no atacante
        local fear = Condition(CONDITION_FEARED, CONDITIONID_COMBAT, 2000)
        target:addCondition(fear)
    end,
    descricaoEfeito = "bloqueio causa medo no agressor",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="O leão ruge!", [2]="Medo imposto.", [3]="O inimigo recua."},
    posturaMod = {[1]={chanceMult=0.5}, [2]={}, [3]={chanceMult=2.0}}
}

-- Gatilho 6: Redenção (nível 18)
HABILIDADES[13115] = {
    nome = "Redenção",
    tipo = "gatilho",
    dominio = {131},
    nivelMin = 18,
    gatilho = "onKill",
    chanceBase = 100,
    buffType = "custom",
    efeito = function(player, target)
        local heal = math.floor(player:getMaxHealth() * 0.15)
        player:addHealth(heal)
        player:addMana(math.floor(player:getMaxMana() * 0.15))
    end,
    descricaoEfeito = "ao matar, recupera 15% da vida e mana máximas",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="A morte te fortalece.", [2]="Redenção.", [3]="Energia restaurada."}
}

-- Gatilho 7: Último Bastião (nível 19)
HABILIDADES[13116] = {
    nome = "Último Bastião",
    tipo = "gatilho",
    dominio = {131},
    nivelMin = 19,
    gatilho = "onReceiveDamage",
    condicao = "vidaBaixa",
    chanceBase = 100,
    buffType = "custom",
    efeito = function(player, attacker, damage)
        -- Quando a vida está < 20%, ganha um escudo temporário
        local shield = math.floor(player:getMaxHealth() * 0.25)
        player:setCombatModifier("escudo_temporario", shield)
        player:addHealth(shield)
    end,
    descricaoEfeito = "quando a vida está baixa, ganha 25% da vida máxima como escudo",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Último bastião!", [2]="Escudo de emergência.", [3]="Ainda não é o fim."}
}

-- Passiva 1: Fortaleza (nível 6)
HABILIDADES[13120] = {
    nome = "Fortaleza",
    tipo = "passiva",
    dominio = {131},
    nivelMin = 6,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(131))
        player:setCombatModifier("defesa_passiva", nivel * 0.5)
    end,
    descricaoEfeito = "+defesa passiva por nível",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Tua defesa cresce.", [2]="Mais resistente.", [3]="Fortaleza."}
}

-- Passiva 2: Vitalidade do Tanque (nível 8)
HABILIDADES[13121] = {
    nome = "Vitalidade do Tanque",
    tipo = "passiva",
    dominio = {131},
    nivelMin = 8,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(131))
        player:setCombatModifier("vida_maxima_percent", 100 + nivel * 0.5)
    end,
    descricaoEfeito = "+0.5% de vida máxima por nível",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Tua vitalidade aumenta.", [2]="Mais vida.", [3]="Tanque."}
}

-- Passiva 3: Pele de Aço (nível 12)
HABILIDADES[13122] = {
    nome = "Pele de Aço",
    tipo = "passiva",
    dominio = {131},
    nivelMin = 12,
    efeito = function(player)
        local nivel = getNivelPorAfinidade(player:getDominioAfinidade(131))
        player:setCombatModifier("armadura_extra", nivel * 0.3)
    end,
    descricaoEfeito = "ignora % da armadura do atacante",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Pele de aço.", [2]="Armadura natural.", [3]="Imbatível."}
}

-- Passiva 4: Postura Inquebrável (nível 15)
HABILIDADES[13123] = {
    nome = "Postura Inquebrável",
    tipo = "passiva",
    dominio = {131},
    nivelMin = 15,
    efeito = function(player)
        if getNivelPorAfinidade(player:getDominioAfinidade(131)) >= 15 then
            player:setCombatModifier("imune_knockback", 1)
        end
    end,
    descricaoEfeito = "imune a empurrões e knockback",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Inquebrável.", [2]="Nada te move.", [3]="Firme como rocha."}
}

-- Passiva 5: Regeneração Constante (nível 17)
HABILIDADES[13124] = {
    nome = "Regeneração Constante",
    tipo = "passiva",
    dominio = {131},
    nivelMin = 17,
    efeito = function(player)
        if getNivelPorAfinidade(player:getDominioAfinidade(131)) >= 17 then
            player:setCombatModifier("regeneracao_constante", 1)
        end
    end,
    descricaoEfeito = "regenera vida lentamente fora de combate",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Regeneração constante.", [2]="Feridas se curam.", [3]="Sempre pronto."}
}

-- Transformação 1: Postura do Guardião (nível 10)
HABILIDADES[13130] = {
    nome = "Postura do Guardião",
    tipo = "transformacao",
    dominio = {131},
    nivelMin = 10,
    efeito = function(player)
        if getNivelPorAfinidade(player:getDominioAfinidade(131)) >= 10 then
            local cond = Condition(CONDITION_ATTRIBUTES, CONDITIONID_COMBAT, -1)
            cond:setParameter(CONDITION_PARAM_SUBID, 203)
            cond:setParameter(CONDITION_PARAM_STAT_MAXHITPOINTSPERCENT, 110)
            cond:setParameter(CONDITION_PARAM_BUFF_SPELL, true)
            player:addCondition(cond)
        end
    end,
    descricaoEfeito = "+10% vida máxima",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Postura do guardião.", [2]="Vida aumentada.", [3]="Proteção total."}
}

-- Transformação 2: Fúria Protetora (nível 16)
HABILIDADES[13131] = {
    nome = "Fúria Protetora",
    tipo = "transformacao",
    dominio = {131},
    nivelMin = 16,
    efeito = function(player)
        if getNivelPorAfinidade(player:getDominioAfinidade(131)) >= 16 then
            player:setCombatModifier("furia_protetora", 1)
        end
    end,
    descricaoEfeito = "quando a vida está baixa, dano causado aumenta",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Fúria protetora!", [2]="Defesa e ataque unidos.", [3]="O guardião contra?ataca."}
}

-- Transformação 3: Avatar da Muralha (nível 20)
HABILIDADES[13132] = {
    nome = "Avatar da Muralha",
    tipo = "transformacao",
    dominio = {131},
    nivelMin = 20,
    efeito = function(player)
        player:setSerene(true)
        player:setCombatModifier("avatar_muralha", 1)
    end,
    descricaoEfeito = "Serenidade ativa, redução de dano máxima",
    cor = COR.DOM_COMBATE_DESARMADO,
    mensagem = {[1]="Avatar da muralha!", [2]="Imortal.", [3]="O escudo é eterno."}
}

print("DEBUG: habilidades_desarmado_escudo.lua v4.0 carregado.")