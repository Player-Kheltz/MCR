"""Check KG state"""
import json
kg = json.load(open(r'E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json'))
print(f'Total: {len(kg["licoes"])} licoes')
print(f'Versao: V{kg["versoes"]}')
ctx = {}
for l in kg['licoes']:
    d = l.get('ctx', 'desconhecido')
    ctx[d] = ctx.get(d, 0) + 1
for d, c in sorted(ctx.items()):
    print(f'  {d}: {c}')
