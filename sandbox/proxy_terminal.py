#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Proxy Terminal MCR-DevIA v3 - COM FEEDBACK AO VIVO.
Fala com o MCR-DevIA (pipeline completo), NAO com o Cloud (OpenCode).

Uso: python proxy_terminal.py "sua mensagem"
     python proxy_terminal.py  (modo interativo)

A resposta vem do MCR-DevIA, nao do Cloud. Para falar com Cloud,
use o OpenCode diretamente.
"""
import os, sys, json, subprocess, time, urllib.request

# Forca UTF-8 em todo o processo (corrige caracteres quebrados no Windows)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
os.environ['PYTHONIOENCODING'] = 'utf-8'

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
KERNEL = os.path.join(BASE, 'scripts', 'mcr_devia', 'MCR_DevIA-Kernel.py')

MCR_LOGO = """
  ╔══════════════════════════════╗
  ║     MCR-DevIA v5200          ║
  ║     Pipeline: Mente →        ║
  ║     Supervisor → Orquestrador║
  ║     → Auto-Revisor           ║
  ╚══════════════════════════════╝"""

def _status(msg):
    """Mostra status com timestamp."""
    t = time.strftime('%H:%M:%S')
    try:
        print(f"[{t}] {msg}")
    except:
        # Fallback se encoding falhar
        print(f"[{t}] {msg.encode('ascii', errors='replace').decode()}")
    sys.stdout.flush()

def _ler_contexto():
    """Le regras + identidade para contexto (separado da instrucao)."""
    partes = []
    arquivos = [
        ('AGENTS.md', os.path.join(BASE, 'AGENTS.md')),
        ('MCR_IDENTITY.md', os.path.join(BASE, 'docs', 'MCR_IDENTITY.md')),
    ]
    for nome, path in arquivos:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                # So as partes essenciais (primeiros 1000 chars)
                partes.append(f"=== {nome} ===\n{f.read()[:1000]}")
    return '\n\n'.join(partes)

def enviar(mensagem):
    """Envia mensagem com contexto prependido via JSON IPC.
    Retorna (resposta, status_code, tempo_total)."""
    t0 = time.time()
    
    # SEM prepend de regras. MCR-DevIA ja tem as regras no proprio KG.
    # As regras sao para o Cloud (OpenCode), que ja as recebe via opencode.json
    prompt = mensagem
    
    # Log
    conv_path = os.path.join(BASE, 'sandbox', '.mcr_conversa.jsonl')
    try:
        with open(conv_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                'ts': time.time(), 'role': 'proxy_v3',
                'original': mensagem[:100], 'prompt_size': len(prompt)
            }, ensure_ascii=False) + '\n')
    except: pass
    
    _status(f"Criando JSON IPC ({len(prompt)} chars)...")
    cmd_path = os.path.join(BASE, 'sandbox', '.mcr_cmd.json')
    with open(cmd_path, 'w', encoding='utf-8') as f:
        json.dump({'cmd': 'perguntar', 'args': [prompt]}, f, ensure_ascii=False)
    
    _status("Chamando MCR-DevIA Kernel...")
    
    try:
        r = subprocess.run(
            [sys.executable, KERNEL, '--json', cmd_path],
            capture_output=True, encoding='utf-8', errors='replace', timeout=180
        )
        tempo = round(time.time() - t0, 1)
        
        stdout = r.stdout
        # Extrai a resposta (depois de "perguntar executado em" ou antes)
        if 'perguntar executado em' in stdout:
            # Pega o que vem depois do ultimo [Orquestrador] OK
            lines = stdout.split('\n')
            resposta = []
            capturar = False
            for line in lines:
                if 'Orquestrador] OK' in line or 'Auto-Revisor]' in line:
                    capturar = True
                    continue
                if 'perguntar executado em' in line:
                    break
                if capturar and line.strip():
                    resposta.append(line)
            if resposta:
                return '\n'.join(resposta), 'ok', tempo
        
        return stdout[-1500:], 'ok', tempo
        
    except subprocess.TimeoutExpired:
        _status("TIMEOUT (180s)")
        return None, 'timeout', round(time.time() - t0, 1)
    except Exception as e:
        _status(f"ERRO: {e}")
        return None, 'erro', round(time.time() - t0, 1)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        msg = ' '.join(sys.argv[1:])
        _status("Iniciando...")
        resp, status, tempo = enviar(msg)
        print("\n" + "=" * 50)
        if resp:
            print(resp[:2000])
        else:
            print(f"[{status.upper()}] Sem resposta")
        print(f"\n[Tempo: {tempo}s | Status: {status}]")
    else:
        print("Modo interativo com feedback ao vivo.")
        print("Comandos: sair, status\n")
        while True:
            try:
                msg = input(">>> ")
                if msg.lower() in ('sair', 'quit', 'exit'):
                    break
                if msg.strip():
                    if msg.lower() == 'status':
                        print("Proxy terminal v3 — fala com MCR-DevIA")
                        continue
                    resp, status, tempo = enviar(msg)
                    print("\n" + "=" * 50)
                    print(MCR_LOGO)
                    print(f"[MCR-DevIA] Resposta ({tempo}s):")
                    print("=" * 50)
                    if resp:
                        print(resp[:2000])
                    else:
                        print(f"[{status.upper()}] Sem resposta")
                    print("=" * 50)
                    print("[Cloud] LEMBRE-SE: MCR-DevIA e parte da equipe!")
            except (EOFError, KeyboardInterrupt):
                break
