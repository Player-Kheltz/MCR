--[[
    Projeto MCR ? passivas_ataque.lua (v1.0)
    Efeitos passivos de auto?ataque baseados no nível do domínio e na postura.
    Chamado a cada ataque bem?sucedido pelo evento onDealtDamage.
--]]

-- ============================================================
-- TABELA DE CONFIGURAÇÃO DOS EFEITOS PASSIVOS
-- ============================================================
-- Estrutura: [dominioId] = { nivelMin, posturaNecessaria, efeito }
-- posturaNecessaria: nil = todas, 1 = Ímpeto, 2 = Equilíbrio, 3 = Guarda
-- Se nivel >= 20, o efeito funciona em todas as posturas (tratado na função)

local PASSIVAS_ATAQUE = {
    -- =================== ESPADAS LEVES (100) ===================
    [100] = {
        nome = "Sangramento Leve",
        nivelMin = 15,
        postura = FIGHTMODE_ATTACK,
        chance = 20,
        efeito = function(player, target, damage)
            local bleedDmg = math.floor(damage * 0.05)
            local condition = Condition(CONDITION_BLEEDING, CONDITIONID_COMBAT, 3000)
            condition:setParameter(CONDITION_PARAM_PERIODICDAMAGE, bleedDmg)
            condition:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
            target:addCondition(condition)
            target:getPosition():sendMagicEffect(CONST_ME_DRAWBLOOD)
        end
    },

    -- =================== ESPADAS PESADAS (101) ===================
    [101] = {
        nome = "Knockback",
        nivelMin = 15,
        postura = FIGHTMODE_ATTACK,
        chance = 25,
        efeito = function(player, target, damage)
            local dir = Position(player:getPosition()):getDirectionTo(target:getPosition())
            if dir then
                target:knockback(dir)
                target:getPosition():sendMagicEffect(CONST_ME_HITAREA)
            end
        end
    },

    -- =================== MACHADOS LEVES (110) ===================
    [110] = {
        nome = "Sangramento Moderado",
        nivelMin = 15,
        postura = FIGHTMODE_ATTACK,
        chance = 25,
        efeito = function(player, target, damage)
            local bleedDmg = math.floor(damage * 0.08)
            local condition = Condition(CONDITION_BLEEDING, CONDITIONID_COMBAT, 4000)
            condition:setParameter(CONDITION_PARAM_PERIODICDAMAGE, bleedDmg)
            condition:setParameter(CONDITION_PARAM_TICKINTERVAL, 1000)
            target:addCondition(condition)
            target:getPosition():sendMagicEffect(CONST_ME_DRAWBLOOD)
        end
    },

    -- =================== MACHADOS PESADOS (111) ===================
    [111] = {
        nome = "Medo",
        nivelMin = 15,
        postura = FIGHTMODE_ATTACK,
        chance = 15,
        efeito = function(player, target, damage)
            if target:getHealth() < target:getMaxHealth() * 0.5 then
                local condition = Condition(CONDITION_DAZZLED, CONDITIONID_COMBAT, 2000)
                target:addCondition(condition)
                target:getPosition():sendMagicEffect(CONST_ME_SOUND_RED)
            end
        end
    },

    -- =================== CLAVAS LEVES (112) ===================
    [112] = {
        nome = "Atordoamento",
        nivelMin = 15,
        postura = FIGHTMODE_ATTACK,
        chance = 15,
        efeito = function(player, target, damage)
            local condition = Condition(CONDITION_DAZZLED, CONDITIONID_COMBAT, 1500)
            target:addCondition(condition)
            target:getPosition():sendMagicEffect(CONST_ME_STUN)
        end
    },

    -- =================== CLAVAS PESADAS (113) ===================
    [113] = {
        nome = "Atordoamento em Cone",
        nivelMin = 15,
        postura = FIGHTMODE_ATTACK,
        chance = 10,
        efeito = function(player, target, damage)
            local pos = target:getPosition()
            local dir = Position(player:getPosition()):getDirectionTo(pos)
            local creatures = getCreaturesInArea(pos, 3, 1)
            for _, creature in ipairs(creatures) do
                if creature:isMonster() then
                    local condition = Condition(CONDITION_DAZZLED, CONDITIONID_COMBAT, 1500)
                    creature:addCondition(condition)
                    creature:getPosition():sendMagicEffect(CONST_ME_STUN)
                end
            end
        end
    },

    -- =================== ARREMESSO SEM ESCUDO (121) ===================
    [121] = {
        nome = "Dano Crítico",
        nivelMin = 15,
        postura = FIGHTMODE_ATTACK,
        chance = 10,
        efeito = function(player, target, damage)
            local extraDmg = math.floor(damage * 1.0)
            doTargetCombatHealth(player, target, COMBAT_PHYSICALDAMAGE, extraDmg, extraDmg, CONST_ME_DRAWBLOOD)
            target:getPosition():sendMagicEffect(CONST_ME_DRAWBLOOD)
        end
    },

    -- =================== ARREMESSO COM ESCUDO (121 também) ===================
    -- NOTA: O domínio 121 é partilhado; a condição do escudo é verificada na função principal
    [122] = {  -- ID virtual para Arremesso com Escudo (usamos uma key separada na tabela)
        nome = "Lentidão à Distância",
        nivelMin = 15,
        postura = FIGHTMODE_DEFENSE,
        chance = 20,
        condicaoEscudo = true,
        efeito = function(player, target, damage)
            local dist = getCreatureDistance(player, target)
            if dist > 4 then
                local condition = Condition(CONDITION_PARALYZE, CONDITIONID_COMBAT, 2000)
                condition:setParameter(CONDITION_PARAM_SPEED, -30)
                target:addCondition(condition)
                target:getPosition():sendMagicEffect(CONST_ME_SOUND_BLUE)
            end
        end
    },

    -- =================== ARCOS / ATIRADOR (120) ===================
    [120] = {
        nome = "Dano Crítico",
        nivelMin = 15,
        postura = FIGHTMODE_ATTACK,
        chance = 12,
        efeito = function(player, target, damage)
            local extraDmg = math.floor(damage * 1.5)
            doTargetCombatHealth(player, target, COMBAT_PHYSICALDAMAGE, extraDmg, extraDmg, CONST_ME_DRAWBLOOD)
            target:getPosition():sendMagicEffect(CONST_ME_DRAWBLOOD)
        end
    },

    -- =================== DESARMADO LEVE (130) ===================
    [130] = {
        nome = "Golpe Duplo",
        nivelMin = 15,
        postura = FIGHTMODE_ATTACK,
        chance = 15,
        efeito = function(player, target, damage)
            local extraDmg = math.floor(damage * 0.5)
            doTargetCombatHealth(player, target, COMBAT_PHYSICALDAMAGE, extraDmg, extraDmg, CONST_ME_HITAREA)
            target:getPosition():sendMagicEffect(CONST_ME_HITAREA)
        end
    },

    -- =================== DESARMADO PESADO (131) ===================
    [131] = {
        nome = "Knockback",
        nivelMin = 15,
        postura = FIGHTMODE_ATTACK,
        chance = 20,
        efeito = function(player, target, damage)
            local dir = Position(player:getPosition()):getDirectionTo(target:getPosition())
            if dir then
                target:knockback(dir)
                target:getPosition():sendMagicEffect(CONST_ME_HITAREA)
            end
        end
    },

    -- =================== ESCUDO (15) ===================
    [15] = {
        nome = "Empurrão Defensivo",
        nivelMin = 15,
        postura = FIGHTMODE_DEFENSE,
        chance = 15,
        efeito = function(player, target, damage)
            local dir = Position(player:getPosition()):getDirectionTo(target:getPosition())
            if dir then
                target:knockback(dir)
                target:getPosition():sendMagicEffect(CONST_ME_HITAREA)
            end
        end
    },

    -- =================== WANDS (210) ===================
    [210] = {
        nome = "Roubo de Mana",
        nivelMin = 15,
        postura = FIGHTMODE_BALANCED,
        chance = 100,
        efeito = function(player, target, damage)
            local manaDrain = math.floor(damage * 0.05)
            player:addMana(manaDrain)
        end
    },

    -- =================== RODS (211) ===================
    [211] = {
        nome = "Roubo de Vida",
        nivelMin = 15,
        postura = FIGHTMODE_BALANCED,
        chance = 100,
        efeito = function(player, target, damage)
            local lifeDrain = math.floor(damage * 0.05)
            player:addHealth(lifeDrain)
        end
    },

    -- =================== RUNAS (212) ===================
    [212] = {
        nome = "Custo Reduzido",
        nivelMin = 15,
        postura = FIGHTMODE_BALANCED,
        chance = 15,
        efeito = function(player, target, damage)
            -- A runa não é consumida (o motor trata disso, aqui apenas feedback)
            player:getPosition():sendMagicEffect(CONST_ME_MAGIC_BLUE)
        end
    },
}

