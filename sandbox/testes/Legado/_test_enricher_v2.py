"""Teste do Enricher completo com G1-G8."""
import sys, time
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
sys.path.insert(0, 'E:/Projeto MCR')

from modulos.enricher import (
    Enricher, _extrair_termos_criticos, _validar_relevancia,
    _revisar_alucinacoes, _MCR_IDENTITY, _ROUTER
)
from modulos.ia import IA
from modulos.kg import KnowledgeGraph
from context_infinity import SessionCache

ia = IA()
kg = KnowledgeGraph()
cache = SessionCache()

print("=== Teste Enricher G1-G8 ===\n")

# G3: MCR_Identity
print("G3: MCR_Identity presente...")
assert 'SessionCache' in _MCR_IDENTITY
assert 'MasterAgent' in _MCR_IDENTITY
assert 'MCR' in _MCR_IDENTITY
print("   OK")

# G7: Termos criticos
print("\nG7: Termos criticos...")
termos = _extrair_termos_criticos("O que e SessionCache no MCR-DevIA?")
print(f"   Termos: {termos}")
assert len(termos) > 0
assert 'sessioncache' in termos or 'session' in termos

# G8: Router de modelos
print("\nG8: Router de modelos...")
assert _ROUTER.get('conceito_local') == 'pesado'
assert _ROUTER.get('codigo') == 'code'
assert _ROUTER.get('lore') == 'texto'
print(f"   Tipos: {list(_ROUTER.keys())}")

# G6: Validacao de relevancia
print("\nG6: Validacao de relevancia...")
valido = _validar_relevancia(ia, "O que e Python?", [('teste', 'Python e uma linguagem')])
print(f"   Relevante: {valido}")

# G2: Anti-alucinacao
print("\nG2: Anti-alucinacao...")
resposta = "O SessionCache usa o padrão SingletonFactoryImpl para gerenciar conexões"
revisada = _revisar_alucinacoes(resposta, kg)
print(f"   Revisada: {'AVISO' in revisada}")

resposta_ok = "O SessionCache absorve fragmentos e pesca sob demanda"
revisada_ok = _revisar_alucinacoes(resposta_ok, kg)
print(f"   OK: {'AVISO' not in revisada_ok}")

# Fluxo completo
print("\nFluxo completo: Enricher.enriquecer()...")
enricher = Enricher(ia, kg, cache)
t0 = time.time()
resposta = enricher.enriquecer("O que e o SessionCache no MCR-DevIA?", usar_tot=False)
tempo = time.time() - t0
print(f"   Tempo: {tempo:.1f}s")
print(f"   Resposta: {resposta[:200]}...")
assert len(resposta) > 50
assert "SessionCache" in resposta or "Cache" in resposta

print("\n=== TODOS OS TESTES OK ===")
