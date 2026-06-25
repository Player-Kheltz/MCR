"""Add V12 meta-lesson to KG"""
import json

path = r'E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json'
with open(path, 'r', encoding='utf-8') as f:
    kg = json.load(f)

lesson = {
    'id': f'M{len(kg["licoes"])+1:04d}',
    'erro': 'V12 Pattern: Python estrutura, IA preenche blanks - aplicavel a QUALQUER linguagem',
    'causa': 'O segredo do V12 eh separar ESTRUTURA (fixa, garantida por Python) de CONTEUDO (criativo, preenchido por IA). Funciona pra Lua, C++, Python, OTUI, XML, JSON, markdown - QUALQUER linguagem.',
    'solucao': '1) Identifique a estrutura FIXA (template) 2) Identifique os blanks VARIAVEIS 3) Python monta o template 4) IA preenche blanks 5) Python valida. Isso elimina 100% dos erros de sintaxe.',
    'ctx': 'meta',
    'usos': 0,
}

kg['licoes'].append(lesson)
kg['versoes'] += 1
kg['metricas']['licoes'] = len(kg['licoes'])

with open(path, 'w', encoding='utf-8') as f:
    json.dump(kg, f, ensure_ascii=False, indent=2)

print(f'OK! Lição meta adicionada. Total: {len(kg["licoes"])} licoes, V{kg["versoes"]}')
print(f'Contextos:')
ctx = {}
for l in kg['licoes']:
    d = l.get('ctx', '?')
    ctx[d] = ctx.get(d, 0) + 1
for d, c in sorted(ctx.items()):
    print(f'  {d}: {c}')