-- ============================================================
-- FUNÇÃO PRINCIPAL
-- ============================================================
function aplicarPassivasAtaque(player, target, damage, primary)
    -- Só se aplica a dano físico (armas) ou mágico (wands/rods/runas)
    if primary ~= COMBAT_PHYSICALDAMAGE and primary ~= COMBAT_ENERGYDAMAGE then
        return
    end

    local weapon = player:getSlotItem(CONST_SLOT_LEFT) or player:getSlotItem(CONST_SLOT_RIGHT)
    local especialidade = getWeaponEspecialidade(player, weapon)

    -- Determina a key da tabela: para Arremesso com Escudo, usa 122
    local key = especialidade
    if especialidade == DOMINIO_ARREMESSO and hasShield(player) then
        key = 122
    end

    local cfg = PASSIVAS_ATAQUE[key]
    if not cfg then return end

    -- Verifica o nível do domínio
    local afinidade = player:getDominioAfinidade(especialidade) or 0
    local nivel = getNivelPorAfinidade(afinidade)
    if nivel < cfg.nivelMin then return end

    -- Verifica a postura (nível 20+ ignora a restrição de postura)
    local postura = player:getFightMode()
    if nivel < 20 and cfg.postura and postura ~= cfg.postura then
        return
    end

    -- Verifica condição extra (escudo, etc.)
    if cfg.condicaoEscudo and not hasShield(player) then
        return
    end

    -- Sorteia a chance
    if math.random(100) <= cfg.chance then
        cfg.efeito(player, target, damage)
    end
end

print("DEBUG: passivas_ataque.lua (v1.0) carregado.")