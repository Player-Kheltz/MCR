import re
# Absolutely minimal test
p = 'busc'
print(f'Pattern: {p!r}')
m = re.search(p, 'busque')
print(f'busque: {bool(m)}, group={m.group() if m else None}')

m2 = re.search(p, 'buscar')
print(f'buscar: {bool(m2)}, group={m2.group() if m2 else None}')
