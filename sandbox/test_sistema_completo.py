#!/usr/bin/env python3
"""Teste completo do sistema: Ollama + Server + Bridge + RPC."""
import json, urllib.request, time, socket, os, sys

BASE = r"E:\Projeto MCR"
PASS = 0
FAIL = 0

def check(nome, ok, detalhe=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  ✅ {nome}")
    else:
        FAIL += 1
        print(f"  ❌ {nome}: {detalhe}")

# 1. OLLAMA
print("\n📌 1. OLLAMA")
try:
    req = urllib.request.Request("http://localhost:11434/api/tags")
    with urllib.request.urlopen(req, timeout=5) as r:
        data = json.loads(r.read())
    n = len(data.get("models", []))
    check("Ollama online", n > 0, f"{n} modelos")
except Exception as e:
    check("Ollama online", False, str(e))

# 2. INFERENCIA
print("\n📌 2. INFERENCIA (qwen1.5b)")
try:
    t0 = time.time()
    payload = json.dumps({"model": "qwen2.5-coder:1.5b", "messages": [
        {"role": "user", "content": "Diga 'ok' em 1 palavra."}
    ], "stream": False, "options": {"temperature": 0.1, "max_tokens": 10}}).encode()
    req = urllib.request.Request("http://localhost:11434/api/chat", data=payload,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        resp = json.loads(r.read())["message"]["content"]
    dt = time.time() - t0
    check("Modelo respondeu", resp and len(resp) > 0, f"'{resp}' em {dt:.1f}s")
except Exception as e:
    check("Modelo respondeu", False, str(e))

# 3. SERVER PORTAS
print("\n📌 3. SERVER")
for port in [7171, 7172, 7173]:
    s = socket.socket()
    s.settimeout(2)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        check(f"Porta {port}", True)
    except:
        check(f"Porta {port}", False)

# 4. RPC
print("\n📌 4. RPC")
import os as _os
cmd = _os.path.join(BASE, "Canary", "data", "logs", "server_cmd.txt")
resp = _os.path.join(BASE, "Canary", "data", "logs", "server_resp.txt")

with open(cmd, "w") as f: f.write("")
with open(resp, "w") as f: f.write("")
time.sleep(1)

req_id = str(int(time.time() * 1000))
with open(cmd, "a") as f:
    f.write(f"{req_id}|Test|item_info|Arbalest\n")

for i in range(10):
    time.sleep(1)
    if _os.path.exists(resp):
        with open(resp, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            if req_id in content:
                check("RPC respondeu", True)
                break
else:
    check("RPC respondeu", False, "timeout 10s")

# 5. MCR-DEV
print("\n📌 5. MCR-DEV")
sys.path.insert(0, os.path.join(BASE, "scripts"))
sys.path.insert(0, os.path.join(BASE, "Scripts"))
try:
    from mcr_dev import router, engine, validador, memoria
    r = router.classify("crie um NPC ferreiro")
    check("MCR-Dev router", r[0] == "CRIAR_NPC", str(r))
except Exception as e:
    check("MCR-Dev router", False, str(e))

# RESUMO
print(f"\n{'='*50}")
print(f"  TOTAL: {PASS}/{PASS+FAIL} OK, {FAIL} FAIL")
print(f"{'='*50}")
if FAIL == 0:
    print("\n  ✅ SISTEMA COMPLETO FUNCIONANDO!")
