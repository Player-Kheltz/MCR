#!/usr/bin/env python3
"""Benchmark do sistema MCR — mede consumo, tempo e caminho de cada query."""
import sys, os, json, time, urllib.request, hashlib

sys.path.insert(0, r"E:\Projeto MCR\scripts")
sys.path.insert(0, r"E:\Projeto MCR\Scripts")

REPORT = {"antes": {}, "depois": {}}
MODE = os.environ.get("MODE", "antes")  # 'antes' ou 'depois'

# ============================================================
# QUERIES DE TESTE (cobrem todos os caminhos do pipeline)
# ============================================================
QUERIES = [
    # (id, pergunta, categoria, expected_behavior)
    ("saudacao_1", "ola", "template", "template"),
    ("saudacao_2", "oi tudo bem?", "template", "template"),
    ("agradecimento", "obrigado", "template", "template"),
    ("teste", "testando o sistema", "template", "template"),
    ("senha", "qual a senha do banco?", "bloqueado", "template_blocked"),
    ("item_1", "o que e a War Hammer?", "item_info", "router_rpc"),
    ("item_2", "info sobre dark sword", "item_info", "router_rpc"),
    ("item_3", "qual o dano de uma crown shield?", "item_info", "router_rpc"),
    ("monster_1", "fale sobre o demon", "monster_info", "router_rpc"),
    ("monster_2", "o que e dragon?", "monster_info", "router_rpc"),
    ("complex_1", "como upar rapido no nivel 50?", "complex", "ia"),
    ("complex_2", "o que e o Sistema de Progressao do Aventureiro?", "complex", "ia"),
    ("complex_3", "como funciona o sistema de habilidades?", "complex", "ia"),
    ("complex_4", "onde fica a cidade de Eridanus?", "complex", "ia"),
    ("complex_5", "quais dominios elementais existem?", "complex", "ia"),
    ("historico", "qual o dano de uma espada?", "complex", "ia"),
]

# ============================================================
# FUNCOES DE MEDICAO
# ============================================================

def count_tokens(text):
    """Estimativa simples: ~4 chars por token em portugues."""
    return len(text) // 4

def simulate_template(msg):
    """Simula o template_reply sem importar o bridge."""
    m = msg.lower().strip()
    if any(w in m for w in ["senha", "password", "usuario", "user", "login", "credential"]):
        return "Nao posso fornecer informacoes de acesso.", True
    if m in ("ola", "oi", "oie", "hey", "hello"):
        return "Ola! Sou o assistente MCR.", False
    if "teste" in m or "testando" in m:
        return "Teste recebido! Sistema funcionando.", False
    if "obrigado" in m or "valeu" in m or "brigado" in m:
        return "Disponha!", False
    return None, False  # Nao encaixou em template

def simulate_router(msg):
    """Chama o router real para classificar."""
    try:
        from bridge_auto import route_intent
        return route_intent(msg)
    except Exception as e:
        return {"intent": "complex", "entity": ""}

def simulate_rag(msg):
    """Chama RAG e mede."""
    try:
        from rag_query import get_context
        t0 = time.time()
        ctx = get_context(msg, top_k=5, player_mode=True)
        dt = time.time() - t0
        return ctx or "", dt
    except Exception:
        return "", 0

def simulate_ai(prompt):
    """Chama Ollama 1.5b (mais rapido que 7b para benchmark)."""
    try:
        payload = json.dumps({"model": "qwen2.5-coder:1.5b", "prompt": prompt[:1500], "stream": False,
            "options": {"temperature": 0.1, "max_tokens": 100}}).encode()
        req = urllib.request.Request("http://localhost:11434/api/generate", data=payload,
            headers={"Content-Type": "application/json"})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        dt = time.time() - t0
        return data.get("response", "").strip(), dt
    except Exception as e:
        return f"[ERRO] {e}", 0

# ============================================================
# EXECUTA BENCHMARK
# ============================================================

print("=" * 70)
print(f"  BENCHMARK - MODO: {MODE.upper()}")
print("=" * 70)

results = []
total_time = 0
total_tokens_input = 0
total_tokens_output = 0
total_model_calls = 0
template_hits = 0
router_hits = 0
ai_calls = 0
rpc_attempts = 0

