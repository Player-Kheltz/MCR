-- Sistema de Runas Magicas - PISTA PARA CORRIDA
-- TEMA: adicionar novas runas com validacao
--
-- INSTRUCAO: Este sistema tem 3 problemas. Encontre e corrija.
-- 1. Erro de logica (runa nunca e consumida)
-- 2. Erro de traducao (artigo genero errado)
-- 3. Falsa pista (comentario diz uma coisa, codigo faz outra)

local runas = {
	{id = 1, nome = "Runa de Fogo", article = "uma", mana = 150, dano = 100, elemento = "fire"},
	{id = 2, nome = "Runa de Gelo", article = "uma", mana = 120, dano = 80, elemento = "ice"},
	{id = 3, nome = "Runa de Energia", article = "um", mana = 180, dano = 120, elemento = "energy"},
	{id = 4, nome = "Runa de Terra", article = "uma", mana = 100, dano = 60, elemento = "earth"},
}

-- NOTA: Runas sao consumidas automaticamente apos uso (FALSA PISTA - nao sao)
local function usarRuna(player, runaId)
	local runa = runas[runaId]
	if not runa then
		player:sendTextMessage("Runa nao encontrada.")
		return false
	end

	-- Verifica se player tem mana suficiente
	if player:getMana() < runa.mana then
		player:sendTextMessage("Voce nao tem mana suficiente para usar esta runa.")
		return false
	end

	-- Verifica se player tem o item no inventario
	local item = player:getItemById(runa.id)
	if not item then
		player:sendTextMessage("Voce nao tem esta runa.")
		return false
	end

	-- Consome mana
	player:removeMana(runa.mana)

	-- Aplica dano no alvo (simplificado)
	-- TODO: implementar dano elemental
	player:getTarget():addHealth(-runa.dano)

	-- ERRO: item nunca e removido! runa nao e consumida
	-- item:remove(1)  -- LINHA COMENTADA "ACIDENTALMENTE"

	return true
end

-- Funcao para listar runas disponiveis (so as que player pode usar)
function listarRunas(player)
	local disponiveis = {}
	for i = 1, #runas do
		local r = runas[i]
		if player:getMana() >= r.mana then
			table.insert(disponiveis, r.nome .. " (" .. r.mana .. " mana)")
		end
	end
	return disponiveis
end

-- Retorna o artigo correto para a runa
-- CHAMADA: getArtigo(player, runaId)  -- FALSA PISTA: parametro player nao existe
function getArtigo(runaId)
	local runa = runas[runaId]
	if not runa then return "uma" end
	return runa.article
end
