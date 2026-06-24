#!/usr/bin/env python3
"""Validacao completa: JSON, modelos, agentes, pipeline."""
import json, os, sys, time, urllib.request, subprocess

BASE = r"E:\Projeto MCR"
PASS = 0; FAIL = 0; WARN = 0
DETALHES = []

def testar(nome, resultado, detalhe="", tempo=0):
    global PASS, FAIL, WARN
    if resultado == "PASS": PASS += 1
    elif resultado == "FAIL": FAIL += 1
    else: WARN += 1
    icon = {"PASS":"✅","FAIL":"❌","WARN":"⚠️"}[resultado]
    DETALHES.append({"nome":nome,"resultado":resultado,"detalhe":str(detalhe)[:120],"tempo":round(tempo,2)})
    print(f"  {icon} {nome}: {str(detalhe)[:100]}")

def chat(modelo, msg, system="Responda em 1 frase em portugues.", max_tokens=100):
    payload = json.dumps({"model":modelo,"messages":[
        {"role":"system","content":system},
        {"role":"user","content":msg}
    ],"stream":False,"options":{"temperature":0.1,"max_tokens":max_tokens}}).encode()
    t0 = time.time()
    try:
        req = urllib.request.Request("http://localhost:11434/api/chat",data=payload,headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req,timeout=30) as r:
            data = json.loads(r.read())
        dt = time.time()-t0
        content = data["message"]["content"]
        return content, dt
    except Exception as e:
        return None, time.time()-t0

# ============================================
print("=" * 70)
print("  VALIDACAO COMPLETA - ASSISTENTE LOCAL")
print("=" * 70)

# === 1. JSON ===
print("\n📋 1. VALIDANDO JSON...")
try:
    with open(os.path.join(BASE,"opencode.local.json")) as f:
        cfg = json.load(f)
    testar("opencode.local.json e valido","PASS",f"{len(json.dumps(cfg))} bytes")
except Exception as e:
    testar("opencode.local.json e valido","FAIL",str(e))

# === 2. CHEAGEM DE MODELOS ===
print("\n📦 2. VERIFICANDO MODELOS...")
try:
    req = urllib.request.Request("http://localhost:11434/api/tags")
    with urllib.request.urlopen(req,timeout=5) as r:
        ollama_models = {m["name"] for m in json.loads(r.read()).get("models",[])}
    testar("Ollama online","PASS",f"{len(ollama_models)} modelos instalados")
except Exception as e:
    testar("Ollama online","FAIL",str(e))
    ollama_models = set()

# Verifica cada modelo configurado no provider
provider_models = set()
for m in cfg.get("provider",{}).get("ollama",{}).get("models",{}):
    provider_models.add(m)
    if m in ollama_models:
        testar(f"Modelo {m} esta instalado","PASS",f"Disponivel em E:\\Modelos IA")
    else:
        testar(f"Modelo {m} esta instalado","FAIL","NAO ENCONTRADO - rode 'ollama pull {m}'")

# Verifica agentes vs modelos
for ag, conf in cfg.get("agent",{}).items():
    model_ref = conf.get("model","").replace("ollama/","")
    if model_ref in ollama_models:
        testar(f"Agente {ag} -> {model_ref}","PASS","Modelo disponivel")
    else:
        testar(f"Agente {ag} -> {model_ref}","FAIL","Modelo NAO instalado")

# === 3. TESTE DE RESPOSTA DOS MODELOS ===
print("\n🤖 3. TESTANDO RESPOSTA DOS MODELOS...")

modelos_teste = ["phi3.5:3.8b","qwen2.5-coder:7b","llama3.1:8b","hermes3:8b","deepseek-r1:7b","deepseek-r1:8b"]
for m in modelos_teste:
    if m in ollama_models:
        content, dt = chat(m, "Ola, como voce esta? Em uma frase.")
        if content and len(content) > 5:
            testar(f"Resposta {m}","PASS",f"{len(content)} chars em {dt:.1f}s",dt)
        else:
            testar(f"Resposta {m}","FAIL",f"Resposta vazia ou erro",dt)
    else:
        testar(f"Resposta {m}","WARN","Modelo nao instalado, pulando")

# === 4. TESTE DE TOOL CALLING (agente explore) ===
print("\n🔧 4. TESTANDO TOOL CALLING (agentes)...")

# Testa se o modelo de explore (phi3.5) retorna JSON tool call
system_explore = """Voce e um assistente de exploracao. Use ferramentas para responder.
Disponivel: read_file(caminho), search_file(padrao, dir), list_dir(dir)

Responda SEMPRE no formato JSON: {"tool": "nome", "args": {...}}"""
content, dt = chat("phi3.5:3.8b", "Liste os arquivos do diretorio sandbox", system_explore, 150)
if content:
    try:
        parsed = json.loads(content)
        if "tool" in parsed and parsed["tool"] == "list_dir":
            testar("Phi3.5 tool calling: JSON valido","PASS",f"Chamou {parsed['tool']}({parsed['args']})",dt)
        else:
            testar("Phi3.5 tool calling","WARN",f"JSON parseou mas tool inesperada: {content[:80]}",dt)
    except json.JSONDecodeError:
        testar("Phi3.5 tool calling","WARN",f"Retornou texto em vez de JSON: {content[:80]}",dt)
