"""Teste final de integracao: MCRConversa + MCRSuperLoop + MCRAutoAlimentar."""
import sys, os, time, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from MCR_AGI import *

print("=== TESTE INTEGRACAO COMPLETA ===")
print()

c = CerebroAGI()
c.alimentar("O modelo de 8572MB e o maior com 579 tensores arquitetura qwen2.", "modelo_grande")
c.alimentar("O modelo de 4466MB e medio com 339 tensores.", "modelo_medio")
c.alimentar("O modelo de 262MB e o menor para embeddings com 112 tensores.", "modelo_pequeno")

MCRExpansor.registrar("m", lambda p: [
    {"assinatura": d.get("texto",""), "meta": {"topico": n}}
    for n, d in list(c.topicos.items())
])

# SuperLoop em background
sl = MCRSuperLoop(c)
t = threading.Thread(target=sl.iniciar_loop, daemon=True)
t.start()
time.sleep(0.05)

# Conversa
conv = MCRConversa(c)
print(f"  {conv.historico[0]}")
print()

for p in ["qual o maior modelo", "e qual o menor?", "que horas sao"]:
    print(f"  voce: {p}")
    r = conv.perguntar(p)
    safe = r.encode("ascii", errors="replace").decode("ascii")[:150]
    print(f"  mcr: {safe}")
    print()

# Metricas
print(f"  SuperLoop: {sl.geracao} geracoes")
print(f"  Fitness: {sl.hist_fitness}")
print(f"  Cerebro: {len(c.topicos)} topicos")
print()

# MCRExpansor responde diretamente
for p in ["que horas sao", "qual o maior modelo"]:
    r = MCRExpansor.responder(p)
    safe = r.encode("ascii", errors="replace").decode("ascii")[:120]
    print(f"  MCRExpansor('{p}'): {safe}")

print()
print("=== TESTE CONCLUIDO ===")
