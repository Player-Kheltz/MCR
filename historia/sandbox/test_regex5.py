import re

# The fix: accept both C and QU
patterns = {
    'busc\\w*': re.compile(r'busc\w*'),
    'bus[cq]\\w*': re.compile(r'bus[cq]\w*'),
    '\\bbus[cq]\\w*\\b': re.compile(r'\bbus[cq]\w*\b'),
}

for nome, p in patterns.items():
    resultados = {}
    for t in ['busque', 'buscar', 'buscando', 'busca', 'busco', 'busquem', 'busquemos']:
        resultados[t] = bool(p.search(t))
    print(f"{nome}: {resultados}")

# Test the INTENT_EXPLAIN multi-word fix for 'o que e'
print("\nINTENT_EXPLAIN on 'O que e Canary':")
p = re.compile(r"(o\s+)?qu(anto|ais|al|e|em)\s+(é|e|são|seria|significa)\b", re.IGNORECASE)
print(f"  {bool(p.search('O que e Canary'))} -> {p.search('O que e Canary').group() if p.search('O que e Canary') else None}")
