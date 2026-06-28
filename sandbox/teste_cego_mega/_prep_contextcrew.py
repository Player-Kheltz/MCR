#!/usr/bin/env python3
"""Prepara alteracao no ContextCrew: usar indice do Watchdog em vez de varrer disco.
Depois usa JSON IPC write para MCR-DevIA salvar."""
import os, sys

CONTEXT_CREW_PATH = r"E:\Projeto MCR\scripts\mcr_devia\context_crew.py"

with open(CONTEXT_CREW_PATH, "r", encoding="utf-8") as f:
    current = f.read()

# Adicionar import do Watchdog no inicio do arquivo
current = current.replace(
    'import os, json, re, time, hashlib, urllib.request, threading, concurrent.futures',
    'import os, json, re, time, hashlib, urllib.request, threading, concurrent.futures\nimport importlib as _il'
)

# Modificar _buscar_codigo para usar indice primeiro
old_buscar = '''    def _buscar_codigo(self, termos, max_r=8):
        """Grep universal em diretorios CHAVE do projeto.
        ContextCrew ESTUDA, nunca modifica. Acesso universal a todo codigo relevante."""
        resultados = []
        
        # Diretorios para INCLUIR na busca (apenas codigo FONTE relevante)
        INCLUIR = [
            os.path.join(BASE, 'scripts'),
            os.path.join(BASE, 'docs'),
            os.path.join(BASE, 'sandbox'),
            os.path.join(BASE, 'Canary', 'src'),
            os.path.join(BASE, 'OTClient', 'src'),
        ]
        
        # Extensoes de interesse
        EXTENSOES = {'.py', '.h', '.hpp', '.cpp', '.lua', '.md', '.txt', '.json', '.xml'}
        
        for start_dir in INCLUIR:
            if not os.path.exists(start_dir):
                continue
            try:
                for root, dirs, files in os.walk(start_dir):
                    # Exclui diretorios problematicos
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in 
                              ('__pycache__', 'node_modules', 'vcpkg', '.opencode')]
                    
                    for f in files:
                        ext = os.path.splitext(f)[1].lower()
                        if ext not in EXTENSOES: continue
                        
                        fpath = os.path.join(root, f)
                        try:
                            if os.path.getsize(fpath) > 256000: continue  # Max 250KB
                            with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                                lines = fh.readlines()
                            for i, line in enumerate(lines[:100]):
                                line_lower = line.lower()
                                score = sum(1 for t in termos if t in line_lower)
                                if score > 0 and len(line.strip()) > 20:
                                    ctx_antes = ''.join(lines[max(0,i-1):i])
                                    ctx_depois = ''.join(lines[i:min(len(lines),i+2)])
                                    trecho = ctx_antes + line + ctx_depois
                                    rel = os.path.relpath(fpath, BASE)
                                    resultados.append((score, trecho[:200], f'Code:{rel}:L{i+1}'))
                                    break
                        except: pass
            except: pass
        
        resultados.sort(key=lambda x: -x[0])
        return [(r[1], r[2]) for r in resultados[:max_r]]'''

new_buscar = '''    def _buscar_codigo(self, termos, max_r=8):
        """Grep usando INDICE do Watchdog (mais rapido que varrer disco).
        Fallback: varre diretorios se indice estiver vazio."""
        resultados = []
        
        # Tenta usar indice do Watchdog primeiro
        try:
            from modulos.watchdog import Watchdog
            # Tenta encontrar instancia do watchdog no kernel
            import sys as _sys
            for _mod_name, _mod in sys.modules.copy().items():
                if 'watchdog' in _mod_name.lower() and hasattr(_mod, 'consultar_indice'):
                    for termo in termos[:3]:
                        arquivos = _mod.consultar_indice(termo, max_r=3)
                        for fpath in arquivos:
                            try:
                                if os.path.getsize(fpath) > 256000: continue
                                with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                                    lines = fh.readlines()
                                for i, line in enumerate(lines[:100]):
                                    line_lower = line.lower()
                                    score = sum(1 for t in termos if t in line_lower)
                                    if score > 0 and len(line.strip()) > 20:
                                        ctx_antes = ''.join(lines[max(0,i-1):i])
                                        ctx_depois = ''.join(lines[i:min(len(lines),i+2)])
                                        trecho = ctx_antes + line + ctx_depois
                                        rel = os.path.relpath(fpath, BASE)
                                        resultados.append((score, trecho[:200], f'Code:{rel}:L{i+1}'))
                                        break
                            except: pass
                    if resultados:
                        resultados.sort(key=lambda x: -x[0])
                        return [(r[1], r[2]) for r in resultados[:max_r]]
        except:
            pass
        
        # Fallback: varredura direta (mesmo codigo de antes)
        INCLUIR = [
            os.path.join(BASE, 'scripts'),
            os.path.join(BASE, 'docs'),
            os.path.join(BASE, 'sandbox'),
            os.path.join(BASE, 'Canary', 'src'),
            os.path.join(BASE, 'OTClient', 'src'),
        ]
        EXTENSOES = {'.py', '.h', '.hpp', '.cpp', '.lua', '.md', '.txt', '.json', '.xml'}
        for start_dir in INCLUIR:
            if not os.path.exists(start_dir): continue
            try:
                for root, dirs, files in os.walk(start_dir):
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in 
                              ('__pycache__', 'node_modules', 'vcpkg', '.opencode')]
                    for f in files:
                        ext = os.path.splitext(f)[1].lower()
                        if ext not in EXTENSOES: continue
                        fpath = os.path.join(root, f)
                        try:
                            if os.path.getsize(fpath) > 256000: continue
                            with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                                lines = fh.readlines()
                            for i, line in enumerate(lines[:100]):
                                line_lower = line.lower()
                                score = sum(1 for t in termos if t in line_lower)
                                if score > 0 and len(line.strip()) > 20:
                                    ctx_antes = ''.join(lines[max(0,i-1):i])
                                    ctx_depois = ''.join(lines[i:min(len(lines),i+2)])
                                    trecho = ctx_antes + line + ctx_depois
                                    rel = os.path.relpath(fpath, BASE)
                                    resultados.append((score, trecho[:200], f'Code:{rel}:L{i+1}'))
                                    break
                        except: pass
            except: pass
        resultados.sort(key=lambda x: -x[0])
        return [(r[1], r[2]) for r in resultados[:max_r]]'''

current = current.replace(old_buscar, new_buscar)

# Salva temporario
tmp_path = r"E:\Projeto MCR\sandbox\.mcr_contextcrew_novo.py"
with open(tmp_path, "w", encoding="utf-8") as f:
    f.write(current)

# Envia via JSON IPC write
import json, subprocess, sys as _sys
with open(tmp_path, "r", encoding="utf-8") as f:
    conteudo = f.read()

cmd = {'cmd': 'write', 'args': [CONTEXT_CREW_PATH, conteudo]}
with open(r"E:\Projeto MCR\sandbox\.mcr_cmd.json", "w", encoding="utf-8") as f:
    json.dump(cmd, f, ensure_ascii=False)

r = subprocess.run([_sys.executable, r"E:\Projeto MCR\scripts\mcr_devia\MCR_DevIA-Kernel.py", "--json", r"E:\Projeto MCR\sandbox\.mcr_cmd.json"],
    capture_output=True, text=True, errors='replace', timeout=30)
print(r.stdout[-300:])
print(f"ContextCrew atualizado: {len(conteudo)} chars")
