#!/usr/bin/env python3
"""bridge_auto.py v4 — Bridge com RAG + cache quente + anti-alucinacao."""

import os, sys, time, json, threading, queue, traceback, urllib.request, re

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
CANARY_DIR = os.path.join(BASE_DIR, "Canary")
CHAT_IN = os.path.join(CANARY_DIR, "data", "logs", "chat_in.txt")
CHAT_OUT = os.path.join(CANARY_DIR, "data", "logs", "chat_out.txt")
PENDING = os.path.join(BASE_DIR, "bridge_pending.txt")
RESPONSE = os.path.join(BASE_DIR, "bridge_response.txt")
LOG_FILE = os.path.join(BASE_DIR, "bridge_debug.log")
KNOWLEDGE_FILE = os.path.join(SCRIPTS_DIR, "mcr_knowledge.txt")
HOT_CACHE_FILE = os.path.join(BASE_DIR, ".rag_hot.json")
HISTORY_DIR = os.path.join(CANARY_DIR, "data", "logs", "history")

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5-coder:7b"
OLLAMA_MODEL_FALLBACK = "deepseek-coder:6.7b"
OLLAMA_MODEL_ROUTER = "qwen2.5-coder:1.5b"
OLLAMA_TIMEOUT = 15
OLLAMA_TIMEOUT_FALLBACK = 20  # deepseek-coder e mais lento, precisa de mais timeout
OLLAMA_TIMEOUT_ROUTER = 8    # router 1.5B responde rapido, mas damos margem

# RPC paths (comunicacao bridge ↔ servidor)
SERVER_CMD = os.path.join(CANARY_DIR, "data", "logs", "server_cmd.txt")
SERVER_RESP = os.path.join(CANARY_DIR, "data", "logs", "server_resp.txt")
RPC_POLL_INTERVAL = 0.1  # 100ms entre polls
RPC_TIMEOUT = 4.0  # timeout total para RPC

# Stopwords em portugues para filtro do cache quente
STOPWORDS = {
    "o", "a", "de", "da", "do", "em", "para", "com", "que", "e", "é",
    "um", "uma", "os", "as", "no", "na", "se", "por", "ao", "aos",
    "das", "dos", "num", "não", "nao", "sim", "mas", "mais", "como",
    "ja", "muito", "eu", "tu", "ele", "ela", "nos", "vos", "eles",
    "elas", "me", "te", "se", "lhe", "lhes", "seu", "sua", "seus", "suas",
    "esta", "este", "esse", "essa", "isso", "isto", "aqui", "ali", "la",
    "ate", "apos", "antes", "entre", "sob", "sobre", "sem", "dentro", "fora",
    "ser", "ter", "haver", "fazer", "dizer", "poder", "saber", "dever",
    "querer", "vir", "ir", "dar", "deixar", "passar", "ficar", "entrar",
    "sair", "criar", "usar", "ter", "sua", "voce", "vc", "vou"
}

# --- Sistema de historico por conta (busca semantica) ---
# Em vez de jogar o historico bruto no prompt (que estoura 32k tokens),
# indexamos por embedding e so retornamos as mensagens relevantes.

HISTORY_MAX_STORED = 50   # max mensagens armazenadas por conta
HISTORY_SEARCH_TOP_K = 2  # quantas mensagens retornar na busca

EMBED_CACHE = {}  # {(account_id, idx): [embedding]}

def ensure_history_dir():
    os.makedirs(HISTORY_DIR, exist_ok=True)

def history_path(account_id):
    return os.path.join(HISTORY_DIR, f"hist_{account_id}.json")

def _get_embedding(text):
    """Chama Ollama embedding API. Retorna lista de floats ou None."""
    if not text or not text.strip():
        return None
    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/embeddings",
            data=json.dumps({"model": "nomic-embed-text", "prompt": text[:512]}).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return data.get("embedding")
    except Exception:
        return None

