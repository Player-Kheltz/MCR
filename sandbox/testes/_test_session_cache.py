"""Teste do SessionCache + integracao MasterAgent."""
import sys, os
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
sys.path.insert(0, 'E:/Projeto MCR')

from context_infinity import SessionCache, FragmentoContexto
from modulos.master_agent import MasterAgent

print("=== Teste SessionCache ===\n")

# E1: Absorver sem limite
print("E1: Absorver 100 fragmentos...")
cache = SessionCache()
for i in range(100):
    cache.absorver(f'f_{i}', f'conteudo de teste numero {i}', 'texto')
assert len(cache.fragmentos) == 100
assert len(cache.historico) == 100
print(f"   OK: {len(cache.fragmentos)} fragmentos, {len(cache.historico)} eventos")

# E2: Atualizar fragmento existente
print("\nE2: Atualizar fragmento...")
cache.absorver('f_0', 'conteudo ATUALIZADO', 'codigo', tags=['python'])
assert cache.fragmentos['f_0'].prioridade > 50  # aumentou com atualizacao
assert 'python' in cache.fragmentos['f_0']._tags
print(f"   OK: prioridade={cache.fragmentos['f_0'].prioridade}, tags={cache.fragmentos['f_0']._tags}")

# E3: Pesca por tipo
print("\nE3: Pesca por tipo...")
cache.absorver('codigo_1', 'print("hello world")', 'codigo', tags=['python'])
cache.absorver('explicacao_1', 'Python eh uma linguagem de programacao', 'explicacao')
r = cache.pescar(tipos=['codigo'], n=5)
print(f"   codigo: {len(r)} resultados (esperado >=1)")
assert len(r) >= 1
assert r[0].tipo == 'codigo'

# E4: Pesca por pergunta
print("\nE4: Pesca por pergunta...")
r = cache.pescar(pergunta='python programacao', tipos=['explicacao'], n=3)
print(f"   explicacao: {len(r)} resultados (esperado >=1)")
assert len(r) >= 1

# E5: Pesca com limite de tokens
print("\nE5: Pesca com max_tokens...")
for i in range(10):
    cache.absorver(f'grande_{i}', 'X' * 1000, 'texto')
r = cache.pescar(pergunta='grande', max_tokens=1500, n=10)
tokens_total = sum(f.tokens for f in r)
print(f"   {len(r)} fragmentos, {tokens_total} tokens (max=1500)")
assert tokens_total <= 1500

# E6: Reconstruir estado
print("\nE6: Reconstruir estado...")
estado = cache.reconstruir(tags=['python'], max_chars=500)
print(f"   estado: {len(estado)} chars (max=500)")
assert len(estado) <= 500
assert len(estado) > 0

# E7: Metricas
print("\nE7: Metricas...")
m = cache.metricas()
print(f"   {m}")

# E8: Integracao MasterAgent (criacao e execucao rapida)
print("\nE8: MasterAgent com SessionCache...")
agent = MasterAgent()
r = agent.executar("Cria um script python que imprime hello")
assert hasattr(agent, 'ctx')
assert 'plano' in agent.ctx.fragmentos
assert 'passo_2_gerar_codigo' in agent.ctx.fragmentos or 'passo_1_buscar_exemplos_similares' in agent.ctx.fragmentos
print(f"   OK: {len(agent.ctx.fragmentos)} fragmentos na sessao")
print(f"   IDs: {list(agent.ctx.fragmentos.keys())[:5]}...")

print("\n=== TODOS OS TESTES OK ===")
