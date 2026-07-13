"""VALIDAÇÃO: ExtratorFeatures — cross-idioma, palavras novas, intenção."""
import sys, json, time
sys.path.insert(0, 'E:/MCR')

from mcr.mcr import MCR
from mcr.extrator_features import ExtratorFeatures

print('=' * 65)
print('  VALIDAÇÃO — EXTRATOR DE FEATURES (Filosofia MCR)')
print('=' * 65)

# Inicializa
mcr = MCR()
ext = ExtratorFeatures()

# Treina com KG
from mcr.paths import KG_DIR
patterns = []
for f in sorted(KG_DIR.glob('patterns_*.json'))[:2]:
    with open(f, 'r', encoding='utf-8') as fh:
        patterns.extend(json.load(fh).get('padroes', []))
ext.treinar(patterns)

# ═══════════════════════════════════════════════════════════
# TESTE 1: Cross-idioma — PT vs EN (mesmo estado?)
# ═══════════════════════════════════════════════════════════
print('\n[1] CROSS-IDIOMA: Português vs Inglês')
print('-' * 45)

pares = [
    ("Crie um NPC ferreiro anão", "Create an NPC blacksmith dwarf", "NPC"),
    ("Gere um monstro dragão ancião", "Generate an ancient fire dragon", "MONS"),
    ("Explique o que é entropia", "Explain what entropy is", "ASK"),
    ("Crie uma quest para o ferreiro", "Create a quest for the blacksmith", "QUES"),
    ("Crie um sprite de escudo", "Create a shield sprite", "SPRI"),
]

matches = 0
for pt, en, tipo_esperado in pares:
    e_pt = ext.extrair(pt)
    e_en = ext.extrair(en)
    # Verifica se o tipo de entidade é igual
    tipo_pt = e_pt.split('|')[0] if 'ENT:' in e_pt else '?'
    tipo_en = e_en.split('|')[0] if 'ENT:' in e_en else '?'
    ok = tipo_pt == tipo_en
    if ok:
        matches += 1
    print(f'  {"OK" if ok else "ERR"} | PT: {tipo_pt:20s} | EN: {tipo_en:20s} | {pt[:45]}')

print(f'\n  Cross-idioma: {matches}/{len(pares)} ({matches*100//len(pares)}%)')

# ═══════════════════════════════════════════════════════════
# TESTE 2: Classificação MCR com features (real)
# ═══════════════════════════════════════════════════════════
print('\n[2] CLASSIFICAÇÃO MCR (com features)')
print('-' * 45)

testes_class = [
    ("Crie um NPC ferreiro anão", "gerar_npc"),
    ("Create an NPC blacksmith", "gerar_npc"),
    ("Gere um monstro dragão", "gerar_monstro"),
    ("Generate a fire dragon", "gerar_monstro"),
    ("Explique o que é entropia", "responder"),
    ("Explain what entropy is", "responder"),
    ("Crie uma quest", "gerar_quest"),
    ("Crie um sprite de escudo", "gerar_sprite"),
    ("Create a shield sprite", "gerar_sprite"),
    ("Como funciona o MCR", "responder"),
    ("Faca um NPC orc", "gerar_npc"),
    ("Gere um NPC dragao", "gerar_npc"),
    ("Faca um monstro vendedor", "gerar_monstro"),
    ("Gere um dragao de fogo", "gerar_monstro"),
]

acertos = 0
for entrada, esperado in testes_class:
    r = mcr.processar(entrada)
    ok = r['acao'] == esperado
    if ok:
        acertos += 1
    print(f'  {"OK" if ok else "ERR"} | {r["acao"]:15s} (exp: {esperado:15s}) | {entrada[:50]}')

print(f'\n  Classificação: {acertos}/{len(testes_class)} ({acertos*100//len(testes_class)}%)')

# ═══════════════════════════════════════════════════════════
# TESTE 3: Estados gerados pelo extrator
# ═══════════════════════════════════════════════════════════
print('\n[3] ESTADOS GERADOS (formato das features)')
print('-' * 45)

for pt, en, _ in pares[:3]:
    print(f'  PT: {ext.extrair(pt)}')
    print(f'  EN: {ext.extrair(en)}')
    print()

# ═══════════════════════════════════════════════════════════
# RESULTADO
# ═══════════════════════════════════════════════════════════
print(f'{"="*65}')
print(f'  Cross-idioma: {matches}/{len(pares)} estados idênticos')
print(f'  Classificação: {acertos}/{len(testes_class)} ações corretas')
print(f'  Total: {matches+acertos}/{len(pares)+len(testes_class)} checks')
print(f'{"="*65}')
