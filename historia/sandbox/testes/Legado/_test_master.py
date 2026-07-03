"""Teste basico do MasterAgent (Fase 5)."""
import sys, os
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.master_agent import MasterAgent

print("=== Teste MasterAgent (Fase 5) ===\n")

# 1. Inicializacao
print("1. Inicializando MasterAgent...")
agent = MasterAgent()
print("   OK: MasterAgent criado")
print(f"   Ferramentas: {len(agent.tools.listar())}")
print(f"   Episodios: {agent.memoria.metricas()['total']}")

# 2. Log e metricas (sem execucao)
print("\n2. Metricas iniciais...")
metrics = agent.metricas()
print(f"   Metricas: {metrics}")
assert 'episodios' in metrics
assert 'sandbox' in metrics

# 3. Teste de execucao com request simples (usando template, sem LLM)
print("\n3. Executando request simples (pergunta template)...")
resultado = agent.executar("O que e Python?", "pergunta_simples")
print(f"   Sucesso: {resultado['sucesso']}")
print(f"   Subtarefas: {resultado['n_subtarefas']}")
print(f"   Tempo: {resultado['tempo']}s")
print(f"   Resposta: {str(resultado['artefato'].get('resposta_final',''))[:100]}...")
assert resultado['sucesso'] == True or resultado['n_subtarefas'] > 0

# 4. Verificar que aprendeu
print("\n4. Verificando aprendizado...")
metrics = agent.metricas()
print(f"   Episodios apos execucao: {metrics['episodios']['total']}")
assert metrics['episodios']['total'] > 0

print("\n=== TESTE BASICO PASS OU ===")
