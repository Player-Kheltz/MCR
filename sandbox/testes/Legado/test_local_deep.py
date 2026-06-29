#!/usr/bin/env python3
"""Teste aprofundado de tool calling e alucinacao — modelos locais."""
import json, urllib.request, time, sys, os
sys.path.insert(0, r"E:\Projeto MCR\scripts")

BASE = r"E:\Projeto MCR"

def chat(messages, model="qwen2.5-coder:7b", temperature=0.0, max_tokens=512):
    """API raw do Ollama (/api/chat)."""
    payload = {
        "model": model, "messages": messages,
        "stream": False, "options": {"temperature": temperature, "max_tokens": max_tokens}
    }
    t0 = time.time()
    try:
        req = urllib.request.Request("http://localhost:11434/api/chat",
            data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        dt = time.time() - t0
        msg = data.get("message", {})
        return {"content": msg.get("content", ""), "tool_calls": msg.get("tool_calls", []), "time": dt}
    except Exception as e:
        return {"content": f"[ERRO] {e}", "tool_calls": [], "time": 0}

def chat_openai(messages, model="qwen2.5-coder:7b", tools=None, temperature=0.0):
    """API OpenAI-compativel do Ollama (/v1/chat/completions)."""
    payload = {
        "model": model, "messages": messages,
        "temperature": temperature, "max_tokens": 512, "stream": False
    }
    if tools:
        payload["tools"] = tools
    t0 = time.time()
    try:
        req = urllib.request.Request("http://localhost:11434/v1/chat/completions",
            data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        dt = time.time() - t0
        choice = data.get("choices", [{}])[0]
        msg = choice.get("message", {})
        return {"content": msg.get("content", ""), "tool_calls": msg.get("tool_calls", []), "time": dt}
    except Exception as e:
        return {"content": f"[ERRO] {e}", "tool_calls": [], "time": 0}

tools = [
    {"type": "function", "function": {
        "name": "ler_arquivo",
        "description": "Le o conteudo de um arquivo",
        "parameters": {"type": "object", "properties": {"caminho": {"type": "string"}}, "required": ["caminho"]}
    }},
    {"type": "function", "function": {
        "name": "buscar_codigo",
        "description": "Busca um padrao no codigo",
        "parameters": {"type": "object", "properties": {"padrao": {"type": "string"}}, "required": ["padrao"]}
    }}
]

print("=" * 70)
print("  TESTE APROFUNDADO - MODELOS LOCAIS")
print("=" * 70)

# ============================================
# 1. TOOL CALLING: API OpenAI vs Raw Ollama
# ============================================
print("\n📌 1. TOOL CALLING")
print("-" * 50)

modelos = ["qwen2.5-coder:7b", "deepseek-r1:7b"]

for model in modelos:
    print(f"\n  Modelo: {model}")
    
    # API Raw Ollama
    r1 = chat([
        {"role": "system", "content": "Voce e um assistente que USA FERRAMENTAS. Quando precisar de informacao, responda EXATAMENTE no formato: {\"tool\": \"ler_arquivo\", \"args\": {\"caminho\": \"...\"}}"},
        {"role": "user", "content": "Leia o arquivo AGENTS.md"}
    ], model=model)
    
    has_json = False
    try:
        parsed = json.loads(r1["content"])
        has_json = "tool" in parsed or "name" in parsed
    except:
        pass
    
    status = "✅ JSON tool call" if has_json else "⚠️  resposta textual"
    print(f"    Raw Ollama: {status} ({r1['time']:.1f}s) → {r1['content'][:100]}")
    
    # API OpenAI-compativel
    r2 = chat_openai([
        {"role": "system", "content": "Voce e um assistente que usa ferramentas. Chame a funcao apropriada quando precisar de dados."},
        {"role": "user", "content": "Leia o arquivo E:\\Projeto MCR\\AGENTS.md"}
    ], model=model, tools=tools)
    
    if r2["tool_calls"]:
        tc = r2["tool_calls"][0]
        fn = tc.get("function", {}).get("name", "?")
        print(f"    OpenAI API: ✅ tool_call: {fn} ({r2['time']:.1f}s)")
    elif r2["content"]:
        # Verifica se o conteudo tem JSON de tool call
        has_tc_json = False
        try:
            parsed = json.loads(r2["content"])
            has_tc_json = "name" in parsed or "tool" in parsed
        except:
            pass
        status = "✅ JSON tool call" if has_tc_json else "⚠️  resposta textual"
        print(f"    OpenAI API: {status} ({r2['time']:.1f}s) → {r2['content'][:100]}")
    else:
        print(f"    OpenAI API: ❌ erro ({r2['time']:.1f}s)")

# ============================================
# 2. TESTE DE ALUCINACAO (mais rigido)
# ============================================
print("\n\n📌 2. TESTE DE ALUCINACAO (T2.2 - Funcao falsa)")
print("-" * 50)

# Testa T2.2 especificamente com mais variacoes
testes_alucinacao = [
    {
        "nome": "Funcao falsa (calculateDamageMCR)",
        "prompt": "Como usar a funcao calculateDamageMCR() no codigo do MCR? Explique os parametros.",
        "modelo": "qwen2.5-coder:7b"
    },
    {
        "nome": "Funcao falsa (calculateDamageMCR) - TEMPERATURA 0",
        "prompt": "Como usar a funcao calculateDamageMCR() no codigo do MCR?",
        "modelo": "qwen2.5-coder:7b"
    },
    {
        "nome": "Funcao falsa (addEffect)",
        "prompt": "Qual a diferenca entre addEffect() e sendMagicEffect() no MCR?",
        "modelo": "qwen2.5-coder:7b"
    },
    {
        "nome": "Metodo falso de Player",
        "prompt": "Como usar player:getSpecialLevel() no MCR?",
        "modelo": "qwen2.5-coder:7b"
    },
    {
        "nome": "CONST inexistente",
        "prompt": "O que significa CONST_ME_FIRESWELL?",
        "modelo": "qwen2.5-coder:7b"
    },
]

for t in testes_alucinacao:
    r = chat([
        {"role": "system", "content": "Voce e um assistente do Projeto MCR. Responda APENAS com base no seu conhecimento do codigo real. Se nao tiver certeza se uma funcao existe, diga: 'Nao encontrei essa funcao na base de codigo do MCR.' NUNCA invente APIs ou funcoes."},
        {"role": "user", "content": t["prompt"]}
    ], model=t["modelo"])
    
    content = r["content"].lower()
    recusou = any(p in content for p in ["nao encontrei", "nao existe", "nao tenho", "nao conheco", "nao e uma funcao", "nao faz parte"])
    
    # Verificacao adicional: se explicou PARAMETROS de uma funcao falsa, e alucinacao
    explicou = any(p in content for p in ["parametro", "parametro", "recebe", "retorna"])
    
    if recusou:
        print(f"  ✅ {t['nome']}: RECUSOU → {r['content'][:100]}")
    elif explicou and "calculate" in content or "addEffect" in content or "getSpecialLevel" in content or "FIRESWELL" in content:
        print(f"  ❌ {t['nome']}: ALUCINOU → {r['content'][:120]}")
    else:
        print(f"  ⚠️  {t['nome']:45s} → {r['content'][:100]}")

# ============================================
# 3. TESTE DE CONFIABILIDADE COM RACIOCINIO
# ============================================
print("\n\n📌 3. RACIOCINIO: deepseek-r1:7b vs qwen7b")
print("-" * 50)

perguntas_raciocinio = [
    "Analise o seguinte codigo: local x = 5; local y = x + '10'; print(y). Ha algum erro? Se sim, qual?",
    "Se um jogador tem nivel 50 e ganha 10% de XP bonus, quantos niveis ele precisa para chegar ao 55 se cada nivel requer 1000 XP?",
]

for pergunta in perguntas_raciocinio:
    for model in ["qwen2.5-coder:7b", "deepseek-r1:7b"]:
        r = chat([
            {"role": "system", "content": "Responda de forma precisa e concisa."},
            {"role": "user", "content": pergunta}
        ], model=model, max_tokens=512)
        print(f"  [{model}] ({r['time']:.1f}s): {r['content'][:100]}")

print("\n" + "=" * 70)
print("  TESTE CONCLUIDO")
print("=" * 70)
