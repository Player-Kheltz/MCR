import re
# Check actual characters
palavras = ['busque', 'buscar', 'busca', 'buscando']
for p in palavras:
    print(f"'{p}': chars={[hex(ord(c)) for c in p]}, len={len(p)}")
    
# Try different ways
texto = 'busque'
print(f"\nre.search('busc', texto) = {bool(re.search('busc', texto))}")
print(f"'busc' in texto = {'busc' in texto}")
print(f"texto.startswith('busc') = {texto.startswith('busc')}")
print(f"texto[:4] = '{texto[:4]}'")

# Also test 'O que e' 
texto2 = 'o que e'
padrao = r"(o\s+)?qu(anto|ais|al|e|em)\s+(é|e|são|seria|significa)\b"
print(f"\nEXPLAIN on '{texto2}': {bool(re.search(padrao, texto2))}")
# Test simpler
padrao2 = r"qu(anto|ais|al|e|em)\s+(é|e)\b"  # shortened version
print(f"EXPLAIN(simple) on '{texto2}': {bool(re.search(padrao2, texto2))}")
# Even simpler
padrao3 = r"o que e"
print(f"literal on '{texto2}': {bool(re.search(padrao3, texto2))}")