def _cosine_similarity(a, b):
    if not a or not b:
        return 0
    dot = sum(x*y for x, y in zip(a, b))
    na = sum(x*x for x in a) ** 0.5
    nb = sum(x*x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0
    return dot / (na * nb)

def load_history(account_id):
    """Carrega historico completo da conta."""
    if not account_id:
        return []
    path = history_path(account_id)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

def save_to_history(account_id, player, msg, reply):
    """Salva interacao com embedding pre-computado para busca futura."""
    if not account_id:
        return
    ensure_history_dir()
    path = history_path(account_id)
    history = load_history(account_id)

    # Pre-computa embedding da msg do jogador para busca futura
    emb = _get_embedding(msg)

    history.append({
        "t": int(time.time()),
        "p": player,
        "m": msg,
        "r": reply,
        "e": emb,  # embedding pre-computado
    })
    # Limpa o cache de embeddings para esta conta
    keys_to_remove = [k for k in EMBED_CACHE if k[0] == account_id]
    for k in keys_to_remove:
        EMBED_CACHE.pop(k, None)

    # Mantem apenas as ultimas HISTORY_MAX_STORED
    if len(history) > HISTORY_MAX_STORED:
        history = history[-HISTORY_MAX_STORED:]
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False)
    except OSError:
        pass

def search_history(account_id, query, top_k=HISTORY_SEARCH_TOP_K):
    """Busca no historico as mensagens mais relevantes para a query.
    
    Retorna string formatada com as top_k interacoes mais similares,
    ou string vazia se nao houver historico ou similaridade relevante.
    """
    history = load_history(account_id)
    if not history:
        return ""
    
    # Embed da query
    query_emb = _get_embedding(query)
    if not query_emb:
        return ""
    
    # Calcula similaridade com cada entrada (usando embedding armazenado ou
    # embedding do texto da mensagem como fallback)
    scored = []
    for i, h in enumerate(history):
        emb = h.get("e")
        if not emb:
            # Fallback: computa e armazena no cache em memoria
            cache_key = (account_id, i)
            if cache_key in EMBED_CACHE:
                emb = EMBED_CACHE[cache_key]
            else:
                emb = _get_embedding(h["m"])
                if emb:
                    EMBED_CACHE[cache_key] = emb
        if emb:
            score = _cosine_similarity(query_emb, emb)
            # Bonus temporal: mensagens recentes tem peso extra
            age_bonus = 0.1 * (1 - min(i, 10) / 10)  # ultimas 10 tem bonus
            scored.append((score + age_bonus, h))
    
    # Ordena por similaridade + bonus temporal
    scored.sort(key=lambda x: x[0], reverse=True)
    
    # Pega as top_k com score minimo de 0.5
    relevant = [h for s, h in scored if s > 0.5][:top_k]
    
    if not relevant:
        return ""
    
    lines = []
    for h in relevant:
        lines.append(f"Jogador: {h['m']}")
        lines.append(f"Assistente: {h['r']}")
    return "\n".join(lines)

_out_lock = threading.Lock()
last_in_size = 0
last_response_size = 0
ai_queue = queue.Queue()
KNOWLEDGE = ""
rag_ctx = None
HOT_CACHE = []  # [(pergunta_chave, resposta, contexto)]


def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{time.time()}|{msg}\n")


def ensure():
    for p in [CHAT_IN, CHAT_OUT, PENDING, RESPONSE, LOG_FILE, SERVER_CMD, SERVER_RESP]:
        d = os.path.dirname(p)
        try:
            os.makedirs(d, exist_ok=True)
            if not os.path.exists(p):
                with open(p, "w", encoding="utf-8") as f:
                    f.write("")
        except Exception as e:
            log(f"ensure ERRO: {e}")


def to_latin1(s):
    try:
        return s.encode("latin-1").decode("latin-1")
    except UnicodeEncodeError:
        return s.encode("latin-1", errors="replace").decode("latin-1")

def send_out(msg, channel=False, account_id=""):
    with _out_lock:
        msg_id = int(time.time() * 1000)
        with open(CHAT_OUT, "a", encoding="latin-1") as f:
            if channel:
                f.write(f"CHANNEL_{msg_id}|{to_latin1(msg)}\n")
            else:
                f.write(f"{msg_id}|{to_latin1(msg)}\n")
    log(f"ENVIADO #{msg_id}: {msg[:60]}")


