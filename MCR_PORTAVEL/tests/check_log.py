import json
with open('E:/MCR/cache/mcr_execucoes.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f'Total: {len(data)}')
sucessos = sum(1 for e in data if e.get('sucesso') == 1)
print(f'Sucessos: {sucessos}')
for i, ex in enumerate(data[:5]):
    checks = ex.get('checks', '?')[:80]
    print(f'[{i}] sucesso={ex.get("sucesso")} | nota={ex.get("nota")} | acao={ex.get("acao")} | checks={checks}')
