--[[
    Projeto MCR ? SPA v4.0 ? Sincronizador da Base de Dados
    Mantém a tabela habilidades_def sempre actualizada.
--]]

-- Sincroniza uma habilidade na tabela habilidades_def
function sincronizarHabilidadeBD(habId, hab)
    if not habId or not hab then return end
    local nome = db.escapeString(hab.nome or "Desconhecida")
    local tipo = db.escapeString(hab.tipo or "passiva")
    local dominioId = hab.dominio and hab.dominio[1] or 0
    local nivelMin = hab.nivelMin or 0
    local descricao = type(hab.descricaoEfeito) == "function"
        and db.escapeString("Descrição dinâmica")
        or db.escapeString(hab.descricaoEfeito or "")
    
    db.asyncQuery(string.format(
        "INSERT INTO habilidades_def (id, nome, dominio_id, tipo, requisito_afinidade, descricao) " ..
        "VALUES (%d, %s, %d, %s, %d, %s) " ..
        "ON DUPLICATE KEY UPDATE nome=%s, dominio_id=%d, tipo=%s, requisito_afinidade=%d, descricao=%s",
        habId, nome, dominioId, tipo, nivelMin, descricao,
        nome, dominioId, tipo, nivelMin, descricao
    ))
end

-- Metatable para a tabela HABILIDADES ? sincroniza automaticamente ao adicionar
local habilidadesMetatable = {
    __newindex = function(table, key, value)
        rawset(table, key, value)
        if type(key) == "number" and type(value) == "table" then
            sincronizarHabilidadeBD(key, value)
        end
    end
}

-- Aplicar a metatable à tabela HABILIDADES (se ainda não tiver)
if HABILIDADES and not getmetatable(HABILIDADES) then
    setmetatable(HABILIDADES, habilidadesMetatable)
end

-- Função para varrer todas as habilidades já carregadas e garantir que estão na BD
function sincronizarTodasHabilidades()
    for habId, hab in pairs(HABILIDADES) do
        if type(habId) == "number" and type(hab) == "table" then
            sincronizarHabilidadeBD(habId, hab)
        end
    end
end

-- Executar a sincronização inicial após todos os scripts carregarem
addEvent(function()
    sincronizarTodasHabilidades()
    print("DEBUG: Sincronização de habilidades com a BD concluída.")
end, 2000)

print("DEBUG: sincronizador_bd.lua v4.0 carregado.")