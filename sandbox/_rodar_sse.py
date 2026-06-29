"""Servidor SSE para teste do dashboard unificado."""
import sys, os, time
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.sse_server import iniciar_sse
iniciar_sse(8765)
print('[SSE] Servidor rodando na porta 8765')
while True:
    time.sleep(60)
