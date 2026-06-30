"""Léxico V2 — Vocabulário compartilhado entre IntentionEngine e tokenização rica.

Contém:
- _LEXICO: patterns de INTENÇÃO + DOMÍNIO + GRAMÁTICA (fonte única da verdade)
- tokenizar_v2(): produz tokens RICOS (não PAL_CURTA/PAL_MEDIA)
- MARKOV_POR_INTENCAO: sequência esperada para cada intenção

Uso:
    from modulos.lexico_v2 import tokenizar_v2, MARKOV_POR_INTENCAO
    tokens = tokenizar_v2("Crie um NPC Ferreiro")
    # → [("INTENT_CREATE", "Crie", 0.9), ("DOM_NPC", "NPC", 0.8), ...]
"""
import re
from typing import List, Tuple, Dict, Optional

# ============================================================
# LÉXICO UNIFICADO — padrão único de reconhecimento
# ============================================================
# Cada entrada: (categoria, pattern_regex, confiança_base)
# A ORDEM IMPORTA! Padrões mais específicos primeiro.

_LEXICO = [
    # ---- INTENÇÕES (verbos imperativos) ----
    ("INTENT_CREATE", r"\bcri\w*\b|\bfaç\w*\b|\bfaz\w*\b|\bger\w*\b|\bimplement\w*\b|\bdesenvolv\w*\b|\bconstru\w*\b|\bmont\w*\b|\bproduz\w*\b|\belabor\w*\b", 0.90),
    ("INTENT_EXPLAIN", r"(o\s+)?qu(anto|ais|al|e|em)\s+(é|e|são|seria|significa)\b|\bexpli[cq]\w*\b|\bdefin\w*\b|\bsignifi[cq]\w*\b|\bcomo\s+funcion\w*\b|\bconceit\w*\b|\bdescrev\w*\b|\bme\s+fale\w*\b", 0.90),
    ("INTENT_SEARCH", r"\bbus[cq]\w*\b|\bencontr\w*\b|\bprocur\w*\b|\bach\w*\b|\blocaliz\w*\b|\bdescubr\w*\b|\bgrep\b|\blist\w*\b|\bonde\s+fic\w*\b", 0.85),
    ("INTENT_EDIT", r"\badicion\w*\b|\binser\w*\b|\bedi\w*\b|\bmodific\w*\b|\balter\w*\b|\batualiz\w*\b|\bcoloq\w*\b|\binsir\w*\b|\bacrescent\w*\b", 0.90),
    ("INTENT_REVIEW", r"\brevis\w*\b|\banalis\w*\b|\bavali\w*\b|\bverifi[cq]\w*\b|\bchec\w*\b|\binspeci\w*\b", 0.85),

    # ---- DOMÍNIOS SEMÂNTICOS ----
    ("DOM_NPC", r"\bnpc\b|\bpersonagem\b|\bvendedor\b|\btrader\b|\bgui[ae]\b|\bguide\b|\bferreir[ao]\b|\bblacksmith\b|\bguard(a|ião)\b|\bmercador\b|\bmestre\b|\bprofessor\b|\bmentor\b|\blojista\b", 0.80),
    ("DOM_LORE", r"\blore\b|\bhistó?ria\b|\bfundação\b|\bcidad[ea]\b|\bregião\b|\bmundo\b|\bcontinente\b|\breino\b|\blenda\b|\bmito\b|\bcriatur[as]\b|\bpersonagem\b|\bnarrativa\b", 0.75),
    ("DOM_SYSTEM", r"\bsistema\b|\bmecânic[ao]\b|\bdomínio\b|\bprogressão\b|\bnível\b|\blevel\b|\bpostur[ae]\b|\bsinergi[ae]\b|\bestado\b|\bcondição\b|\bconfig\b|\bconfiguração\b", 0.80),
    ("DOM_CODE", r"\bc[oó]digo\b|\bfunção\b|\bfuncao\b|\barquivo\b|\bscript\b|\bclasse\b|\bmódulo\b|\bbiblioteca\b|\bapi\b|\bprograma\b|\bfunção\b|\bmetodo\b|\bmétodo\b", 0.75),
    ("DOM_QUEST", r"\bmissão\b|\bmissao\b|\bquest\b|\btaref[ae]\b|\bdesafi[ao]\b|\bobjetivo\b|\bprêmio\b|\brecompens[ae]\b", 0.75),
    ("DOM_SKILL", r"\bhabilidades?\b|\bskill\b|\bpoder\b|\bcomb[o]?\b|\btalent[o]\b|\bcapacidade\b|\bperícia\b|\bpericia\b", 0.75),
    ("DOM_ELEMENT", r"\bfogo\b|\bgelo\b|\bterr[ao]\b|\benergi[ae]\b|\belement[ao]\b|\bvento\b|\btrovão\b|\btrovao\b|\bfog(o|u)\b|\bgelo\b", 0.80),
    ("DOM_ITEM", r"\bitem\b|\bitens\b|\barma\b|\barmadura\b|\bferrament[ae]\b|\bpocao\b|\bpoção\b|\bequipamento\b|\bacessório\b|\bacessorio\b|\bconsumível\b|\bconsumivel\b", 0.70),

    # ---- SERVIÇOS/INFRA (Canary, OTServ, etc) ----
    ("DOM_SERVER", r"\bcanary\b|\botserv\b|\bservidor\b|\bclient\b|\botclient\b|\bemulador\b", 0.75),

    # ---- RELAÇÕES GRAMATICAIS ----
    ("PREP_PURPOSE", r"\bpara\b|\bpra\b|\bafim\s+de\b", 0.70),
    ("PREP_WITH", r"\bcom\b", 0.70),
    ("PREP_IN", r"\bem\b|\bna\b|\bno\b|\bdentro\b", 0.65),
    ("PREP_OF", r"\bde\b|\bda\b|\bdo\b|\bdas\b|\bdos\b", 0.60),
    ("CONJUNCTION", r"\be\b|\bmas\b|\bou\b|\bpor[ée]m\b|\bcontudo\b|\bentretanto\b|\btodavia\b", 0.60),
]

