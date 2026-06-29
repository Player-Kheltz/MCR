"""Teste RAPIDO do Dashboard SSE + EMERGIR V4.
Inicia SSE server, executa EMERGIR com streaming, mostra metricas.
Abra http://localhost:8765/thought_dashboard.html no navegador ANTES de rodar!
"""
import os, sys, time
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia'))

print("Iniciando servidor SSE...")
from modulos.sse_server import iniciar_sse, emit
server = iniciar_sse(8765)

print("=" * 60)
print("DASHBOARD DE PENSAMENTO EM TEMPO REAL")
print("http://localhost:8765/thought_dashboard.html")
print("=" * 60)
print()
print("ABRA ESSE LINK NO NAVEGADOR AGORA!")
print("Iniciando EMERGIR V4 imediatamente...")
print()

# Sem delay - comeca direto
emit('narrator', 'Sistema iniciado. EMERGIR V4 iniciando...')

print()
print("Executando EMERGIR V4 com streaming SSE...")
print("-" * 60)

from modulos.master_agent import MasterAgent
ma = MasterAgent()
ma._execution_count = 5

t0 = time.time()
ma._processar_emergencia()
elapsed = time.time() - t0

print("-" * 60)
print()
print(f"EMERGIR concluido em {elapsed:.1f}s")
print("Verifique o dashboard para ver o pensamento completo!")
print("Resultado salvo no KG: sandbox/.mcr_devia/knowledge.json")
print()
print("Servidor SSE permanece rodando. Pressione Ctrl+C para parar.")
