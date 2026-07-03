#!/usr/bin/env python3
"""
test_local_model.py — Suite completa de validacao de modelos locais Ollama.
Fases: Tool Calling, Alucinacao, Instrucoes, Benchmark.

Uso: python test_local_model.py [--model qwen2.5-coder:7b]
"""
import sys, os, json, time, urllib.request, hashlib, re, subprocess

sys.path.insert(0, r"E:\Projeto MCR\scripts")

OLLAMA_CHAT = "http://localhost:11434/v1/chat/completions"
OLLAMA_GEN = "http://localhost:11434/api/generate"
BASE_DIR = r"E:\Projeto MCR"
MODELO_PADRAO = "qwen2.5-coder:7b"

# ============================================================
# Resultados globais
# ============================================================
resultados = []
PASS = 0
FAIL = 0
WARN = 0

def reportar(fase, nome, status, detalhes="", tempo=0):
    global PASS, FAIL, WARN
    r = {"fase": fase, "nome": nome, "status": status, "detalhes": detalhes[:200], "tempo": round(tempo, 2)}
    if status == "PASS":
        PASS += 1
    elif status == "FAIL":
        FAIL += 1
    else:
        WARN += 1
    resultados.append(r)
    icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}.get(status, "❓")
    print(f"  {icon} [{fase}] {nome}: {detalhes[:120]}")

# ============================================================
# HELPERS
# ============================================================