# Mapa: categoria → lista de patterns (para acesso rápido)
_CATEGORIA_PATTERNS = {}
for cat, pattern, conf in _LEXICO:
    if cat not in _CATEGORIA_PATTERNS:
        _CATEGORIA_PATTERNS[cat] = []
    _CATEGORIA_PATTERNS[cat].append((pattern, conf))


# ============================================================
# TOKENIZAÇÃO V2
# ============================================================

def tokenizar_v2(texto: str, incluir_fallback: bool = True) -> List[Tuple[str, str, float]]:
    """Tokeniza texto com tipos RICOS (domínio + intenção + gramática).
    
    Fluxo:
    1. Fase FRASE COMPLETA: patterns de INTENÇÃO (podem ser multi-word)
    2. Fase PALAVRA: patterns de DOMÍNIO + GRAMÁTICA (sempre single-word)
    3. Pós-processamento: PROPER_NOUN para ALL CAPS
    
    Args:
        texto: texto a tokenizar
        incluir_fallback: se True, tokens sem match viram PAL_CURTA/MEDIA/LONGA
    
    Returns:
        Lista de (tipo, palavra_original, confiança)
    """
    if not texto:
        return []
    
    texto_lower = texto.lower()
    palavras = re.findall(r'\b[\wáéíóúãõàèìòùâêîôûçÁÉÍÓÚÃÕÀÈÌÒÙÂÊÎÔÛÇ]+\b', texto)
    palavras_lower = [p.lower() for p in palavras]
    
    # ============================================================
    # FASE 1: FRASE COMPLETA — patterns de INTENÇÃO
    # Patterns multi-word (ex: "o que e", "como funciona") só funcionam
    # na frase completa, não palavra por palavra.
    # ============================================================
    intencoes_detectadas = {}  # palavra_lower -> (prefixo, conf)
    
    for cat, pattern, conf_base in _LEXICO:
        if cat.startswith("INTENT_"):
            if re.search(pattern, texto_lower):
                # Qual palavra do texto matchou?
                for palavra, palavra_lower in zip(palavras, palavras_lower):
                    if re.search(pattern, palavra_lower):
                        # Match palavra a palavra dentro dos patterns de intenção
                        if palavra_lower not in intencoes_detectadas:
                            conf = min(0.95, conf_base + 0.05)
                            intencoes_detectadas[palavra_lower] = (cat, conf)
    
    # Se pattern multi-word não matchou palavra a palavra, 
    # tenta match do fragmento multi-word na frase completa
    if not intencoes_detectadas:
        for cat, pattern, conf_base in _LEXICO:
            if cat.startswith("INTENT_"):
                m = re.search(pattern, texto_lower)
                if m:
                    # Extrai a palavra-chave do match (evita artigos)
                    match_text = m.group(0).strip()
                    # Pega a última palavra (a principal, ex: "e" em "o que e")
                    palavras_match = re.findall(r'\b\w+\b', match_text)
                    for pm in reversed(palavras_match):
                        if len(pm) > 1:  # ignora artigos
                            conf = min(0.95, conf_base + 0.05)
                            intencoes_detectadas[pm] = (cat, conf)  # pm já é lowercase
                            break
    
    # ============================================================
    # FASE 2: PALAVRA POR PALAVRA — DOMÍNIO + GRAMÁTICA + fallback
    # ============================================================
    tokens = []
    
    for palavra, palavra_lower in zip(palavras, palavras_lower):
        melhor_tipo = None
        melhor_conf = 0
        
        # Primeiro: intenção detectada na fase 1?
        if palavra_lower in intencoes_detectadas:
            cat, conf = intencoes_detectadas[palavra_lower]
            tokens.append((cat, palavra, conf))
            continue
        
        # Segundo: match DOM_ + PREP_ + CONJ palavra por palavra
        for cat, pattern, conf_base in _LEXICO:
            if not cat.startswith("INTENT_"):  # DOM, PREP, CONJ, PROPER_NOUN
                if re.search(pattern, palavra_lower):
                    conf = conf_base
                    if len(palavra) > 7:
                        conf = min(0.95, conf + 0.03)
                    if conf > melhor_conf:
                        melhor_tipo = cat
                        melhor_conf = conf
        
        # Fallback
        if not melhor_tipo and incluir_fallback:
            if len(palavra) <= 3:
                melhor_tipo = "PAL_CURTA"
                melhor_conf = 0.30
            elif len(palavra) <= 7:
                melhor_tipo = "PAL_MEDIA"
                melhor_conf = 0.30
            else:
                melhor_tipo = "PAL_LONGA"
                melhor_conf = 0.30
        
        if melhor_tipo:
            tokens.append((melhor_tipo, palavra, melhor_conf))
    
    # ============================================================
    # FASE 3: Pós-processamento — ALL CAPS
    # ============================================================
    for m in re.finditer(r'\b[A-Z]{2,}\b', texto):
        palavra_upper = m.group()
        for i, (tipo, pal, conf) in enumerate(tokens):
            if pal == palavra_upper and tipo in ("PAL_CURTA", "PAL_MEDIA", "PAL_LONGA"):
                tokens[i] = ("PROPER_NOUN", pal, 0.95)
            elif pal == palavra_upper and tipo.startswith("DOM_"):
                tokens[i] = (tipo, pal, min(0.95, conf + 0.1))
    
    return tokens


