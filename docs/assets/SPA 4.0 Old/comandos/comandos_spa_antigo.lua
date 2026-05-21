--[[
    Projeto MCR ? Comandos de Teste do SPA (v2.1)
    Todos os talkactions reunidos num único ficheiro.
    Comandos: !semideus, !resetspa, !aprendertodas, !fistcheck,
              !frases, !todascores, !testarbatch, !ajuda
--]]

-- ============================================================
-- !semideus ? Maximiza todos os domínios
-- ============================================================
local talkSemideus = TalkAction("!semideus")
function talkSemideus.onSay(player, words, param)
    local maxAf = 180000
    local processados = 0
    for _, domId in ipairs(ALL_DOMINIOS) do
        local atual = player:getDominioAfinidade(domId)
        local pontos = maxAf - atual
        if pontos > 0 then
            player:addDominioAfinidade(domId, pontos)
            processados = processados + 1
        end
        verificarDesbloqueio(player, domId)
    end
    aplicarPassivasBasicas(player)
    player:setStealth(false)
    aplicarPostura(player, player:getFightMode())
    enviarMsgColorida(player, c("Você agora é um ", COR.RARIDADE_LENDARIO) .. c("Semi-Deus", COR.RARIDADE_OURO) .. c("! Todos os domínios foram elevados ao máximo.", COR.SISTEMA_INFO))
    return false
end
talkSemideus:separator(" ")
talkSemideus:groupType(1)
talkSemideus:register()

-- ============================================================
-- !resetspa ? Zera completamente o progresso do SPA
-- ============================================================
local talkReset = TalkAction("!resetspa")
function talkReset.onSay(player, words, param)
    local playerId = player:getId()
    for _, domId in ipairs(ALL_DOMINIOS) do
        local atual = player:getDominioAfinidade(domId)
        if atual > 0 then
            player:addDominioAfinidade(domId, -atual)
        end
    end
    db.query("DELETE FROM player_habilidades WHERE player_id = " .. playerId)
    for i = 90000, 99999 do
        player:setStorageValue(i, 0)
    end
    for _, domId in ipairs(ALL_DOMINIOS) do
        player:setDominioState(domId, 0)
    end
    if player.clearActionHistory then
        player:clearActionHistory()
    end
    player:setStealth(false)
    aplicarPostura(player, player:getFightMode())
    enviarMsgColorida(player, c("Todo o progresso do SPA foi completamente zerado.", COR.SISTEMA_INFO))
    return false
end
talkReset:separator(" ")
talkReset:groupType(1)
talkReset:register()

-- ============================================================
-- !aprendertodas ? Aprende todas as habilidades
-- ============================================================
local talkAprender = TalkAction("!aprendertodas")
function talkAprender.onSay(player, words, param)
    local aprendidas = 0
    for habId, _ in pairs(HABILIDADES) do
        if not jogadorConheceHabilidade(player, habId) then
            aprenderHabilidade(player, habId)
            aprendidas = aprendidas + 1
        end
    end
    enviarMsgColorida(player, c(aprendidas .. " habilidades foram aprendidas.", COR.SUCESSO_CURA))
    return false
end
talkAprender:separator(" ")
talkAprender:groupType(1)
talkAprender:register()

