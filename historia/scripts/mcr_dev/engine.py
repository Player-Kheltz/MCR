"""engine.py — Motor central do MCR-Dev. Coordena: router -> busca exemplo -> gera -> valida -> salva -> aprende."""
import os, sys, json, subprocess, time, re, urllib.request
from pathlib import Path

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE, "scripts"))
sys.path.insert(0, os.path.join(BASE, "Scripts"))

from mcr_dev import router, validador, memoria

OLLAMA_CHAT = "http://localhost:11434/api/chat"

# Modelos
MODEL_CODE = "qwen2.5-coder:7b"     # geracao de codigo
MODEL_CHAT = "llama3.1:8b"          # conversa geral
MODEL_DEEP = "deepseek-r1:8b"       # analise profunda
MODEL_QUICK = "phi3.5:3.8b"        # tarefas rapidas

# TTL para modelos (segundos sem uso para descarregar)
MODEL_TTL = 30

MODEL_ARGS = {
    MODEL_CODE: {"temperature": 0.1, "max_tokens": 4096},
    MODEL_CHAT: {"temperature": 0.1, "max_tokens": 2048},
    MODEL_DEEP: {"temperature": 0.1, "max_tokens": 4096},
    MODEL_QUICK: {"temperature": 0.0, "max_tokens": 1024},
}

