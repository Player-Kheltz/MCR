"""Teste RPC final - verifica se o discovery funciona."""
import time, json, os

BASE = r"E:\Projeto MCR"
CMD = os.path.join(BASE, "Canary", "data", "logs", "server_cmd.txt")
RESP = os.path.join(BASE, "Canary", "data", "logs", "server_resp.txt")

def rpc(action, param):
    req = str(int(time.time() * 1000))
    with open(CMD, "a") as f:
        f.write(f"{req}|Test|{action}|{param}\n")
    for i in range(8):
        time.sleep(1)
        if os.path.exists(RESP):
            with open(RESP, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if req in line:
                        return line.strip()
    return None

# Limpa
for f in [CMD, RESP]:
    with open(f, "w") as fh: fh.write("")
time.sleep(1)

# 1. knows_item para Arbalest (5803)
resp = rpc("knows_item", "5803")
if resp:
    data = json.loads(resp.split("|", 2)[2])
    print(f"knows_item(5803) antes: known={data.get('known')} ✅" if data.get('known') is not None else f"knows_item: {resp[:80]}")
else:
    print("knows_item: TIMEOUT ❌")

# 2. item_info para Arbalest
resp2 = rpc("item_info", "Arbalest")
if resp2:
    data = json.loads(resp2.split("|", 2)[2])
    name = data.get("name", "?")
    known = data.get("known", "?")
    print(f"item_info(Arbalest): name={name}, known={known}, id={data.get('id')}")
else:
    print("item_info: TIMEOUT ❌")

# 3. Teste usando jogador Criador (que existe)
print("\n--- Teste com jogador Criador ---")

# knows_item para jogador Criador
req3 = str(int(time.time() * 1000))
with open(CMD, "a") as f:
    f.write(f"{req3}|Criador|knows_item|5803\n")
time.sleep(4)
with open(RESP, "r") as f:
    for line in f:
        if req3 in line:
            data = json.loads(line.split("|", 2)[2])
            print(f"knows_item(5803) Criador: known={data.get('known')}")
            break
    else:
        print("knows_item Criador: TIMEOUT")

# 4. item_info para jogador Criador
req4 = str(int(time.time() * 1000))
with open(CMD, "a") as f:
    f.write(f"{req4}|Criador|item_info|Arbalest\n")
time.sleep(4)
with open(RESP, "r") as f:
    for line in f:
        if req4 in line:
            try:
                data = json.loads(line.split("|", 2)[2])
                print(f"item_info(Arbalest) Criador: known={data.get('known')}")
            except:
                print(f"item_info Criador: {line.strip()[:100]}")
            break
    else:
        print("item_info Criador: TIMEOUT")
