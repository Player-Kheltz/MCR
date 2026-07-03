"""Debug: buffer do KG contem as lessons?"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.kg import KnowledgeGraph, _LESSONS_BUFFER

kg = KnowledgeGraph()

print(f"Buffer contem {len(_LESSONS_BUFFER)} lessons")
for l in _LESSONS_BUFFER:
    print(f"  ctx={l.get('ctx')} | fp={str(l.get('fingerprint',[]))[:30]}")
print()
print(f"Disco contem {len([l for l in kg._get_licoes() if l.get('ctx') == 'bloco_aprendido'])} blocos")
print(f"Buffer contem {len([l for l in _LESSONS_BUFFER if l.get('ctx') == 'bloco_aprendido'])} blocos")
