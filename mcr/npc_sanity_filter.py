"""mcr.npc_sanity_filter — Filtra respostas de NPCs para o chat do Tibia.
Garante que respostas sejam curtas, seguras e sem vazamento de informacoes."""
import re

_MAX_CHARS = 200  # Limite do chat do Tibia
_FALLBACK = "Nao tenho nada a dizer sobre isso agora."

# Padroes para remover
_PADROES_REMOVER = [
    # Caminhos do Windows
    r'[A-Za-z]:\\(?:[^\\"]+\\)+[^\\"]*',
    # Blocos de codigo Lua
    r'(?:local|function|if|for|while|end)\s+\w+.*?(?:\n|$)',
    r'(?:end|return|true|false|nil)\s*',
    r'```lua.*?```',
    r'```.*?```',
    r'--.*',
    # Comandos internos
    r'\[.*?\]',
    r'\(.*?\)',
]

# Vocabulario base para NPCs sem personalidade definida
_VOCABULARIOS = {
    'default': [
        "Ola, viajante.", "Precisa de algo?", "Cuidado com os monstros.",
        "O vento sopra forte hoje.", "Que os deuses te protejam.",
    ],
    'blacksmith': [
        "Precisa de armas?", "Tenho o melhor aco da regiao.",
        "Uma boa armadura vale mais que ouro.", "O ferro precisa de fogo para se moldar.",
    ],
    'druid': [
        "A natureza e sabia.", "As ervas curam, mas tambem podem matar.",
        "Respeite a floresta.", "Os espiritos da natureza estao em paz.",
    ],
    'shop': [
        "Veja meus produtos.", "Ouro bem gasto e ouro investido.",
        "Tenho itens raros hoje.", "Compre agora, antes que acabe.",
    ],
}


def _extrair_vocabulario(npc_id: str) -> list:
    """Extrai o vocabulario base para um NPC especifico."""
    npc_lower = npc_id.lower()
    for palavra, vocab in _VOCABULARIOS.items():
        if palavra in npc_lower:
            return vocab
    return _VOCABULARIOS['default']


def filtrar_resposta(texto: str, npc_id: str = '') -> str:
    """Filtra e limpa a resposta de um NPC.
    
    Args:
        texto: Resposta gerada pelo MCR.
        npc_id: Nome do NPC (para vocabulario especifico).
    
    Returns:
        String limpa e truncada.
    """
    if not texto or not texto.strip():
        return _FALLBACK

    resultado = texto.strip()

    # Remove padroes problematicos
    for padrao in _PADROES_REMOVER:
        resultado = re.sub(padrao, '', resultado, flags=re.IGNORECASE | re.MULTILINE)

    # Remove espacos extras
    resultado = re.sub(r'\s+', ' ', resultado).strip()

    # Se ficou vazio apos limpeza, usa vocabulario
    if not resultado or len(resultado) < 10:
        if npc_id:
            vocab = _extrair_vocabulario(npc_id)
            import random
            resultado = random.choice(vocab)
        else:
            resultado = _FALLBACK

    # Trunca para o limite do chat do Tibia
    if len(resultado) > _MAX_CHARS:
        resultado = resultado[:_MAX_CHARS]
        ultimo_espaco = resultado.rfind(' ', 0, _MAX_CHARS)
        if ultimo_espaco > 0:
            resultado = resultado[:ultimo_espaco]
        else:
            resultado = resultado[:_MAX_CHARS - 3] + '...'

    return resultado


def enriquecer_com_historia(resposta: str, historico: list) -> str:
    """Adiciona contexto baseado no historico de conversas com o player."""
    if not historico:
        return resposta

    # Se o player ja agrediu o NPC, muda o tom
    for entrada in historico:
        if 'agredir' in str(entrada).lower() or 'atacar' in str(entrada).lower():
            return "Voce nao e bem-vindo aqui. Va embora."

    return resposta
