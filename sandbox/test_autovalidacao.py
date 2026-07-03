"""Teste do ciclo completo: reconstruir + auto-validar + corrigir."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.kg import KnowledgeGraph
from modulos.aprendiz_de_padroes import AprendizDePadroes
from modulos.intention_engine import IntentionEngine
from modulos.tool_orchestrator import ToolOrchestrator

pe = PatternEngine()
kg = KnowledgeGraph()
ie = IntentionEngine(pe=pe)
tools = ToolOrchestrator()
ap = AprendizDePadroes(pe=pe, kg=kg)

pergunta = "Explique o sistema SPA do MCR"

# 1. Tokeniza + IE
tokens = pe.tokenizar_universal(pergunta)
fp = pe.fingerprint(tokens)
intencoes = ie.detectar(pergunta)
cat = intencoes[0][0] if intencoes else "GERAL"

print(f"1. Pergunta: {pergunta}")
print(f"   IE: {cat}")

# 2. Reconstruir
print(f"\n2. Reconstruindo...")
resposta = ap.reconstruir_resposta(fp, intencoes[0] if intencoes else None, tokens)
print(f"   Resposta bruta ({len(resposta) if resposta else 0} chars):")
print(f"   {resposta[:200] if resposta else 'None'}")

# 3. Auto-validar
print(f"\n3. Auto-validando...")
if resposta and '@' in resposta:
    corrigida = ap.preencher_resposta(
        resposta,
        tipos_gerados=[t[0] for t in tokens],
        pergunta_original=pergunta,
        tools=tools,
    )
    if corrigida and corrigida != resposta:
        print(f"   ✅ Corrigida ({len(corrigida)} chars):")
        print(f"   {corrigida[:200]}")
    elif corrigida:
        print(f"   ⚠️ Corrigida mas sem mudanca: {corrigida[:100]}")
    else:
        print(f"   ❌ Correcao falhou (retornou None)")
else:
    print(f"   ✅ Resposta nao tem placeholders")
