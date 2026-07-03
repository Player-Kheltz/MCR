"""Debug detalhado do reconstruir_com_blocos."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
from modulos.pattern_engine import PatternEngine
from modulos.kg import KnowledgeGraph
from modulos.aprendiz_de_padroes import AprendizDePadroes

pe = PatternEngine()
kg = KnowledgeGraph()
ap = AprendizDePadroes(pe=pe, kg=kg)

pergunta = "Explique o sistema SPA do MCR"
tokens = pe.tokenizar_universal(pergunta)
fp_atual = pe.fingerprint(tokens)

# Simula o que reconstruir_com_blocos faz
licoes = kg._get_licoes()
blocos = []
for l in licoes:
    if l.get('inactive') or l.get('ctx') != 'bloco_aprendido':
        continue
    fp_l = l.get('fingerprint', [])
    print(f"Bloco encontrado: ctx={l.get('ctx')}, fp_len={len(fp_l)}, fp_atual_len={len(fp_atual)}")
    if not fp_l or len(fp_l) != len(fp_atual):
        print(f"  SKIP: fp_l={len(fp_l)} vs fp={len(fp_atual)}")
        continue
    dot = sum(a*b for a,b in zip(fp_l, fp_atual))
    print(f"  Similaridade: {dot:.2f}")
    if dot >= 0.5:
        l['_sim'] = dot
        blocos.append(l)

print(f"\nBlocos qualificados: {len(blocos)}")
if blocos:
    melhor = max(blocos, key=lambda x: x.get('_sim', 0))
    sol_raw = melhor.get('solucao', '')
    print(f"Solucao raw: {sol_raw[:100]}")
    try:
        data = json.loads(sol_raw)
        fragmento = data.get('fragmento', sol_raw)
        print(f"Fragmento extraido: {fragmento[:100]}")
    except:
        print(f"Falhou parse JSON")
else:
    print("Nenhum bloco qualificado")
