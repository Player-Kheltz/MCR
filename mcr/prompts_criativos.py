#!/usr/bin/env python3
"""prompts_criativos.py — Prompts otimizados para geracao criativa.

Define templates de prompt por classe de tarefa, com instrucoes
para forcar personalidade, contraste e ancoragem no universo.
"""
from typing import Dict

# Mapeamento: classe MarkovDecider → modelo preferido
# Baseado no benchmark: Mistral vence em prosa, Qwen em codigo
ROTEADOR_MODELOS: Dict[str, str] = {
    'criar_npc': 'mistral:7b-32k',
    'criar_monstro': 'mistral:7b-32k',
    'criar_quest': 'mistral:7b-32k',
    'criar_lore': 'mistral:7b-32k',
    'explicar_conceito': 'mistral:7b-32k',
    'conversa': 'mistral:7b-32k',
    'criar_codigo': 'qwen2.5-coder:7b-32k',
    'busca_informacao': 'qwen2.5-coder:7b-32k',
    'criar_sql': 'qwen2.5-coder:7b-32k',
    'desconhecido': None,  # None = Ensemble
}


def prompt_npc(tema: str) -> str:
    """Prompt otimizado para geracao de NPC."""
    return f'''Crie um NPC completo para o jogo Tibia (fantasia medieval).
TEMA: {tema}

IMPORTANTE:
- De a este NPC um TRAÇO DE PERSONALIDADE INESPERADO (um medo secreto, um hobby bizarro, uma opiniao polemica).
- A historia de fundo deve explicar POR QUE ele esta onde esta.
- As falas devem soar NATURAIS, como alguem falaria em uma conversa.
- Use nomes proprios para lugares (pode inventar, mas manter tom Tibia).

FORMATO EXATO (preencha todos os campos):
NOME:
RACA: (humano|elfo|anao|orc|etc)
SEXO: (masculino|feminino)
IDADE:
HISTORIA: (3-4 frases de background)
PERSONALIDADE: (3 adjetivos, sendo UM deles inesperado para o papel)
TRACO_SECRETO: (um medo, hobby ou opiniao que o torna unico)
FALA_APRESENTACAO: (o que ele diz ao ver um estranho se aproximando)
FALA_SOBRE_SUA_VIDA: (o que ele diz se perguntarem sobre ele)
FALA_DESPEDIDA: (o que ele diz ao encerrar a conversa)

Comece agora.'''


def prompt_quest(titulo: str, tipo: str, npc: str, resumo: str) -> str:
    return f'''Crie uma quest completa para o jogo Tibia (RPG de fantasia medieval).

TITULO: {titulo}
TIPO: {tipo}
NPC_ENTREGADOR: {npc}
RESUMO: {resumo}

DIRETRIZES:
- Dialogo de inicio deve ser INTRIGANTE, nao expositivo (max 3 frases).
- Dialogo de conclusao deve dar satisfacao ao jogador.
- Objective deve ser claro e mensuravel.
- Historia de fundo deve explicar POR QUE esta quest existe no mundo.
- Use lugares com nomes de fantasia (Thais, Carlin, Venore, etc).

FORMATO:
DIALOGO_INICIO:
DIALOGO_PROGRESSO:
DIALOGO_CONCLUSAO:
OBJETIVO:
RECOMPENSA_XP:
RECOMPENSA_GOLD:
RECOMPENSA_ITEM:
HISTORIA_FUNDO:'''


def prompt_lore(tema: str) -> str:
    return f'''Escreva um paragrafo de lore (mitologia/historia) para o mundo de Tibia.
TEMA: {tema}

DIRETRIZES:
- Use um tom epico e misterioso, como um mito antigo.
- Crie nomes proprios para personagens e lugares.
- A historia deve soar como se fosse contada por um bardo ou historiador do mundo.
- Se possivel, conecte a lore a lugares ou conceitos conhecidos de Tibia.
- Seja criativo(a) — a mitologia deve ser memoravel.'''


def prompt_npc_benchmark() -> str:
    """Prompt padrao de benchmark para comparar modelos."""
    return '''Descreva um guerreiro orc que guarda uma ponte, com uma fala de apresentacao e uma fala de derrota.

Use o formato:
NOME: (nome)
RACA: Orc
CLASSE: Guarda
HISTORIA: (2-3 frases de background)
PERSONALIDADE: (3 adjetivos)
FALA_APRESENTACAO: (o que ele diz ao ver alguem se aproximando)
FALA_DERROTA: (o que ele diz ao ser vencido)'''


