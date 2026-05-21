local talkSPACheck = TalkAction("!spacheck")

function talkSPACheck.onSay(player, words, param)
    local results = {}
    local startTime = os.time()

    local function addResult(categoria, item, status, extra)
        table.insert(results, {
            categoria = categoria,
            item = item,
            status = status, -- "OK", "ERRO", "INFO"
            extra = extra or ""
        })
    end

    enviarMsgColorida(player, c("=== INICIANDO DIAGNÓSTICO DO SPA 4.0 ===", COR.RARIDADE_LENDARIO))
    enviarMsgColorida(player, c("O diagnóstico levará alguns segundos...", COR.SISTEMA_NEUTRO))

    -- Fase 1: SPAManager (imediato)
    addResult("SPAManager", "Tabela SPA existe", SPA and "OK" or "ERRO")
    addResult("SPAManager", "SPA.registerDomain", (SPA and SPA.registerDomain) and "OK" or "ERRO")
    addResult("SPAManager", "SPA.getDomain", (SPA and SPA.getDomain) and "OK" or "ERRO")
    addResult("SPAManager", "SPA.onEvent", (SPA and SPA.onEvent) and "OK" or "ERRO")
    addResult("SPAManager", "SPA.dispatchEvent", (SPA and SPA.dispatchEvent) and "OK" or "ERRO")

    -- Teste de registerDomain e getDomain
    if SPA and SPA.registerDomain then
        SPA.registerDomain(99999, "Domínio de Teste", 1)
        local def = SPA.getDomain(99999)
        if def and def.name == "Domínio de Teste" then
            addResult("SPAManager", "Registro dinâmico de domínio", "OK", "Domínio 99999 criado e lido")
        else
            addResult("SPAManager", "Registro dinâmico de domínio", "ERRO", "getDomain retornou nil ou nome errado")
        end
    end

    -- Fase 2: Modificadores de Combate (imediato)
    if player.setCombatModifier and player.getCombatModifier then
        player:setCombatModifier("spacheck_test", 99.9)
        local val = player:getCombatModifier("spacheck_test")
        if math.abs(val - 99.9) < 0.01 then
            addResult("Modificadores", "setCombatModifier / getCombatModifier", "OK", "Valor: " .. tostring(val))
        else
            addResult("Modificadores", "setCombatModifier / getCombatModifier", "ERRO", "Esperado 99.9, obtido " .. tostring(val))
        end
        player:setCombatModifier("spacheck_test", 0) -- limpar
    else
        addResult("Modificadores", "setCombatModifier / getCombatModifier", "ERRO", "Métodos indisponíveis")
    end

    -- Fase 3: Atributos de Item (imediato)
    local weapon = player:getSlotItem(CONST_SLOT_LEFT)
    if not weapon or (weapon:getType():getWeaponType() == WEAPON_SHIELD) then
        weapon = player:getSlotItem(CONST_SLOT_RIGHT)
    end
    if weapon then
        addResult("Itens", "Arma equipada", "INFO", weapon:getName())
        if weapon.getElementalBond then
            addResult("Itens", "getElementalBond", "OK", tostring(weapon:getElementalBond()))
        else
            addResult("Itens", "getElementalBond", "ERRO", "Método indisponível")
        end
        if weapon.getMagicLevelPoints then
            addResult("Itens", "getMagicLevelPoints", "OK", "+" .. weapon:getMagicLevelPoints())
        else
            addResult("Itens", "getMagicLevelPoints", "ERRO", "Método indisponível")
        end
        if weapon.getSkillFist then
            local sf = weapon:getSkillFist()
            if sf > 0 then
                addResult("Itens", "getSkillFist", "OK", "+" .. sf)
            end
        end
    else
        addResult("Itens", "Arma equipada", "INFO", "Nenhuma")
    end

    -- Fase 4: Métodos Nativos (imediato)
    if player.getTile then
        local tile = player:getTile()
        if tile and tile.hasFlag then
            addResult("Nativos", "Tile.hasFlag", "OK", "PZ=" .. tostring(tile:hasFlag(TILESTATE_PROTECTIONZONE)))
        else
            addResult("Nativos", "Tile.hasFlag", "ERRO", "Método indisponível")
        end
    end
    if player.getParty then
        local party = player:getParty()
        addResult("Nativos", "getParty", "OK", party and "Em grupo" or "Sem grupo")
    else
        addResult("Nativos", "getParty", "ERRO", "Método indisponível")
    end
    if Game and Game.getWorldType then
        addResult("Nativos", "Game.getWorldType", "OK", "Tipo " .. tostring(Game.getWorldType()))
    else
        addResult("Nativos", "Game.getWorldType", "ERRO", "Método indisponível")
    end

    -- Fase 5: SkillTrees (imediato)
    if SPA and SPA.registerSkillTree and SPA.checkSkillTrees then
        addResult("SkillTrees", "SPA.registerSkillTree", "OK")
        addResult("SkillTrees", "SPA.checkSkillTrees", "OK")
    else
        addResult("SkillTrees", "SPA.registerSkillTree", "ERRO", "Módulo não carregado")
        addResult("SkillTrees", "SPA.checkSkillTrees", "ERRO", "Módulo não carregado")
    end

    -- Fase 6: Raça do Monstro (depende de target)
    local target = player:getTarget()
    if target and target:isMonster() then
        if target.getRaceId then
            local race = target:getRaceId()
            addResult("Nativos", "Monster.getRaceId", "OK", "Raça: " .. tostring(race))
        else
            addResult("Nativos", "Monster.getRaceId", "ERRO", "Método indisponível")
        end
    else
        addResult("Nativos", "Monster.getRaceId", "INFO", "Sem monstro selecionado")
    end

    -- Fase 7: Event Bus (adiado para depuração posterior)
    addResult("Event Bus", "onEvent / dispatchEvent", "INFO", "Teste adiado ? use !testebus")
    sendFinalReport(player, results, os.time() - startTime)

    return false
