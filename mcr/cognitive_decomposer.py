"""mcr.cognitive_decomposer — Decompoe problemas complexos em conceitos e sub-perguntas.
Tudo em < 0.001s usando apenas regex e heuristica."""
import re
from typing import List, Dict

# Stop words para filtrar
_STOP = {
    'de', 'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 'com',
    'nao', 'uma', 'os', 'no', 'se', 'na', 'por', 'mais', 'as', 'dos',
    'como', 'mas', 'ao', 'ele', 'das', 'tem', 'esta', 'vai', 'ser',
    'era', 'muito', 'sem', 'todo', 'pelo', 'cada', 'ate', 'depois',
    'sobre', 'entre', 'sua', 'meu', 'minha', 'teu', 'sou', 'the',
    'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
    'her', 'was', 'one', 'our', 'out', 'has', 'have', 'been',
    'some', 'them', 'than', 'what', 'when', 'where', 'which', 'will',
    'your', 'into', 'only', 'over', 'such', 'that', 'this', 'from',
    'their', 'there', 'these', 'they', 'this', 'with', 'very', 'just',
    'also', 'well', 'said', 'now', 'then', 'here', 'usar', 'fazer',
    'usa', 'faz', 'pode', 'podemos', 'para', 'pra',
}


def decompor(mensagem: str) -> Dict:
    """Decompoe uma mensagem complexa em conceitos e sub-perguntas.
    
    Args:
        mensagem: texto do usuario.
    
    Returns:
        dict com 'conceitos', 'sub_perguntas', 'relacoes', 'tema_central'
    """
    msg = mensagem.lower().strip()

    # 1. Extrai palavras-chave (ignorando stop words)
    palavras_brutas = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', msg)
    conceitos = [p for p in palavras_brutas if p not in _STOP and len(p) > 3]

    # 2. Identifica bigramas significativos (conceitos compostos)
    bigramas = []
    for i in range(len(palavras_brutas) - 1):
        bigrama = palavras_brutas[i] + '_' + palavras_brutas[i + 1]
        if (palavras_brutas[i] not in _STOP or palavras_brutas[i + 1] not in _STOP):
            bigramas.append(bigrama)

    # 3. Tema central (primeiro bigrama ou primeiro conceito)
    tema_central = ''
    if bigramas:
        tema_central = bigramas[0]
    elif conceitos:
        tema_central = conceitos[0]

    # 4. Gera sub-perguntas baseadas nos conceitos
    sub_perguntas = set()
    padroes_pergunta = [
        'O que e %s?',
        'Como %s funciona?',
        'Por que %s e importante?',
        'Qual a relacao entre %s e o projeto MCR?',
        'O que o KG sabe sobre %s?',
    ]

    for c in conceitos[:4]:  # Limite de 4 conceitos
        for padrao in padroes_pergunta:
            sub_perguntas.add(padrao % c)

    # 5. Identifica relacoes entre conceitos
    relacoes = []
    palavras_ordem = msg.split()
    for i, palavra in enumerate(palavras_ordem):
        if palavra in ('e', 'com', 'para', 'usando', 'atraves', 'sem', 'mas'):
            if i > 0 and i < len(palavras_ordem) - 1:
                antes = palavras_ordem[i - 1]
                depois = palavras_ordem[i + 1]
                if antes not in _STOP and depois not in _STOP:
                    relacoes.append({'a': antes, 'relacao': palavra, 'b': depois})

    return {
        'conceitos': conceitos[:8],
        'bigramas': bigramas[:5],
        'sub_perguntas': sorted(sub_perguntas)[:8],
        'relacoes': relacoes[:3],
        'tema_central': tema_central,
        'msg_original': mensagem,
    }
