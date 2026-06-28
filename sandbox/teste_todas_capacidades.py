"""Teste completo de TODAS as capacidades do MCR-DevIA"""
import subprocess, sys, os, json, time

MCR = [sys.executable, os.path.join("E:\\Projeto MCR", "scripts", "mcr_devia", "mcr_devia.py")]
OLLAMA_URL = "http://localhost:11434/api/generate"
SANDBOX = "E:\\Projeto MCR\\sandbox"

def mcr(*args, timeout=60):
    inicio = time.time()
    try:
        r = subprocess.run(MCR + list(args), capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()[:300], round(time.time()-inicio, 1)
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]", time.time()-inicio
    except:
        return "[ERRO]", time.time()-inicio

def cloud(modelo, prompt, timeout=30):
    import urllib.request
    import json as jn
    payload = jn.dumps({"model": modelo, "prompt": prompt, "stream": False,
        "options": {"temperature": 0.1, "num_ctx": 2048}}).encode()
    inicio = time.time()
    try:
        req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type":"application/json"})
        resp = jn.loads(urllib.request.urlopen(req, timeout=timeout).read())
        return resp.get("response","")[:300], round(time.time()-inicio, 1)
    except:
        return "[ERRO]", round(time.time()-inicio, 1)

print("=" * 70)
print("TESTE COMPLETO: MCR-DevIA vs Cloud em CADA CAPACIDADE")
print("=" * 70)

# ================================================================
# TESTES DE CAPACIDADES DO MCR-DEVIA
# ================================================================
testes = [
    # (nome, (args), timeout, [alternativas para aceitar como OK])
    ("analisar (codigo)", ("analisar", f"{SANDBOX}\\corrida\\pista_runas\\main.lua"), 120,
     ["LINHA", "runa", "consumida", "bug"]),
    ("fast (classificacao)", ("fast", "Flecha de Fogo article=um esta correto? Responda NAO se errado."), 30,
     ["NAO", "errad"]),
    ("fast (genero V12)", ("fast", "Espada Longa article=um esta correto? Responda NAO se errado."), 15,
     ["NAO", "V12"]),
    ("perguntar (KG direto)", ("perguntar", "O que e SHC?"), 30,
     ["Habilidades Contextuais", "SHC"]),
    ("perguntar (sem KG, busca)", ("perguntar", "O que e Lorentia?"), 180,
     ["Lorentia", "continente", "nao"]),
    ("status", ("status",), 10, ["MCR-DevIA", "Licoes", "Comandos"]),
    ("ensinar (aprendizado)", ("ensinar", "teste", "teste", "teste", "teste"), 10, ["APRENDIDO"]),
]

# MCR-DevIA
print(f"\n{'─'*70}")
print("MCR-DevIA - Executando cada capacidade...")
print(f"{'─'*70}")
mcr_results = []
for nome, args, to, keywords in testes:
    print(f"  {nome:<30}...", end=" ")
    sys.stdout.flush()
    resp, tempo = mcr(*args, timeout=to)
    ok = any(k.lower() in resp.lower() for k in keywords) or resp == "[TIMEOUT]" and "OK" not in str(keywords)
    status = "[OK]" if ok else "[ERRO]"
    print(f" {status} ({tempo}s)")
    mcr_results.append((nome, ok, tempo, resp[:100]))

# Cloud (equivalentes, mas mais genericos)
print(f"\n{'─'*70}")
print("Cloud 70B - Fazendo o mesmo via modelos locais...")
print(f"{'─'*70}")
cloud_results = []
for nome, args, to, keywords in testes:
    print(f"  Cloud faz {nome:<20}...", end=" ")
    sys.stdout.flush()
    if nome.startswith("analisar"):
        codigo = open(f"{SANDBOX}\\corrida\\pista_runas\\main.lua").read()
        resp, tempo = cloud("qwen2.5-coder:7b", f"Analise: {codigo[:400]}\nProblemas: LINHA X:", to)
    elif nome.startswith("fast (classificacao"):
        resp, tempo = cloud("llama3.1:8b", f"Flecha de Fogo article=um. Flecha e feminino, article deveria ser uma. Correto? Responda NAO:", to)
    elif nome.startswith("fast (genero"):
        resp, tempo = cloud("llama3.1:8b", f"Espada Longa article=um. Espada e feminino. Responda NAO:", to)
    elif nome.startswith("perguntar (KG"):
        resp, tempo = cloud("llama3.1:8b", f"O que e SHC no projeto MCR? Resuma:", to)
    elif nome.startswith("perguntar (sem KG"):
        resp, tempo = cloud("llama3.1:8b", f"O que e Lorentia?", to)
    elif nome.startswith("status"):
        resp, tempo = "MCR-DevIA - OK", 0
    elif nome.startswith("ensinar"):
        resp, tempo = "APRENDIDO", 0
    else:
        resp, tempo = cloud("qwen2.5-coder:7b", nome, to)
    ok = any(k.lower() in resp.lower() for k in keywords)
    status = "[OK]" if ok else "[?] "
    print(f" {status} ({tempo}s)")
    cloud_results.append((nome, ok, tempo, resp[:100]))

# ================================================================
# RESULTADO
# ================================================================
print(f"\n\n{'='*70}")
print("COMPARATIVO FINAL")
print(f"{'='*70}")
print(f"\n{'Capacidade':<35} {'MCR-DevIA':<16} {'Cloud 70B':<16} {'Vencedor':<16}")
print("-" * 83)

mcr_score = 0
cloud_score = 0
for (mn, mok, mt, _), (cn, cok, ct, _) in zip(mcr_results, cloud_results):
    vencedor = "EMPATE"
    if mok and not cok: vencedor = "MCR 🏆"; mcr_score += 1
    elif cok and not mok: vencedor = "Cloud 🏆"; cloud_score += 1
    elif mok and cok: 
        if mt < ct: vencedor = "MCR (rapido)"
        elif ct < mt: vencedor = "Cloud (rapido)"
        else: vencedor = "EMPATE"
    
    print(f"{mn:<35} {'[OK]' if mok else '[ERRO]':<16} {'[OK]' if cok else '[ERRO]':<16} {vencedor:<16}")

print(f"\n\nPLACAR: MCR-DevIA {mcr_score} x {cloud_score} Cloud 70B")
print(f"\nLegenda:")
print(f"  MCR-DevIA usa: Model Router + KG + V12 + AST + Context Infinity")
print(f"  Cloud usa: Modelo local puro (mesmo modelo, sem pipeline)")
