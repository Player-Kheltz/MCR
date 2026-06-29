"""Teste Dashboard Unificado EMERGIR V4."""
import os, sys, time
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia'))

from modulos.sse_server import iniciar_sse, emit
iniciar_sse(8765)

print("="*60)
print("DASHBOARD UNIFICADO — EMERGIR V4")
print("http://localhost:8765/thought_dashboard.html")
print("="*60)
print()
print("Abra o link no navegador e veja em tempo real!")
print("Iniciando EMERGIR em 5 segundos...")
for i in range(5,0,-1):
    print(f"  {i}...", flush=True)
    time.sleep(1)

emit('narrator', 'EMERGIR V4 iniciando...')

from modulos.master_agent import MasterAgent
ma = MasterAgent()
ma._execution_count = 5

t0 = time.time()
ma._processar_emergencia()
elapsed = time.time() - t0

print("-"*60)
print(f"EMERGIR concluido em {elapsed:.1f}s")
print("Resultado salvo no KG.")
print("Servidor SSE continua rodando na porta 8765.")
print("Pressione Ctrl+C para parar.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