-- ============================================================
-- !fistcheck ? Diagnóstico do bônus de Desarmado
-- ============================================================
local talkFist = TalkAction("!fistcheck")
function talkFist.onSay(player, words, param)
    local weapon = player:getSlotItem(CONST_SLOT_LEFT) or player:getSlotItem(CONST_SLOT_RIGHT)
    local wt = weapon and weapon:getType():getWeaponType() or WEAPON_FIST
    local nivelDesarmado = getNivelPorAfinidade(player:getDominioAfinidade(14) or 0)
    local hasSkill = player:getCondition(CONDITION_ATTRIBUTES, CONDITIONID_COMBAT, 98)
    local hasDmg = player:getCondition(CONDITION_ATTRIBUTES, CONDITIONID_COMBAT, 99)

    enviarMsgColorida(player, c("=== Diagnóstico Desarmado ===", COR.SISTEMA_INFO))
    enviarMsgColorida(player, c("Arma equipada: ", COR.SISTEMA_NEUTRO) .. (weapon and weapon:getName() or "Nenhuma"))
    enviarMsgColorida(player, c("WeaponType: ", COR.SISTEMA_NEUTRO) .. wt .. " (FIST = " .. WEAPON_FIST .. ")")
    enviarMsgColorida(player, c("Nível Desarmado: ", COR.SISTEMA_NEUTRO) .. nivelDesarmado)
    enviarMsgColorida(player, c("Skill Fist nativa: ", COR.SISTEMA_NEUTRO) .. player:getSkillLevel(SKILL_FIST))
    enviarMsgColorida(player, c("Condição Skill Fist: ", COR.SISTEMA_NEUTRO) .. (hasSkill and c("ATIVA", COR.SUCESSO_CURA) or c("INATIVA", COR.SISTEMA_ERRO)))
    enviarMsgColorida(player, c("Condição Dano: ", COR.SISTEMA_NEUTRO) .. (hasDmg and c("ATIVA", COR.SUCESSO_CURA) or c("INATIVA", COR.SISTEMA_ERRO)))
    return false
end
talkFist:separator(" ")
talkFist:groupType(1)
talkFist:register()

-- ============================================================
-- !frases ? Exibe todas as mensagens do SPA
-- ============================================================
local talkFrases = TalkAction("!frases")
function talkFrases.onSay(player, words, param)
    player:sendTextMessage(24, "Sua afinidade com " .. c("Lâminas", COR.DOM_COMBATE_LAMINAS) .. " se aprofunda.")
    player:sendTextMessage(24, "Você sente um salto de poder em " .. c("Lâminas", COR.DOM_COMBATE_LAMINAS) .. "!")
    player:sendTextMessage(24, "Você aprofunda um Vínculo com " .. c("Lâminas", COR.DOM_COMBATE_LAMINAS) .. ".")
    player:sendTextMessage(24, "Seu Vínculo com " .. c("Lâminas", COR.DOM_COMBATE_LAMINAS) .. " se dissipou.")
    player:sendTextMessage(24, "Você se tornou um(a) " .. c("Mestre das Lâminas", COR.RARIDADE_LENDARIO) .. "!")
    player:sendTextMessage(24, "Postura ajustada: " .. c("Ímpeto", COR.POSTURA_IMPETO) .. " adaptada à sua arma.")
    player:sendTextMessage(24, "Postura ajustada: " .. c("Equilíbrio", COR.POSTURA_EQUILIBRIO) .. " adaptada à sua arma.")
    player:sendTextMessage(24, "Postura ajustada: " .. c("Guarda", COR.POSTURA_GUARDA) .. " adaptada à sua arma.")
    player:sendTextMessage(23, "[" .. c("Disparo Duplo", COR.DOM_COMBATE_PRECISAO) .. "] " .. c("Duas flechas partem em uníssono!", COR.COMBO_AVISO) .. " - " .. c("dispara uma segunda flecha", COR.COMBO_AVISO) .. ".")
    player:sendTextMessage(23, "[" .. c("Vórtice de Aço", COR.DOM_COMBATE_LAMINAS) .. "] " .. c("Afastas os inimigos com um golpe circular!", COR.COMBO_AVISO) .. " - " .. c("Dano em área", COR.COMBO_AVISO) .. ".")
    player:sendTextMessage(23, "[" .. c("Selo de Poder", COR.DOM_MAGIA_RUNOLOGIA) .. "] " .. c("A varinha atinge o seu ápice!", COR.COMBO_AVISO) .. " - " .. c("disparo devastador após 5 ataques", COR.COMBO_AVISO) .. ".")
    player:sendTextMessage(23, "[" .. c("Corte Dilacerante", COR.DOM_COMBATE_LAMINAS) .. "] causou " .. c("Sangramento", COR.COND_SANGRAMENTO) .. " em " .. c("Centopeia", COR.INIMIGO_MONSTRO) .. "!")
    player:sendTextMessage(23, "[" .. c("Disparo Duplo", COR.DOM_COMBATE_PRECISAO) .. "] causou " .. c("42", COR.DANO_FISICO) .. " de dano extra em " .. c("Centopeia", COR.INIMIGO_MONSTRO) .. ".")
    player:sendTextMessage(24, c("Kheltz", COR.ALIADO_JOGADOR) .. " tornou-se " .. c("Mestre das Lâminas", COR.RARIDADE_LENDARIO) .. "!")
    return false
