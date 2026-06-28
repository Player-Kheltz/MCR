"""CORRIDA - Rodada 1: Cloud 70B corre pista MCR-DevIA"""
import urllib.request, json, time

OLLAMA = "http://localhost:11434/api/generate"

def chamar(modelo, prompt, temp=0.3, ctx=2048):
    payload = json.dumps({"model": modelo, "prompt": prompt,
        "stream": False, "options": {"temperature": temp, "num_ctx": ctx}}).encode()
    inicio = time.time()
    try:
        req = urllib.request.Request(OLLAMA, data=payload,
            headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=120).read()
        r = json.loads(resp).get("response", "")
        return r, round(time.time() - inicio, 1)
    except Exception as e:
        return f"[ERRO] {e}", round(time.time() - inicio, 1)

# Pista do MCR-DevIA: detector.py
codigo = open("E:\\Projeto MCR\\sandbox\\corrida\\pista_mcrdevia\\detector.py").read()

print("=" * 60)
print("CORRIDA - RODADA 1")
print("Cloud 70B corre pista_mcrdevia (detector.py)")
print("=" * 60)

print("\n--- Problema 1: validar_config ---")
prompt1 = f"Analise este codigo Python e encontre os 2 problemas e 1 falsa pista:\n\n{codigo}\n\nProblema 1 (logica):"
r1, t1 = chamar("qwen2.5-coder:7b", prompt1, 0.3)
print(f"  ({t1}s) {r1[:200]}")

print("\n--- Problema 2: processar_itens (None crash) ---")
prompt2 = f"{codigo}\n\nProblema 2 (crash com None):"
r2, t2 = chamar("qwen2.5-coder:7b", prompt2, 0.3)
print(f"  ({t2}s) {r2[:200]}")

print("\n--- Falsa pista: salvar_resultado ---")
prompt3 = f"{codigo}\n\nFalsa pista (oque parece mas nao e):"
r3, t3 = chamar("qwen2.5-coder:7b", prompt3, 0.3)
print(f"  ({t3}s) {r3[:200]}")

print("\n=== RESULTADO RODADA 1 ===")
print(f"Cloud encontrou problemas? {r1[:50]}... | {r2[:50]}...")
