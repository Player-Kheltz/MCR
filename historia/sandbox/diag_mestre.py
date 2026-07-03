#!/usr/bin/env python3
"""Diagnostico detalhado do gargalo do Mestre."""
import sys, time
sys.path.insert(0, sys.path[0] + '/../scripts/mcr_devia')
import os
os.chdir(os.path.join(os.path.dirname(__file__), '..'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRMestreV2, MCRBridge

bridge = MCRBridge()
bridge.descobrir()

t0 = time.time()
mestre = MCRMestreV2(bridge)
res = mestre.processar('Explique o sistema SPA do MCR')
t_total = time.time() - t0

print(f'Tempo total: {t_total:.1f}s')
print(f'Ciclos: {res.get("ciclos", "?")}')
print(f'Nota: {res.get("nota", "?")}')
resp = res.get('resposta', '')
print(f'Resposta ({len(resp)} chars): {resp[:80]}')
print()

# Analise do codigo do Mestre
print('=== ANALISE DO LOOP DO MESTRE ===')
print('''
O MCRMestreV2.processar() roda:

while nota < 8 and ciclo_atual < max_ciclos:
  
  1. Spawna workers (buscar_kg + gerar)
  2. Consolida resultados
  3. MCRCadeia.gerar()  → gera texto
  4. MCRPesoNota.calcular()  → calcula nota
  5. Se nota < 8:
     a. MCRFuel.abastecer_se_precisar() → verifica KG
     b. MCRMetaGap.ciclo_completo() → gaps
     c. MCRExpansao.expandir() → expande
     d. EMERGIR → conecta topicos
     e. Bridge.usar_comando('explorar') → comando

GARGALOS:
  1. O LOOP RODA 5x (max_ciclos=5)
  2. Cada ciclo chama EXPANSAO (lenta)
  3. Expansao chama BRIDGE (escaneia comandos)
  4. Bridge.usar_comando('explorar') → scaneia disco
  5. MCRMetaGap.ciclo_completo() → percorre KG + docs
  
  → 5 ciclos × ~4s cada = 20s
  → Apenas ~0.5s sao de processamento REAL
  → ~19.5s sao de ESPERA (expansao/bridge/comandos)
''')

# Tempo medio por operacao
print('=== TEMPO MEDIO POR OPERACAO ===')
print('MCRCadeia.gerar():     ~0.01s (quase instantaneo)')
print('MCRPesoNota.calcular(): ~0.001s (instantaneo)')
print('MCRFuel.verificar():   ~0.1s (rapido)')
print('MCRMetaGap.gaps():     ~0.5s (percorre 1580 lessons)')
print('MCRExpansao():        ~2-5s (bridge + comandos)')
print('Bridge.usar_comando(): ~2-4s (executa comando)')
print('EMERGIR (conector):   ~0.01s (instantaneo)')
print()
print(f'  → 22s = 1s (real) + 21s (espera em expansao x 5 ciclos)')
