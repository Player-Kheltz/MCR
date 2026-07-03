"""Debug: onde o prototipo esta travando?"""
import sys, os, time as _time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

print("[1] Iniciando...")
t0 = _time.time()

print(f"[2] Importando modulos... ({_time.time()-t0:.1f}s)")
from modulos.pattern_engine import PatternEngine
from modulos.pi_engine import PiEngine
from modulos.kg import KnowledgeGraph
print(f"[3] Modulos importados ({_time.time()-t0:.1f}s)")

print(f"[4] Iniciando PatternEngine...")
pe = PatternEngine()
print(f"[5] PatternEngine OK ({_time.time()-t0:.1f}s)")

print(f"[6] Iniciando PiEngine...")
pi = PiEngine(pe=pe)
print(f"[7] PiEngine OK ({_time.time()-t0:.1f}s)")

print(f"[8] Iniciando KG...")
kg = KnowledgeGraph()
print(f"[9] KG OK ({_time.time()-t0:.1f}s)")

print(f"[10] Testando PE.tokenizar_universal()...")
tokens = pe.tokenizar_universal("teste de texto simples")
print(f"[11] Tokens: {[t[0] for t in tokens]} ({_time.time()-t0:.1f}s)")

print(f"[12] Testando PE.extrair_padroes()...")
padroes = pe.extrair_padroes(tokens)
print(f"[13] Entropia: {padroes.get('entropia', 'ERRO')} ({_time.time()-t0:.1f}s)")

print(f"[14] Testando PiEngine.predizer()...")
markov_teste = {"teste": {"de": 0.8, "simples": 0.2}}
prox, conf = pi.predizer(markov_teste, "teste")
print(f"[15] predizer: {prox} ({conf}) ({_time.time()-t0:.1f}s)")

print(f"[16] Testando tokenizar_fragmentado()...")
frags = pe.tokenizar_fragmentado("Explique SPA. Crie um NPC.")
print(f"[17] Fragmentos: {len(frags)} ({_time.time()-t0:.1f}s)")

print(f"\n✅ Tudo OK em {_time.time()-t0:.1f}s")