else:
    testar("Phi3.5 tool calling","FAIL","Sem resposta",dt)

# Testa Hermes 3 tool calling
content2, dt2 = chat("hermes3:8b", "Leia o arquivo AGENTS.md", system_explore, 150)
if content2:
    try:
        parsed2 = json.loads(content2)
        if "tool" in parsed2 and parsed2["tool"] == "read_file":
            testar("Hermes3 tool calling: JSON valido","PASS",f"Chamou {parsed2['tool']}({parsed2['args']})",dt2)
        else:
            testar("Hermes3 tool calling","WARN",f"JSON mas tool inesperada: {content2[:80]}",dt2)
    except json.JSONDecodeError:
        testar("Hermes3 tool calling","WARN",f"Texto: {content2[:80]}",dt2)
else:
    testar("Hermes3 tool calling","FAIL","Sem resposta",dt2)

# === 5. TESTE DE CONSISTENCIA ===
print("\n🔄 5. TESTANDO CONSISTENCIA (2x mesma pergunta)...")
for m in ["phi3.5:3.8b","hermes3:8b","llama3.1:8b"]:
    if m in ollama_models:
        c1, _ = chat(m, "Qual a capital do Brasil?", "Responda de forma concisa.", 50)
        c2, _ = chat(m, "Qual a capital do Brasil?", "Responda de forma concisa.", 50)
        if c1 and c2:
            words1 = set(c1.lower().split())
            words2 = set(c2.lower().split())
            if words1 and words2:
                jaccard = len(words1 & words2) / len(words1 | words2)
                if jaccard > 0.5:
                    testar(f"Consistencia {m}","PASS",f"Jaccard={jaccard:.2f}")
                else:
                    testar(f"Consistencia {m}","WARN",f"Respostas divergentes Jaccard={jaccard:.2f}")
            else:
                testar(f"Consistencia {m}","FAIL","Resposta vazia")

# === 6. TESTE DE ALUCINACAO ===
print("\n🧠 6. TESTANDO RESISTENCIA A ALUCINACAO...")
testes_aluc = [
    ("Phi3.5", "phi3.5:3.8b", "Como usar a funcao calculateDamageMCR() que nao existe?"),
    ("Hermes3", "hermes3:8b", "Como usar a funcao calculateDamageMCR() que nao existe?"),
    ("Llama3.1", "llama3.1:8b", "Como usar a funcao calculateDamageMCR() que nao existe?"),
]
for nome, modelo, pergunta in testes_aluc:
    if modelo in ollama_models:
        content, dt = chat(modelo, pergunta, 
            "Voce e um assistente do Projeto MCR. Se nao souber, diga 'nao encontrei'. NUNCA invente APIs.", 200)
        if content:
            recusou = any(p in content.lower() for p in ["nao encontrei","nao existe","nao sei","nao tenho"])
            testar(f"Anti-alucinacao {nome}","PASS" if recusou else "FAIL",
                   f"{'Recusou' if recusou else 'Pode ter inventado'}: {content[:80]}", dt)

# === 7. TESTE RAG ===
print("\n📚 7. TESTANDO RAG...")
try:
    sys.path.insert(0, os.path.join(BASE,"scripts"))
    from rag_query import get_context
    ctx = get_context("O que e o SPA?", top_k=3, player_mode=True)
    if ctx and len(ctx) > 50:
        testar("RAG responde com contexto","PASS",f"{len(ctx)} chars retornados")
    else:
        testar("RAG responde com contexto","WARN","Contexto vazio ou muito curto")
except Exception as e:
    testar("RAG responde com contexto","FAIL",str(e))

# === RESUMO ===
print("\n" + "=" * 70)
total = PASS+FAIL+WARN
print(f"  RESUMO FINAL: {PASS}/{total} PASS, {FAIL} FAIL, {WARN} WARN")
print(f"  Taxa de sucesso: {PASS/total*100:.0f}%")
print("=" * 70)

if FAIL > 0:
    print("\n  FALHAS:")
    for d in DETALHES:
        if d["resultado"] == "FAIL":
            print(f"    ❌ {d['nome']}: {d['detalhe']}")

# Salva
with open(os.path.join(BASE,"sandbox","validacao_completa.json"),"w") as f:
    json.dump({"resumo":{"total":total,"pass":PASS,"fail":FAIL,"warn":WARN},"detalhes":DETALHES},f,ensure_ascii=False,indent=2)
print(f"\n  Resultados salvos: sandbox/validacao_completa.json")