def poll_in():
    global last_in_size
    if not os.path.exists(CHAT_IN):
        return []
    try:
        current = os.path.getsize(CHAT_IN)
    except OSError:
        return []
    if current <= last_in_size:
        return []
    try:
        with open(CHAT_IN, "rb") as f:
            f.seek(last_in_size)
            raw = f.read()
        try:
            new_data = raw.decode("utf-8")
        except UnicodeDecodeError:
            new_data = raw.decode("latin-1")
    except Exception as e:
        log(f"poll_in ERRO: {e}")
        return []
    last_in_size = current
    lines = []
    for line in new_data.strip().split("\n"):
        line = line.strip()
        if line:
            parts = line.split("|", 4)
            if len(parts) >= 3:
                if parts[1] == "CHANNEL":
                    # Formato: timestamp|CHANNEL|account_id|player|msg
                    if len(parts) == 5:
                        lines.append({"time": parts[0], "player": parts[3], "msg": parts[4], "channel": True, "account_id": parts[2]})
                else:
                    # Formato: timestamp|player|msg|account_id (do !assistente)
                    account_id = parts[3] if len(parts) >= 4 else ""
                    lines.append({"time": parts[0], "player": parts[1], "msg": parts[2], "channel": False, "account_id": account_id})
    return lines


def poll_response():
    global last_response_size
    if not os.path.exists(RESPONSE):
        return []
    try:
        current = os.path.getsize(RESPONSE)
    except OSError:
        return []
    if current <= last_response_size:
        return []
    try:
        with open(RESPONSE, "r", encoding="utf-8", errors="replace") as f:
            f.seek(last_response_size)
            new_data = f.read()
    except Exception:
        return []
    last_response_size = current
    return [l.strip() for l in new_data.strip().split("\n") if l.strip()]


