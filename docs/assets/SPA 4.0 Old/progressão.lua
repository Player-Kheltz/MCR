--[[
    Projeto MCR ? SPA v4.0 ? Progressão
    Buffer de afinidade, desbloqueio de habilidades.
--]]

function adicionarAfinidade(player, dominioId, pontos)
    if pontos <= 0 or not dominioId then return end
    local bufferKey = STORAGE.AFINIDADE_BUFFER + dominioId
    local acumulado = player:getStorageValue(bufferKey) or 0
    player:setStorageValue(bufferKey, acumulado + pontos)
    player:registerDominioAction(dominioId)
end

function descarregarBuffer(player)
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

function getNivelPorAfinidade(acumulado)
    for nivel, pts in ipairs(NIVEL_PONTOS) do
        if acumulado < pts then return nivel - 1 end
    end
    return #NIVEL_PONTOS
end

function verificarDesbloqueio(player, dominioId)
    local afinidades = player:getDominioAfinidades(dominioId)
    local nivelDominio = getNivelPorAfinidade(afinidades[dominioId] or 0)
    for habId, hab in pairs(HABILIDADES) do
        if not jogadorConheceHabilidade(player, habId) then
            if nivelDominio >= hab.nivelMin and pertenceAoDominio(hab, dominioId) then
                aprenderHabilidade(player, habId)
                local descricao = hab.descricaoEfeito
                if type(descricao) == "function" then
                    descricao = descricao(player)
                end
                enviarMsgColorida(player, c("Você aprendeu ", COR.SISTEMA_INFO) .. c(hab.nome, corDominio(dominioId)) .. c("! ", COR.SISTEMA_INFO) .. c(descricao, COR.COMBO_AVISO) .. ".")
            end
        end
    end
    if nivelDominio > 0 then
        local nome = getNomeDominio(dominioId)
        enviarMsgColorida(player, "Sua afinidade com " .. c(nome, corDominio(dominioId)) .. " se aprofunda.")
        if nivelDominio % 5 == 0 then
            enviarMsgColorida(player, "Salto de poder em " .. c(nome, corDominio(dominioId)) .. "!")
        end
    end
end

function pertenceAoDominio(hab, dominioId)
    for _, d in ipairs(hab.dominio) do
        if d == dominioId then return true end
    end
    return false
end

print("DEBUG: progressao.lua v4.0 carregado.")