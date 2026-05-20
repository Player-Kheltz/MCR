--[[
    Projeto MCR ? progressao.lua (v10.0)
    Buffer de progressão: acumula afinidade em memória e descarrega a cada 3s.
    Também verifica e desbloqueia habilidades automaticamente.
--]]

-- ============================================================
-- BUFFER DE PROGRESSÃO
-- ============================================================
-- Acumula pontos de afinidade em storages temporárias (95001 + dominioId)
-- Em vez de escrever na BD a cada ataque.
function adicionarAfinidade(player, dominioId, pontos)
    if pontos <= 0 or not dominioId then return end

    -- Acumula no buffer (storage temporária)
    local bufferKey = STORAGE.AFINIDADE_BUFFER + dominioId
    local acumulado = player:getStorageValue(bufferKey) or 0
    player:setStorageValue(bufferKey, acumulado + pontos)

    -- Regista a ação no histórico (para Lampejos/Vínculos) ? esta é barata
    player:registerDominioAction(dominioId)
end

-- Descarrega o buffer de todos os domínios para a BD (usa lote)
function descarregarBuffer(player)
    if not ALL_DOMINIOS then
        print("AVISO: ALL_DOMINIOS não está definida no momento do descarregamento.")
        return
    end

    local dados = {}
    for _, domId in ipairs(ALL_DOMINIOS) do
        local bufferKey = STORAGE.AFINIDADE_BUFFER + domId
        local acumulado = player:getStorageValue(bufferKey) or 0
        if acumulado > 0 then
            dados[domId] = acumulado
            player:setStorageValue(bufferKey, 0)
        end
    end

    if next(dados) then
        player:addDominioAfinidadeBatch(dados)
        for domId, _ in pairs(dados) do
            verificarDesbloqueio(player, domId)
        end
    end
end

-- ============================================================
-- NÍVEL POR AFINIDADE
-- ============================================================
function getNivelPorAfinidade(acumulado)
    for nivel, pts in ipairs(NIVEL_PONTOS) do
        if acumulado < pts then return nivel - 1 end
    end
    return #NIVEL_PONTOS
end

-- ============================================================
-- VERIFICAÇÃO DE DESBLOQUEIO DE HABILIDADES
-- ============================================================
function pertenceAoDominio(hab, dominioId)
    for _, d in ipairs(hab.dominio) do
        if d == dominioId then return true end
    end
    return false
end

function verificarDesbloqueio(player, dominioId)
    -- Obtém as afinidades em lote para todos os domínios relevantes
    local dominiosParaVerificar = {dominioId}
    local afinidades = player:getDominioAfinidades(unpack(dominiosParaVerificar))
    local nivelDominio = getNivelPorAfinidade(afinidades[dominioId] or 0)

    for habId, hab in pairs(HABILIDADES) do
        if not jogadorConheceHabilidade(player, habId) then
            if nivelDominio >= hab.nivelMin and pertenceAoDominio(hab, dominioId) then
                aprenderHabilidade(player, habId)
                local msg = c("Você aprendeu ", COR.SISTEMA_INFO) ..
                            c(hab.nome, corDominio(dominioId)) ..
                            c("! ", COR.SISTEMA_INFO) ..
                            c(hab.descricaoEfeito, COR.COMBO_AVISO) .. "."
                enviarMsgColorida(player, msg)
            end
        end
    end

    -- Feedback de progressão de afinidade (apenas quando o buffer descarrega)
    if nivelDominio > 0 then
        local nome = getNomeDominio(dominioId)
        enviarMsgColorida(player, "Sua afinidade com " .. c(nome, corDominio(dominioId)) .. " se aprofunda.")
        if nivelDominio % 5 == 0 then
            enviarMsgColorida(player, "Salto de poder em " .. c(nome, corDominio(dominioId)) .. "!")
        end
    end
end

-- ============================================================
-- FEEDBACK DE PROGRESSÃO (mantido para quando o buffer descarrega)
-- ============================================================
-- (O feedback agora é feito dentro de verificarDesbloqueio, pois
--  é o momento em que a afinidade realmente sobe na BD.)

print("DEBUG: progressao.lua (v10.0) carregado.")