def chat_completion(messages, model=MODELO_PADRAO, temperature=0.0, tools=None, max_tokens=256):
    """Chama Ollama via API compatível com OpenAI."""
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if tools:
        payload["tools"] = tools
    
    t0 = time.time()
    try:
        req = urllib.request.Request(
            OLLAMA_CHAT,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        dt = time.time() - t0
        
        choice = data.get("choices", [{}])[0]
        msg = choice.get("message", {})
        content = msg.get("content", "")
        tool_calls = msg.get("tool_calls", [])
        
        return {
            "content": content,
            "tool_calls": tool_calls,
            "finish_reason": choice.get("finish_reason", ""),
            "time": dt,
            "raw": data
        }
    except Exception as e:
        dt = time.time() - t0
        return {"content": None, "tool_calls": [], "error": str(e), "time": dt}

def generate(prompt, model=MODELO_PADRAO, temperature=0.0, max_tokens=256):
    """Chama Ollama via API generate."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature, "max_tokens": max_tokens}
    }
    t0 = time.time()
    try:
        req = urllib.request.Request(
            OLLAMA_GEN,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        dt = time.time() - t0
        return {"content": data.get("response", ""), "time": dt}
    except Exception as e:
        return {"content": f"[ERRO] {e}", "time": 0}

# ============================================================
# FASE 1: TOOL CALLING
# ============================================================
def fase1_tool_calling():
    print("\n" + "=" * 60)
    print("  FASE 1: TOOL CALLING")
    print("=" * 60)
    
    model = MODELO_PADRAO
    
    # T1.1: Testar function calling via API OpenAI-compativel
    tools_def = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Le o conteudo de um arquivo",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Caminho do arquivo"}
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_code",
                "description": "Busca um padrao no codigo",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "description": "Padrao a buscar"},
                        "path": {"type": "string", "description": "Diretorio"}
                    },
                    "required": ["pattern"]
                }
            }
        }
    ]
    
    # T1.1: Modelo consegue usar tool call?
    resp = chat_completion([
        {"role": "system", "content": "Voce e um assistente que usa ferramentas para responder. Quando precisar de informacao, chame a ferramenta apropriada."},
        {"role": "user", "content": "Qual o conteudo do arquivo E:\\Projeto MCR\\AGENTS.md?"}
    ], tools=tools_def)
    
    has_tool = len(resp.get("tool_calls", [])) > 0
    has_content = bool(resp.get("content"))
    
    if has_tool:
        tc = resp["tool_calls"][0]
        fn = tc.get("function", {}).get("name", "")
        args = tc.get("function", {}).get("arguments", "")
        reportar("F1", "Tool calling: modelo escolheu ferramenta correta",
                "PASS" if "read" in fn.lower() else "WARN",
                f"Chamou: {fn}({str(args)[:80]})", resp["time"])
    elif has_content:
        reportar("F1", "Tool calling: modelo respondeu sem ferramenta",
                "WARN", f"Resposta: {resp['content'][:100]}", resp["time"])
    else:
        reportar("F1", "Tool calling: sem resposta",
                "FAIL", f"Erro: {resp.get('error', 'vazio')}", resp["time"])
    
    # T1.2: Seguir instrucao de NAO inventar
    resp2 = chat_completion([
        {"role": "system", "content": "Responda APENAS com base no contexto fornecido. Se nao souber, diga 'nao sei'. NUNCA invente."},
        {"role": "user", "content": "Qual o dano da espada 'Flamberga Mítica'?"}
    ])
    
    content2 = (resp2.get("content") or "").lower()
    if "nao sei" in content2 or "nao encontrei" in content2 or "nao tenho" in content2:
        reportar("F1", "Instrucao negativa: recusou inventar", "PASS", f"Resposta: {resp2['content'][:100]}", resp2["time"])
    else:
        reportar("F1", "Instrucao negativa: pode ter inventado", "WARN", f"Resposta: {resp2['content'][:100]}", resp2["time"])

# ============================================================
# FASE 2: RESISTENCIA A ALUCINACAO
# ============================================================
def fase2_alucinacao():
    print("\n" + "=" * 60)
    print("  FASE 2: RESISTENCIA A ALUCINACAO")
    print("=" * 60)
    
    tests = [
        ("T2.1", "Arquivo inexistente",
         "Resuma o conteudo do arquivo E:\\Projeto MCR\\src\\nao_existe.cpp",
         ["nao encontrei", "nao existe", "nao tenho", "nao sei", "inexistente"]),
        
        ("T2.2", "Funcao falsa",
         "Como usar a funcao calculateDamageMCR() no codigo do MCR?",
         ["nao encontrei", "nao existe", "nao sei", "nao tenho"]),
        
        ("T2.3", "API inventada",
         "Qual o efeito de CONST_EFFECT_FIRESWELL?",
         ["nao encontrei", "nao existe", "nao sei", "nao tenho", "nao e"]),
        
        ("T2.4", "Item falso com RAG-like",
         "Contexto: O sistema SPA tem dominios de fogo, gelo, terra.\nPergunta: Qual o dano do dominio 'Void'?",
         ["nao encontrei", "nao existe", "nao sei", "nao mencionado"]),
        
        ("T2.5", "Consistencia (repetir 2x)",
         "Quantos dominios elementais existem no SPA?",
         ["3", "4", "5", "seis", "cinco", "quatro", "tres"]),
    ]
    
    for tid, nome, pergunta, keywords_ok in tests:
        resp = chat_completion([
            {"role": "system", "content": "Voce e um assistente do Projeto MCR. Responda APENAS com base no que sabe. Se nao souber, diga 'Nao encontrei essa informacao no codigo ou documentacao do MCR.' NUNCA invente."},
            {"role": "user", "content": pergunta}
        ])
        content = (resp.get("content") or "").lower()
        
        # Verifica se recusou (qualquer keyword de recusa)
        recusou = any(kw in content for kw in keywords_ok)
        
        if recusou:
            reportar("F2", f"{tid} {nome}", "PASS", f"Recusou: {resp['content'][:80]}", resp["time"])
        else:
            # Se respondeu algo, verifica se parece inventado
            reportar("F2", f"{tid} {nome}", "WARN", f"Respondeu sem contexto: {resp['content'][:80]}", resp["time"])
    
    # T2.5: Consistencia (faz a mesma pergunta 2x e compara)
    resp_a = chat_completion([
        {"role": "system", "content": "Responda em portugues, 1-2 frases."},
        {"role": "user", "content": "Quantos dominios elementais existem no SPA? Cite os nomes."}
    ])
    resp_b = chat_completion([
        {"role": "system", "content": "Responda em portugues, 1-2 frases."},
        {"role": "user", "content": "Quantos dominios elementais existem no SPA? Cite os nomes."}
    ])
    
    ca = (resp_a.get("content") or "").lower()
    cb = (resp_b.get("content") or "").lower()
    
    # Similaridade simples: palavras em comum / total
    words_a = set(ca.split())
    words_b = set(cb.split())
    if words_a and words_b:
        jaccard = len(words_a & words_b) / len(words_a | words_b)
        if jaccard > 0.5:
            reportar("F2", "T2.5 Consistencia (2x mesma pergunta)", "PASS",
                    f"Similaridade Jaccard: {jaccard:.2f}", max(resp_a["time"], resp_b["time"]))
        else:
            reportar("F2", "T2.5 Consistencia (2x mesma pergunta)", "WARN",
                    f"Respostas divergentes (Jaccard: {jaccard:.2f})", max(resp_a["time"], resp_b["time"]))
    else:
        reportar("F2", "T2.5 Consistencia", "FAIL", "Respostas vazias", 0)

# ============================================================
# FASE 3: COMPARATIVO ENTRE MODELOS
# ============================================================
def fase3_comparativo():
    print("\n" + "=" * 60)
    print("  FASE 3: COMPARATIVO ENTRE MODELOS")
    print("=" * 60)
    
    modelos = ["qwen2.5-coder:7b", "deepseek-r1:7b", "deepseek-r1:8b"]
    
    # Perguntas padrao para comparar
    perguntas = [
        ("Complexa", "Explique o que e o Sistema de Progressao do Aventureiro (SPA) no MCR em 2 frases."),
        ("Tecnica", "O que significa COMBAT_FIREDAMAGE no codigo do Canary?"),
        ("Simples", "Qual a capital do Brasil?"),
    ]
    
    for modelo in modelos:
        print(f"\n  --- Modelo: {modelo} ---")
        for tipo, pergunta in perguntas:
            try:
                resp = chat_completion([
                    {"role": "system", "content": "Responda de forma concisa em portugues."},
                    {"role": "user", "content": pergunta}
                ], model=modelo)
                content = resp.get("content", "") or "(vazio)"
                tempo = resp.get("time", 0)
                reportar("F3", f"{modelo} - {tipo}", "PASS" if len(content) > 10 else "WARN",
                        f"{len(content)} chars em {tempo:.1f}s: {content[:80]}", tempo)
            except Exception as e:
                reportar("F3", f"{modelo} - {tipo}", "FAIL", str(e), 0)

# ============================================================
# FASE 4: BENCHMARK DE VELOCIDADE
# ============================================================
def fase4_benchmark():
    print("\n" + "=" * 60)
    print("  FASE 4: BENCHMARK DE VELOCIDADE")
    print("=" * 60)
    
    modelos = ["qwen2.5-coder:7b", "deepseek-r1:7b"]
    
    for modelo in modelos:
        print(f"\n  --- Modelo: {modelo} ---")
        
        # prompt curto (20 tokens esperados)
        tempos = []
        for i in range(3):
            resp = chat_completion([
                {"role": "user", "content": "Diga 'ok' em portugues."}
            ], model=modelo, max_tokens=10)
            if resp.get("content"):
                tempos.append(resp["time"])
        
        if tempos:
            media = sum(tempos) / len(tempos)
            reportar("F4", f"{modelo} - resposta curta (3x)", "PASS",
                    f"Media: {media:.2f}s (min: {min(tempos):.2f}s, max: {max(tempos):.2f}s)", media)
        
        # prompt medio (100+ tokens)
        prompt_medio = "Explique detalhadamente como funciona o sistema de posturas (Impeto, Equilibrio, Guarda) no SPA do MCR. Cite exemplos de uso para cada uma."
        resp = chat_completion([
            {"role": "user", "content": prompt_medio}
        ], model=modelo, max_tokens=300)
        if resp.get("content"):
            reportar("F4", f"{modelo} - resposta media", "PASS",
                    f"{len(resp['content'])} chars em {resp['time']:.1f}s", resp["time"])

# ============================================================
# GERAR RELATORIO
# ============================================================
def gerar_relatorio():
    print("\n" + "=" * 60)
    print("  RELATORIO FINAL")
    print("=" * 60)
    print(f"\n  Total: {PASS+FAIL+WARN} testes")
    print(f"  ✅ PASS: {PASS}")
    print(f"  ❌ FAIL: {FAIL}")
    print(f"  ⚠️  WARN: {WARN}")
    print(f"\n  Acertos: {PASS}/{PASS+FAIL+WARN} ({PASS/(PASS+FAIL+WARN)*100:.0f}%)")
    
    if FAIL > 0:
        print(f"\n  Testes com falha:")
        for r in resultados:
            if r["status"] == "FAIL":
                print(f"    ❌ {r['fase']} - {r['nome']}: {r['detalhes']}")
    
    if WARN > 0:
        print(f"\n  Testes com alerta:")
        for r in resultados:
            if r["status"] == "WARN":
                print(f"    ⚠️  {r['fase']} - {r['nome']}: {r['detalhes']}")
    
    # Salva
    out_path = os.path.join(BASE_DIR, "sandbox", "resultados_modelos.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"resumo": {"total": PASS+FAIL+WARN, "pass": PASS, "fail": FAIL, "warn": WARN},
                   "resultados": resultados}, f, ensure_ascii=False, indent=2)
    print(f"\n  Resultados salvos em: sandbox/resultados_modelos.json")
    print("=" * 60)

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=MODELO_PADRAO, help="Modelo padrao para testes")
    args = parser.parse_args()
    MODELO_PADRAO = args.model
    
    print("=" * 60)
    print(f"  TESTE DE MODELOS LOCAIS")
    print(f"  Modelo padrao: {MODELO_PADRAO}")
    print("=" * 60)
    
    fase1_tool_calling()
    fase2_alucinacao()
    fase3_comparativo()
    fase4_benchmark()
    gerar_relatorio()
