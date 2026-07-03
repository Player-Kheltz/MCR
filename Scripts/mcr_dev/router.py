"""router.py — Classifica intencao do usuario (qwen1.5b, <1s)."""
import json, urllib.request, time, re

OLLAMA_CHAT = "http://localhost:11434/api/chat"
MODEL = "qwen2.5-coder:1.5b"

# Router SEMPRE local (1.5b = 986MB, carga em <1s)
# Nao precisa de sistema complexo — palavras-chave sao 90% precisas

KEYWORD_MAP = [
    # (padrao_regex, intent, prioridade)
    (r"cri(a|r|e|ar)\s+(um|uma|o|a)?\s*(npc|personagem)", "CRIAR_NPC", 90),
    (r"(npc|personagem|vendedor|trader|shop)", "CRIAR_NPC", 50),
    (r"cri(a|r|e|ar)\s+(um|uma|o|a)?\s*(habilidade|skill|poder)", "CRIAR_HABILIDADE", 90),
    (r"(habilidade|skill|shc|dominio|spa)", "CRIAR_HABILIDADE", 40),
    (r"cri(a|r|e|ar)\s+(um|uma|o|a)?\s*(arquivo|script|modulo|classe)", "CRIAR_CODIGO", 80),
    (r"cri(a|r|e|ar)\s+(um|uma|o|a)?\s*(layout|tela|janela|interface|ui)", "CRIAR_OTUI", 90),
    (r"(otui|layout|interface|ui)", "CRIAR_OTUI", 40),
    (r"cri(a|r|e|ar)\s+(um|uma|o|a)?\s*(quest|missao)", "CRIAR_QUEST", 90),
    (r"(quest|missao|sqh)", "CRIAR_QUEST", 40),
    (r"cri(a|r|e|ar)\s+(um|uma|o|a)?\s*(banco|tabela|sql|schema)", "CRIAR_SQL", 90),
    (r"cri(a|r|e|ar)\s+(um|uma|o|a)?\s*(item|objeto|arma)", "CRIAR_ITEM", 90),
    (r"(criar|fazer|gerar|produzir|implementar|desenvolver)", "CRIAR_CODIGO", 70),
    (r"(alterar|modificar|editar|mudar|atualizar|corrigir)", "EDITAR", 80),
    (r"(deletar|remover|apagar|excluir)", "DELETAR", 90),
    (r"(o que e|o que é|explique|como funciona|me fale sobre)", "PERGUNTA", 80),
    (r"(cpu|memoria|ram|disco|processo|sistema|windows)", "SISTEMA", 80),
    (r"(ola|oi|oie|hey|hello|bom dia|boa tarde)", "SAUDACAO", 90),
    (r"(obrigado|valeu|brigado|tchau|ate mais|flw)", "DESPEDIDA", 90),
    (r"(teste|testando)", "TESTE", 90),
    (r"(ajuda|help|comandos|o que voce faz)", "AJUDA", 90),
]

GREETINGS = {
    "ola": "Ola! Sou o MCR-Dev, assistente local do Projeto MCR.",
    "oi": "Oi! MCR-Dev pronto para ajudar.",
    "hey": "Hey! MCR-Dev na escuta.",
    "hello": "Hello! MCR-Dev ready.",
    "bom dia": "Bom dia! MCR-Dev pronto.",
    "boa tarde": "Boa tarde! MCR-Dev a disposicao.",
    "boa noite": "Boa noite! MCR-Dev ativo.",
}


def classify(message):
    """Classifica intencao usando keywords (sem chamar modelo)."""
    msg = message.lower().strip()
    
    # Tenta match por palavra-chave primeiro (0 chamadas de API)
    best_intent = "CHAT"
    best_score = 0
    
    for pattern, intent, priority in KEYWORD_MAP:
        if re.search(pattern, msg):
            if priority > best_score:
                best_score = priority
                best_intent = intent
    
    # Se tiver score baixo, usa modelo 1.5b como fallback (mas NUNCA para saudacao)
    if best_score < 40:
        try:
            llm_intent = _llm_classify(msg)
            if llm_intent:
                return llm_intent
        except:
            pass
    
    # Logica de fallback segura
    if best_intent == "SAUDACAO":
        for k, v in GREETINGS.items():
            if k in msg:
                return ("SAUDACAO", v)
        return ("SAUDACAO", "Ola! MCR-Dev pronto.")
    
    if best_intent == "DESPEDIDA":
        return ("SAUDACAO", "Disponha! MCR-Dev a disposicao.")
    
    if best_intent == "TESTE":
        return ("TESTE", "Teste OK! Sistema MCR-Dev funcionando.")
    
    if best_intent == "AJUDA":
        return ("AJUDA", _get_help())
    
    return (best_intent, None)


def _llm_classify(msg):
    """Fallback: usa 1.5b para classificar."""
    prompt = f"""Classifique em UMA palavra: {msg}
Opcoes: CRIAR_CODIGO, PERGUNTA, SISTEMA, EDITAR, DELETAR, CHAT
Resposta:"""
    
    payload = json.dumps({
        "model": MODEL, "messages": [
            {"role": "system", "content": "Classifique a mensagem em uma unica palavra."},
            {"role": "user", "content": prompt}
        ], "stream": False, "options": {"temperature": 0.0, "max_tokens": 20}
    }).encode()
    
    try:
        req = urllib.request.Request(OLLAMA_CHAT, data=payload,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        intent = data["message"]["content"].strip().upper()
        if intent in ("CRIAR_CODIGO", "PERGUNTA", "SISTEMA", "EDITAR", "DELETAR", "CHAT"):
            return (intent, None)
    except:
        pass
    return None


def _get_help():
    return (
        "Comandos MCR-Dev:\n"
        "  CRIAR NPC      - Cria NPC com lore, dialogos, loja\n"
        "  CRIAR CODIGO   - Gera scripts, modulos, classes\n"
        "  CRIAR OTUI     - Layouts de interface\n"
        "  CRIAR HABILIDADE - Habilidades SHC\n"
        "  CRIAR QUEST    - Missoes SQH\n"
        "  CRIAR SQL      - Tabelas e schemas\n"
        "  EDITAR         - Altera arquivos existentes\n"
        "  DELETAR        - Remove arquivos\n"
        "  PERGUNTA       - Duvidas sobre o projeto\n"
        "  SISTEMA        - Info do Windows (CPU, RAM, disco)\n"
        "  CHAT           - Conversa geral\n"
        "\nExemplos:\n"
        '  "crie um NPC ferreiro com lore e dialogos"\n'
        '  "crie uma habilidade SHC de gelo"\n'
        '  "qual o uso de CPU?"\n'
        '  "crie um layout OTUI de inventory"'
    )
