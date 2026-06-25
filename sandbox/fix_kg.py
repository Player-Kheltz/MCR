"""Sanitize KG file"""
import json
path = r'E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json'
with open(path, 'r', encoding='utf-8', errors='replace') as f:
    data = f.read()
# Fix: replace problematic chars
cleaned = ''
for c in data:
    if ord(c) >= 32 or c in '\n\r\t':
        cleaned += c
with open(path, 'w', encoding='utf-8') as f:
    f.write(cleaned)
kg = json.loads(cleaned)
print(f'OK! {len(kg["licoes"])} licoes, V{kg["versoes"]}')
ctx = {}
for l in kg['licoes']:
    d = l.get('ctx', '?')
    ctx[d] = ctx.get(d, 0) + 1
for d, c in sorted(ctx.items()):
    print(f'  {d}: {c}')
