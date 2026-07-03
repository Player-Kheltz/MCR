"""Debug: por que reconstruir_com_blocos falha?"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
from modulos.pattern_engine import PatternEngine
from modulos.kg import KnowledgeGraph

pe = PatternEngine()
kg = KnowledgeGraph()

# Verifica blocos no KG
licoes = kg._get_licoes()
blocos = [l for l in licoes if l.get('ctx') == 'bloco_aprendido']
print(f"Blocos encontrados: {len(blocos)}")
for b in blocos:
    sol = b.get('solucao', '')
    fp = b.get('fingerprint', [])
    print(f"  FP: {[round(x,2) for x in fp[:5]]}...")
    try:
        data = json.loads(sol)
        print(f"  Fragmento: {data.get('fragmento','')[:80]}")
    except:
        print(f"  Solucao: {sol[:80]}")

# Calcula fingerprint da pergunta atual
pergunta = "Explique o sistema SPA do MCR"
tokens = pe.tokenizar_universal(pergunta)
fp_atual = pe.fingerprint(tokens)
print(f"\nFingerprint pergunta atual: {[round(x,2) for x in fp_atual[:5]]}...")

# Busca similaridade manual
for b in blocos:
    fp_b = b.get('fingerprint', [])
    if fp_b and len(fp_b) == len(fp_atual):
        dot = sum(a*b for a,b in zip(fp_b, fp_atual))
        print(f"  Similaridade com bloco: {dot:.2f}")