def ask_ollama(prompt, timeout=OLLAMA_TIMEOUT, model=OLLAMA_MODEL):
    payload = json.dumps({
        "model": model, "prompt": prompt, "stream": False,
        "options": {"temperature": 0.1, "max_tokens": 200}
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = json.loads(resp.read())
        return data.get("response", "").strip()
    except urllib.request.URLError as e:
        if "Connection refused" in str(e):
            log(f"ask_ollama: Ollama OFFLINE ({model})")
        else:
            log(f"ask_ollama ERRO ({model}): {e}")
        return None
    except Exception as e:
        log(f"ask_ollama ERRO ({model}): {e}")
        return None


def ask_ollama_chat(messages, model=OLLAMA_MODEL_ROUTER, timeout=OLLAMA_TIMEOUT_ROUTER):
    """Usa a API de chat do Ollama (aplica template do modelo corretamente).
    Util para o router (qwen1.5b) que precisa do chat template para classificar."""
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.0, "max_tokens": 40}
    }).encode()
    req = urllib.request.Request(
        OLLAMA_CHAT_URL, data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = json.loads(resp.read())
        return data.get("message", {}).get("content", "").strip()
    except urllib.request.URLError as e:
        if "Connection refused" in str(e):
            log(f"ask_ollama_chat: Ollama OFFLINE ({model})")
        else:
            log(f"ask_ollama_chat ERRO ({model}): {e}")
        return None
    except Exception as e:
        log(f"ask_ollama_chat ERRO ({model}): {e}")
        return None


def _remove_stopwords(words):
    """Remove stopwords e palavras muito curtas (&lt;3 chars) de um conjunto."""
    return {w for w in words if len(w) >= 3 and w not in STOPWORDS}

def get_hot_cache(msg):
    """
    Retorna resposta do cache quente se pergunta similar ja foi respondida.
    Usa similaridade Jaccard com remocao de stopwords para evitar
    falsos-positivos como 'o que e afinidade' casando com 'o que e MariaDB'.
    """
    m = msg.lower().strip()
    words_msg = _remove_stopwords(set(m.split()))
    if len(words_msg) < 2:
        return None

    # Encontra a palavra mais longa e mais especifica da pergunta
    longest_word = max(words_msg, key=len)

    for entry in HOT_CACHE:
        key = entry.get("key", "")
        if not key:
            continue
        words_key = _remove_stopwords(set(key.split()))
        if len(words_key) < 2:
            continue

        # A palavra mais especifica da pergunta DEVE estar na chave do cache
        if longest_word not in key:
            continue

        # Jaccard similarity: |A ∩ B| / |A ∪ B|
        intersection = len(words_key & words_msg)
        union = len(words_key | words_msg)
        jaccard = intersection / union if union > 0 else 0

        if jaccard > 0.6:
            return entry.get("context", "")

    return None


def update_hot_cache(msg, context):
    """Atualiza cache quente com nova resposta."""
    global HOT_CACHE
    HOT_CACHE.append({"key": msg.lower().strip(), "context": context, "time": time.time()})
    # Mantem so as ultimas 50
    if len(HOT_CACHE) > 50:
        HOT_CACHE = HOT_CACHE[-50:]
    try:
        with open(HOT_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(HOT_CACHE, f, ensure_ascii=False)
    except Exception:
        pass


# --- Router (classificador de intencao) ---

ROUTER_SYSTEM_PROMPT = """Classifique a mensagem do jogador em uma das intencoes:
- item_info: o jogador esta PERGUNTANDO sobre um ITEM especifico (ex: "o que e Dark Sword?", "me fale sobre a War Hammer", "info golden armor", "como e a Crown Shield")
- monster_info: o jogador esta PERGUNTANDO sobre um MONSTRO especifico (ex: "o que e Dragon?", "info sobre Demon", "fale do Orc Berserker")
- complex: QUALQUER OUTRA COISA (dúvida geral, estrategia, quest, como fazer, onde fica, etc)

Mensagem: "{message}"

Responda APENAS o JSON: {{"intent": "item_info|monster_info|complex", "entity": "nome_do_item_ou_monstro_encontrado"}}"""


def route_intent(message):
    """
    Classifica a intencao da mensagem usando qwen2.5-coder:1.5b.
    Retorna {"intent": "item_info|monster_info|complex", "entity": "..."}
    Se falhar, retorna complex (fallback seguro).
    """
    if not message or not message.strip():
        return {"intent": "complex", "entity": ""}

    prompt = ROUTER_SYSTEM_PROMPT.format(message=message.strip()[:200])

    response = ask_ollama_chat([
        {"role": "system", "content": "Você classifica mensagens de jogadores de Tibia."},
        {"role": "user", "content": prompt}
    ])

    if not response:
        log(f"route_intent: sem resposta do router, fallback para complex")
        return {"intent": "complex", "entity": ""}

    # Tenta extrair JSON (modelo pode envolver em ```)
    try:
        clean = response.strip()
        if "```" in clean:
            # Extrai conteudo do bloco de codigo
            for part in clean.split("```"):
                part = part.strip()
                if part.startswith("{") or part.startswith("json"):
                    clean = part
                    if clean.startswith("json"):
                        clean = clean[4:].strip()
                    break
        result = json.loads(clean)
        intent = result.get("intent", "complex")
        entity = result.get("entity", "")
        if intent not in ("item_info", "monster_info", "complex"):
            intent = "complex"
        log(f"route_intent: {message[:50]} -> {intent}/{entity}")
        return {"intent": intent, "entity": entity}
    except (json.JSONDecodeError, Exception) as e:
        log(f"route_intent: erro parse JSON '{response[:100]}': {e}")
        return {"intent": "complex", "entity": ""}


# --- Handlers de resposta (formata dados do servidor RPC) ---

# Mapeamento de slotPosition (bitfield)
SLOT_NAMES = {
    0: "duas maos",
    1: "cabeca", 2: "pescoco", 4: "torso",
    8: "maos", 16: "pernas", 32: "pes",
    64: "anel", 128: "amuleto",
}

# Mapeamento de weaponType
WEAPON_TYPES = {
    0: None, 1: "espada", 2: "maca", 3: "machado",
    4: "escudo", 5: "distancia", 6: "vara", 7: "municao",
}


def parse_slot_position(pos):
    """Converte bitfield de slotPosition para lista de nomes."""
    pos = pos or 0
    if pos == 0:
        return "duas maos"
    parts = []
    for bit, name in sorted(SLOT_NAMES.items()):
        if bit > 0 and pos & bit:
            parts.append(name)
    return ", ".join(parts) if parts else "mao"


def format_item_response(data):
    """Formata resposta de item_info."""
    if not data:
        return None

    known = data.get("known", False)
    name = data.get("name", "Item")

    if not known:
        return f"{name}: Voce ainda nao descobriu este item! Olhe para ele no jogo."

    parts = [f"[{name}]"]

    desc = data.get("description")
    if desc:
        parts.append(desc)

    # Stats
    stats = []
    if data.get("attack"):
        stats.append(f"Atq {data['attack']}")
    if data.get("defense"):
        stats.append(f"Def {data['defense']}")
    if data.get("armor"):
        stats.append(f"Arm {data['armor']}")
    if stats:
        parts.append(" | ".join(stats))

    # Info extra
    extras = []
    wt = data.get("weapon_type", 0)
    weapon_name = WEAPON_TYPES.get(wt)
    if weapon_name:
        extras.append(weapon_name)

    slot = parse_slot_position(data.get("slot_pos"))
    if slot:
        extras.append(slot)

    w_str = data.get("weight_str")
    if w_str:
        extras.append(w_str)

    if extras:
        parts.append("(" + ", ".join(extras) + ")")

    lvl = data.get("req_level")
    if lvl:
        parts.append(f"Nivel: {lvl}")

    return " | ".join(parts)


def format_monster_response(data):
    """Formata resposta de monster_info."""
    if not data:
        return None

    name = data.get("name", "Monstro")
    parts = [f"[{name}]"]

    stats = []
    hp = data.get("health")
    if hp:
        max_hp = data.get("max_health")
        if max_hp and max_hp != hp:
            stats.append(f"HP {hp}/{max_hp}")
        else:
            stats.append(f"HP {hp}")
    exp = data.get("experience")
    if exp:
        stats.append(f"Exp {exp}")
    if stats:
        parts.append(" | ".join(stats))

    extras = []
    if data.get("armor"):
        extras.append(f"Arm {data['armor']}")
    if data.get("defense"):
        extras.append(f"Def {data['defense']}")
    if data.get("hostile"):
        extras.append("Hostil")
    if data.get("summonable"):
        mc = data.get("mana_cost")
        if mc:
            extras.append(f"Conjuravel ({mc} mana)")
        else:
            extras.append("Conjuravel")
    if extras:
        parts.append("(" + ", ".join(extras) + ")")

    return " | ".join(parts)


# --- RPC Client (comunicacao com o servidor) ---

def rpc_request(player_name, action, param, timeout=RPC_TIMEOUT):
    """
    Envia comando RPC para o servidor via server_cmd.txt e aguarda resposta.
    Retorna {"status": "...", "data": ...} ou {"status": "timeout", "data": None}.
    """
    request_id = str(int(time.time() * 1000)) + str(hash(player_name + action + param) % 1000)

    # Escreve comando
    line = f"{request_id}|{player_name}|{action}|{param}\n"
    try:
        with open(SERVER_CMD, "a", encoding="utf-8") as f:
            f.write(line)
        log(f"RPC enviado: {request_id} {action} '{param[:50]}'")
    except Exception as e:
        log(f"RPC ERRO escrita: {e}")
        return {"status": "error", "data": {"reason": f"write_error: {e}"}}

    # Poll por resposta
    last_size = 0
    try:
        last_size = os.path.getsize(SERVER_RESP)
    except OSError:
        pass

    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(RPC_POLL_INTERVAL)
        try:
            current = os.path.getsize(SERVER_RESP)
        except OSError:
            continue
        if current <= last_size:
            continue

        try:
            with open(SERVER_RESP, "r", encoding="utf-8", errors="replace") as f:
                f.seek(last_size)
                new_data = f.read()
            last_size = current
        except Exception:
            continue

        for resp_line in new_data.strip().split("\n"):
            resp_line = resp_line.strip()
            if not resp_line:
                continue
            # Formato: requestId|status|json_data
            parts = resp_line.split("|", 2)
            if len(parts) == 3 and parts[0] == request_id:
                status = parts[1]
                try:
                    resp_data = json.loads(parts[2])
                except json.JSONDecodeError:
                    resp_data = {"raw": parts[2]}
                log(f"RPC resposta: {request_id} -> {status}")
                return {"status": status, "data": resp_data}

    log(f"RPC TIMEOUT: {request_id} (action={action}, param={param[:50]})")
    return {"status": "timeout", "data": None}


# --- Template de respostas rapidas (NUNCA alucina) ---
def template_reply(player, msg):
    """Retorna (resposta, blocked) onde blocked=True = IA nao deve processar."""
    m = msg.lower().strip()

    # PERGUNTAS PROIBIDAS (credenciais, senhas) — blocked=True impede IA de processar
    if any(w in m for w in ["senha", "password", "usuario", "user", "login", "credential"]):
        return f"{player}, nao posso fornecer informacoes de acesso. Consulte o arquivo de configuracao ou o administrador.", True

    if any(w in m for w in ["admin", "root", "mysql", "banco", "database"]):
        if any(w in m for w in ["senha", "password", "usuario", "user", "login"]):
            return f"{player}, informacoes de acesso ao banco de dados sao confidenciais. Nao posso compartilha-las.", True

    # Ola
    if m in ("ola", "oi", "oie", "hey", "hello"):
        return f"Ola {player}! Sou o assistente MCR.", False

    # Teste
    if "teste" in m or "testando" in m:
        return f"Teste recebido, {player}! Sistema funcionando.", False

    # Obrigado
    if "obrigado" in m or "valeu" in m or "brigado" in m:
        return f"Disponha, {player}!", False

    return f"{player}, mensagem recebida!", False


ANTI_HALLUCINATION_PROMPT = """Voce e o assistente do Projeto MCR, um servidor CUSTOMIZADO de Tibia.
O CONHECIMENTO abaixo contem informacoes VERIFICADAS sobre o projeto.
O CONTEXTO DO CODIGO abaixo contem trechos REAIS do codigo fonte (pode estar vazio).

REGRAS:
1. Responda APENAS com base no CONHECIMENTO + CONTEXTO DO CODIGO fornecidos.
2. Se nao souber a resposta, diga exatamente: "Nao encontrei essa informacao no codigo ou documentacao do MCR."
3. NUNCA invente dados, valores, senhas, usuarios ou informacoes.
4. Responda em portugues, 1-3 frases.
5. IMPORTANTE: Este e um servidor CUSTOMIZADO (Canary). APIs, funcoes e constantes de outros
   projetos Tibia (TFS, OTX, otservbr) podem NAO existir aqui.
6. Use APENAS nomes exatos de funcoes e constantes que aparecem no CONTEXTO DO CODIGO fornecido.
   NAO invente nomes como CONST_EFFECT_FIRESWELL, addEffect, increaseTime ou similares.
7. Voce NAO pode criar, editar ou modificar arquivos. Voce apenas RESPONDE perguntas.
8. NUNCA responda com codigo a menos que seja explicitamente solicitado.

HISTORICO RELEVANTE DA CONVERSA (apenas mensagens relacionadas a pergunta atual):
{history}

CONHECIMENTO DO MCR:
{knowledge}

CONTEXTO DO CODIGO:
{rag_context}

Pergunta de {player}: {msg}

Resposta:"""


def ai_worker():
    global rag_ctx
    # Carrega RAG
    try:
        if SCRIPTS_DIR not in sys.path:
            sys.path.insert(0, SCRIPTS_DIR)
        from rag_query import get_context as rag_ctx_fn
        rag_ctx = rag_ctx_fn
        log("RAG carregado")
    except Exception as e:
        rag_ctx = None
        log(f"RAG nao disponivel: {e}")

    # Carrega cache quente
    global HOT_CACHE
    try:
        if os.path.exists(HOT_CACHE_FILE):
            with open(HOT_CACHE_FILE, "r", encoding="utf-8") as f:
                HOT_CACHE = json.load(f)
            log(f"Cache quente carregado: {len(HOT_CACHE)} entradas")
    except Exception:
        HOT_CACHE = []

    ensure_history_dir()
    while True:
        try:
            data = ai_queue.get()
            player = data["player"]
            msg = data["msg"]
            is_channel = data.get("channel", False)
            account_id = data.get("account_id", "")
            log(f"IA processando: {player} (acc={account_id[:8]}): {msg[:50]}")

            # 1. Verifica cache quente
            cached = get_hot_cache(msg)
            if cached:
                log(f"Cache quente HIT: {cached[:60]}")
                send_out(f"[IA] {cached}", channel=is_channel)
                ai_queue.task_done()
                continue

            # 2. Busca historico relevante para a pergunta (busca semantica)
            history_str = search_history(account_id, msg, top_k=2)
            if history_str:
                log(f"Historico: busca semantica retornou contexto relevante")

            # 3. Busca RAG
            rag = ""
            if rag_ctx:
                try:
                    rag = rag_ctx(msg, top_k=5, player_mode=True)
                except Exception:
                    rag = ""
                if rag:
                    log(f"RAG: {len(rag)} bytes")
                else:
                    log("RAG: sem resultado relevante")

            # 4. Monta prompt anti-alucinacao
            rag_context = rag if rag else "(RAG VAZIO - sem contexto relevante. Nao invente informacoes.)"
            hist_context = history_str if history_str else "(Sem historico recente.)"
            prompt = ANTI_HALLUCINATION_PROMPT.format(
                history=hist_context,
                knowledge=KNOWLEDGE,
                rag_context=rag_context,
                player=player,
                msg=msg
            )

            # 5. Pergunta ao Ollama (7b primeiro, fallback 1.5b)
            log(f"Modelo: {OLLAMA_MODEL}")
            reply = ask_ollama(prompt, timeout=OLLAMA_TIMEOUT, model=OLLAMA_MODEL)
            if not reply:
                log(f"Fallback: {OLLAMA_MODEL_FALLBACK}")
                reply = ask_ollama(prompt, timeout=OLLAMA_TIMEOUT_FALLBACK, model=OLLAMA_MODEL_FALLBACK)

            # 6. Salva no historico da conta
            if reply:
                save_to_history(account_id, player, msg, reply)

            # 7. Resposta final
            if reply:
                send_out(f"[IA] {reply}", channel=is_channel)
                update_hot_cache(msg, reply)
            else:
                log("IA: todas as tentativas falharam (Ollama offline?)")
                send_out(f"[IA] Assistente indisponivel no momento.", channel=is_channel)

            ai_queue.task_done()

        except Exception as e:
            log(f"ai_worker ERRO: {e}\n{traceback.format_exc()}")
            try:
                ai_queue.task_done()
            except Exception:
                pass


def main():
    global last_in_size, KNOWLEDGE
    ensure()

    # Carrega conhecimento
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            KNOWLEDGE = f.read()
        log(f"Conhecimento carregado ({len(KNOWLEDGE)} bytes)")

    if os.path.exists(CHAT_IN):
        last_in_size = os.path.getsize(CHAT_IN)
    log(f"last_in_size={last_in_size}")

    t = threading.Thread(target=ai_worker, daemon=True)
    t.start()
    log("Thread IA iniciada")

    # Timeout para nao travar: se o loop principal ficar 30s sem resposta, loga
    last_activity = time.time()

    while True:
        try:
            msgs = poll_in()
            if msgs:
                last_activity = time.time()
                for m in msgs:
                    is_channel = m.get('channel', False)
                    player_name = m['player']
                    msg_text = m['msg']
                    line = f"{m['time']}|{'CHANNEL|' if is_channel else ''}{player_name}|{msg_text}\n"
                    with open(PENDING, "a", encoding="utf-8") as f:
                        f.write(line)

                    # 1. Template imediato (sempre, da feedback rapido)
                    reply, blocked = template_reply(player_name, msg_text)
                    send_out(reply, channel=is_channel, account_id=m.get('account_id', ''))

                    # 2. Se bloqueado pelo template (senhas etc), nao processa mais
                    if blocked:
                        continue

                    # 3. Router: classifica intencao
                    route = route_intent(msg_text)

                    # 4. Se for item_info ou monster_info, usa RPC (sem GPU)
                    if route['intent'] in ('item_info', 'monster_info') and route.get('entity'):
                        rpc_result = rpc_request(player_name, route['intent'], route['entity'])

                        if rpc_result['status'] in ('found_known', 'found_unknown', 'found'):
                            # Sucesso: formata e envia
                            if route['intent'] == 'item_info':
                                formatted = format_item_response(rpc_result['data'])
                            else:
                                formatted = format_monster_response(rpc_result['data'])
                            if formatted:
                                send_out(f"[Item] {formatted}", channel=is_channel)
                                log(f"RPC resposta enviada para {player_name}: {formatted[:60]}")
                                continue  # Pula IA
                            else:
                                # Falha formatacao, fallback
                                log(f"RPC format falhou, fallback IA")
                        else:
                            # RPC falhou (timeout, erro, not_found)
                            log(f"RPC {rpc_result['status']} para {route['intent']} '{route['entity']}', fallback IA")

                    # 5. Fallback: IA processa (GPU) com account_id
                    ai_queue.put({"player": player_name, "msg": msg_text, "channel": is_channel, "account_id": m.get('account_id', '')})

            for r in poll_response():
                send_out(r)

            # Watchdog: se ficou 30s sem atividade, apenas loga (nao reinicia)
            if time.time() - last_activity > 30:
                log("WATCHDOG: 30s sem atividade (normal)")
                last_activity = time.time()

            time.sleep(1)
        except KeyboardInterrupt:
            log("Encerrado manualmente")
            break
        except Exception as e:
            log(f"loop ERRO: {e}\n{traceback.format_exc()}")
            time.sleep(5)


if __name__ == "__main__":
    main()
