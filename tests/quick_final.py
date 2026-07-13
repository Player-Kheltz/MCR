"""Teste rápido — Extrator 100% descoberto."""
import sys; sys.path.insert(0,'E:/MCR')
from mcr.extrator_features import ExtratorFeatures

e = ExtratorFeatures()
e.treinar()
print(e.diagnosticar())
print()

pares = [
    ("Crie um NPC ferreiro anao", "Create an NPC blacksmith dwarf"),
    ("Gere um monstro dragao anciao", "Generate a fire dragon"),
    ("Explique o que e entropia", "Explain what entropy is"),
    ("Crie uma quest", "Create a quest"),
    ("Crie um sprite de escudo", "Create a shield sprite"),
    ("Faca um NPC orc", "Make an orc NPC"),
    ("Gere um monstro demonio", "Generate a lightning demon"),
]
matches = 0
for pt, en in pares:
    e_pt = e.extrair(pt)
    e_en = e.extrair(en)
    ok = e_pt == e_en
    if ok: matches += 1
    print(f'{"MATCH" if ok else "DIFF"} | PT: {e_pt[:55]}')
    if not ok:
        print(f'      | EN: {e_en[:55]}')
print(f'\nCross-idioma: {matches}/{len(pares)}')
