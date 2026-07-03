"""Debug: porque gerar_sequencia retorna vazio?"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
from modulos.pi_engine import PiEngine
from modulos.pattern_engine import PatternEngine
from modulos.kg import KnowledgeGraph

pe = PatternEngine()
kg = KnowledgeGraph()
pi = PiEngine(pe=pe)

# Pega a melhor lesson
licoes = kg._get_licoes()
melhor = None
melhor_score = 0
fp = pe.fingerprint(pe.tokenizar_universal("Explique o sistema SPA do MCR"))
for l in licoes:
    fp_l = l.get('fingerprint', [])
    if not fp_l or len(fp_l) != len(fp):
        continue
    dot = sum(a*b for a,b in zip(fp_l, fp))
    if dot > melhor_score:
        melhor_score = dot
        melhor = l

print(f"Melhor lesson: {melhor.get('erro','')[:50]}")
print(f"Score: {melhor_score}")

tm = melhor.get('tipos_markov', {})
print(f"Tipos Markov keys: {list(tm.keys())[:8]}")
print(f"Tipos Markov values:")
for k in list(tm.keys())[:5]:
    print(f"  {k}: {tm[k]}")

# Testa predizer com o PRIMEIRO token
semente = list(tm.keys())[0]
print(f"\nSemente: {semente}")
prox, conf = pi.predizer(tm, semente)
print(f"predizer({semente}) -> ({prox}, {conf})")

# Testa gerar_sequencia com conf_min=0.1
seq1 = pi.gerar_sequencia(tm, semente, max_passos=8, conf_min=0.1, max_repeticoes=2)
print(f"\ngerar_sequencia(conf_min=0.1): {seq1}")

seq2 = pi.gerar_sequencia(tm, semente, max_passos=8, conf_min=0.05, max_repeticoes=2)
print(f"gerar_sequencia(conf_min=0.05): {seq2}")

seq3 = pi.gerar_sequencia(tm, semente, max_passos=8, conf_min=0.01, max_repeticoes=2)
print(f"gerar_sequencia(conf_min=0.01): {seq3}")
