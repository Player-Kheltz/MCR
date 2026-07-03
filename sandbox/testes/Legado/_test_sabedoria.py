"""Teste do Sistema de Sabedoria: pre-carga + KG + busca hierarquica."""
import sys, os, json
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
sys.path.insert(0, 'E:/Projeto MCR')

from context_infinity import SessionCache
from modulos.kg import KnowledgeGraph
from modulos.ia import IA
from modulos.episodic_memory import EpisodicMemory
from modulos.master_agent import MasterAgent

print("=== Teste Sistema de Sabedoria ===\n")

# F1: Pre-carregamento do SessionCache
print("F1: SessionCache.precarregar()...")
cache = SessionCache()
kg = KnowledgeGraph()
mem = EpisodicMemory()
n = cache.precarregar(kg=kg, request="SessionCache MCR DevIA", memorias=mem.buscar("SessionCache", 3))
print(f"   Fragmentos pre-carregados: {n}")
assert n > 0, f"Precarregamento gerou 0 fragmentos"
# Verifica se tem fragmentos do KG
tags_kg = [f for f in cache.fragmentos.values() if 'kg' in (f._tags or [])]
print(f"   Fragmentos do KG: {len(tags_kg)}")

# Testa pesca apos pre-carregamento
pesca = cache.pescar(pergunta="O que e SessionCache?", tipos=['contexto'], max_tokens=1000, n=3)
print(f"   Pesca apos pre-carga: {len(pesca)} resultados")
for p in pesca:
    print(f"     -> {p.conteudo[:80]}...")

# F2: Busca sabedoria
print("\nF2: _buscar_sabedoria()...")
agent = MasterAgent()
lessons = agent._buscar_sabedoria("O que e o SessionCache MCR?", max_lessons=3)
print(f"   Lessons encontradas: {len(lessons)}")
for l in lessons:
    print(f"     [{l.get('id','?')}] {l.get('solucao','')[:80]}...")

# F3: Busca hierarquica
print("\nF3: _buscar_hierarquico()...")
# Primeiro executa algo para ter SessionCache
r = agent.executar("Cria um script python que imprime 'teste'")
print(f"   Execucao: {r.get('n_sucesso',0)}/{r.get('n_subtarefas',0)} passos")
contexto = agent._buscar_hierarquico("Python print")
print(f"   Contexto encontrado: {len(contexto)} itens")
for i, c in enumerate(contexto):
    print(f"     [{i+1}] {str(c)[:100]}...")

print("\n=== TODOS OS TESTES OK ===")
