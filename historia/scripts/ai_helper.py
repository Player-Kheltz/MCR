#!/usr/bin/env python3
"""
ai_helper.py — Helper de IA local (Ollama) para o assistente MCR.

Uso:
    python "scripts/ai_helper.py" generate "crie um eval Lua para testar posicao"
    python "scripts/ai_helper.py" reply "Criador" "qual minha posicao?"
    python "scripts/ai_helper.py" validate "los 1094,998,6;1095,998,6" "true" "PASS/FAIL"
"""
import os
import sys
import json
import urllib.request
import urllib.error

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TIMEOUT = 30


def ask(model, prompt, max_tokens=300, temperature=0.5):
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature, "max_tokens": max_tokens}
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT)
        data = json.loads(resp.read())
        return data.get("response", "").strip()
    except Exception as e:
        print(f"[ERRO] {e}", file=sys.stderr)
        return None


def cmd_generate(args):
    prompt = " ".join(args)
    if not prompt:
        print("Digite o que quer gerar.")
        return
    full = f"Gere apenas o codigo Lua para test_bot.lua (sem explicacao): {prompt}"
    result = ask("qwen2.5-coder:1.5b", full)
    print(result or "(falha)")


def cmd_reply(args):
    if len(args) < 2:
        print("Uso: ai_helper.py reply <jogador> <mensagem>")
        return
    player = args[0]
    msg = " ".join(args[1:])
    sys_prompt = (
        "Voce e o assistente do Projeto MCR, um servidor customizado de Tibia. "
        "Responda de forma curta, amigavel e em portugues (1-2 frases). "
        "Nao use emojis."
    )
    full = f"{sys_prompt}\n\nJogador {player} disse: {msg}\n\nAssistente:"
    result = ask("qwen2.5-coder:1.5b", full, max_tokens=150)
    print(result or "(falha)")


def cmd_validate(args):
    if len(args) < 2:
        print("Uso: ai_helper.py validate <comando> <resultado>")
        return
    comando = args[0]
    resultado = " ".join(args[1:])
    full = (
        f"Analise se o teste abaixo passou ou falhou. "
        f"Responda apenas PASS ou FAIL, e o motivo em 1 frase.\n\n"
        f"Comando: {comando}\n"
        f"Resultado: {resultado}\n\n"
        f"Veredito:"
    )
    result = ask("qwen2.5-coder:1.5b", full, max_tokens=100, temperature=0.3)
    print(result or "(falha)")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "generate":
        cmd_generate(args)
    elif cmd == "reply":
        cmd_reply(args)
    elif cmd == "validate":
        cmd_validate(args)
    elif cmd == "ping":
        result = ask("qwen2.5-coder:1.5b", "Responda apenas: pong")
        print(result or "falha")
    else:
        print(f"Comando desconhecido: {cmd}")


if __name__ == "__main__":
    main()
