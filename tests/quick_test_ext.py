"""Teste rápido do extrator de features."""
import sys, json
sys.path.insert(0, 'E:/MCR')
from mcr.extrator_features import ExtratorFeatures
from mcr.paths import KG_DIR

e = ExtratorFeatures()
patterns = []
for f in sorted(KG_DIR.glob('patterns_*.json'))[:2]:
    with open(f, 'r', encoding='utf-8') as fh:
        patterns.extend(json.load(fh).get('padroes', []))
e.treinar(patterns)
print(f'Contextos: {len(e._contextos)}')

tests = [
    ('Crie um NPC ferreiro anao', 'ENT:NPC'),
    ('Create an NPC blacksmith dwarf', 'ENT:NPC'),
    ('Gere um monstro dragao', 'ENT:MONS'),
    ('Generate a fire dragon', 'ENT:GEN'),  # dragon not in entity list yet
    ('Explique o que e entropia', 'INT:ASK'),
    ('Explain what entropy is', 'INT:ASK'),
    ('Crie uma quest', 'ENT:QUES'),
    ('Create a quest', 'ENT:QUES'),
    ('Crie um sprite de escudo', 'ENT:SPRI'),
    ('Create a shield sprite', 'ENT:SPRI'),
    ('Como funciona o MCR', 'INT:ASK'),
    ('Faca um NPC orc', 'ENT:NPC'),
    ('Faca um monstro vendedor', 'ENT:MONS'),
]
matches = 0
for text, expected in tests:
    estado = e.extrair(text)
    ent = estado.split('|')[0] if estado else 'VAZIO'
    ok = expected in estado
    if ok:
        matches += 1
    print(f'  {"OK" if ok else "ERR"} | {ent:20s} | {text[:45]}')
print(f'\nMatches: {matches}/{len(tests)}')