end

function sendFinalReport(player, results, elapsed)
    enviarMsgColorida(player, c("=== RELATÓRIO FINAL DO SPA 4.0 ===", COR.RARIDADE_LENDARIO))
    enviarMsgColorida(player, "Tempo de diagnóstico: " .. c(elapsed .. "s", COR.SISTEMA_INFO))

    local categorias = {}
    for _, r in ipairs(results) do
        categorias[r.categoria] = true
    end

    local totalOK, totalErro, totalInfo = 0, 0, 0
    for _, r in ipairs(results) do
        if r.status == "OK" then totalOK = totalOK + 1
        elseif r.status == "ERRO" then totalErro = totalErro + 1
        else totalInfo = totalInfo + 1 end
    end

    for cat, _ in pairs(categorias) do
        enviarMsgColorida(player, c("[" .. cat .. "]", COR.SISTEMA_INFO))
        for _, r in ipairs(results) do
            if r.categoria == cat then
                local cor = r.status == "OK" and COR.SUCESSO_CURA or (r.status == "ERRO" and COR.SISTEMA_ERRO or COR.SISTEMA_NEUTRO)
                local line = "  " .. r.item .. ": " .. c(r.status, cor)
                if r.extra ~= "" then line = line .. " (" .. r.extra .. ")" end
                enviarMsgColorida(player, line)
            end
        end
    end

    enviarMsgColorida(player, c("Resumo: ", COR.SISTEMA_INFO) ..
        c(totalOK .. " OK", COR.SUCESSO_CURA) .. " | " ..
        c(totalErro .. " ERROS", COR.SISTEMA_ERRO) .. " | " ..
        c(totalInfo .. " INFO", COR.SISTEMA_NEUTRO))

    if totalErro == 0 then
        enviarMsgColorida(player, c("SPA 4.0 está TOTALMENTE OPERACIONAL!", COR.RARIDADE_LENDARIO))
    else
        enviarMsgColorida(player, c("ATENÇÃO: " .. totalErro .. " falhas detectadas.", COR.SISTEMA_ERRO))
    end
end

talkSPACheck:separator(" ")
talkSPACheck:groupType(1)
talkSPACheck:register()

