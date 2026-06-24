#!/usr/bin/env python3
"""Benchmark REAL — testa o bridge_auto.py de verdade."""
import sys, os, json, time

sys.path.insert(0, r"E:\Projeto MCR\scripts")
sys.path.insert(0, r"E:\Projeto MCR\Scripts")

# Importa as funcoes REAIS do bridge
from bridge_auto import template_reply, route_intent, exact_cache_store, exact_cache_lookup, get_hot_cache
from bridge_auto import format_item_response, format_monster_response

QUERIES = [
    ("saudacao_1", "ola", "template"),
    ("saudacao_2", "oi tudo bem?", "template"),
    ("saudacao_3", "bom dia", "template"),
    ("agradecimento", "obrigado", "template"),
    ("despedida", "tchau", "template"),
    ("teste", "testando o sistema", "template"),
    ("ajuda", "o que voce faz?", "template"),
    ("senha", "qual a senha do banco?", "bloqueado"),
    ("item_1", "o que e a War Hammer?", "item_info"),
    ("item_2", "info sobre dark sword", "item_info"),
    ("monstro_1", "fale sobre o demon", "monster_info"),
    ("complex_1", "como upar rapido no nivel 50?", "complex"),
    ("complex_2", "o que e o sistema de progressao?", "complex"),
    ("complex_3", "quais dominios elementais existem?", "complex"),
    ("avaliacao", "esse assistente e muito util obrigado", "template"),
]

print("=" * 70)
print("  BENCHMARK REAL - bridge_auto.py v4")
print("=" * 70)

results = []
template_hits = 0
router_calls = 0
ai_fallbacks = 0
blocked_count = 0
total_model_calls = 0

for qid, pergunta, esperado in QUERIES:
    r = {"id": qid, "pergunta": pergunta, "esperado": esperado}
    t0 = time.time()
    
    # PASSO 1: Template
    reply, blocked = template_reply("Testador", pergunta)
    
    if blocked:
        r["caminho"] = "template_blocked"
        r["resposta"] = reply
        r["tempo"] = time.time() - t0
        r["model_calls"] = 0
        blocked_count += 1
        results.append(r)
        continue
    
    if reply:
        r["caminho"] = "template"
        r["resposta"] = reply
        r["tempo"] = time.time() - t0
        r["model_calls"] = 0
        template_hits += 1
        results.append(r)
        continue
    
    # PASSO 2: Router (chama 1.5b)
    route = route_intent(pergunta)
    router_calls += 1
    total_model_calls += 1
    
    if route["intent"] in ("item_info", "monster_info") and route.get("entity"):
        r["caminho"] = f"router_{route['intent']}"
        r["entity"] = route["entity"]
        r["resposta"] = f"[Router -> {route['intent']}] Entity: {route['entity']}"
        r["tempo"] = time.time() - t0
        r["model_calls"] = 1
        results.append(r)
        continue
    
    # PASSO 3: AI (1.5b para teste)
    r["caminho"] = "ia"
    r["resposta"] = "[simulado] IA seria chamada aqui"
    r["tempo"] = time.time() - t0
    r["model_calls"] = 1
    ai_fallbacks += 1
    results.append(r)

# ============================================================
print(f"\n{'─' * 70}")
print(f"  RESULTADOS")
print(f"{'─' * 70}")
print(f"  {'ID':<20} {'ESPERADO':<14} {'CAMINHO':<20} {'TEMPO':<8} {'MODEL':<6}")
print(f"  {'─' * 20} {'─' * 14} {'─' * 20} {'─' * 8} {'─' * 6}")
for r in results:
    tempo = f"{r['tempo']*1000:.0f}ms"
    calls = r.get("model_calls", 0)
    print(f"  {r['id']:<20} {r['esperado']:<14} {r['caminho']:<20} {tempo:<8} {calls:<6}")

print(f"\n{'─' * 70}")
print(f"  RESUMO")
print(f"{'─' * 70}")
print(f"  Total:               {len(results)}")
print(f"  Template (sem modelo): {template_hits + blocked_count}  ({(template_hits+blocked_count)/len(results)*100:.0f}%)")
print(f"    → Saudacoes/ajuda:   {template_hits}")
print(f"    → Bloqueados:        {blocked_count}")
print(f"  Router (1.5b):        {router_calls}  ({router_calls/len(results)*100:.0f}%)")
print(f"  AI (1.5b+):           {ai_fallbacks}  ({ai_fallbacks/len(results)*100:.0f}%)")
print(f"  Total model calls:    {total_model_calls}")
print(f"{'─' * 70}")

# Salva
out = {"mode": "pos_otimizacao", "timestamp": time.time(), "results": results,
       "summary": {"total": len(results), "template": template_hits+blocked_count, 
                   "router": router_calls, "ai": ai_fallbacks, "model_calls": total_model_calls}}
with open(r"E:\Projeto MCR\sandbox\benchmark_real.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n  Salvo: sandbox/benchmark_real.json")
print(f"{'─' * 70}")
