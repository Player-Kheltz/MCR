"""
Dedup KG: encontra e mescla lessons duplicadas no Knowledge Graph.
Mantem a de maior score (mais usos) e marca as outras como inativas.
"""
import json, os
from collections import Counter

KG_PATH = "E:\\Projeto MCR\\sandbox\\.mcr_devia\\knowledge.json"

with open(KG_PATH, encoding='utf-8') as f:
    kg = json.load(f)

licoes = kg.get('licoes', [])
print(f'Total lessons: {len(licoes)}')
print(f'Ativas: {sum(1 for l in licoes if not l.get("inactive", False))}')
print(f'Inativas: {sum(1 for l in licoes if l.get("inactive", False))}')

# Agrupar por inicio da solucao (primeiros 60 chars)
from collections import defaultdict
grupos = defaultdict(list)
for l in licoes:
    if l.get('inactive', False):
        continue
    chave = l.get('solucao', '')[:60].strip().lower()
    if chave:
        grupos[chave].append(l)

# Mesclar duplicatas
dups_encontradas = 0
mescladas = 0
for chave, grupo in grupos.items():
    if len(grupo) <= 1:
        continue
    dups_encontradas += 1
    # Ordenar por usos (decrescente), manter a melhor
    grupo.sort(key=lambda x: -(x.get('usos', 0) or 0))
    melhor = grupo[0]
    for dup in grupo[1:]:
        # Mesclar usos
        melhor['usos'] = (melhor.get('usos', 0) or 0) + (dup.get('usos', 0) or 0)
        # Marcar como inativa
        dup['inactive'] = True
        mescladas += 1
        print(f'  Mesclada: "{melhor["id"]}" <- "{dup["id"]}" (solucao: {chave[:40]}...)')

print(f'\nDuplicatas encontradas: {dups_encontradas}')
print(f'Mescladas (marcadas inativas): {mescladas}')

# Salvar
kg['versoes'] = kg.get('versoes', 0) + 1
with open(KG_PATH, 'w', encoding='utf-8') as f:
    json.dump(kg, f, indent=2, ensure_ascii=False)

print(f'KG salvo. Nova versao: {kg["versoes"]}')
print(f'Agora: {sum(1 for l in licoes if not l.get("inactive", False))} ativas, '
      f'{sum(1 for l in licoes if l.get("inactive", False))} inativas')