local talkDominios = TalkAction("!dominios")
function talkDominios.onSay(player, words, param)
    enviarMsgColorida(player, c("=== DOMÍNIOS REGISTADOS NO SPA ===", COR.RARIDADE_LENDARIO))

    -- Validar o método C++
    if not SPA.getAllDomainIds then
        enviarMsgColorida(player, c("SPA.getAllDomainIds: método indisponível!", COR.SISTEMA_ERRO))
        return false
    end

    local ids = SPA.getAllDomainIds()
    if not ids or #ids == 0 then
        enviarMsgColorida(player, c("Nenhum domínio registado.", COR.SISTEMA_ERRO))
        return false
    end

    enviarMsgColorida(player, "Total de domínios: " .. c(tostring(#ids), COR.SISTEMA_INFO))

    local linha = ""
    for i, id in ipairs(ids) do
        local def = SPA.getDomain(id)
        local nome = def and def.name or "???"
        local parent = def and def.parentId or 0
        local parte = c(id .. ":" .. nome, COR.SISTEMA_INFO)
        if parent > 0 then
            parte = parte .. c("(->" .. parent .. ")", COR.SISTEMA_NEUTRO)
        end
        if #linha + #parte > 300 then
            enviarMsgColorida(player, linha)
            linha = ""
        end
        linha = linha .. parte .. "  "
    end
    if linha ~= "" then
        enviarMsgColorida(player, linha)
    end

    enviarMsgColorida(player, c("=== FIM DA LISTA ===", COR.RARIDADE_LENDARIO))
    return false
end
talkDominios:separator(" ")
talkDominios:groupType(1)
talkDominios:register()

local talkTesteBus = TalkAction("!testebus")
function talkTesteBus.onSay(player, words, param)
    enviarMsgColorida(player, c("=== TESTE DO EVENT BUS ===", COR.RARIDADE_LENDARIO))

    if not SPA.onEvent or not SPA.dispatchEvent then
        enviarMsgColorida(player, c("Métodos do Event Bus indisponíveis.", COR.SISTEMA_ERRO))
        return false
    end

    local recebido = false
    SPA.onEvent("__testebus", function(arg1, arg2)
        recebido = true
    end)

    SPA.dispatchEvent("__testebus", "hello", 42)

    addEvent(function()
        if recebido then
            enviarMsgColorida(player, c("Event Bus: OK ? callback recebido.", COR.SUCESSO_CURA))
        else
            enviarMsgColorida(player, c("Event Bus: ERRO ? callback não foi chamado.", COR.SISTEMA_ERRO))
        end
    end, 500)

    return false
end
talkTesteBus:separator(" ")
talkTesteBus:groupType(1)
talkTesteBus:register()

local talkCheckHierarchy = TalkAction("!checkhier")
function talkCheckHierarchy.onSay(player, words, param)
    enviarMsgColorida(player, "domainHierarchy[132] = " .. tostring(domainHierarchy[132]))
    enviarMsgColorida(player, "domainHierarchy[133] = " .. tostring(domainHierarchy[133]))
    enviarMsgColorida(player, "secondaryParent[14] = " .. tostring(secondaryParent[14]))
    return false
end
talkCheckHierarchy:separator(" ")
talkCheckHierarchy:groupType(1)
talkCheckHierarchy:register()

local talkDiagHab = TalkAction("!diaghab")
function talkDiagHab.onSay(player, words, param)
    enviarMsgColorida(player, c("=== DIAGNÓSTICO DE HABILIDADES ===", COR.RARIDADE_LENDARIO))

    -- 1. Quantas habilidades existem na tabela HABILIDADES?
    local count = 0
    for _ in pairs(HABILIDADES) do count = count + 1 end
    enviarMsgColorida(player, "Total de habilidades em HABILIDADES: " .. c(tostring(count), COR.SISTEMA_INFO))

    -- 2. Listar as primeiras 5 habilidades (IDs)
    local ids = {}
    for id, _ in pairs(HABILIDADES) do
        if type(id) == "number" then table.insert(ids, id) end
    end
    table.sort(ids)
    local amostra = {}
    for i = 1, math.min(5, #ids) do
        local hab = HABILIDADES[ids[i]]
        amostra[#amostra + 1] = ids[i] .. ":" .. (hab.nome or "?")
    end
    enviarMsgColorida(player, "Amostra: " .. c(table.concat(amostra, ", "), COR.SISTEMA_NEUTRO))

    -- 3. O jogador conhece alguma habilidade?
    local conhecidas = 0
    for _, id in ipairs(ids) do
        if jogadorConheceHabilidade(player, id) then
            conhecidas = conhecidas + 1
        end
    end
    enviarMsgColorida(player, "Habilidades conhecidas: " .. c(tostring(conhecidas), COR.SUCESSO_CURA))

    -- 4. Verificar uma habilidade específica (ex.: 13210 - Corte Duplo)
    local testId = 13210
    local hab = HABILIDADES[testId]
    if hab then
        enviarMsgColorida(player, "Habilidade " .. testId .. " (" .. hab.nome .. "):")
        enviarMsgColorida(player, "  Existe na tabela: " .. c("SIM", COR.SUCESSO_CURA))
        enviarMsgColorida(player, "  Conhecida: " .. (jogadorConheceHabilidade(player, testId) and c("SIM", COR.SUCESSO_CURA) or c("NÃO", COR.SISTEMA_ERRO)))
        enviarMsgColorida(player, "  Storage " .. (STORAGE.HABILIDADE_BASE + testId) .. " = " .. tostring(player:getStorageValue(STORAGE.HABILIDADE_BASE + testId) or 0))
    else
        enviarMsgColorida(player, "Habilidade " .. testId .. " NÃO existe na tabela!", COR.SISTEMA_ERRO)
    end

    -- 5. Força aprender uma habilidade de teste
    if hab then
        aprenderHabilidade(player, testId)
        enviarMsgColorida(player, "Forçada aprendizagem de " .. hab.nome .. ". Storage agora = " .. tostring(player:getStorageValue(STORAGE.HABILIDADE_BASE + testId) or 0))
    end

    return false
end
talkDiagHab:separator(" ")
talkDiagHab:groupType(1)
talkDiagHab:register()

local talkTesteExec = TalkAction("!testeexec")
function talkTesteExec.onSay(player, words, param)
    -- Força a chamada do executor manualmente
    local target = player:getTarget()
    if not target then
        enviarMsgColorida(player, "Seleccione um alvo primeiro.", COR.SISTEMA_ERRO)
        return false
    end

    enviarMsgColorida(player, c("=== TESTE DO EXECUTOR ===", COR.RARIDADE_LENDARIO))
    executarHabilidades(player, "onAttack", target, 100, COMBAT_PHYSICALDAMAGE)
    enviarMsgColorida(player, "Executor chamado manualmente. Verifique o chat para habilidades.", COR.SISTEMA_INFO)
    return false
end
talkTesteExec:separator(" ")
talkTesteExec:groupType(1)
talkTesteExec:register()

local talkDiagExec = TalkAction("!diagexec")
function talkDiagExec.onSay(player, words, param)
    local status = player:getStorageValue(99999)
    if status == 1 then
        player:setStorageValue(99999, 0)
        enviarMsgColorida(player, c("Modo de depuração DESATIVADO.", COR.SISTEMA_NEUTRO))
    else
        player:setStorageValue(99999, 1)
        enviarMsgColorida(player, c("Modo de depuração ATIVADO. Cada ataque mostrará as habilidades que FALHARAM no teste de armaCompativeis.", COR.SISTEMA_INFO))
    end
    return false
end
talkDiagExec:separator(" ")
talkDiagExec:groupType(1)
talkDiagExec:register()

local talkDiagArma = TalkAction("!diagarma")
function talkDiagArma.onSay(player, words, param)
    local weapon = player:getSlotItem(CONST_SLOT_LEFT) or player:getSlotItem(CONST_SLOT_RIGHT)
    enviarMsgColorida(player, c("=== DIAGNÓSTICO DE ARMA ===", COR.RARIDADE_LENDARIO))
    if weapon then
        enviarMsgColorida(player, "Arma: " .. weapon:getName())
        local wt = weapon:getType():getWeaponType()
        enviarMsgColorida(player, "WeaponType: " .. tostring(wt))
        local esp = getWeaponEspecialidade(player, weapon)
        enviarMsgColorida(player, "Especialidade retornada: " .. tostring(esp))
        enviarMsgColorida(player, "domainHierarchy[" .. tostring(esp) .. "] = " .. tostring(domainHierarchy[esp] or "nil"))
        local hier = domainHierarchy[esp]
        if hier then
            enviarMsgColorida(player, "secondaryParent[" .. tostring(hier) .. "] = " .. tostring(secondaryParent[hier] or "nil"))
        end
        local compat = armaCompativeis(player, {132})
        enviarMsgColorida(player, "armaCompativeis({132}): " .. (compat and c("TRUE", COR.SUCESSO_CURA) or c("FALSE", COR.SISTEMA_ERRO)))
    else
        enviarMsgColorida(player, "Nenhuma arma equipada.", COR.SISTEMA_NEUTRO)
    end
    return false
end
talkDiagArma:separator(" ")
talkDiagArma:groupType(1)
talkDiagArma:register()

local talkAddFist = TalkAction("!addfist")
function talkAddFist.onSay(player, words, param)
    player:addSkillTries(SKILL_FIST, 1000)
    enviarMsgColorida(player, c("Foram adicionados 1000 tries de Fist Fighting.", COR.SISTEMA_INFO))
    return false
end
talkAddFist:separator(" ")
talkAddFist:groupType(1)
talkAddFist:register()

local talkForceChance = TalkAction("!forcechance")
function talkForceChance.onSay(player, words, param)
    local count = 0
    for id, hab in pairs(HABILIDADES) do
        if hab.tipo == "gatilho" and hab.chanceBase then
            hab._oldChanceBase = hab.chanceBase
            hab.chanceBase = 100
            count = count + 1
        end
    end
    enviarMsgColorida(player, c(count .. " habilidades tiveram chance alterada para 100%.", COR.SUCESSO_CURA))
    return false
end
talkForceChance:separator(" ")
talkForceChance:groupType(1)
talkForceChance:register()

local talkRestoreChance = TalkAction("!restorechance")
function talkRestoreChance.onSay(player, words, param)
    local count = 0
    for id, hab in pairs(HABILIDADES) do
        if hab._oldChanceBase then
            hab.chanceBase = hab._oldChanceBase
            hab._oldChanceBase = nil
            count = count + 1
        end
    end
    enviarMsgColorida(player, c(count .. " habilidades restauradas.", COR.SISTEMA_INFO))
    return false
end
talkRestoreChance:separator(" ")
talkRestoreChance:groupType(1)
talkRestoreChance:register()

local talkDiagProg = TalkAction("!diagprog")
function talkDiagProg.onSay(player, words, param)
    enviarMsgColorida(player, "Especialidade atual: " .. tostring(getWeaponEspecialidade(player, player:getSlotItem(CONST_SLOT_LEFT) or player:getSlotItem(CONST_SLOT_RIGHT))))
    local dom = getWeaponEspecialidade(player, nil) -- sem arma
    enviarMsgColorida(player, "Desarmado seria: " .. tostring(dom))
    return false
end
talkDiagProg:separator(" ")
talkDiagProg:groupType(1)
talkDiagProg:register()

local talkClearLocks = TalkAction("!clearlocks")
function talkClearLocks.onSay(player, words, param)
    local count = 0
    for habId, hab in pairs(HABILIDADES) do
        if type(habId) == "number" and hab.tipo == "gatilho" then
            player:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 0)
            count = count + 1
        end
    end
    enviarMsgColorida(player, c(count .. " locks de habilidades foram limpos.", COR.SUCESSO_CURA))
    return false
end
talkClearLocks:separator(" ")
talkClearLocks:groupType(1)
talkClearLocks:register()

local talkTesteHab = TalkAction("!testehab")
function talkTesteHab.onSay(player, words, param)
    local habId = tonumber(param)
    if not habId then
        enviarMsgColorida(player, "Uso: !testehab <id>", COR.SISTEMA_ERRO)
        return false
    end
    local hab = HABILIDADES[habId]
    if not hab then
        enviarMsgColorida(player, "Habilidade " .. habId .. " não encontrada.", COR.SISTEMA_ERRO)
        return false
    end
    local target = player:getTarget()
    if not target then
        enviarMsgColorida(player, "Seleccione um alvo.", COR.SISTEMA_ERRO)
        return false
    end

    if hab.tipo ~= "gatilho" then
        enviarMsgColorida(player, "Apenas habilidades de gatilho podem ser testadas.", COR.SISTEMA_NEUTRO)
        return false
    end

    -- Limpar o lock desta habilidade antes de testar
    player:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 0)

    enviarMsgColorida(player, "Forçando " .. hab.nome .. "...")

    -- Simula o processamento do executor
    local ok, err = pcall(function()
        if hab.buffType == "speedBurst" then
            applySpeedBurst(player, hab.buffMultiplier, hab.buffDurationMs or 500)
        elseif hab.buffType == "nextAttackCondition" then
            applyNextAttackCondition(player, hab.conditionType, hab.conditionDuration, hab.conditionDamage)
        elseif hab.buffType == "damageBoost" then
            applyDamageBoost(player, hab.percentExtra, hab.buffHits)
        elseif hab.buffType == "lifeLeech" then
            applyLifeLeech(player, hab.leechPercent, hab.durationSec)
        elseif hab.buffType == "custom" and hab.efeito then
            hab.efeito(player, target, 100)
        else
            enviarMsgColorida(player, "Habilidade sem efeito executável.", COR.SISTEMA_NEUTRO)
        end
        if hab.efeitoVisual then
            hab.efeitoVisual(player, target)
        end
    end)
    if not ok then
        enviarMsgColorida(player, "Erro: " .. tostring(err), COR.SISTEMA_ERRO)
    else
        enviarMsgColorida(player, "Efeito executado.", COR.SUCESSO_CURA)
    end
    -- Libertar o lock
    player:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 0)
    return false
end
talkTesteHab:separator(" ")
talkTesteHab:groupType(1)
talkTesteHab:register()

local talkForceLearnPunho = TalkAction("!learnpunho")
function talkForceLearnPunho.onSay(player, words, param)
    local count = 0
    for habId, hab in pairs(HABILIDADES) do
        if type(habId) == "number" and hab.tipo == "gatilho" then
            for _, dom in ipairs(hab.dominio) do
                if dom == 132 then
                    aprenderHabilidade(player, habId)
                    count = count + 1
                    break
                end
            end
        end
    end
    enviarMsgColorida(player, c(count .. " habilidades de Armas de Punho foram forçadas.", COR.SUCESSO_CURA))
    return false
end
talkForceLearnPunho:separator(" ")
talkForceLearnPunho:groupType(1)
talkForceLearnPunho:register()

local talkSPAReset = TalkAction("!spareset")
function talkSPAReset.onSay(player, words, param)
    local playerId = player:getId()

    -- 1. Zera afinidades de todos os domínios
    for _, domId in ipairs(ALL_DOMINIOS) do
        local atual = player:getDominioAfinidade(domId)
        if atual > 0 then
            player:addDominioAfinidade(domId, -atual)
        end
    end

    -- 2. Apaga todas as habilidades aprendidas (BD)
    db.query("DELETE FROM player_habilidades WHERE player_id = " .. playerId)

    -- 3. Zera TODAS as storages do SPA (faixa 90000?99999)
    for i = 90000, 99999 do
        player:setStorageValue(i, 0)
    end

    -- 4. Remove todos os estados de alma (Lampejo/Vínculo)
    for _, domId in ipairs(ALL_DOMINIOS) do
        player:setDominioState(domId, 0)
    end

    -- 5. Limpa histórico de ações
    if player.clearActionHistory then
        player:clearActionHistory()
    end

    -- 6. Reseta Virtude e Serenidade
    player:setVirtue(Virtue_t.None)
    if player.setSerene then
        player:setSerene(false)
    end

    -- 7. Limpa locks de habilidades (storages 91600+)
    for habId, _ in pairs(HABILIDADES) do
        if type(habId) == "number" then
            player:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 0)
        end
    end

    -- 8. Reaplica postura padrão
    player:setStealth(false)
    aplicarPostura(player, FIGHTMODE_BALANCED)

    enviarMsgColorida(player, c("SPA completamente resetado. O personagem está como recém?criado.", COR.SISTEMA_INFO))
    return false
end
talkSPAReset:separator(" ")
talkSPAReset:groupType(1)
talkSPAReset:register()

local talkSPAPlat = TalkAction("!spaplat")
function talkSPAPlat.onSay(player, words, param)
    local maxAf = 180000  -- nível 20 garantido (ver NIVEL_PONTOS)

    -- 1. Maximiza afinidade de todos os domínios
    for _, domId in ipairs(ALL_DOMINIOS) do
        local atual = player:getDominioAfinidade(domId)
        local pontos = maxAf - atual
        if pontos > 0 then
            player:addDominioAfinidade(domId, pontos)
        end
        verificarDesbloqueio(player, domId)
    end

    -- 2. Aprende TODAS as habilidades da tabela HABILIDADES
    for habId, _ in pairs(HABILIDADES) do
        if type(habId) == "number" and not jogadorConheceHabilidade(player, habId) then
            aprenderHabilidade(player, habId)
        end
    end

    -- 3. Chi máximo
    player:fillHarmony()
    player:setStorageValue(STORAGE.HARMONY, 5)

    -- 4. Virtude (Harmony como padrão, mas podes trocar)
    player:setVirtue(Virtue_t.Harmony)

    -- 5. Serenidade ativa
    if player.setSerene then
        player:setSerene(true)
    end

    -- 6. Limpa todos os locks de habilidades
    for habId, _ in pairs(HABILIDADES) do
        if type(habId) == "number" then
            player:setStorageValue(STORAGE.HABILIDADE_LOCK + habId, 0)
        end
    end

    -- 7. Reaplica passivas e postura
    aplicarPassivasBasicas(player)
    player:setStealth(false)
    aplicarPostura(player, player:getFightMode())

    enviarMsgColorida(player, c("SPA platinado! Todos os domínios, habilidades e bónus ativos.", COR.RARIDADE_LENDARIO))
    return false
end
talkSPAPlat:separator(" ")
talkSPAPlat:groupType(1)
talkSPAPlat:register()

print("DEBUG: Comandos Novos carregado.")