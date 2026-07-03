"""Testa se discoverItem persiste no banco."""
import time, json

# item_info para ver known atual
req = str(int(time.time() * 1000))
with open(r"E:\Projeto MCR\Canary\data\logs\server_cmd.txt", "a") as f:
    f.write(f"{req}|Testador|item_info|Arbalest\n")
print(f"Request: {req}")
time.sleep(4)

with open(r"E:\Projeto MCR\Canary\data\logs\server_resp.txt", "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

if req in content:
    for line in content.split("\n"):
        if req in line:
            parts = line.split("|", 2)
            data = json.loads(parts[2])
            known = data.get("known", "?")
            print(f"known = {known}")
            if known:
                print("✅ Item descoberto!")
            else:
                print("❌ Item nao descoberto (jogador precisa olhar para ele no jogo)")
            break
else:
    print("Sem resposta do servidor")
    # Mostra ultima linha do arquivo
    with open(r"E:\Projeto MCR\Canary\data\logs\server_resp.txt", "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
        if lines:
            print(f"Ultima resposta: {lines[-1].strip()[:100]}")
