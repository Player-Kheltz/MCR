"""Debug: porque reconstrucao retorna None?"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.aprendiz_de_padroes import AprendizDePadroes
from modulos.kg import KnowledgeGraph
from modulos.intention_engine import IntentionEngine

pe = PatternEngine()
kg = KnowledgeGraph()
ie = IntentionEngine(pe=pe)
ap = AprendizDePadroes(pe=pe, kg=kg)

# Simula pergunta 2
pergunta2 = "Explique o que e SPA"
intencoes = ie.detectar(pergunta2)
print("Intencoes:", intencoes)

tokens = pe.tokenizar_universal(pergunta2)
fp = pe.fingerprint(tokens) if tokens else []
print("Tokens:", [t[0] for t in tokens])
print("FP:", fp[:5])

# Chama reconstrucao
resp = ap.reconstruir_resposta(fp, intencoes[0] if intencoes else None, tokens_input=tokens)
print("Resultado:", repr(resp[:80] if resp else None))
