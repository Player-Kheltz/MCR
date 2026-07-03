"""Debug DETALHADO: o que acontece dentro de reconstruir_resposta()."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.kg import KnowledgeGraph
from modulos.aprendiz_de_padroes import AprendizDePadroes
from modulos.intention_engine import IntentionEngine

pe = PatternEngine()
kg = KnowledgeGraph()
ie = IntentionEngine(pe=pe)
ap = AprendizDePadroes(pe=pe, kg=kg)

pergunta = "Explique o sistema SPA do MCR"
tokens = pe.tokenizar_universal(pergunta)
fp = pe.fingerprint(tokens)
intencoes = ie.detectar(pergunta)

print(f"1. Fingerprint: {[round(x,2) for x in fp[:5]]}...")
print(f"2. IE: {intencoes}")

# Simula exatamente o que reconstruir_resposta() faz
print(f"\n3. Buscando lessons com fingerprint similar...")
licoes = kg._get_licoes()
lessons_encontradas = []

for l in licoes:
    if l.get('inactive', False):
        continue
    fp_l = l.get('fingerprint', [])
    if not fp_l or len(fp_l) != len(fp):
        continue
    dot = sum(a * b for a, b in zip(fp_l, fp))
    if dot >= 0.3:
        l['_sim'] = dot
        lessons_encontradas.append(l)

print(f"   Encontradas: {len(lessons_encontradas)}")
for l in lessons_encontradas[:5]:
    sim = l.get('_sim', 0)
    tm = bool(l.get('tipos_markov'))
    nota = l.get('nota', 0)
    score = (sim * 0.7) + (min(nota, 10) / 10.0 * 0.3) if nota > 0 else sim
    print(f"   [{sim:.2f}] tm={tm} nota={nota} score={score:.3f} | {l.get('ctx','?')} | {l.get('erro','')[:40]}")

# Encontra a melhor
melhor = None
melhor_score = 0
for l in lessons_encontradas:
    tm = l.get('tipos_markov')
    sim = l.get('_sim', 0)
    nota = l.get('nota', 0)
    score = (sim * 0.7) + (min(nota, 10) / 10.0 * 0.3) if nota > 0 else sim
    if tm and score > melhor_score:
        melhor_score = score
        melhor = l

if melhor:
    print(f"\n4. MELHOR: score={melhor_score:.3f} | {melhor.get('ctx','?')} | {melhor.get('erro','')[:40]}")
    if melhor_score >= 0.35:
        print("   Score >= 0.35 -> GERARIA SEQUENCIA")
        # Simula geracao
        from modulos.pi_engine import PiEngine
        pi = PiEngine(pe=pe)
        tm = melhor['tipos_markov']
        tp = melhor.get('tipo_palavra_freq', {})
        # Limita ciclo
        tm_fixed = {}
        for token, trans in tm.items():
            nt = dict(trans)
            if len(nt) == 1:
                saida = list(nt.keys())[0]
                prob = nt[saida]
                if prob > 0.8:
                    nt[saida] = round(prob * 0.85, 3)
                    nt['FIM_FRASE'] = round(prob * 0.15, 3)
            tm_fixed[token] = nt
        
        seq = pi.gerar_sequencia(tm_fixed, 'INTENT_EXPLAIN', max_passos=8, conf_min=0.1, max_repeticoes=2)
        print(f"   Sequencia gerada: {seq}")
        
        palavras = []
        for tipo in seq:
            if tipo in tp:
                palavra = max(tp[tipo], key=tp[tipo].get)
                palavras.append(palavra if palavra else f'@{tipo}')
            else:
                palavras.append(f'@{tipo}')
        print(f"   Palavras: {' '.join(palavras)}")
    else:
        print(f"   Score < 0.35 -> FALHA")
else:
    print(f"\n4. Nenhuma lesson qualificada")
