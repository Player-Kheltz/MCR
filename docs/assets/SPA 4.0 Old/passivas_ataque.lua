--[[
    Projeto MCR ? passivas_ataque.lua (v1.0)
    Efeitos passivos de auto?ataque baseados no n�vel do dom�nio e na postura.
--]]

local PASSIVAS_ATAQUE = {
    [100] = { nome="Sangramento Leve", nivelMin=15, postura=FIGHTMODE_ATTACK, chance=20, efeito=function(p,t,d) local bleed=math.floor(d*0.05); local c=Condition(CONDITION_BLEEDING,CONDITIONID_COMBAT,3000); c:setParameter(CONDITION_PARAM_PERIODICDAMAGE,bleed); c:setParameter(CONDITION_PARAM_TICKINTERVAL,1000); t:addCondition(c); t:getPosition():sendMagicEffect(CONST_ME_DRAWBLOOD) end },
    [101] = { nome="Knockback", nivelMin=15, postura=FIGHTMODE_ATTACK, chance=25, efeito=function(p,t,d) local dir=Position(p:getPosition()):getDirectionTo(t:getPosition()); if dir then t:knockback(dir); t:getPosition():sendMagicEffect(CONST_ME_HITAREA) end end },
    [110] = { nome="Sangramento Moderado", nivelMin=15, postura=FIGHTMODE_ATTACK, chance=25, efeito=function(p,t,d) local bleed=math.floor(d*0.08); local c=Condition(CONDITION_BLEEDING,CONDITIONID_COMBAT,4000); c:setParameter(CONDITION_PARAM_PERIODICDAMAGE,bleed); c:setParameter(CONDITION_PARAM_TICKINTERVAL,1000); t:addCondition(c); t:getPosition():sendMagicEffect(CONST_ME_DRAWBLOOD) end },
    [111] = { nome="Medo", nivelMin=15, postura=FIGHTMODE_ATTACK, chance=15, efeito=function(p,t,d) if t:getHealth()<t:getMaxHealth()*0.5 then local c=Condition(CONDITION_DAZZLED,CONDITIONID_COMBAT,2000); t:addCondition(c); t:getPosition():sendMagicEffect(CONST_ME_SOUND_RED) end end },
    [112] = { nome="Atordoamento", nivelMin=15, postura=FIGHTMODE_ATTACK, chance=15, efeito=function(p,t,d) local c=Condition(CONDITION_DAZZLED,CONDITIONID_COMBAT,1500); t:addCondition(c); t:getPosition():sendMagicEffect(CONST_ME_STUN) end },
    [113] = { nome="Atordoamento em Cone", nivelMin=15, postura=FIGHTMODE_ATTACK, chance=10, efeito=function(p,t,d) local pos=t:getPosition(); local dir=Position(p:getPosition()):getDirectionTo(pos); local creatures=getCreaturesInArea(pos,3,1); for _,c in ipairs(creatures) do if c:isMonster() then local cc=Condition(CONDITION_DAZZLED,CONDITIONID_COMBAT,1500); c:addCondition(cc); c:getPosition():sendMagicEffect(CONST_ME_STUN) end end end },
    [121] = { nome="Dano Cr�tico", nivelMin=15, postura=FIGHTMODE_ATTACK, chance=10, efeito=function(p,t,d) local extra=math.floor(d*1.0); doTargetCombatHealth(p,t,COMBAT_PHYSICALDAMAGE,extra,extra,CONST_ME_DRAWBLOOD); t:getPosition():sendMagicEffect(CONST_ME_DRAWBLOOD) end },
    [122] = { nome="Lentid�o � Dist�ncia", nivelMin=15, postura=FIGHTMODE_DEFENSE, chance=20, condicaoEscudo=true, efeito=function(p,t,d) local dist=getCreatureDistance(p,t); if dist>4 then local c=Condition(CONDITION_PARALYZE,CONDITIONID_COMBAT,2000); c:setParameter(CONDITION_PARAM_SPEED,-30); t:addCondition(c); t:getPosition():sendMagicEffect(CONST_ME_SOUND_BLUE) end end },
    [120] = { nome="Dano Cr�tico", nivelMin=15, postura=FIGHTMODE_ATTACK, chance=12, efeito=function(p,t,d) local extra=math.floor(d*1.5); doTargetCombatHealth(p,t,COMBAT_PHYSICALDAMAGE,extra,extra,CONST_ME_DRAWBLOOD); t:getPosition():sendMagicEffect(CONST_ME_DRAWBLOOD) end },
    [130] = { nome="Golpe Duplo", nivelMin=15, postura=FIGHTMODE_ATTACK, chance=15, efeito=function(p,t,d) local extra=math.floor(d*0.5); doTargetCombatHealth(p,t,COMBAT_PHYSICALDAMAGE,extra,extra,CONST_ME_HITAREA); t:getPosition():sendMagicEffect(CONST_ME_HITAREA) end },
    [131] = { nome="Knockback", nivelMin=15, postura=FIGHTMODE_ATTACK, chance=20, efeito=function(p,t,d) local dir=Position(p:getPosition()):getDirectionTo(t:getPosition()); if dir then t:knockback(dir); t:getPosition():sendMagicEffect(CONST_ME_HITAREA) end end },
    [15]  = { nome="Empurr�o Defensivo", nivelMin=15, postura=FIGHTMODE_DEFENSE, chance=15, efeito=function(p,t,d) local dir=Position(p:getPosition()):getDirectionTo(t:getPosition()); if dir then t:knockback(dir); t:getPosition():sendMagicEffect(CONST_ME_HITAREA) end end },
    [210] = { nome="Roubo de Mana", nivelMin=15, postura=FIGHTMODE_BALANCED, chance=100, efeito=function(p,t,d) local mana=math.floor(d*0.05); p:addMana(mana) end },
    [211] = { nome="Roubo de Vida", nivelMin=15, postura=FIGHTMODE_BALANCED, chance=100, efeito=function(p,t,d) local life=math.floor(d*0.05); p:addHealth(life) end },
    [212] = { nome="Custo Reduzido", nivelMin=15, postura=FIGHTMODE_BALANCED, chance=15, efeito=function(p,t,d) p:getPosition():sendMagicEffect(CONST_ME_MAGIC_BLUE) end },
}

function aplicarPassivasAtaque(player, target, damage, primary)
    if primary ~= COMBAT_PHYSICALDAMAGE and primary ~= COMBAT_ENERGYDAMAGE then return end
    local weapon = player:getSlotItem(CONST_SLOT_LEFT) or player:getSlotItem(CONST_SLOT_RIGHT)
    local especialidade = getWeaponEspecialidade(player, weapon)
    local key = especialidade
    if especialidade == DOMINIO_ARREMESSO and hasShield(player) then key = 122 end
    local cfg = PASSIVAS_ATAQUE[key]
    if not cfg then return end
    local afinidade = player:getDominioAfinidade(especialidade) or 0
    local nivel = getNivelEfetivo(player, especialidade)
    if nivel < cfg.nivelMin then return end
    local postura = player:getFightMode()
    if nivel < 20 and cfg.postura and postura ~= cfg.postura then return end
    if cfg.condicaoEscudo and not hasShield(player) then return end
    if math.random(100) <= cfg.chance then
        cfg.efeito(player, target, damage)
    end
end

print("DEBUG: passivas_ataque.lua v1.0 carregado.")