def resumo_tokens(tokens: List[Tuple[str, str, float]]) -> Dict[str, int]:
    """Resumo dos tipos de token para debug."""
    from collections import Counter
    return dict(Counter(t[0] for t in tokens).most_common(15))


def tipos_unicos(tokens: List[Tuple[str, str, float]]) -> List[str]:
    """Lista de tipos sem repetição, mantendo ordem."""
    vistos = set()
    resultado = []
    for t, _, _ in tokens:
        if t not in vistos:
            vistos.add(t)
            resultado.append(t)
    return resultado


# ============================================================
# MARKOV POR INTENÇÃO
# ============================================================

MARKOV_POR_INTENCAO = {
    "CREATE": {
        "npc": {
            "peso": 2.0,
            "sequencia": [
                ("INTENT_CREATE", 0.95),
                ("DOM_NPC", 0.90),
                ("DOM_LORE", 0.40),
                ("PREP_IN", 0.35),
                ("DOM_SYSTEM", 0.25),
                ("DOM_ITEM", 0.20),
                ("CONJUNCTION", 0.15),
            ],
            "proibido": ["INTENT_EXPLAIN", "INTENT_SEARCH", "INTENT_REVIEW"],
            "descricao": "Comando de criação de NPC: Crie + NPC + [local] + [sistema]"
        },
        "lore": {
            "peso": 2.0,
            "sequencia": [
                ("INTENT_CREATE", 0.95),
                ("DOM_LORE", 0.90),
                ("PREP_OF", 0.50),
                ("DOM_NPC", 0.30),
                ("DOM_SYSTEM", 0.20),
                ("CONJUNCTION", 0.15),
            ],
            "proibido": ["INTENT_SEARCH", "INTENT_EDIT"],
            "descricao": "Comando de criação de lore: Crie + lore + [de] + [NPC/sistema]"
        },
        "codigo": {
            "peso": 1.8,
            "sequencia": [
                ("INTENT_CREATE", 0.95),
                ("DOM_CODE", 0.85),
                ("DOM_SYSTEM", 0.40),
                ("PREP_IN", 0.30),
                ("DOM_SKILL", 0.20),
            ],
            "proibido": ["INTENT_EXPLAIN", "INTENT_REVIEW"],
            "descricao": "Comando de criação de código: Crie + código/função"
        },
        "default": {
            "peso": 1.5,
            "sequencia": [
                ("INTENT_CREATE", 0.90),
                ("DOM_CODE", 0.40),
                ("DOM_SYSTEM", 0.40),
                ("DOM_NPC", 0.20),
                ("DOM_LORE", 0.20),
            ],
            "proibido": [],
            "descricao": "Comando de criação genérico"
        },
    },
    "EXPLAIN": {
        "conceito": {
            "peso": 2.0,
            "sequencia": [
                ("INTENT_EXPLAIN", 0.95),
                ("DOM_SYSTEM", 0.70),
                ("DOM_SKILL", 0.50),
                ("DOM_ELEMENT", 0.40),
                ("PROPER_NOUN", 0.35),
                ("PREP_OF", 0.30),
            ],
            "proibido": ["INTENT_CREATE", "INTENT_EDIT"],
            "descricao": "Pergunta de conceito: O que e + sistema/habilidade/sigla"
        },
        "default": {
            "peso": 1.8,
            "sequencia": [
                ("INTENT_EXPLAIN", 0.95),
                ("DOM_SYSTEM", 0.50),
                ("PROPER_NOUN", 0.50),
                ("PREP_OF", 0.40),
                ("DOM_SERVER", 0.30),
                ("DOM_ELEMENT", 0.25),
                ("DOM_SKILL", 0.20),
                ("CONJUNCTION", 0.15),
            ],
            "proibido": ["INTENT_CREATE", "INTENT_EDIT", "INTENT_REVIEW"],
            "descricao": "Pergunta de explicação geral"
        },
    },
    "SEARCH": {
        "default": {
            "peso": 1.5,
            "sequencia": [
                ("INTENT_SEARCH", 0.95),
                ("DOM_CODE", 0.50),
                ("DOM_SYSTEM", 0.40),
                ("PROPER_NOUN", 0.35),
                ("DOM_NPC", 0.20),
            ],
            "proibido": ["INTENT_CREATE", "INTENT_EDIT"],
            "descricao": "Comando de busca: Busque + código/sistema/sigla"
        },
    },
    "EDIT": {
        "default": {
            "peso": 1.5,
            "sequencia": [
                ("INTENT_EDIT", 0.95),
                ("DOM_CODE", 0.50),
                ("DOM_LORE", 0.25),
                ("PREP_IN", 0.30),
                ("PREP_OF", 0.20),
            ],
            "proibido": ["INTENT_CREATE", "INTENT_EXPLAIN"],
            "descricao": "Comando de edição: Adicione + conteúdo + em + arquivo"
        },
        "lore": {
            "peso": 1.5,
            "sequencia": [
                ("INTENT_EDIT", 0.95),
                ("DOM_LORE", 0.70),
                ("DOM_CODE", 0.50),
                ("PREP_IN", 0.40),
                ("PREP_OF", 0.20),
            ],
            "proibido": ["INTENT_CREATE", "INTENT_EXPLAIN"],
            "descricao": "Comando de edição de lore/documento"
        },
    },
    "REVIEW": {
        "default": {
            "peso": 1.5,
            "sequencia": [
                ("INTENT_REVIEW", 0.95),
                ("DOM_CODE", 0.60),
                ("DOM_SYSTEM", 0.30),
                ("PROPER_NOUN", 0.20),
            ],
            "proibido": ["INTENT_CREATE", "INTENT_EDIT"],
            "descricao": "Comando de revisão: Revise + código/sistema"
        },
    },
}


