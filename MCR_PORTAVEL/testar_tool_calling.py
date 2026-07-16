"""Testa se tool calling funciona via chat completions API."""
import requests, json

OLLAMA_CHAT = "http://localhost:11434/v1/chat/completions"

models_to_test = ["qwen3:8b", "phi4-mini:latest", "qwen3.5:9b"]

tools_def = [{
    "type": "function",
    "function": {
        "name": "glob",
        "description": "Lista arquivos por padrao",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"}
            },
            "required": ["pattern"]
        }
    }
}]

for model in models_to_test:
    print(f"\n=== {model} ===")
    try:
        r = requests.post(OLLAMA_CHAT, json={
            "model": model,
            "messages": [
                {"role": "system", "content": "Voce e um assistente que explora projetos de codigo."},
                {"role": "user", "content": "liste os arquivos python no diretorio mcr"}
            ],
            "tools": tools_def,
            "max_tokens": 300,
        }, timeout=30)
        d = r.json()
        if "choices" not in d:
            print(f"  ERRO: {d}")
            continue
        msg = d["choices"][0]["message"]
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                print(f"  [TOOL CALL] {tc['function']['name']}")
                print(f"    args: {tc['function']['arguments']}")
        else:
            content = msg.get("content", "")
            print(f"  [TEXTUAL] {content[:200]}")
    except Exception as e:
        print(f"  ERRO: {e}")
