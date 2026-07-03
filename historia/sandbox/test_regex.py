import re

# Test the INTENT_SEARCH pattern directly
p = r'\bbusc\w*\b'
for t in ['busque', 'Busque', 'buscar', 'buscando', 'busca', 'busco']:
    m = re.search(p, t.lower())
    print(f"  {t} -> {bool(m)}, match='{m.group() if m else None}'")

# Test simpler version
p2 = r'busque'
print(f"\nSimpler:")
for t in ['busque', 'buscar']:
    m = re.search(p2, t)
    print(f"  {t} -> {bool(m)}")

# What about \bbusc?
p3 = r'\bbusc'
for t in ['busque', 'buscar']:
    m = re.search(p3, t)
    print(f"  \\bbusc on {t} -> {bool(m)}, match='{m.group() if m else None}'")

# And just busc
p4 = r'busc'
for t in ['busque', 'buscar']:
    m = re.search(p4, t)
    print(f"  busc on {t} -> {bool(m)}")