def _chat(model, messages, system=""):
    """Chama modelo local."""
    if system:
        messages = [{"role": "system", "content": system}] + messages
    
    opts = MODEL_ARGS.get(model, {"temperature": 0.1, "max_tokens": 2048})
    payload = json.dumps({"model": model, "messages": messages, "stream": False,
        "options": opts}).encode()
    
    try:
        req = urllib.request.Request(OLLAMA_CHAT, data=payload,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        return data["message"]["content"]
    except Exception as e:
        return f"[ERRO] {e}"


def _find_examples(query, top_k=3):
    """Encontra exemplos no projeto."""
    try:
        result = subprocess.run(
            ["python", os.path.join(BASE, "scripts", "find_example.py"),
             query, "--project", BASE, "-k", str(top_k)],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout
        if "=== EXEMPLO:" in output:
            return output
    except:
        pass
    return ""


def _salvar_arquivo(path, conteudo, tipo=""):
    """Salva arquivo no sandbox ou path especificado."""
    # Seguranca: se nao for sandbox, avisa
    full_path = os.path.join(BASE, path) if not os.path.isabs(path) else path
    sandbox_dir = os.path.join(BASE, "sandbox")
    
    if not full_path.startswith(sandbox_dir):
        # Forca para sandbox (seguranca)
        filename = os.path.basename(path)
        full_path = os.path.join(sandbox_dir, filename)
    
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(conteudo)
    
    return full_path


def processar(entrada, loop_correcao=True):
    """Processa uma entrada do usuario. Retorna (resposta, arquivo_gerado)."""
    t0 = time.time()
    arquivo_gerado = ""
    
    # PASSO 1: Classificar intencao
    intent, resposta_imediata = router.classify(entrada)
    
    if resposta_imediata:
        memoria.learn(entrada, resposta_imediata, intent)
        return resposta_imediata, ""
    
    # PASSO 2: Buscar aprendizados anteriores
    lembretes = memoria.recall(entrada)
    contexto_extra = ""
    if lembretes:
        contexto_extra = "\nExperiencias passadas similares:\n"
        for l in lembretes:
            if l.get("arquivo"):
                contexto_extra += f"- {l['entrada']} -> {l['arquivo']}\n"
    
    # PASSO 3: Processar segundo a intencao
    kwargs = {"loop_correcao": loop_correcao}
    
    if intent == "CRIAR_NPC":
        resposta, arquivo = _criar_npc(entrada, contexto_extra, **kwargs)
    elif intent == "CRIAR_HABILIDADE":
        resposta, arquivo = _criar_habilidade(entrada, contexto_extra, **kwargs)
    elif intent == "CRIAR_OTUI":
        resposta, arquivo = _criar_otui(entrada, contexto_extra)
    elif intent == "CRIAR_QUEST":
        resposta, arquivo = _criar_quest(entrada, contexto_extra)
    elif intent == "CRIAR_SQL":
        resposta, arquivo = _criar_sql(entrada, contexto_extra)
    elif intent == "CRIAR_ITEM":
        resposta, arquivo = _criar_item(entrada, contexto_extra)
    elif intent == "CRIAR_CODIGO":
        resposta, arquivo = _criar_codigo(entrada, contexto_extra)
    elif intent == "EDITAR":
        resposta, arquivo = _editar(entrada, contexto_extra)
    elif intent == "DELETAR":
        resposta, arquivo = _deletar(entrada)
    elif intent == "PERGUNTA":
        resposta = _pergunta(entrada, contexto_extra)
    elif intent == "SISTEMA":
        resposta = _sistema(entrada)
    else:
        resposta = _chat_geral(entrada, contexto_extra)
        arquivo = ""
    
    if 'arquivo' not in dir() or not arquivo:
        arquivo = ""
    
    # PASSO 4: Registrar aprendizado
    arquivo_rel = os.path.relpath(arquivo, BASE) if arquivo else ""
    memoria.learn(entrada, resposta[:200], intent, arquivo_rel)
    
    tempo = time.time() - t0
    if arquivo:
        resposta += f"\n\n[Arquivo: {arquivo_rel} | {tempo:.1f}s]"
    else:
        resposta += f"\n\n[{tempo:.1f}s]"
    
    return resposta, arquivo


# ============ HANDLERS ESPECIFICOS ============

def _criar_npc(entrada, contexto_extra, loop_correcao=True):
    print("  Buscando exemplos de NPC...")
    exemplos = _find_examples("npc canary selfSay NPCHandler")
    
    system = f"""Voce e um criador de NPCs para Canary (Tibia).

FORMATO OBRIGATORIO (exemplo real do projeto):
{exemplos[:1500]}

REGRAS:
- Use NPCHandler
- Use selfSay() para o NPC falar
- PROIBIDO sendTextMessage
- Inclua: saudacao, loja (onSell/onBuy), dialogos tematicos
- Crie lore: nome, historia, personalidade
{contexto_extra}"""
    
    prompt = f"Crie um NPC completo baseado em: {entrada}\n\nGere o codigo Lua completo com lore, dialogos e sistema de loja."
    
    print("  Gerando NPC...")
    resultado = _chat(MODEL_CODE, [{"role": "user", "content": prompt}], system)
    
    # Valida e corrige (loop ate 2x)
    for tentativa in range(3):
        valido, erros, sugs = validador.validar_codigo(resultado, "NPC")
        if valido:
            break
        if erros and loop_correcao:
            print(f"  Ajustando: {erros[0]}")
            prompt2 = f"Corriga: {erros[0]}. {sugs[0] if sugs else ''}\n\nReescreva completo:\n\n{resultado}"
            resultado = _chat(MODEL_CODE, [{"role": "user", "content": prompt2}], system)
        else:
            break
    
    nome = _extrair_nome(resultado, "npc")
    path = _salvar_arquivo(f"sandbox/mcr_dev_{nome}.lua", resultado)
    
    return f"NPC '{nome}' criado com dialogo e loja!\n\n{resultado[:800]}", path


def _criar_habilidade(entrada, contexto_extra, loop_correcao=True):
    print("  Buscando exemplos de habilidades SHC...")
    exemplos = _find_examples("shc habilidade HABILIDADES efeitoConfig")
    
    system = f"""Voce e um criador de habilidades SHC para o SPA do MCR.

EXEMPLO REAL (formato OBRIGATORIO):
{exemplos[:2000]}

REGRAS:
- HABILIDADES[ID] = {{ nome, tipo, dominio, efeitoConfig, postura, niveis }}
- efeitoConfig: {{ tipo, dano (numero), percentual (0.0-1.0), elemento }}
- postura: {{ [1] = {{ efeitoConfig = {{...}} }} }}
- niveis: {{ [5] = {{ {{ mod = "efeitoConfig", dano = "*1.15" }} }} }}
- PROIBIDO usar danoMinimo/danoMaximo
{contexto_extra}"""
    
    prompt = f"Crie habilidades SHC para: {entrada}\n\nGere o codigo Lua completo no formato SHC."
    
    print("  Gerando habilidades...")
    resultado = _chat(MODEL_CODE, [{"role": "user", "content": prompt}], system)
    
    for tentativa in range(3):
        valido, erros, sugs = validador.validar_codigo(resultado, "HABILIDADE")
        if valido:
            break
        if erros and loop_correcao:
            print(f"  Ajustando: {erros[0]}")
            prompt2 = f"Corrija: {erros[0]}. {sugs[0] if sugs else ''}\n\n{resultado}"
            resultado = _chat(MODEL_CODE, [{"role": "user", "content": prompt2}], system)
        else:
            break
    
    nome = _extrair_nome(resultado, "habilidade")
    path = _salvar_arquivo(f"sandbox/mcr_dev_{nome}.lua", resultado)
    
    return f"Habilidades SHC criadas!\n\n{resultado[:800]}", path


def _criar_otui(entrada, contexto_extra):
    exemplos = _find_examples("otui layout anchors")
    system = f"Crie layouts OTUI para OTClient.\n\nFormato:\n{exemplos[:1000]}\n\n{contexto_extra}"
    prompt = f"Crie layout OTUI para: {entrada}"
    resultado = _chat(MODEL_CODE, [{"role": "user", "content": prompt}], system)
    nome = _extrair_nome(resultado, "layout")
    path = _salvar_arquivo(f"sandbox/mcr_dev_{nome}.otui", resultado)
    return f"✅ Layout OTUI criado!\n\n{resultado[:600]}", path


def _criar_quest(entrada, contexto_extra):
    exemplos = _find_examples("quest sqh")
    system = f"Crie missoes no formato SQH.\n\n{contexto_extra}"
    prompt = f"Crie uma quest para: {entrada}"
    resultado = _chat(MODEL_CODE, [{"role": "user", "content": prompt}], system)
    nome = _extrair_nome(resultado, "quest")
    path = _salvar_arquivo(f"sandbox/mcr_dev_{nome}.lua", resultado)
    return f"✅ Quest criada!\n\n{resultado[:600]}", path


def _criar_sql(entrada, contexto_extra):
    system = f"Crie schemas SQL.\n\n{contexto_extra}"
    prompt = f"Crie SQL para: {entrada}"
    resultado = _chat(MODEL_CODE, [{"role": "user", "content": prompt}], system)
    nome = _extrair_nome(resultado, "schema")
    path = _salvar_arquivo(f"sandbox/mcr_dev_{nome}.sql", resultado)
    return f"✅ SQL criado!\n\n{resultado[:600]}", path


def _criar_item(entrada, contexto_extra):
    exemplos = _find_examples("item ItemType")
    system = f"Crie definicoes de itens.\n\n{exemplos[:800]}\n\n{contexto_extra}"
    prompt = f"Crie um item para: {entrada}"
    resultado = _chat(MODEL_CODE, [{"role": "user", "content": prompt}], system)
    nome = _extrair_nome(resultado, "item")
    path = _salvar_arquivo(f"sandbox/mcr_dev_{nome}.lua", resultado)
    return f"✅ Item criado!\n\n{resultado[:600]}", path


def _criar_codigo(entrada, contexto_extra):
    # Detecta linguagem
    ling = "lua"
    if any(w in entrada.lower() for w in ["python", ".py", "flask", "django"]):
        ling = "py"
    elif any(w in entrada.lower() for w in ["c++", "cpp", "c plus"]):
        ling = "cpp"
    elif any(w in entrada.lower() for w in ["powershell", "ps1", "batch", "cmd"]):
        ling = "ps1"
    
    exemplos = _find_examples(entrada)
    system = f"Crie codigo seguindo o formato dos exemplos.\n\n{exemplos[:1500]}\n\n{contexto_extra}"
    prompt = f"Crie codigo para: {entrada}"
    resultado = _chat(MODEL_CODE, [{"role": "user", "content": prompt}], system)
    
    nome = _extrair_nome(resultado, "script")
    ext = {"lua": ".lua", "py": ".py", "cpp": ".cpp", "ps1": ".ps1"}.get(ling, ".txt")
    path = _salvar_arquivo(f"sandbox/mcr_dev_{nome}{ext}", resultado)
    
    return f"✅ Codigo criado!\n\n{resultado[:600]}", path


def _editar(entrada, contexto_extra):
    """Edita arquivo existente."""
    # Extrai nome do arquivo da entrada
    words = entrada.split()
    arquivo = None
    for w in words:
        if "." in w and os.path.exists(os.path.join(BASE, "sandbox", w)):
            arquivo = os.path.join(BASE, "sandbox", w)
            break
    
    if not arquivo:
        return "Qual arquivo deseja editar? Inclua o nome do arquivo na mensagem.", ""
    
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            conteudo_atual = f.read()[:1000]
    except:
        return f"Nao foi possivel ler {arquivo}", ""
    
    ext = os.path.splitext(arquivo)[1]
    system = f"Edite o codigo conforme solicitado.\n\n{contexto_extra}"
    prompt = f"Arquivo atual ({ext}):\n{conteudo_atual}\n\nSolicitacao: {entrada}\n\nMostre APENAS o novo conteudo completo do arquivo."
    
    resultado = _chat(MODEL_CODE, [{"role": "user", "content": prompt}], system)
    
    with open(arquivo, "w", encoding="utf-8") as f:
        f.write(resultado)
    
    return f"✅ Arquivo editado: {os.path.basename(arquivo)}\n\n{resultado[:500]}", arquivo


def _deletar(entrada):
    """Deleta arquivo no sandbox."""
    words = entrada.split()
    for w in words:
        if "." in w:
            path = os.path.join(BASE, "sandbox", w)
            if os.path.exists(path):
                os.remove(path)
                return f"✅ Deletado: {w}", path
    return "Arquivo nao encontrado no sandbox. Inclua o nome do arquivo.", ""


def _pergunta(entrada, contexto_extra):
    """RAG -> responde com contexto."""
    print("  📚 Buscando no RAG...")
    try:
        sys.path.insert(0, os.path.join(BASE, "scripts"))
        from rag_query import get_context
        ctx = get_context(entrada, top_k=5, player_mode=True)
    except:
        ctx = ""
    
    system = f"""Responda com base SOMENTE no contexto abaixo. Nao invente.

Contexto:
{ctx[:2000] if ctx else "(vazio)"}

{contexto_extra}
"""
    prompt = f"{entrada}\n\nResponda em portugues, 2-3 paragrafos."
    resultado = _chat(MODEL_QUICK, [{"role": "user", "content": prompt}], system)
    return resultado


def _sistema(entrada):
    """Executa comando Windows."""
    print("  💻 Executando comando de sistema...")
    try:
        result = subprocess.run(
            ["python", os.path.join(BASE, "scripts", "win_tools.py"), "system_info"],
            capture_output=True, text=True, timeout=10
        )
        info = result.stdout[:800] if result.stdout else "Sem dados"
        
        # Se pediu processo, pega process_list
        if any(w in entrada.lower() for w in ["processo", "executando", "programa", "task"]):
            result2 = subprocess.run(
                ["python", os.path.join(BASE, "scripts", "win_tools.py"), "process_list"],
                capture_output=True, text=True, timeout=10
            )
            info += "\n\n" + result2.stdout[:800]
        
        return f"Dados do sistema:\n{info[:1000]}"
    except Exception as e:
        return f"Erro ao acessar sistema: {e}"


def _chat_geral(entrada, contexto_extra):
    """Conversa geral (llama3.1)."""
    system = f"Converse de forma natural em portugues.\n\n{contexto_extra}"
    resultado = _chat(MODEL_CHAT, [{"role": "user", "content": entrada}], system)
    return resultado


def _extrair_nome(texto, padrao="arquivo"):
    """Extrai um nome de arquivo do texto gerado."""
    # Tenta achar um nome nas primeiras linhas
    linhas = texto.split("\n")[:5]
    for linha in linhas:
        # Procura por nome =
        m = re.search(r'nome\s*=\s*["\']([^"\']+)["\']', linha)
        if m:
            nome = m.group(1).lower().replace(" ", "_")[:30]
            return nome
    
    # Procura por --[[ header
    m = re.search(r'--\s*(.+?)(?:\s*-)', texto[:200])
    if m:
        return m.group(1).strip().lower().replace(" ", "_")[:20]
    
    return f"{padrao}_{int(time.time())}"
