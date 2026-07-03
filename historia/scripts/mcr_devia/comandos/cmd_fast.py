"""Comando: fast - Classificacao rapida via IA (usa router padronizado)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast as _util_fast

def register():
    return {
        "name": "fast",
        "desc": "Classificacao rapida via Ollama (SIM/NAO, extracoes simples)",
        "handler": execute,
        "args": [{"name": "texto", "type": "str", "required": True}],
        "categoria": "ia",
    }

def execute(kg, ia, args, ctx_crew=None):
    if not args:
        print('[Fast] Uso: fast <texto>')
        return True
    
    texto = ' '.join(args)
    
    # Usa router padronizado (modelo definido em ia.py/util.py)
    try:
        resp = _util_fast(texto, 0.1, "fast")
        if resp:
            print(f'[Fast] {resp}')
        else:
            print('[Fast] Sem resposta')
    except Exception as e:
        print(f"[Fast] ERRO: {e}")
    
    return True
