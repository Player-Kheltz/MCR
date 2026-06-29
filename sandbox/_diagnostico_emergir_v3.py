"""Diagnostico: captura resposta EMERGIR mesmo se bloqueada pela verificacao."""
import os, sys, json, time

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia'))

from modulos.master_agent import MasterAgent

ma = MasterAgent()
ma._execution_count = 5

# Monkey-patch _verificar_alucinacao_siglas para capturar a resposta
original_verificar = ma._verificar_alucinacao_siglas
def verificar_captura(texto):
    # Salva a resposta em arquivo para diagnostico
    with open(os.path.join(os.path.dirname(__file__), '.emergir_v3_response.txt'), 'w', encoding='utf-8') as f:
        f.write(texto)
    print(f"[DIAG] Resposta capturada: {len(texto)} chars")
    return original_verificar(texto)

ma._verificar_alucinacao_siglas = verificar_captura

print("Executando _processar_emergencia com captura...")
ma._processar_emergencia()
print("OK")
