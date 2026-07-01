"""Debug completo: por que a reconstrucao falha apos aprender?"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.kg import KnowledgeGraph
from modulos.aprendiz_de_padroes import AprendizDePadroes

pe = PatternEngine()
kg = KnowledgeGraph()
aprendiz = AprendizDePadroes(pe=pe, kg=kg)

# 1. Criar fingerprint de exemplo
pergunta = "Explique o sistema SPA do MCR"
tokens = pe.tokenizar_universal(pergunta)
fp = pe.fingerprint(tokens) if tokens else []
print(f"1. Fingerprint da pergunta: {[round(x,2) for x in fp[:5]]}...")

# 2. Ver quantas lessons tem fingerprint agora
licoes = kg._get_licoes()
com_fp = [l for l in licoes if l.get('fingerprint')]
com_auto = [l for l in licoes if l.get('ctx') == 'aprendido_auto']
print(f"2. Lessons totais: {len(licoes)}, com fingerprint: {len(com_fp)}, auto: {len(com_auto)}")

# 3. Verificar a ULTIMA lesson salva com fingerprint
if com_auto:
    ultima = com_auto[-1]
    print(f"3. Ultima lesson auto-aprendida:")
    print(f"   ctx: {ultima.get('ctx')}")
    print(f"   erro: {ultima.get('erro','')[:60]}")
    fp_salvo = ultima.get('fingerprint', [])
    print(f"   fingerprint: {[round(x,2) for x in fp_salvo[:5]]}...")
    print(f"   fingerprint len: {len(fp_salvo)}")
    print(f"   tipos_markov: {list(ultima.get('tipos_markov', {}).keys())[:5]}")

# 4. Testar buscar_rotas com o fingerprint da pergunta
print(f"\n4. Testando kg.buscar_rotas(fp, min_sim=0.3)...")
if hasattr(kg, 'buscar_rotas'):
    try:
        rotas = kg.buscar_rotas(fp, min_sim=0.3)
        print(f"   Resultados: {len(rotas)}")
        for r in rotas[:3]:
            sim = r.get('_sim', '?')
            ctx = r.get('ctx', '?')
            fp_r = r.get('fingerprint', [])
            tm = list(r.get('tipos_markov', {}).keys())[:3] if r.get('tipos_markov') else []
            print(f"   [{sim}] ctx={ctx} | fp={[round(x,2) for x in fp_r[:3]]} | tm={tm}")
    except Exception as e:
        print(f"   ERRO: {e}")
else:
    print("   KG nao tem buscar_rotas")

# 5. Testar buscar_rotas DIRETAMENTE (simulando o que reconstruir_resposta faz)
print(f"\n5. Busca manual de similaridade...")
for l in licoes:
    fp_l = l.get('fingerprint', [])
    if fp_l and len(fp_l) == len(fp):
        sim = sum(a*b for a,b in zip(fp_l, fp))
        if sim > 0.5:
            tm = list(l.get('tipos_markov', {}).keys())[:3] if l.get('tipos_markov') else []
            print(f"   [{sim:.2f}] {l.get('ctx','?')} | {l.get('erro','')[:40]} | tm={tm}")

# 6. Testar reconstruir_resposta DIRETAMENTE
print(f"\n6. Testando Aprendiz.reconstruir_resposta()...")
from modulos.intention_engine import IntentionEngine
ie = IntentionEngine(pe=pe)
intencoes = ie.detectar(pergunta)

resp = aprendiz.reconstruir_resposta(fp, intencoes[0] if intencoes else None, tokens_input=tokens)
if resp and len(resp) > 30:
    print(f"   ✅ FUNCIONOU: {resp[:100]}")
else:
    print(f"   ❌ FALHOU (retornou None ou curto)")
    # Verificar o método buscar_rotas dentro de reconstruir_resposta
    print(f"\n   Simulando o que reconstruir_resposta faz internamente:")
    lessons_encontradas = []
    try:
        lessons_encontradas = kg.buscar_rotas(fp, min_sim=0.5) or []
        print(f"   buscar_rotas(min_sim=0.5): {len(lessons_encontradas)} resultados")
    except Exception as e:
        print(f"   ERRO buscar_rotas: {e}")
    
    if not lessons_encontradas:
        # Tenta match por tipos
        print(f"   Tentando match por tipos (fallback)...")
        tipos_input = [t[0] for t in tokens]
        for l in licoes:
            tm = l.get('tipos_markov')
            if not tm:
                continue
            # Extrai tipos da causa
            causa = l.get('causa', '')
            import re
            m_tipos = re.search(r'tipos=\[([^\]]+)\]', causa)
            if m_tipos:
                tipos_lesson = m_tipos.group(1).split(',')
                match = sum(1 for t in tipos_input if t in tipos_lesson)
                if match >= 2:
                    print(f"   MATCH por tipos: [{match}] {l.get('erro','')[:40]}")
