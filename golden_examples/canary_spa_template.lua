--- CANARY SPA SKILL TEMPLATE — API 100% real do servidor
--- Use ESTRITAMENTE esta estrutura. Nao invente campos novos.

--- ARQUIVO: sopro_do_dragao.lua ---
HABILIDADES[200001] = {
    nome = "Sopro do Dragao",
    tipo = "ativo",
    dominio = {53},             -- Fogo = 53 (dominio primario)
    nivelMin = 1,               -- Nivel minimo no dominio
    focoMin = 50,               -- Foco minimo necessario (porcentagem)
    cooldown = 10,              -- Cooldown em segundos
    custo = {10, 5},            -- {mana, stamina}

    efeitoConfig = {
        danoBase = 50,
        danoExtra = 20,          -- dano_extra
        elemento = "fire",
        chanceQueima = 30,       -- chance de queimar (porcentagem)
        duracaoQueima = 3,       -- duracao em segundos
        tipo = "single",
    },

    descricao = "Um sopro ardente que queima o alvo.",
}

--- ARQUIVO: npc_mestre_fogo.lua ---
-- NPC que ensina a habilidade SPA
local internalNpcName = "Mestre do Fogo"
local npcType = Game.createNpcType(internalNpcName)
local npcConfig = {}

npcConfig.name = internalNpcName
npcConfig.outfit = { lookType = 130 }

local keywordHandler = KeywordHandler:new()
npcType:register(keywordHandler)

HABILIDADES_NPC[200001] = {
    npcName = internalNpcName,
    dominio = {53},
    nivelMin = 10,
}
