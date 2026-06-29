"""Teste final do pipeline: RPC respondendo e discovery funcional."""
import time, json, os

CMD = r"E:\Projeto MCR\Canary\data\logs\server_cmd.txt"
RESP = r"E:\Projeto MCR\Canary\data\logs\server_resp.txt"

# Limpa para comecar fresco
with open(CMD, "w") as f: f.write("")
with open(RESP, "w") as f: f.write("")
time.sleep(1)

req_id = str(int(time.time() * 1000))
with open(CMD, "a") as f:
    f.write(f"{req_id}|Test|item_info|Espada de Fogo\n")
print(f"Request: {req_id}")

for i in range(10):
    time.sleep(1)
    if os.path.exists(RESP):
        with open(RESP, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            if req_id in content:
                # Encontra a linha completa (multi-line JSON)
                start = content.find(req_id)
                end = content.find("\n", start)
                if end == -1:
                    end = len(content)
                line = content[start:end]
                parts = line.split("|", 2)
                if len(parts) == 3:
                    print(f"Status: {parts[1]}")
                    print("✅ RPC RESPONDENDO!")
                    # Mostra preview
                    print(f"  Preview: {parts[2][:100]}")
                break
else:
    print("❌ RPC sem resposta em 10s")