end
talkFrases:separator(" ")
talkFrases:groupType(1)
talkFrases:register()

-- ============================================================
-- !todascores ? Lista todas as cores da tabela COR
-- ============================================================
local talkCores = TalkAction("!todascores")
function talkCores.onSay(player, words, param)
    if not COR then
        enviarMsgColorida(player, c("[ERRO] Tabela COR não encontrada.", COR.SISTEMA_ERRO))
        return false
    end
    local sortedKeys = {}
    for k in pairs(COR) do table.insert(sortedKeys, k) end
    table.sort(sortedKeys)
    local linha = ""
    local count = 0
    for _, nome in ipairs(sortedKeys) do
        local parte = c(nome, COR[nome]) .. "  "
        if #linha + #parte > 500 then
            enviarMsgColorida(player, linha)
            linha = ""
        end
        linha = linha .. parte
        count = count + 1
    end
    if linha ~= "" then enviarMsgColorida(player, linha) end
    enviarMsgColorida(player, c(count .. " cores listadas.", COR.RARIDADE_OURO))
    return false
end
talkCores:separator(" ")
talkCores:groupType(1)
talkCores:register()

-- ============================================================
-- !testarbatch ? Testa as funções em lote (getStorages, setStorages, etc.)
-- ============================================================
local talkBatch = TalkAction("!testarbatch")
function talkBatch.onSay(player, words, param)
    local dados = {[99001]=100, [99002]=200, [99003]=300, [99004]=400, [99005]=500}
    player:setStorages(dados)
    local chaves = {99001, 99002, 99003, 99004, 99005}
    local resultado = player:getStorages(unpack(chaves))
    local msg1 = "Storages em lote: "
    for _, k in ipairs(chaves) do msg1 = msg1 .. k .. "=" .. (resultado[k] or "nil") .. " " end
    enviarMsgColorida(player, c(msg1, COR.SUCESSO_CURA))

    local afinAdd = {[1]=10, [10]=20, [14]=30}
    player:addDominioAfinidadeBatch(afinAdd)
    local dominios = {1, 10, 14}
    local afinidades = player:getDominioAfinidades(unpack(dominios))
    local msg2 = "Afinidades em lote: "
    for _, d in ipairs(dominios) do msg2 = msg2 .. getNomeDominio(d) .. "=" .. (afinidades[d] or 0) .. " " end
    enviarMsgColorida(player, c(msg2, COR.RARIDADE_OURO))

    local limpeza = {[99001]=-1, [99002]=-1, [99003]=-1, [99004]=-1, [99005]=-1}
    player:setStorages(limpeza)
    enviarMsgColorida(player, c("Teste em lote concluído com sucesso!", COR.SISTEMA_INFO))
    return false
end
talkBatch:separator(" ")
talkBatch:groupType(1)
talkBatch:register()

-- ============================================================
-- !ajuda ? Lista todos os comandos de teste disponíveis
-- ============================================================
local talkAjuda = TalkAction("!ajuda")
function talkAjuda.onSay(player, words, param)
    enviarMsgColorida(player, c("=== Comandos de Teste do SPA ===", COR.SISTEMA_INFO))
    enviarMsgColorida(player, c("!semideus", COR.RARIDADE_OURO) .. c(" ? Maximiza todos os domínios.", COR.SISTEMA_NEUTRO))
    enviarMsgColorida(player, c("!resetspa", COR.SISTEMA_ERRO) .. c(" ? Zera completamente o progresso.", COR.SISTEMA_NEUTRO))
    enviarMsgColorida(player, c("!aprendertodas", COR.SUCESSO_CURA) .. c(" ? Aprende todas as habilidades.", COR.SISTEMA_NEUTRO))
    enviarMsgColorida(player, c("!fistcheck", COR.DOM_COMBATE_DESARMADO) .. c(" ? Diagnóstico do bônus de Desarmado.", COR.SISTEMA_NEUTRO))
    enviarMsgColorida(player, c("!frases", COR.POSTURA_INFO) .. c(" ? Exibe todas as mensagens do SPA.", COR.SISTEMA_NEUTRO))
    enviarMsgColorida(player, c("!todascores", COR.DOM_MAGIA_RUNOLOGIA) .. c(" ? Lista todas as cores disponíveis.", COR.SISTEMA_NEUTRO))
    enviarMsgColorida(player, c("!testarbatch", COR.SISTEMA_INFO) .. c(" ? Testa as funções em lote.", COR.SISTEMA_NEUTRO))
    enviarMsgColorida(player, c("!ajuda", COR.SISTEMA_NEUTRO) .. c(" ? Mostra esta lista.", COR.SISTEMA_NEUTRO))
    return false
