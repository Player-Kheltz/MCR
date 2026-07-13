"""VALIDAÇÃO FINAL: Extrator 100% descoberto + MCR pipeline."""
import sys, time
sys.path.insert(0, 'E:/MCR')

from mcr.extrator_features import ExtratorFeatures
from mcr.mcr import MCR

print('=' * 65)
print('  VALIDACAO FINAL — Extrator 100% Descoberto')
print('  ZERO hardcode. ZERO rotulos humanos.')
print('=' * 65)

# Testa o extrator isolado
e = ExtratorFeatures()
e.treinar()
print('\n' + e.diagnosticar())

# Testa cross-idioma
print('\n[1] CROSS-IDIOMA (estados descobertos):')
pares_pt_en = [
    ("Crie um NPC ferreiro anao", "Create an NPC blacksmith dwarf"),
    ("Gere um monstro dragao anciao", "Generate a fire dragon"),
    ("Explique o que e entropia", "Explain what entropy is"),
    ("Crie uma quest", "Create a quest"),
    ("Crie um sprite de escudo", "Create a shield sprite"),
    ("Faca um NPC orc", "Make an orc NPC"),
    ("Gere um monstro demonio", "Generate a lightning demon"),
]
matches = 0
for pt, en in pares_pt_en:
    e_pt = e.extrair(pt)
    e_en = e.extrair(en)
    ok = e_pt == e_en
    if ok: matches += 1
    status = "MATCH" if ok else "DIFF"
    print(f'  {status:5s} | PT: {e_pt[:50]:50s} | {pt[:45]}')
    if not ok:
        print(f'         | EN: {e_en[:50]:50s} | {en[:45]}')

print(f'\n  Cross-idioma: {matches}/{len(pares_pt_en)} estados identicos')

# Testa MCR pipeline com o novo extrator
print('\n[2] MCR PIPELINE (com extrator descoberto):')
m = MCR()
testes = [
    ("Crie um NPC ferreiro anao", "gerar_npc"),
    ("Create an NPC blacksmith", "gerar_npc"),
    ("Gere um monstro dragao", "gerar_monstro"),
    ("Explique o que e entropia", "responder"),
    ("Crie uma quest", "gerar_quest"),
    ("Crie um sprite de escudo", "gerar_sprite"),
    ("Faca um NPC orc", "gerar_npc"),
    ("Gere um NPC dragao", "gerar_npc"),
    ("Faca um monstro vendedor", "gerar_monstro"),
    ("Como funciona o MCR", "responder"),
]
acertos = 0
for entrada, esperado in testes:
    r = m.processar(entrada)
    ok = r['acao'] == esperado
    if ok: acertos += 1
    print(f'  {"OK" if ok else "ERR"} | {r["acao"]:15s} (exp: {esperado:15s}) | {entrada[:50]}')

print(f'\n  MCR Pipeline: {acertos}/{len(testes)}')

# Resultado final
print(f'\n{"="*65}')
print(f'  Cross-idioma: {matches}/{len(pares_pt_en)}')
print(f'  MCR Pipeline: {acertos}/{len(testes)}')
print(f'{"="*65}')
