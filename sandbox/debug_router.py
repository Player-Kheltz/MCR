"""Debug do router."""
import sys, json, urllib.request
sys.path.insert(0, r"E:\Projeto MCR\scripts")

msg = "o que e a War Hammer?"
prompt_template = """Classifique a mensagem do jogador em uma das intencoes:
- item_info: o jogador esta PERGUNTANDO sobre um ITEM especifico (ex: "o que e Dark Sword?")
- monster_info: o jogador esta PERGUNTANDO sobre um MONSTRO especifico (ex: "o que e Dragon?")
- complex: QUALQUER OUTRA COISA

Mensagem: {message}

Responda APENAS o JSON: {{"intent": "item_info|monster_info|complex", "entity": "nome_do_item_ou_monstro_encontrado"}}"""

prompt = prompt_template.format(message=msg)

req = urllib.request.Request(
    "http://localhost:11434/api/chat",
    data=json.dumps({"model": "qwen2.5-coder:1.5b", "messages": [
        {"role": "system", "content": "Voce classifica mensagens de jogadores de Tibia."},
        {"role": "user", "content": prompt}
    ], "stream": False}).encode(),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req, timeout=15) as r:
    resp = json.loads(r.read())
    content = resp["message"]["content"]
    print("RESPOSTA CRUA:", repr(content[:300]))
    
    clean = content.strip()
    if "```" in clean:
        for part in clean.split("```"):
            part = part.strip()
            if part.startswith("{") or part.startswith("json"):
                clean = part
                if clean.startswith("json"):
                    clean = clean[4:].strip()
                break
    print("CLEAN:", repr(clean[:300]))
    try:
        result = json.loads(clean)
        print("PARSED OK:", result)
        print("INTENT:", repr(result.get("intent")))
        print("ENTITY:", repr(result.get("entity")))
    except json.JSONDecodeError as e:
        print("PARSE ERROR:", e)
        print("CLEAN:", repr(clean[:500]))
