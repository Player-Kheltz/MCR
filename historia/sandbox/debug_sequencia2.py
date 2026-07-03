"""Debug: porque a lesson aprendido_auto nao gera sequencia?"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.kg import KnowledgeGraph
from modulos.pi_engine import PiEngine

pe = PatternEngine()
kg = KnowledgeGraph()
pi = PiEngine(pe=pe)

fp = pe.fingerprint(pe.tokenizar_universal('Explique o sistema SPA do MCR'))

# Pega a lesson aprendido_auto com maior score
melhor = None
ms = 0
for l in kg._get_licoes():
    fp_l = l.get('fingerprint', [])
    if not fp_l or len(fp_l) != len(fp) or l.get('ctx') != 'aprendido_auto':
        continue
    dot = sum(a*b for a,b in zip(fp_l, fp))
    if dot > ms:
        ms = dot
        melhor = l

if melhor:
    tm = melhor.get('tipos_markov', {})
    print(f'Lesson: {melhor.get("erro","")[:50]}')
    print(f'Markov keys: {list(tm.keys())[:6]}')
    if tm:
        seed = list(tm.keys())[0]
        print(f'Semente: {seed}')
        prox, conf = pi.predizer(tm, seed)
        print(f'predizer({seed}) -> ({prox}, {conf})')
        print(f'Transicoes de {seed}: {tm.get(seed, {})}')
        
        for conf_min in [0.1, 0.05, 0.01]:
            seq = pi.gerar_sequencia(tm, seed, max_passos=5, conf_min=conf_min, max_repeticoes=2)
            print(f'Sequencia(conf_min={conf_min}): {seq}')
    else:
        print('Markov vazio')
else:
    print('Nenhuma lesson aprendido_auto encontrada')
