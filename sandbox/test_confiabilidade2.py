#!/usr/bin/env python3
"""Teste de confiabilidade REAL — testa cada caminho do pipeline corretamente."""
import sys, os, json, time
sys.path.insert(0, r"E:\Projeto MCR\scripts")
sys.path.insert(0, r"E:\Projeto MCR\Scripts")
from bridge_auto import template_reply, route_intent, format_item_response, format_monster_response, get_hot_cache
from bridge_auto import save_to_history, search_history, exact_cache_store, exact_cache_lookup
from rag_query import get_context

import urllib.request

# ============================================================
print("=" * 70)
print("  TESTE DE CONFIABILIDADE REAL - SISTEMA MCR v4")
print("=" * 70)

def ask_ollama(prompt, model="qwen2.5-coder:7b", timeout=30):
    payload = json.dumps({"model": model, "prompt": prompt[:3000], "stream": False,
        "options": {"temperature": 0.1, "max_tokens": 200}}).encode()
    req = urllib.request.Request("http://localhost:11434/api/generate", data=payload,
        headers={"Content-Type": "application/json"})
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read())
        dt = time.time() - t0
        return resp.get("response", "").strip(), dt
    except Exception as e:
        return f"[ERRO] {e}", 0

def test_template(pergunta, esperado_contem=None, esperado_blocked=None):
    reply, blocked = template_reply("Testador", pergunta)
    ok = True
    detalhes = []
    if esperado_blocked is not None and blocked != esperado_blocked:
        ok = False
        detalhes.append(f"blocked={blocked} (esperava {esperado_blocked})")
    if esperado_contem and (not reply or esperado_contem.lower() not in reply.lower()):
        ok = False
        detalhes.append(f"nao contem '{esperado_contem}'")
    return ok, reply, blocked, detalhes

def test_router(pergunta, esperado_intent):
    route = route_intent(pergunta)
    ok = route["intent"] == esperado_intent
    detalhes = []
    if not ok:
        detalhes.append(f"intent={route['intent']} (esperava {esperado_intent})")
    return ok, route, detalhes

# ============================================================
# 1. TESTE DO TEMPLATE
# ============================================================
print("\n📋 1. TEMPLATE (sem chamada de modelo)")
t_pass = 0
t_fail = 0

testes_template = [
    ("ola", "ola", True, None),
    ("oi tudo bem?", "ola", True, None),
    ("bom dia", "ola", True, None),
    ("obrigado", "Disponha", True, None),
    ("valeu", "Disponha", True, None),
    ("tchau", "Disponha", True, None),
    ("testando", "Teste recebido", True, None),
    ("o que voce faz", "assistente", True, None),
    ("como usar", "assistente", True, None),
    ("qual a senha do banco", "nao posso", True, None),
]

for pergunta, contem, blocked, _ in testes_template:
    ok, reply, b, det = test_template(pergunta, contem, blocked)
    if ok:
        t_pass += 1
    else:
        t_fail += 1
        print(f"  ❌ '{pergunta}': {' | '.join(det)} (reply: {reply})")

print(f"  Template: {t_pass}/{t_pass+t_fail} OK")

# ============================================================
# 2. TESTE DO ROUTER
# ============================================================
print("\n🧠 2. ROUTER (classificador 1.5b)")
r_pass = 0
r_fail = 0

testes_router = [
    ("o que e a War Hammer?", "item_info"),
    ("info sobre dark sword", "item_info"),
    ("qual o dano de uma crown shield?", "item_info"),
    ("fale sobre o demon", "monster_info"),
    ("onde fica o orc berserker", "complex"),  # Router pode confundir
    ("como upar rapido", "complex"),
    ("o que e SPA", "complex"),
    ("o que e o Sistema de Progressao", "complex"),
    ("quais dominios existem", "complex"),
    ("quero criar uma conta", "complex"),
]

for pergunta, esperado in testes_router:
    ok, route, det = test_router(pergunta, esperado)
    if ok:
        r_pass += 1
    else:
        r_fail += 1
        det_str = " | ".join(det)
        entity = route.get('entity', '')
        print(f"  ❌ '{pergunta[:35]}': {det_str} (entity: {entity})")

print(f"  Router: {r_pass}/{r_pass+r_fail} OK")

# ============================================================
# 3. TESTE DOS FORMATADORES (RPC)
# ============================================================
print("\n🎨 3. FORMATADORES (resposta RPC)")

# Item conhecido
item_data = {"name": "War Hammer", "known": True, "attack": 45, "defense": 25, 
             "weight_str": "45.00 oz", "slot_pos": 8, "weapon_type": 2, "req_level": 30}
