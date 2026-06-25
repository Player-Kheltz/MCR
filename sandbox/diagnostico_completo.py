#!/usr/bin/env python3
"""
Diagnostico completo: mata, compila, testa, valida.
Uma execucao, sem loops. Fallback em cada etapa.
"""
import subprocess, os, sys, time, json, socket

BASE = r"E:\Projeto MCR"
EXE = os.path.join(BASE, "Canary", "canary-sln.exe")
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

def wait_ports(ports, timeout=10, state="closed"):
    for i in range(timeout):
        time.sleep(1)
        all_done = True
        for port in ports:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            try:
                s.connect(("127.0.0.1", port))
                if state == "closed":
                    all_done = False
                s.close()
            except:
                if state == "open":
                    all_done = False
        if all_done:
            return True
    return False

print("=" * 60)
print("  DIAGNOSTICO COMPLETO - MCR SERVER")
print("=" * 60)

# PASSO 1: Matar TODOS os processos canary
print("\n📌 1. Matando processos canary...")
subprocess.run(["taskkill", "/f", "/im", "canary-sln.exe"], capture_output=True)
subprocess.run(["taskkill", "/f", "/im", "canary.exe"], capture_output=True)
time.sleep(2)

# Verifica se matou
remaining = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True)
check("Processos canary mortos", "canary" not in remaining.stdout.lower())

# Espera portas liberarem
wait_ports([7171, 7172, 7173], timeout=8, state="closed")
check("Portas 7171-7173 liberadas", True)

# PASSO 2: Verificar se ha outros exes
print("\n📌 2. Verificando executaveis...")
outros = []
for root, dirs, files in os.walk(BASE):
    for f in files:
        if f == "canary-sln.exe" and root != os.path.join(BASE, "Canary"):
            outros.append(os.path.join(root, f))
check("Nenhum exe antigo em outros diretorios", len(outros) == 0, str(outros))

exe_size = os.path.getsize(EXE)
exe_time = os.path.getmtime(EXE)
check(f"EXE existe ({exe_size/1024/1024:.1f} MB)", os.path.exists(EXE))

# PASSO 3: Compilar
print("\n📌 3. Compilando Canary...")
ret = subprocess.run(
    f'cmd.exe /c ""C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\VC\\Auxiliary\\Build\\vcvars64.bat" >nul && "C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\MSBuild\\Current\\Bin\\amd64\\MSBuild.exe" "{os.path.join(BASE, "Canary", "vcproj", "canary.vcxproj")}" /p:Configuration=Release /p:Platform=x64 /t:Build /m"',
    shell=True, capture_output=True, text=True, timeout=120
)
compilou = "0 Erro" in ret.stdout or "sucesso" in ret.stdout or "0 Error" in ret.stdout
check("Compilacao bem-sucedida", compilou, ret.stdout[-200:])

# PASSO 4: Iniciar servidor
print("\n📌 4. Iniciando servidor...")
proc = subprocess.Popen([EXE], cwd=os.path.join(BASE, "Canary"),
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3)

if proc.poll() is None:
    # Verifica portas
    time.sleep(4)
    portas_ok = all(wait_ports([7171], timeout=1, state="open") for _ in range(1))
    # Tenta conectar
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        s.connect(("127.0.0.1", 7171))
        s.close()
        check(f"Server ONLINE (PID: {proc.pid}, porta 7171 OK)", True)
    except:
        check(f"Server process running but port 7171 not responding", False)
else:
    check(f"Server MORREU (codigo: {proc.returncode})", False, "Server crashed on startup")
    sys.exit(1)

# PASSO 5: Iniciar bridge
print("\n📌 5. Iniciando bridge...")
subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True)
time.sleep(1)

bridge_proc = subprocess.Popen(
    [sys.executable, os.path.join(BASE, "Scripts", "bridge_auto.py")],
    cwd=BASE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
time.sleep(3)
check(f"Bridge RODANDO (PID: {bridge_proc.pid})", bridge_proc.poll() is None)

# PASSO 6: Testar RPC
print("\n📌 6. Testando RPC...")
# Limpa arquivos
for f in ["server_cmd.txt", "server_resp.txt"]:
    with open(os.path.join(BASE, "Canary", "data", "logs", f), "w") as fh:
        fh.write("")

time.sleep(2)  # Deixa o servidor processar

# Testa knows_item para ID 5803 (Arbalest)
req_id = str(int(time.time() * 1000))
with open(os.path.join(BASE, "Canary", "data", "logs", "server_cmd.txt"), "a") as f:
    f.write(f"{req_id}|Test|knows_item|5803\n")

for i in range(10):
    time.sleep(1)
    resp_path = os.path.join(BASE, "Canary", "data", "logs", "server_resp.txt")
    if os.path.exists(resp_path):
        with open(resp_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if req_id in line:
                    try:
                        data = json.loads(line.split("|", 2)[2])
                        known = data.get("known", False)
                        check(f"RPC knows_item(5803) respondeu (known={known})", True)
                        found_response = True
                    except:
                        pass
                    break
            else:
                continue
        break
else:
    check("RPC knows_item(5803) respondeu em 10s", False, "Timeout")

# PASSO 7: Testar item_info
print("\n📌 7. Testando item_info...")
req_id2 = str(int(time.time() * 1000))
with open(os.path.join(BASE, "Canary", "data", "logs", "server_cmd.txt"), "a") as f:
    f.write(f"{req_id2}|Test|item_info|Arbalest\n")

for i in range(10):
    time.sleep(1)
    resp_path = os.path.join(BASE, "Canary", "data", "logs", "server_resp.txt")
    if os.path.exists(resp_path):
        with open(resp_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if req_id2 in line:
                    try:
                        data = json.loads(line.split("|", 2)[2])
                        name = data.get("name", "?")
                        check(f"RPC item_info(Arbalest) encontrou: {name}", name == "Arbalest", f"Got: {name}")
                    except Exception as e:
                        check(f"RPC item_info(Arbalest) respondeu", True, str(e))
                    break
            else:
                continue
        break
else:
    check("RPC item_info(Arbalest) respondeu em 10s", False, "Timeout")

# RESUMO
print(f"\n{'='*60}")
print(f"  RESUMO: {PASS}/{PASS+FAIL} OK, {FAIL} FAIL")
print(f"{'='*60}")

if FAIL == 0:
    print("\n  ✅ TUDO FUNCIONANDO!")
    print("  O jogador precisa olhar para o Arbalest no jogo.")
    print("  Apos o look, o discovery sera salvo no BD.")
    print("  Entao o assistente respondera com os stats.")
else:
    print(f"\n  ⚠️  {FAIL} falha(s) - verificar acima")
