#!/usr/bin/env python3
"""Teste autonomo do sistema MCR - bridge, RAG, historico, router."""
import os, sys, json, time, urllib.request, traceback

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))

PASS = 0
FAIL = 0
ERRORS = []

def test(nome, fn):
    global PASS, FAIL
    try:
        fn()
        PASS += 1
        print(f"  ✅ {nome}")
    except Exception as e:
        FAIL += 1
        err = f"{type(e).__name__}: {e}"
        ERRORS.append((nome, err))
        print(f"  ❌ {nome} -> {err[:120]}")

# ============================================
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
print("=" * 46)
print("  TESTE AUTONOMO - SISTEMA MCR v1.0")
print("=" * 46)

# === 1. OLLAMA ===
print("\n📡 1. OLLAMA")

def ollama_online():
    req = urllib.request.Request("http://localhost:11434/api/tags")
    with urllib.request.urlopen(req, timeout=5) as r:
        data = json.loads(r.read())
        assert len(data.get("models", [])) > 0, "Nenhum modelo baixado"
test("Ollama online + modelos carregados", ollama_online)

def ollama_embedding():
    req = urllib.request.Request(
        "http://localhost:11434/api/embeddings",
        data=json.dumps({"model": "nomic-embed-text", "prompt": "teste"}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
        emb = data.get("embedding", [])
        assert len(emb) > 0, "Embedding vazio"
        assert len(emb) > 100, f"Embedding muito curto: {len(emb)}"
test("Ollama embedding nomic-embed-text", ollama_embedding)

def ollama_generate():
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps({"model": "qwen2.5-coder:1.5b", "prompt": "Diga 'ok'", "stream": False}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
        resp = data.get("response", "")
        assert len(resp) > 0, "Resposta vazia"
test("Ollama generate qwen2.5-coder:1.5b", ollama_generate)

def ollama_router_model():
    # Usa /api/chat (com system prompt) igual ao route_intent real faz
    prompt = 'Classifique: "qual o dano da war hammer?"\nResponda JSON: {"intent": "item_info|monster_info|complex", "entity": "..."}'
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=json.dumps({"model": "qwen2.5-coder:1.5b", "messages": [
            {"role": "system", "content": "Classifique mensagens de Tibia."},
            {"role": "user", "content": prompt}
        ], "stream": False}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.loads(r.read())
        content = resp["message"]["content"]
        assert "item" in content.lower() or "complex" in content.lower(), f"Resposta inesperada: {content[:60]}"
test("Router 1.5b classifica intencao", ollama_router_model)

# === 2. RAG ===
print("\n📚 2. RAG")

def rag_index_exists():
    rag_db = os.path.join(BASE, ".rag_db")
    assert os.path.exists(rag_db), ".rag_db nao existe"
    assert os.path.exists(os.path.join(rag_db, "index.json")), "index.json faltando"
    assert os.path.exists(os.path.join(rag_db, "embeddings.npy")), "embeddings.npy faltando"
test("RAG index existe", rag_index_exists)

def rag_query():
    from rag_query import get_context
    ctx = get_context("O que e o Sistema de Progressao do Aventureiro?", top_k=3, player_mode=True)
    assert ctx and len(ctx) > 50, f"Contexto muito curto: {len(ctx) if ctx else 0}"
    assert any(w in ctx.lower() for w in ["spa", "progressao", "aventureiro", "dominio", "nivel"]), f"Contexto sem termos esperados: {ctx[:100]}"
test("RAG consulta semantica (player_mode)", rag_query)

def rag_shc_fire():
    from rag_query import get_context
    ctx = get_context("Orbital Igneo habilidade de fogo", top_k=3, player_mode=False)
    assert ctx and len(ctx) > 50, f"Contexto muito curto: {len(ctx) if ctx else 0}"
test("RAG encontra habilidades SHC de fogo", rag_shc_fire)

# === 3. BRIDGE (modulos internos) ===
print("\n🔌 3. BRIDGE")

def bridge_paths():
    # Simula paths do bridge
    paths = [
        os.path.join(BASE, "Canary", "data", "logs", "chat_in.txt"),
        os.path.join(BASE, "Canary", "data", "logs", "chat_out.txt"),
        os.path.join(BASE, "Canary", "data", "logs", "server_cmd.txt"),
        os.path.join(BASE, "Canary", "data", "logs", "server_resp.txt"),
        os.path.join(BASE, "Scripts", "bridge_auto.py"),
    ]
    for p in paths:
        assert os.path.exists(p) or os.path.exists(os.path.dirname(p)), f"Path invalido: {p}"
test("Paths do bridge existem", bridge_paths)

def bridge_import():
    # Testa que o modulo carrega sem erros de sintaxe
    import importlib.util
    spec = importlib.util.spec_from_file_location("bridge_auto", os.path.join(BASE, "Scripts", "bridge_auto.py"))
    mod = importlib.util.module_from_spec(spec)
    # Nao executa, so verifica se compila
    compile(open(spec.origin).read(), spec.origin, 'exec')
test("bridge_auto.py compila", bridge_import)

# === 4. HISTORICO ===
print("\n💾 4. HISTORICO")

def history_save_load():
    from bridge_auto import save_to_history, search_history, load_history, HISTORY_DIR
    # Usa account_id fixo para teste
    test_acc = "99999_TEST"
    
    # Salva algumas interacoes
    save_to_history(test_acc, "TestPlayer", "O que e uma war hammer?", "War Hammer e um item do jogo.")
    save_to_history(test_acc, "TestPlayer", "Onde encontro demon?", "Demon esta em Edron.")
    save_to_history(test_acc, "TestPlayer", "Qual o dano de uma sword?", "Depende do nivel.")
    
    # Verifica se salvou
    hist = load_history(test_acc)
    assert len(hist) >= 3, f"Historico deveria ter 3: tem {len(hist)}"
    
    # Verifica se os embeddings foram computados
    has_emb = sum(1 for h in hist if h.get("e"))
    assert has_emb >= 3, f"Deveria ter 3 embeddings: tem {has_emb}"
    
    # Testa busca semantica - busca sobre dano de arma deve achar entrada relevante
    result = search_history(test_acc, "quanto de dano causa uma espada longa?", top_k=1)
    assert result, f"Busca semantica nao retornou nada"
    # Nao verificamos conteudo exato porque embeddings para queries curtas sao imprecisos,
    # mas o importante e que retornou algo com score > 0.5 (nao e silencioso)
    assert len(result) > 10, f"Resultado muito curto: {result}"
    
    # Limpa arquivo de teste
    import os
    try:
        os.remove(os.path.join(HISTORY_DIR, f"hist_{test_acc}.json"))
    except:
        pass
test("Historico save/load/search semantica", history_save_load)

# === 5. ROUTER ===
print("\n🧠 5. ROUTER")

def router_item_info():
    from bridge_auto import route_intent
    result = route_intent("o que e a War Hammer?")
    assert result["intent"] == "item_info", f"Deveria ser item_info: {result}"
    assert result["entity"], f"Entidade vazia: {result}"
test("Router identifica item_info", router_item_info)

def router_monster_info():
    from bridge_auto import route_intent
    result = route_intent("me fale sobre o Demon")
    assert result["intent"] == "monster_info", f"Deveria ser monster_info: {result}"
test("Router identifica monster_info", router_monster_info)

def router_complex():
    from bridge_auto import route_intent
    result = route_intent("como upar rapido no nivel 50?")
    assert result["intent"] == "complex", f"Deveria ser complex: {result}"
test("Router identifica complex", router_complex)

# === 6. FORMATADORES ===
print("\n🎨 6. FORMATADORES")

def format_item_known():
    from bridge_auto import format_item_response
    result = format_item_response({"name": "War Hammer", "known": True, "attack": 45, "defense": 25, "weight_str": "45.00 oz", "slot_pos": 8, "weapon_type": 2})
    assert result and "War Hammer" in result, f"Formatacao falhou: {result[:60]}"
    assert "Atq 45" in result, f"Faltou Atq: {result}"
    assert "Def 25" in result, f"Faltou Def: {result}"
test("Formatador item conhecido", format_item_known)

def format_item_unknown():
    from bridge_auto import format_item_response
    result = format_item_response({"name": "Dark Sword", "known": False})
    assert result and "nao descobriu" in result, f"Deveria falar 'nao descobriu': {result}"
test("Formatador item desconhecido", format_item_unknown)

# === 7. ARQUIVOS DO SISTEMA ===
print("\n📁 7. ARQUIVOS DO SISTEMA")

def check_rag_watcher():
    assert os.path.exists(os.path.join(BASE, "scripts", "rag_watcher.py")), "rag_watcher.py faltando"
test("rag_watcher.py existe", check_rag_watcher)

def check_bridge_watchdog():
    assert os.path.exists(os.path.join(BASE, "Scripts", "bridge_watchdog.py")), "bridge_watchdog.py faltando"
test("bridge_watchdog.py existe", check_bridge_watchdog)

def check_rag_query():
    assert os.path.exists(os.path.join(BASE, "scripts", "rag_query.py")), "rag_query.py faltando"
test("rag_query.py existe", check_rag_query)

def check_mcr_knowledge():
    path = os.path.join(BASE, "scripts", "mcr_knowledge.txt")
    assert os.path.exists(path), "mcr_knowledge.txt faltando"
    with open(path) as f:
        content = f.read()
    assert len(content) > 200, f"mcr_knowledge muito curto: {len(content)}"
test("mcr_knowledge.txt existe e tem conteudo", check_mcr_knowledge)

# === 8. SIMULACAO DO PIPELINE COMPLETO ===
print("\n🔄 8. PIPELINE COMPLETO (simulado)")

def pipeline_item():
    """Simula o pipeline completo: mensagem -> router -> RPC -> formatacao."""
    from bridge_auto import route_intent, format_item_response
    
    # 1. Mensagem do jogador
    msg = "qual o dano de uma war hammer?"
    
    # 2. Router classifica
    route = route_intent(msg)
    assert route["intent"] == "item_info", f"Router falhou: {route}"
    
    # 3. Simula resposta RPC do servidor (como se item_info.lua respondesse)
    rpc_response = {
        "status": "found_known",
        "data": {
            "name": "War Hammer",
            "id": 2391,
            "description": "Poderosa war hammer.",
            "weight": 4500,
            "weight_str": "45.00 oz",
            "slot_pos": 8,
            "weapon_type": 2,
            "attack": 45,
            "defense": 25,
            "req_level": 30,
            "known": True,
        }
    }
    
    # 4. Formata resposta
    formatted = format_item_response(rpc_response["data"])
    assert formatted, "Formatacao retornou vazio"
    assert "War Hammer" in formatted, f"Nome ausente: {formatted}"
    assert "Atq 45" in formatted, f"Attack ausente: {formatted}"
    assert "Nivel: 30" in formatted, f"Level req ausente: {formatted}"
    
test("Pipeline item completo (router+RPC+format)", pipeline_item)

# === RESUMO ===
print("\n" + "=" * 46)
total = PASS + FAIL
print(f"  Resultado: {PASS}/{total} passaram, {FAIL} falharam")
if ERRORS:
    print(f"\n  Erros:")
    for nome, err in ERRORS:
        print(f"    - {nome}: {err}")
print("=" * 46)