end
talkAjuda:separator(" ")
talkAjuda:groupType(1)
talkAjuda:register()

local talkLeechCheck = TalkAction("!leechcheck")
function talkLeechCheck.onSay(player, words, param)
    local lifeLeech = player:getLifeLeechModifier()
    local manaLeech = player:getManaLeechModifier()
    enviarMsgColorida(player, c("Life Leech: " .. tostring(math.floor(lifeLeech * 100)) .. "%", COR.SUCESSO_CURA))
    enviarMsgColorida(player, c("Mana Leech: " .. tostring(math.floor(manaLeech * 100)) .. "%", COR.SISTEMA_INFO))
    return false
end
talkLeechCheck:separator(" ")
talkLeechCheck:groupType(1)
talkLeechCheck:register()

local talkLeechTest = TalkAction("!leechtest")
function talkLeechTest.onSay(player, words, param)
    player:setLifeLeechModifier(0.10)  -- valor normalizado
    local val = player:getLifeLeechModifier()
    enviarMsgColorida(player, "Valor lido: " .. tostring(val * 100) .. "%")
    return false
end
talkLeechTest:separator(" ")
talkLeechTest:groupType(1)
talkLeechTest:register()

local talkTesteItem = TalkAction("!testeitem")
function talkTesteItem.onSay(player, words, param)
    local weapon = player:getSlotItem(CONST_SLOT_LEFT)
    if not weapon or (weapon:getType():getWeaponType() == WEAPON_SHIELD) then
        weapon = player:getSlotItem(CONST_SLOT_RIGHT)
    end

    if not weapon then
        enviarMsgColorida(player, c("[Teste] Nenhuma arma equipada.", COR.SISTEMA_ERRO))
        return false
    end

    enviarMsgColorida(player, c("=== Teste de Atributos da Arma ===", COR.SISTEMA_INFO))
    enviarMsgColorida(player, "Arma: " .. c(weapon:getName(), COR.ITEM_RARO))
    enviarMsgColorida(player, "ID: " .. weapon:getId())

    -- Elemental Bond (se o método existir)
    if weapon.getElementalBond then
        local elemento = weapon:getElementalBond()
        enviarMsgColorida(player, "Elemental Bond: " .. c(tostring(elemento), COR.ELEM_FOGO))
    else
        enviarMsgColorida(player, "Elemental Bond: " .. c("método indisponível", COR.SISTEMA_NEUTRO))
    end

    -- Magic Level Points
    if weapon.getMagicLevelPoints then
        local ml = weapon:getMagicLevelPoints()
        enviarMsgColorida(player, "Magic Level Points: " .. c(tostring(ml), COR.SISTEMA_INFO))
    else
        enviarMsgColorida(player, "Magic Level Points: " .. c("método indisponível", COR.SISTEMA_NEUTRO))
    end

    -- Skills
    local skills = {
        {"Fist", "getSkillFist"},
        {"Sword", "getSkillSword"},
        {"Axe", "getSkillAxe"},
        {"Club", "getSkillClub"},
        {"Distance", "getSkillDistance"},
        {"Shield", "getSkillShield"},
    }
    for _, sk in ipairs(skills) do
        if weapon[sk[2]] then
            local val = weapon[sk[2]](weapon)
            if val > 0 then
                enviarMsgColorida(player, "Skill " .. sk[1] .. ": " .. c("+" .. val, COR.SUCESSO_CURA))
            end
        end
    end

    -- Crítico
    if weapon.getCriticalHitChance then
        local critC = weapon:getCriticalHitChance()
        local critD = weapon:getCriticalHitDamage()
        if critC > 0 then enviarMsgColorida(player, "Crit Chance: " .. c(critC .. "%", COR.COMBO_AVISO)) end
        if critD > 0 then enviarMsgColorida(player, "Crit Damage: " .. c(critD .. "%", COR.COMBO_AVISO)) end
    end

    -- Leech
    if weapon.getLifeLeechAmount then
        local la = weapon:getLifeLeechAmount()
        local lc = weapon:getLifeLeechChance()
        local ma = weapon:getManaLeechAmount()
        local mc = weapon:getManaLeechChance()
        if la > 0 then enviarMsgColorida(player, "Life Leech: " .. c(la .. "%", COR.SUCESSO_CURA) .. " (Chance: " .. lc .. "%)") end
        if ma > 0 then enviarMsgColorida(player, "Mana Leech: " .. c(ma .. "%", COR.SISTEMA_INFO) .. " (Chance: " .. mc .. "%)") end
    end

    -- Reflect Damage
    if weapon.getReflectDamage then
        local ref = weapon:getReflectDamage()
        if ref > 0 then enviarMsgColorida(player, "Reflect Damage: " .. c(ref .. "%", COR.DOM_ESCUDO)) end
    end

    return false