for qid, pergunta, categoria, esperado in QUERIES:
    r = {"id": qid, "pergunta": pergunta, "categoria": categoria, "caminho": "", 
         "tempo": 0, "tokens_input": 0, "tokens_output": 0, "model_calls": 0, "resposta": ""}
    
    t_total = time.time()
    
    # 1. TEMPLATE (sempre executado primeiro)
    templ_resp, blocked = simulate_template(pergunta)
    
    if blocked:
        r["caminho"] = "template_blocked"
        r["resposta"] = templ_resp
        r["tempo"] = time.time() - t_total
        template_hits += 1
        results.append(r)
        continue
    
    if templ_resp:
        # Template respondeu sem precisar de IA
        r["caminho"] = "template"
        r["resposta"] = templ_resp
        r["tempo"] = time.time() - t_total
        template_hits += 1
        results.append(r)
        continue
    
    # 2. ROUTER (chama 1.5b)
    route = simulate_router(pergunta)
    r["model_calls"] += 1
    total_model_calls += 1
    
    if route["intent"] in ("item_info", "monster_info") and route.get("entity"):
        r["caminho"] = "router_rpc"
        router_hits += 1
        rpc_attempts += 1
        r["resposta"] = f"[{route['intent']}] Entity: {route['entity']}"
        r["tempo"] = time.time() - t_total
        results.append(r)
        continue
    
    # 3. RAG + AI
    r["caminho"] = "ia"
    ai_calls += 1
    
    # RAG
    rag_ctx, rag_time = simulate_rag(pergunta)
    
    # Monta prompt (simplificado)
    prompt = f"Pergunta: {pergunta}\nContexto: {rag_ctx[:500]}\nResposta curta:"
    
    # AI call
    ai_resp, ai_time = simulate_ai(prompt)
    r["model_calls"] += 1
    total_model_calls += 1
    r["tokens_input"] = count_tokens(prompt)
    r["tokens_output"] = count_tokens(ai_resp)
    r["tempo"] = time.time() - t_total
    r["resposta"] = ai_resp[:100]
    r["rag_time"] = rag_time
    r["ai_time"] = ai_time
    
    total_tokens_input += r["tokens_input"]
    total_tokens_output += r["tokens_output"]
    
    results.append(r)

# ============================================================
# RELATORIO
# ============================================================

print(f"\n{'─' * 70}")
print(f"  RESUMO DO BENCHMARK ({MODE.upper()})")
print(f"{'─' * 70}")
print(f"  Total de queries:          {len(results)}")
print(f"  Template hits:             {template_hits}  ({template_hits/len(results)*100:.0f}%)")
print(f"  Router -> RPC:             {router_hits}  ({router_hits/len(results)*100:.0f}%)")
print(f"  AI calls (1.5b):           {ai_calls}  ({ai_calls/len(results)*100:.0f}%)")
print(f"  Total model calls:         {total_model_calls}")
print(f"  Total tokens input:        {total_tokens_input}")
print(f"  Total tokens output:       {total_tokens_output}")
print(f"{'─' * 70}")

print(f"\n{'─' * 70}")
print(f"  DETALHAMENTO POR QUERY")
print(f"{'─' * 70}")
print(f"  {'ID':<20} {'CATEGORIA':<14} {'CAMINHO':<20} {'TOKENS':<8} {'TEMPO':<8}")
print(f"  {'─' * 20} {'─' * 14} {'─' * 20} {'─' * 8} {'─' * 8}")
for r in results:
    tokens = r["tokens_input"] + r["tokens_output"]
    tempo = f"{r['tempo']:.2f}s"
    print(f"  {r['id']:<20} {r['categoria']:<14} {r['caminho']:<20} {tokens:<8} {tempo:<8}")

# Salva resultados para comparacao
out = {
    "mode": MODE,
    "timestamp": time.time(),
    "summary": {
        "total_queries": len(results),
        "template_hits": template_hits,
        "router_hits": router_hits,
        "ai_calls": ai_calls,
        "total_model_calls": total_model_calls,
        "total_tokens_input": total_tokens_input,
        "total_tokens_output": total_tokens_output,
    },
    "results": results
}

report_path = os.path.join(r"E:\Projeto MCR\sandbox", f"benchmark_{MODE}.json")
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n  Relatorio salvo: {report_path}")
print(f"{'─' * 70}")