def verificar_markov(tokens_v2: List[Tuple[str, str, float]],
                     cat: str, tipo: str) -> Dict:
    """Verifica se os tokens reais correspondem ao Markov esperado para a intenção.
    
    Args:
        tokens_v2: tokens produzidos por tokenizar_v2()
        cat: categoria da intenção (CREATE, EXPLAIN, etc)
        tipo: tipo específico (npc, lore, default, etc)
    
    Returns:
        dict com: taxa_markov, hits, misses, penalidade, bonus
    """
    tipos_encontrados = tipos_unicos(tokens_v2)
    
    # Pega Markov esperado
    markov_intencao = MARKOV_POR_INTENCAO.get(cat, {})
    markov_tipo = markov_intencao.get(tipo) or markov_intencao.get('default')
    
    if not markov_tipo:
        return {
            "taxa_markov": 0.0,
            "peso": 0.5,
            "hits": [],
            "misses": tipos_encontrados[:8],
            "penalidade": 0,
            "bonus": 0,
            "entropia_sugerida": 0.8,
        }
    
    seq_esperada = markov_tipo['sequencia']
    tipos_esperados = [t for t, _ in seq_esperada]
    proibido = markov_tipo.get('proibido', [])
    peso = markov_tipo.get('peso', 1.0)
    
    # Markov Score
    acertos = 0
    hits = []
    for tipo_real in tipos_encontrados[:8]:
        if tipo_real in tipos_esperados:
            prob = dict(seq_esperada).get(tipo_real, 0)
            acertos += prob
            hits.append((tipo_real, prob))
    
    misses = [t for t in tipos_encontrados[:8] if t not in tipos_esperados]
    
    # Normaliza
    max_possivel = sum(p for _, p in seq_esperada)
    taxa_markov = acertos / max_possivel if max_possivel > 0 else 0
    taxa_markov = min(1.0, taxa_markov)
    
    # Penalidade por proibidos
    penalidade = sum(0.3 for t in tipos_encontrados if t in proibido)
    
    # Bônus por match específico de domínio
    bonus = 0.0
    if cat == "CREATE" and tipo == "npc" and "DOM_NPC" in tipos_encontrados:
        bonus += 0.15
    if cat == "CREATE" and tipo == "lore" and "DOM_LORE" in tipos_encontrados:
        bonus += 0.15
    if cat == "EXPLAIN" and "DOM_SYSTEM" in tipos_encontrados:
        bonus += 0.10
    if cat == "SEARCH" and "INTENT_SEARCH" in tipos_encontrados:
        bonus += 0.15
    
    # Entropia sugerida (quanto mais próximo do esperado, menor entropia)
    entropia_sugerida = max(0.1, 1.0 - taxa_markov - bonus + penalidade)
    
    return {
        "taxa_markov": round(taxa_markov, 3),
        "peso": peso,
        "hits": hits[:5],
        "misses": misses[:5],
        "penalidade": round(penalidade, 2),
        "bonus": round(bonus, 2),
        "entropia_sugerida": round(entropia_sugerida, 3),
    }