end
talkTesteItem:separator(" ")
talkTesteItem:groupType(1)
talkTesteItem:register()

local talkTesteSPA = TalkAction("!testespa")
function talkTesteSPA.onSay(player, words, param)
    enviarMsgColorida(player, c("=== DIAGNÓSTICO COMPLETO DO SPA ===", COR.RARIDADE_LENDARIO))

    -- 1. Testar SPAManager (tabela SPA)
    enviarMsgColorida(player, c("[1] SPAManager:", COR.SISTEMA_INFO))
    if SPA and SPA.registerDomain then
        enviarMsgColorida(player, "  SPA.registerDomain: " .. c("OK", COR.SUCESSO_CURA))
    else
        enviarMsgColorida(player, "  SPA.registerDomain: " .. c("INDISPONÍVEL", COR.SISTEMA_ERRO))
    end
    if SPA and SPA.getDomain then
        enviarMsgColorida(player, "  SPA.getDomain: " .. c("OK", COR.SUCESSO_CURA))
    else
        enviarMsgColorida(player, "  SPA.getDomain: " .. c("INDISPONÍVEL", COR.SISTEMA_ERRO))
    end
    if SPA and SPA.onEvent then
        enviarMsgColorida(player, "  SPA.onEvent: " .. c("OK", COR.SUCESSO_CURA))
    else
        enviarMsgColorida(player, "  SPA.onEvent: " .. c("INDISPONÍVEL", COR.SISTEMA_ERRO))
    end
    if SPA and SPA.dispatchEvent then
        enviarMsgColorida(player, "  SPA.dispatchEvent: " .. c("OK", COR.SUCESSO_CURA))
    else
        enviarMsgColorida(player, "  SPA.dispatchEvent: " .. c("INDISPONÍVEL", COR.SISTEMA_ERRO))
    end

    -- 2. Testar Modificadores de Combate
    enviarMsgColorida(player, c("[2] Modificadores de Combate:", COR.SISTEMA_INFO))
    if player.setCombatModifier and player.getCombatModifier then
        player:setCombatModifier("test_fire", 42.5)
        local val = player:getCombatModifier("test_fire")
        enviarMsgColorida(player, "  set/get: " .. c("OK (" .. tostring(val) .. ")", COR.SUCESSO_CURA))
        -- limpar
        player:setCombatModifier("test_fire", 0)
    else
        enviarMsgColorida(player, "  set/get: " .. c("INDISPONÍVEL", COR.SISTEMA_ERRO))
    end

    -- 3. Testar atributos de Item (getElementalBond, etc.)
    enviarMsgColorida(player, c("[3] Atributos de Item:", COR.SISTEMA_INFO))
    local weapon = player:getSlotItem(CONST_SLOT_LEFT)
    if not weapon or (weapon:getType():getWeaponType() == WEAPON_SHIELD) then
        weapon = player:getSlotItem(CONST_SLOT_RIGHT)
    end
    if weapon then
        enviarMsgColorida(player, "  Arma: " .. c(weapon:getName(), COR.ITEM_RARO))
        if weapon.getElementalBond then
            local bond = weapon:getElementalBond()
            enviarMsgColorida(player, "  Elemental Bond: " .. c(tostring(bond), COR.ELEM_FOGO))
        else
            enviarMsgColorida(player, "  Elemental Bond: " .. c("método indisponível", COR.SISTEMA_NEUTRO))
        end
        if weapon.getMagicLevelPoints then
            local ml = weapon:getMagicLevelPoints()
            enviarMsgColorida(player, "  Magic Level Points: " .. c("+" .. ml, COR.SISTEMA_INFO))
        else
            enviarMsgColorida(player, "  Magic Level Points: " .. c("método indisponível", COR.SISTEMA_NEUTRO))
        end
        if weapon.getSkillFist then
            local sf = weapon:getSkillFist()
            if sf > 0 then enviarMsgColorida(player, "  Skill Fist: " .. c("+" .. sf, COR.SUCESSO_CURA)) end
        end
    else
        enviarMsgColorida(player, "  Nenhuma arma equipada.", COR.SISTEMA_NEUTRO)
    end

    -- 4. Testar Raça do Monstro (se tiveres um target)
    enviarMsgColorida(player, c("[4] Raça do Monstro:", COR.SISTEMA_INFO))
    local target = player:getTarget()
    if target and target:isMonster() then
        if target.getRaceId then
            local race = target:getRaceId()
            enviarMsgColorida(player, "  Raça: " .. c(tostring(race), COR.ELEM_TERRA))
        else
            enviarMsgColorida(player, "  getRaceId: " .. c("método indisponível", COR.SISTEMA_NEUTRO))
        end
    else
        enviarMsgColorida(player, "  Sem monstro selecionado.", COR.SISTEMA_NEUTRO)
    end

    -- 5. Testar Métodos Nativos (Tile, Party, Game)
    enviarMsgColorida(player, c("[5] Métodos Nativos:", COR.SISTEMA_INFO))
    local tile = player:getTile()
    if tile and tile.hasFlag then
        local isPz = tile:hasFlag(TILESTATE_PROTECTIONZONE)
        enviarMsgColorida(player, "  Tile.hasFlag: " .. c("OK (PZ=" .. tostring(isPz) .. ")", COR.SUCESSO_CURA))
    else
        enviarMsgColorida(player, "  Tile.hasFlag: " .. c("método indisponível", COR.SISTEMA_NEUTRO))
    end

    if player.getParty then
        local party = player:getParty()
        if party then
            enviarMsgColorida(player, "  Party: " .. c("Sim", COR.SUCESSO_CURA))
        else
            enviarMsgColorida(player, "  Party: " .. c("Nenhuma", COR.SISTEMA_NEUTRO))
        end
    else
        enviarMsgColorida(player, "  getParty: " .. c("método indisponível", COR.SISTEMA_NEUTRO))
    end

    if Game.getWorldType then
        local wt = Game.getWorldType()
        enviarMsgColorida(player, "  World Type: " .. c(tostring(wt), COR.SISTEMA_INFO))
    else
        enviarMsgColorida(player, "  Game.getWorldType: " .. c("método indisponível", COR.SISTEMA_NEUTRO))
    end

    -- 6. Testar SkillTrees (Lua puro)
    enviarMsgColorida(player, c("[6] SkillTrees (Lua):", COR.SISTEMA_INFO))
    if SPA and SPA.registerSkillTree and SPA.checkSkillTrees then
        enviarMsgColorida(player, "  SPA.registerSkillTree: " .. c("OK", COR.SUCESSO_CURA))
        enviarMsgColorida(player, "  SPA.checkSkillTrees: " .. c("OK", COR.SUCESSO_CURA))
    else
        enviarMsgColorida(player, "  SkillTrees: " .. c("módulo Lua não carregado", COR.SISTEMA_NEUTRO))
    end

    enviarMsgColorida(player, c("=== DIAGNÓSTICO CONCLUÍDO ===", COR.RARIDADE_LENDARIO))
    return false
end
talkTesteSPA:separator(" ")
talkTesteSPA:groupType(1)
talkTesteSPA:register()

print("DEBUG: comandos_spa.lua (v2.1)")