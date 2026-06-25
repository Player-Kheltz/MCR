#!/usr/bin/env python3
"""Diagnostico do servidor MCR."""
import os, sys, socket, subprocess, time, json

BASE = r"E:\Projeto MCR"
print("=" * 60)
print("  DIAGNOSTICO DO SERVIDOR MCR")
print("=" * 60)

# 1. CHECK PORTS
print("\n📡 PORTAS:")
portas = {"MySQL": 3306, "Login": 7171, "Status": 7172, "Game": 7173}
for nome, porta in portas.items():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect(("127.0.0.1", porta))
        print(f"  ✅ {nome}:{porta} - ABERTA")
        s.close()
    except:
        print(f"  ❌ {nome}:{porta} - FECHADA")

# 2. CHECK MYSQL
print("\n🗄️  MYSQL:")
try:
    import mysql.connector
    conn = mysql.connector.connect(
        host="127.0.0.1", port=3306, user="root",
        password="kjkszpks", database="BancoServer"
    )
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES LIKE '%account%'")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"  ✅ Conectado ao banco 'BancoServer'")
    print(f"  Tabelas de conta: {tables}")
    
    cursor.execute("SELECT COUNT(*) FROM accounts")
    n_contas = cursor.fetchone()[0]
    print(f"  Total de contas: {n_contas}")
    
    cursor.execute("SELECT COUNT(*) FROM players")
    n_players = cursor.fetchone()[0]
    print(f"  Total de players: {n_players}")
    
    conn.close()
except ImportError:
    print("  ⚠️  mysql-connector-python nao instalado, testando via socket...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(("127.0.0.1", 3306))
        # MySQL handshake
        data = s.recv(1024)
        if data:
            print(f"  ✅ MySQL respondeu ({len(data)} bytes no handshake)")
        s.close()
    except Exception as e:
        print(f"  ❌ MySQL nao responde: {e}")
except Exception as e:
    print(f"  ❌ {e}")

# 3. CHECK EXECUTAVEL
print("\n📦 EXECUTAVEL:")
exe = os.path.join(BASE, "Canary", "canary-sln.exe")
if os.path.exists(exe):
    size = os.path.getsize(exe)
    mtime = os.path.getmtime(exe)
    print(f"  ✅ canary-sln.exe ({size/1024/1024:.1f} MB)")
    print(f"  Ultima modificacao: {time.strftime('%Y-%m-%d %H:%M', time.localtime(mtime))}")
else:
    print(f"  ❌ canary-sln.exe NAO ENCONTRADO")

# 4. CHECK CONFIG
print("\n⚙️  CONFIG.LUA:")
cfg_path = os.path.join(BASE, "Canary", "config.lua")
if os.path.exists(cfg_path):
    with open(cfg_path, encoding="utf-8", errors="replace") as f:
        cfg = f.read()
    # Extrai settings relevantes
    for line in cfg.split("\n"):
        line = line.strip()
        if any(k in line for k in ["ip =", "port", "mysqlHost", "mysqlUser", "mysqlDatabase", "worldType", "ownerName"]):
            print(f"  {line}")
else:
    print("  ❌ config.lua NAO ENCONTRADO")

# 5. CHECK OTClient CONFIG
print("\n🎮 OTClient CONFIG:")
for path in [
    os.path.join(BASE, "OTClient", "config.json"),
    os.path.join(BASE, "OTClient", "data", "config.json"),
]:
    if os.path.exists(path):
        with open(path, encoding="utf-8", errors="replace") as f:
            content = f.read()
        for line in content.split("\n"):
            if any(k in line.lower() for k in ["ip", "port", "host", "world", "login"]):
                print(f"  {path.split(os.sep)[-2]}: {line.strip()[:100]}")

# 6. TENTAR INICIAR
print("\n🚀 TESTE DE INICIALIZACAO:")
try:
    proc = subprocess.Popen(
        [exe],
        cwd=os.path.join(BASE, "Canary"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(5)
    if proc.poll() is None:
        print(f"  ✅ Servidor iniciou (PID: {proc.pid})")
        # Tenta conectar na porta de login
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        try:
            s.connect(("127.0.0.1", 7171))
            print(f"  ✅ Porta de login 7171 respondeu!")
            s.close()
        except:
            print(f"  ❌ Porta de login 7171 nao respondeu")
        proc.terminate()
        proc.wait(timeout=5)
        print(f"  Servidor encerrado.")
    else:
        stdout, stderr = proc.communicate(timeout=3)
        print(f"  ❌ Servidor morreu (codigo: {proc.returncode})")
        if stdout: print(f"  STDOUT: {stdout[:200]}")
        if stderr: print(f"  STDERR: {stderr[:200]}")
except Exception as e:
    print(f"  ❌ {e}")

print("\n" + "=" * 60)
print("  DIAGNOSTICO CONCLUIDO")
print("=" * 60)
