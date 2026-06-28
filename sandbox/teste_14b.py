"""Teste direto do qwen2.5:14b com num_ctx=1024"""
import urllib.request, json, time

payload = json.dumps({
    "model": "qwen2.5:14b",
    "prompt": "Responda SIM ou NAO: Flecha de Fogo article=um esta correto?",
    "stream": False,
    "options": {"temperature": 0.1, "num_ctx": 1024}
}).encode()

print("Chamando qwen2.5:14b (ctx=1024)...")
inicio = time.time()
try:
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=180).read()
    dados = json.loads(resp)
    duracao = time.time() - inicio
    resposta = dados.get("response", "")
    print(f"Resposta ({duracao:.1f}s): {resposta[:300]}")
except Exception as e:
    duracao = time.time() - inicio
    print(f"ERRO ({duracao:.1f}s): {e}")
