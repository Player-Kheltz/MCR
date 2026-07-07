#!/usr/bin/env python3
"""Teste KG direto — busca conceitos sem MCRPergunta."""
import sys
sys.path.insert(0, r'E:\MCR')
from mcr_devia import _cerebro

print("1. KG:", type(_cerebro.kg))

if _cerebro.kg:
    # Tenta buscar diretamente
    if hasattr(_cerebro.kg, 'buscar'):
        print("2. Tem metodo buscar!")
        res = _cerebro.kg.buscar("SPA", max_r=3)
        print("3. Resultados:", res[:2] if res else "vazio")
    else:
        print("2. NAO tem metodo buscar")
        print("   Metodos:", [m for m in dir(_cerebro.kg) if not m.startswith('_')][:20])
    
    # Tenta aprender um conceito
    if hasattr(_cerebro.kg, 'aprender_conceito'):
        _cerebro.kg.aprender_conceito("SPA", "Sistema de Progressao do Aventureiro", ctx="manual")
        print("4. Aprendido via aprender_conceito")
        res2 = _cerebro.kg.buscar("SPA", max_r=3)
        print("5. Agora:", res2[:2] if res2 else "vazio")
