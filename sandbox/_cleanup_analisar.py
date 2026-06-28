#!/usr/bin/env python
"""Remove lessons falsas do analisar que poluiram o KG."""
import json

path = r'E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json'
with open(path, 'r', encoding='utf-8') as f:
    kg = json.load(f)

# As lessons falsas podem estar em:
# - kg['licoes'] (formato V1: erro, causa, solucao, ctx)
# - kg['lessons'] (formato antigo: context, arquivo, antes, depois)
total_removidas = 0

for chave in ['licoes', 'lessons']:
    items = kg.get(chave, [])
    antes = len(items)
    if not items:
        continue
    # Detecta formato
    sample = items[0]
    if isinstance(sample, dict):
        # Tenta encontrar campo de erro
        campo_erro = None
        for k in ['erro', 'context', 'antes']:
            if k in sample:
                campo_erro = k
                break
        if campo_erro:
            novas = []
            removidas = []
            for l in items:
                txt_erro = str(l.get(campo_erro, ''))
                if 'Bug em context_crew' in txt_erro or 'Bug em analisar' in txt_erro:
                    removidas.append(txt_erro[:80])
                else:
                    novas.append(l)
            kg[chave] = novas
            removidas_count = antes - len(novas)
            total_removidas += removidas_count
            if removidas_count > 0:
                print(f'Removidas {removidas_count} de {chave}:')
                for r in removidas:
                    print(f'  - {r}')
    elif isinstance(sample, str):
        novas = [s for s in items if 'Bug em context_crew' not in s and 'Bug em analisar' not in s]
        kg[chave] = novas
        removidas_count = antes - len(novas)
        total_removidas += removidas_count
        if removidas_count > 0:
            print(f'Removidas {removidas_count} de {chave}')

print(f'\nTotal removidas: {total_removidas}')
print(f'Restante: {len(kg.get("licoes", []))} licoes + {len(kg.get("lessons", []))} lessons')
with open(path, 'w', encoding='utf-8') as f:
    json.dump(kg, f, indent=2, ensure_ascii=False)

print(f'Removidas {len(removidas)} lessons falsas:')
for r in removidas:
    print(f'  - {r[:80]}')
print(f'Restam {len(novas)} lessons no KG.')
