"""Teste do Dashboard de Pensamento em Tempo Real.
1. Inicia o servidor SSE
2. Executa EMERGIR com emit() hooks
3. O dashboard em http://localhost:8765/thought_dashboard.html mostra o pensamento ao vivo
"""
import os, sys, time
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia'))

from modulos.sse_server import iniciar_sse
from modulos.master_agent import MasterAgent

print("=" * 60)
print("DASHBOARD DE PENSAMENTO EM TEMPO REAL")
print("=" * 60)

# 1. Inicia o SSE server
server = iniciar_sse(8765)
print("Dashboard: http://localhost:8765/thought_dashboard.html")
print()
print("ABRA ESSE LINK NO SEU NAVEGADOR AGORA!")
print("Depois pressione ENTER para iniciar o EMERGIR...")
input()

# 2. Executa EMERGIR
print("\nIniciando EMERGIR V4...")
print("-" * 60)
ma = MasterAgent()
ma._execution_count = 5  # Forca o trigger

t0 = time.time()
ma._processar_emergencia()
elapsed = time.time() - t0

print()
print("-" * 60)
print(f"EMERGIR concluido em {elapsed:.1f}s")
print(f"Dashboard permanece em http://localhost:8765/thought_dashboard.html")
print()
print("O RESULTADO completo esta salvo no Knowledge Graph (sandbox/.mcr_devia/knowledge.json)")
print()
print("Pressione ENTER para encerrar o servidor...")
input()
