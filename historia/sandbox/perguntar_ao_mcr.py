#!/usr/bin/env python3
"""Perguntar ao MCR o que falta, em vez de eu inventar."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRMetaGap, MCRSelfIndex, MCRAutoMelhoria, MCRSignature, MCRMetaNivel

print('=' * 60)
print('PERGUNTA 1: O que falta no KG? (MCRMetaGap)')
print('=' * 60)
mg = MCRMetaGap()
gaps = mg.diagnosticar_gaps(min_por_prefixo=5)
print(f'Gaps encontrados: {len(gaps)}')
for g in gaps[:10]:
    print(f'  {g["prefixo"]:15s}: {g["n_lessons"]} lessons (score={g["score"]})')

print()
print('=' * 60)
print('PERGUNTA 2: O que existe no codigo? (MCRSelfIndex)')
print('=' * 60)
si = MCRSelfIndex()
si.indexar_tudo()
est = si.estatisticas()
print(f'Classes MCR: {est["classes"]}')
print(f'Modulos externos: {est["modulos"]}')
print(f'Comandos externos: {est["comandos"]}')

# Classes MCR
classes_mcr = set(si._indice['classes'].keys())
mods_externos = set(si._indice['modulos'].keys())
print(f'\nClasses MCR ({len(classes_mcr)}):')
for nome in sorted(classes_mcr):
    print(f'  {nome}')

print()
print('=' * 60)
print('PERGUNTA 3: Modulos externos SEM alias MCR')
print('=' * 60)
mods_sem_alias = []
for m in sorted(mods_externos):
    encontrou = False
    for c in classes_mcr:
        if m.upper().replace('_', '') == c.upper().replace('MCR', '').replace('_', ''):
            encontrou = True
            break
        if m.lower() in c.lower() or c.lower() in m.lower():
            if len(m) > 5 and len(c) > 5:
                encontrou = True
                break
    if not encontrou:
        mods_sem_alias.append(m)

print(f'Modulos sem alias MCR: {len(mods_sem_alias)} de {len(mods_externos)}')
for m in mods_sem_alias:
    print(f'  {m}')

print()
print('=' * 60)
print('PERGUNTA 4: O que MCR descobre de si mesmo? (MetaNivel)')
print('=' * 60)
with open('scripts/mcr_devia/modulos/MCR.py', 'rb') as f:
    mcr_bytes = f.read(2000)
meta = MCRMetaNivel()
meta.alimentar(mcr_bytes[:1000])
diag = meta.diagnosticar()
print(f'Niveis descobertos: {diag["n_niveis"]}')
print(f'Ordem: {diag.get("ordem",[])}')
meta.auto_expandir(10)
diag2 = meta.diagnosticar()
print(f'Apos expandir: {diag2["n_niveis"]} niveis')
print(f'Ordem final: {diag2.get("ordem",[])}')

print()
print('=' * 60)
print('PERGUNTA 5: AutoMelhoria — o que o MCR acha que precisa?')
print('=' * 60)
am = MCRAutoMelhoria()
ciclo = am.ciclo()
print(f'Acoes sugeridas: {ciclo["n"]}')
for a in ciclo['acoes']:
    print(f'  {a}')

print()
print('=' * 60)
print('DIAGNOSTICO: O que REALMENTE falta')
print('=' * 60)
print(f'''
MCR diz:
  Gaps no KG: {len(gaps)} (ex: {[g['prefixo'] for g in gaps[:5]]})
  Modulos sem alias MCR: {len(mods_sem_alias)} de {len(mods_externos)}
  AutoMelhoria acoes: {ciclo['n']}
  MetaNiveis: {diag2['n_niveis']} niveis descobertos

Isso e o que o MCR DESCOBRIU, nao o que eu inventei.
''')
