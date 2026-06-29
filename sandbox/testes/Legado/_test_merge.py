"""Teste comparativo: Conselho (fundido) vs Enricher (atalho)"""
import sys, time
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
sys.path.insert(0, 'E:/Projeto MCR')

# Teste 1: Import de compatibilidade (enricher.py)
print("1. Import Enricher via atalho...")
from modulos.enricher import Enricher as EnricherAlias
from modulos.conselho import Conselho
print(f"   Enricher = Conselho? {EnricherAlias is Conselho}")
assert EnricherAlias is Conselho, "Enricher deve ser Conselho"
print("   OK")

# Teste 2: Funcoes novas disponiveis
print("\n2. Funcoes novas no conselho...")
from modulos.conselho import tree_of_thought, extrair_termos_criticos, validar_relevancia, PromptCache
print(f"   tree_of_thought: {callable(tree_of_thought)}")
print(f"   extrair_termos_criticos: {callable(extrair_termos_criticos)}")
print(f"   validar_relevancia: {callable(validar_relevancia)}")
print(f"   PromptCache: {type(PromptCache)}")
assert callable(tree_of_thought)
assert callable(extrair_termos_criticos)
assert callable(validar_relevancia)
assert PromptCache is not None
print("   OK")

# Teste 3: Termos criticos
print("\n3. extrair_termos_criticos...")
termos = extrair_termos_criticos("O que e SessionCache no MCR-DevIA?")
print(f"   Termos: {termos}")
assert len(termos) > 0
assert 'sessioncache' in termos or 'session' in termos
print("   OK")

# Teste 4: PromptCache
print("\n4. PromptCache...")
cache = PromptCache()
cache.set("teste", "prompt_teste")
assert cache.get("teste") == "prompt_teste"
print("   OK")

# Teste 5: Conselho ainda funciona como antes
print("\n5. Conselho.deliberar()...")
from modulos.ia import IA
from modulos.kg import KnowledgeGraph
ia = IA()
kg = KnowledgeGraph()
conselho = Conselho(kg=kg, ia=ia)
# Teste classificar
tipo = conselho._classificar("Explique o que e SPA no MCR")
print(f"   Tipo classificado: {tipo}")
assert tipo in ('factual', 'procedimental', 'ambientacao', 'opiniao', 'codigo', 'desconhecido')
print("   OK")

# Teste 6: Fluxo completo (sem TreeOfThought para nao demorar)
print("\n6. Fluxo completo (lento - pode levar 2-3 min)...")
t0 = time.time()
resultado = conselho.deliberar("O que e o SessionCache no MCR-DevIA?")
tempo = time.time() - t0
print(f"   Tempo: {tempo:.1f}s")
print(f"   Veredito: {resultado.get('veredito','')[:150]}...")
print(f"   Tipo: {resultado.get('tipo','?')}")
assert resultado.get('veredito')
assert len(resultado.get('veredito','')) > 50

print("\n=== TODOS OS TESTES OK ===")