def obter_modelo(classe: str) -> str:
    """Retorna o modelo recomendado para uma classe de tarefa."""
    modelo = ROTEADOR_MODELOS.get(classe, None)
    if modelo is None:
        return 'mistral:7b-32k'  # fallback padrao
    return modelo


def prompt_sql(tema: str) -> str:
    """Prompt otimizado para geracao de SQL."""
    return f'''Gere uma query SQL para a seguinte solicitacao:
{tema}

REGRAS:
- Use apenas SQL padrao (SQLite-compativel)
- Nao use DROP, ALTER, TRUNCATE, EXEC, PRAGMA
- Inclua CREATE TABLE se for definicao de schema
- Inclua INSERT, SELECT, UPDATE ou DELETE conforme apropriado
- Use nomes descritivos para tabelas e colunas

FORMATO:
-- {tema}
<SQL AQUI>

Comece agora.'''


def prompt_codigo_lua(tema: str) -> str:
    """Prompt otimizado para geracao de codigo Lua do Canary."""
    return f'''Gere APENAS codigo Lua para o servidor Canary (MMORPG Tibia).
TAREFA: {tema}

REGRAS:
- Gere APENAS codigo Lua, sem introducao, sem comentarios sobre o codigo, sem marcacao.
- Nao use formatacao markdown (````, **, etc).
- Nao inclua historias, personalidades, nome, raca, idade.
- Nao inclua FALA_APRESENTACAO, FALA_DESPEDIDA, TRACO_SECRETO, HISTORIA.
- Use as APIs do servidor Canary: Game, NpcHandler, MonsterHandler, etc.
- Use funcoes como: Game.createNpc, Game.createMonster, Game.createItem.
- Nao invente APIs que nao existem: nao use Game.getMonsterNames, Game.getRandomNpcName.
- Para NPCs: defina keywordHandler, topic, onSay, addModule.

FORMATO (exemplo):
function onSay(cid, words, param)
    local npc = NpcHandler()
    npc:addModule(...)
    return true
end

Comece o codigo agora, APENAS codigo Lua.'''


def prompt_sistema(tema: str) -> str:
    """Prompt otimizado para geracao de sistema/ mecanica."""
    return f'''Gere APENAS codigo Lua para implementar um sistema no servidor Canary.
TAREFA: {tema}

REGRAS:
- Gere APENAS codigo Lua, sem introducao, sem comentarios sobre o codigo, sem marcacao.
- Nao use formatacao markdown.
- Use eventos do Canary: CreatureEvent, GlobalEvent, Action, etc.
- Use registros como: CreatureEvent(), GlobalEvent(), Action().
- Nao invente APIs que nao existem.

Comece o codigo agora, APENAS codigo Lua.'''


def prompt_habilidade_spa(tema: str) -> str:
    """Prompt otimizado para geracao de habilidade SPA."""
    return f'''Gere APENAS codigo Lua para uma habilidade SPA (Special Ability) no servidor Canary.
TAREFA: {tema}

REGRAS:
- Gere APENAS codigo Lua, sem introducao, sem marcacao.
- Nao use formatacao markdown.
- Use a estrutura padrao de SPA: EfeitoConfig, condicoes, duracao, alvo.
- Nao invente APIs que nao existem.

Comece o codigo agora, APENAS codigo Lua.'''


def obter_prompt(classe: str, tema: str, **kwargs) -> str:
    """Retorna o prompt apropriado para a classe e tema."""
    if classe == 'criar_npc' or classe == 'criar_monstro':
        return prompt_npc(tema)
    elif classe == 'criar_quest':
        return prompt_quest(tema, kwargs.get('tipo', 'coleta'),
                           kwargs.get('npc', 'NPC'), kwargs.get('resumo', ''))
    elif classe == 'criar_sql':
        return prompt_sql(tema)
    elif 'lore' in classe or 'explicar' in classe:
        return prompt_lore(tema)
    elif classe == 'criar_codigo':
        return prompt_codigo_lua(tema)
    elif classe == 'criar_habilidade_spa':
        return prompt_habilidade_spa(tema)
    elif classe == 'criar_sistema':
        return prompt_sistema(tema)
    else:
        return prompt_npc(tema)