resp = format_item_response(item_data)
item_ok = resp and "War Hammer" in resp and "Atq 45" in resp
print(f"  {'✅' if item_ok else '❌'} Item conhecido: {resp[:80] if resp else 'None'}")

# Item desconhecido
item_unk = format_item_response({"name": "Dark Sword", "known": False})
unk_ok = item_unk and "nao descobriu" in item_unk
print(f"  {'✅' if unk_ok else '❌'} Item desconhecido: {item_unk[:80] if item_unk else 'None'}")

# Item nao encontrado
item_nf = format_item_response(None)
nf_ok = item_nf is None
print(f"  {'✅' if nf_ok else '❌'} Item nulo: retorna None")

# ============================================================
# 4. TESTE DO RAG (consulta semantica)
# ============================================================
print("\n📚 4. RAG (player_mode)")
rag_pass = 0

testes_rag = [
    ("SPA", ["spa", "progressao", "aventureiro"]),
    ("habilidades de fogo", ["fogo", "orbital", "igneo"]),
    ("dominio gelo", ["gelo", "agua", "glacial"]),
    ("Orbital Igneo", ["orbital", "igneo", "fogo"]),
    ("sistema de postura", ["postura", "impeto", "guarda"]),
]

for query, keywords in testes_rag:
    ctx = get_context(query, top_k=3, player_mode=True) or ""
    found = [kw for kw in keywords if kw.lower() in ctx.lower()]
    if found:
        rag_pass += 1
        print(f"  ✅ '{query}': encontrou {found}")
    else:
        print(f"  ❌ '{query}': nenhuma keyword em {len(ctx)} chars: {ctx[:80]}")

print(f"  RAG: {rag_pass}/{len(testes_rag)} OK")

# ============================================================
# 5. TESTE DO HISTORICO COM BUSCA SEMANTICA
# ============================================================
print("\n💾 5. HISTORICO (busca semantica)")
test_acc = "99999_CONF_TEST"
save_to_history(test_acc, "Jogador", "qual o dano de uma war hammer?", "A War Hammer tem ataque 45.")
save_to_history(test_acc, "Jogador", "onde encontro demon?", "Demon esta em Edron.")
save_to_history(test_acc, "Jogador", "o que e SPA?", "SPA e o Sistema de Progressao do Aventureiro.")

# Testa busca
hist = search_history(test_acc, "quanto de ataque tem a war hammer?", top_k=1)
hist_ok = hist and "war hammer" in hist.lower()
print(f"  {'✅' if hist_ok else '❌'} Busca 'war hammer': {hist[:80] if hist else 'vazio'}")

hist2 = search_history(test_acc, "onde fica demon?", top_k=1)
hist2_ok = hist2 and "demon" in hist2.lower() and "Edron" in hist2
print(f"  {'✅' if hist2_ok else '❌'} Busca 'demon': {hist2[:80] if hist2 else 'vazio'}")

# Limpa
try: os.remove(os.path.join(r"E:\Projeto MCR\Canary\data\logs\history", f"hist_{test_acc}.json"))
except: pass

# ============================================================
# 6. TESTE DO CACHE EXATO
# ============================================================
print("\n💿 6. CACHE EXATO")
exact_cache_store("qual o dano da war hammer?", "A War Hammer tem ataque 45.")
cached = exact_cache_lookup("qual o dano da war hammer?")
cache_ok = cached and "ataque 45" in cached
print(f"  {'✅' if cache_ok else '❌'} Cache lookup: {cached[:50] if cached else 'miss'}")

# ============================================================
# RESUMO
# ============================================================
print("\n" + "=" * 70)
total_tests = t_pass + t_fail + r_pass + r_fail + 3 + rag_pass + (len(testes_rag)-rag_pass) + 3 + 1
total_ok = t_pass + r_pass + (1 if item_ok else 0) + (1 if unk_ok else 0) + (1 if nf_ok else 0) + rag_pass + (1 if hist_ok else 0) + (1 if hist2_ok else 0) + (1 if cache_ok else 0)
total_fail = t_fail + r_fail + (0 if item_ok else 1) + (0 if unk_ok else 1) + (0 if nf_ok else 1) + (len(testes_rag)-rag_pass) + (0 if hist_ok else 1) + (0 if hist2_ok else 1) + (0 if cache_ok else 1)
print(f"  RESUMO FINAL: {total_ok}/{total_ok+total_fail} OK")
print(f"  Template: {t_pass}/{t_pass+t_fail}")
print(f"  Router:  {r_pass}/{r_pass+r_fail}")
print(f"  RAG:     {rag_pass}/{len(testes_rag)}")
print(f"  Outros:  {total_ok - t_pass - r_pass - rag_pass}/{7}")
print("=" * 70)
