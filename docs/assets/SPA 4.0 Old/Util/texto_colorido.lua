--[[
    Projeto MCR ? texto_colorido.lua (v9.1)
    Tabela de cores revista com teoria cromática para fundo escuro.
    Inclui cores para missões, NPCs e interacções.
    Compatível com OTClient Redemption (sintaxe {Texto, #Cor}).
--]]

COR = {
    -- ============================================================
    -- POSITIVO / SUCESSO / ALIADOS
    -- ============================================================
    SUCESSO_CURA         = "#2ECC71",   -- Verde esmeralda ? cura, vida, positivo
    ALIADO_JOGADOR       = "#58D68D",   -- Verde suave ? nome de aliado
    ALIADO_SUMMON        = "#7DCEA0",   -- Verde mais claro ? invocação aliada
    RARIDADE_OURO        = "#F1C40F",   -- Dourado ? raro, valioso
    RARIDADE_LENDARIO    = "#E67E22",   -- Laranja queimado ? lendário, épico

    -- ============================================================
    -- INFORMAÇÃO / SISTEMA
    -- ============================================================
    SISTEMA_INFO         = "#5DADE2",   -- Azul médio ? agradável, limpo, boa legibilidade
    SISTEMA_NEUTRO       = "#BDC3C7",   -- Cinza prateado ? texto narrativo neutro
    POSTURA_INFO         = "#85C1E9",   -- Azul claro ? informação de estado
    DANO_RECEBIDO_INFO   = "#F5B041",   -- Laranja suave ? alerta de dano recebido
    POSTURA_IMPETO     = "#FF4040",   -- Vermelho (agressivo)
    POSTURA_EQUILIBRIO = "#DFD94B",   -- Amarelo (versátil)
    POSTURA_GUARDA     = "#26C326",   -- Azul (defensivo)

    -- ============================================================
    -- NPCs E INTERACÇÕES
    -- ============================================================
    NPC_DIALOGO          = "#A3E4D7",   -- Verde água ? fala de NPC amigável
    NPC_COMERCIANTE      = "#F9E79F",   -- Amarelo pastel ? comerciante, negócios
    NPC_GUARDA           = "#D5D8DC",   -- Cinza claro ? autoridade, guarda
    NPC_MISTERIOSO       = "#BB8FCE",   -- Roxo claro ? misterioso, mágico
    NPC_OPCAO            = "#F7DC6F",   -- Amarelo ? uma opção que o jogador pode escolher ("Criar", "Gerenciar")
    NPC_COMANDO          = "#85C1E9",   -- Azul claro ? comando que o jogador pode digitar ("Senha", "Entrar")
    NPC_ITEM             = "#E67E22",   -- Laranja ? nome de item ("Espada de Cristal")
    NPC_LOCAL            = "#2ECC71",   -- Verde ? nome de local ("Thais", "Caverna dos Orcs")
    NPC_INTENCAO         = "#58D68D",   -- Verde suave ? intenção positiva ("Sim", "Aceito")
    NPC_RECUSA           = "#E74C3C",   -- Vermelho ? recusa ("Não", "Cancelar")
    NPC_EMOCAO           = "#BB8FCE",   -- Roxo ? emoção ou estado ("preocupado", "aliviado")
    NPC_NOME             = "#5DADE2",   -- Azul médio ? nome próprio de outro NPC ("Ferumbras")
    NPC_ALERTA           = "#F39C12",   -- Laranja ? aviso ou perigo em diálogo ("cuidado!")

    -- ============================================================
    -- PERIGO / NEGATIVO / INIMIGOS
    -- ============================================================
    DANO_FISICO          = "#E74C3C",   -- Vermelho ? dano físico
    DANO_CRITICO         = "#C0392B",   -- Vermelho escuro ? crítico
    COND_SANGRAMENTO     = "#922B21",   -- Bordô ? sangramento
    COND_VENENO          = "#1E8449",   -- Verde escuro ? veneno
    COND_ATORDOADO       = "#D4AC0D",   -- Amarelo mostarda ? atordoamento
    COND_MEDO            = "#6C3483",   -- Roxo ? medo
    COND_PARALISIA       = "#1ABC9C",   -- Turquesa ? paralisia
    INIMIGO_MONSTRO      = "#E74C3C",   -- Vermelho ? nome de monstro
    INIMIGO_BOSS         = "#8E44AD",   -- Roxo escuro ? chefe
    SISTEMA_ERRO         = "#E74C3C",   -- Vermelho ? erro
    SISTEMA_AVISO        = "#F39C12",   -- Laranja ? aviso

    -- ============================================================
    -- ELEMENTOS MÁGICOS
    -- ============================================================
    ELEM_FOGO            = "#E74C3C",   -- Vermelho ? fogo
    ELEM_AGUA            = "#3498DB",   -- Azul ? água
    ELEM_GELO            = "#85C1E9",   -- Azul gelo ? frio
    ELEM_TERRA           = "#AF601A",   -- Marrom ? terra
    ELEM_VENENO          = "#27AE60",   -- Verde ? veneno
    ELEM_RAIO            = "#F1C40F",   -- Amarelo ? raio / energia
    ELEM_SAGRADO         = "#F7DC6F",   -- Amarelo claro ? sagrado
    ELEM_SOMBRA          = "#7D3C98",   -- Roxo escuro ? sombra / morte

    -- ============================================================
    -- DOMÍNIOS DE COMBATE
    -- ============================================================
    DOM_COMBATE_LAMINAS   = "#C0392B",  -- Vermelho escuro ? lâminas, corte
    DOM_COMBATE_IMPACTO   = "#D35400",  -- Laranja queimado ? impacto, força bruta
    DOM_COMBATE_PRECISAO  = "#2ECC71",  -- Verde ? precisão, tiro certeiro
    DOM_COMBATE_DESARMADO = "#8E44AD",  -- Roxo ? desarmado, chi
    DOM_ESCUDO            = "#7F8C8D",  -- Cinza metálico ? escudo, defesa

    -- ============================================================
    -- DOMÍNIOS MÁGICOS
    -- ============================================================
    DOM_MAGIA_FOGO        = "#E74C3C",  -- Vermelho ? fogo
    DOM_MAGIA_AGUA_GELO   = "#3498DB",  -- Azul ? água/gelo
    DOM_MAGIA_TERRA       = "#AF601A",  -- Marrom ? terra
    DOM_MAGIA_SAGRADO     = "#F7DC6F",  -- Amarelo ? sagrado
    DOM_MAGIA_RUNOLOGIA   = "#AF7AC5",  -- Roxo médio ? runologia, magia arcana

    -- ============================================================
    -- OFÍCIOS E NATUREZA
    -- ============================================================
    DOM_OFICIO_CRAFT      = "#D4AC0D",  -- Amarelo mostarda ? criação, forja
    DOM_OFICIO_MINERACAO  = "#7F8C8D",  -- Cinza ? mineração
    DOM_OFICIO_PESCA      = "#3498DB",  -- Azul ? pesca
    DOM_NATUREZA_CULTIVO  = "#27AE60",  -- Verde ? cultivo
    DOM_NATUREZA_DOMEST   = "#AF601A",  -- Marrom ? domesticação
    DOM_NATUREZA_RASTREAM = "#F39C12",  -- Laranja ? rastreio
    DOM_NATUREZA_SOBREV   = "#1E8449",  -- Verde escuro ? sobrevivência

    -- ============================================================
    -- ITENS E RARIDADES
    -- ============================================================
    ITEM_COMUM            = "#BDC3C7",  -- Cinza ? comum
    ITEM_RARO             = "#3498DB",  -- Azul ? raro
    ITEM_EPICO            = "#8E44AD",  -- Roxo ? épico
    ITEM_LENDARIO         = "#E67E22",  -- Laranja ? lendário

    -- ============================================================
    -- MISSÕES
    -- ============================================================
    MISSAO_MATAR          = "#E74C3C",  -- Vermelho ? missão de combate
    MISSAO_COLETAR        = "#2ECC71",  -- Verde ? missão de coleta
    MISSAO_ENTREGAR       = "#F1C40F",  -- Dourado ? missão de entrega
    MISSAO_EXPLORAR       = "#3498DB",  -- Azul ? missão de exploração
    MISSAO_FALAR          = "#AF7AC5",  -- Roxo ? falar com NPC
    MISSAO_ESCORTAR       = "#F39C12",  -- Laranja ? escolta
    MISSAO_CRAFT          = "#D4AC0D",  -- Amarelo ? criação de itens
    MISSAO_TEMPO          = "#E74C3C",  -- Vermelho ? missão com limite de tempo

    -- ============================================================
    -- COMBATE E FEEDBACK
    -- ============================================================
    COMBO_AVISO           = "#F39C12",  -- Laranja ? ativação de habilidades
}

-- ============================================================
-- FUNÇÕES AUXILIARES
-- ============================================================
function c(texto, cor)
    if not texto or not cor then return texto or "" end
    return "{" .. texto .. ", " .. cor .. "}"
end

function enviarMsgColorida(player, texto)
    if not player then return end
    player:sendTextMessage(24, texto)
end

print("DEBUG: texto_colorido.lua (v9.1) carregado.")