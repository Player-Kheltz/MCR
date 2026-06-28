#!/usr/bin/env python3
"""Transforma intencao, orquestrar, processar em alias para perguntar.
Tudo via JSON IPC write."""
import json, subprocess, sys, os

CMD = r"E:\Projeto MCR\sandbox\.mcr_cmd.json"
KERNEL = r"E:\Projeto MCR\scripts\mcr_devia\MCR_DevIA-Kernel.py"

def ipc_write(path, conteudo):
    cmd = {"cmd": "write", "args": [path, conteudo]}
    with open(CMD, "w", encoding="utf-8") as f:
        json.dump(cmd, f, ensure_ascii=False)
    r = subprocess.run(
        [sys.executable, KERNEL, "--json", CMD],
        capture_output=True, text=True, errors="replace", timeout=30
    )
    return "Write]" in r.stdout

# === ALIAS: intencao → perguntar ===
alias_intencao = '''"""Comando: intencao - ALIAS para perguntar (interpreta intencao)."""
def register():
    return {"name": "intencao", "desc": "ALIAS: interpreta intencao (usa perguntar internamente).",
            "handler": execute, "args": [{"name": "texto", "type": "str", "required": True}], "categoria": "comando"}
def execute(kg, ia, args, ctx_crew=None):
    from comandos.cmd_perguntar import execute as _perguntar
    return _perguntar(kg, ia, args, ctx_crew)
'''

# === ALIAS: orquestrar → perguntar ===
alias_orquestrar = '''"""Comando: orquestrar - ALIAS para perguntar (usa Orquestrador)."""
def register():
    return {"name": "orquestrar", "desc": "ALIAS: orquestra tarefas (usa perguntar internamente).",
            "handler": execute, "args": [{"name": "texto", "type": "str", "required": True}], "categoria": "comando"}
def execute(kg, ia, args, ctx_crew=None):
    from comandos.cmd_perguntar import execute as _perguntar
    return _perguntar(kg, ia, args, ctx_crew)
'''

# === ALIAS: processar → perguntar ===
alias_processar = '''"""Comando: processar - ALIAS para perguntar (processa entrada)."""
def register():
    return {"name": "processar", "desc": "ALIAS: processa entrada (usa perguntar internamente).",
            "handler": execute, "args": [{"name": "texto", "type": "str", "required": True}], "categoria": "comando"}
def execute(kg, ia, args, ctx_crew=None):
    from comandos.cmd_perguntar import execute as _perguntar
    return _perguntar(kg, ia, args, ctx_crew)
'''

COMANDOS_DIR = r"E:\Projeto MCR\scripts\mcr_devia\comandos"

print("Criando alias...")
for nome, conteudo in [("cmd_intencao.py", alias_intencao), 
                        ("cmd_orquestrar.py", alias_orquestrar),
                        ("cmd_processar.py", alias_processar)]:
    path = os.path.join(COMANDOS_DIR, nome)
    ok = ipc_write(path, conteudo)
    print(f"  {nome}: {'OK' if ok else 'ERRO'} ({len(conteudo)} chars)")

print("Concluido!")
