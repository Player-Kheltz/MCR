"""Comando: pensar - Documenta o raciocinio do Cloud no .mcr_conversa.jsonl
Uso: pensar <decisao> [--alt "alt1,alt2,alt3"] [--duvidas "texto"]
     (para raciocinio completo, usar --json)
"""
import os, json, time
from datetime import datetime

def register():
    return {
        "name": "pensar",
        "desc": "Documenta raciocinio no .mcr_conversa.jsonl para MCR aprender",
        "handler": execute,
        "args": [{"name": "decisao", "type": "str", "required": True}],
        "categoria": "kernel",
    }

def execute(kg, ia, args, ctx_crew=None):
    if not args:
        print('[Pensar] Uso: pensar <decisao> [--alt "opcao1,opcao2"] [--duvidas "texto"]')
        return True
    
    # Extrai args
    texto = []
    alternativas = []
    duvidas = ""
    
    i = 0
    while i < len(args):
        if args[i] == '--alt' and i+1 < len(args):
            alternativas = [a.strip() for a in args[i+1].split(',')]
            i += 2
            continue
        elif args[i] == '--duvidas' and i+1 < len(args):
            duvidas = args[i+1]
            i += 2
            continue
        else:
            texto.append(args[i])
            i += 1
    
    decisao = ' '.join(texto)
    
    # Monta entrada
    entrada = {
        "role": "cloud",
        "ts": time.time(),
        "ts_iso": datetime.now().isoformat(),
        "msg": decisao[:500],
    }
    if alternativas:
        entrada["alternativas_consideradas"] = alternativas
    if duvidas:
        entrada["duvidas"] = duvidas[:300]
    
    # Salva no .mcr_conversa.jsonl
    BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    caminho = os.path.join(BASE, 'sandbox', '.mcr_conversa.jsonl')
    
    try:
        with open(caminho, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entrada, ensure_ascii=False) + '\n')
        print(f'[Pensar] Raciocinio salvo ({len(decisao)} chars)')
        if alternativas:
            print(f'[Pensar] Alternativas: {len(alternativas)}')
        if duvidas:
            print(f'[Pensar] Duvidas: {duvidas[:80]}...')
    except Exception as e:
        print(f'[Pensar] ERRO: {e}')
    
    return True
