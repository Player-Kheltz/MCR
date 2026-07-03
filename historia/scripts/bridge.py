#!/usr/bin/env python3
"""
bridge.py — Ponte de comunicacao entre o assistente e o jogo MCR.

Uso:
    python scripts/bridge.py chat             # Modo conversa interativa
    python scripts/bridge.py send "mensagem"  # Envia mensagem unica para o jogo
    python scripts/bridge.py listen           # Mostra mensagens do jogo (uma vez)
    python scripts/bridge.py tail             # Segue o chat_in.txt (monitora)

Arquivos:
    data/logs/chat_in.txt   ← Jogo escreve, assistente le
    data/logs/chat_out.txt  ← Assistente escreve, jogo le
"""

import os
import sys
import time
import threading

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANARY_DIR = os.path.join(BASE_DIR, "Canary")
CHAT_IN = os.path.join(CANARY_DIR, "data", "logs", "chat_in.txt")
CHAT_OUT = os.path.join(CANARY_DIR, "data", "logs", "chat_out.txt")

_out_id = 0


def ensure_files():
    for path in [CHAT_IN, CHAT_OUT]:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write("")


def read_in():
    """Le todas as linhas novas do chat_in.txt."""
    if not os.path.exists(CHAT_IN):
        return []
    with open(CHAT_IN, "r", encoding="utf-8") as f:
        content = f.read()
    lines = []
    for line in content.strip().split("\n"):
        line = line.strip()
        if line:
            parts = line.split("|", 2)
            if len(parts) == 3:
                lines.append({"time": parts[0], "player": parts[1], "msg": parts[2]})
    return lines


def send_out(message):
    """Escreve uma mensagem no chat_out.txt para o jogo ler."""
    global _out_id
    _out_id += 1
    with open(CHAT_OUT, "a", encoding="utf-8") as f:
        f.write(f"{_out_id}|{message}\n")
    print(f"[ENVIADO] {message[:80]}{'...' if len(message) > 80 else ''}")


def cmd_send():
    msg = " ".join(sys.argv[2:])
    if not msg:
        print("[ERRO] Mensagem vazia")
        return
    send_out(msg)


def cmd_listen():
    lines = read_in()
    if not lines:
        print("(nenhuma mensagem)")
        return
    for entry in lines:
        print(f"[{entry['player']}] {entry['msg']}")


def cmd_tail():
    """Monitora continuamente o chat_in.txt."""
    ensure_files()
    last_size = os.path.getsize(CHAT_IN)
    print("[BRIDGE] Monitorando chat_in.txt... Pressione Ctrl+C para sair")
    try:
        while True:
            try:
                current_size = os.path.getsize(CHAT_IN)
                if current_size > last_size:
                    with open(CHAT_IN, "r", encoding="utf-8") as f:
                        f.seek(last_size)
                        new_data = f.read()
                    for line in new_data.strip().split("\n"):
                        line = line.strip()
                        if line:
                            parts = line.split("|", 2)
                            if len(parts) == 3:
                                print(f"[{parts[1]}] {parts[2]}")
                    last_size = current_size
                time.sleep(0.5)
            except Exception:
                break
    except KeyboardInterrupt:
        print("\n[BRIDGE] Monitoramento encerrado")


def cmd_chat():
    """Modo conversa interativa."""
    ensure_files()
    last_in_size = os.path.getsize(CHAT_IN) if os.path.exists(CHAT_IN) else 0

    def monitor_in():
        nonlocal last_in_size
        while True:
            try:
                current = os.path.getsize(CHAT_IN)
                if current > last_in_size:
                    with open(CHAT_IN, "r", encoding="utf-8") as f:
                        f.seek(last_in_size)
                        new_data = f.read()
                    for line in new_data.strip().split("\n"):
                        line = line.strip()
                        if line:
                            parts = line.split("|", 2)
                            if len(parts) == 3:
                                print(f"\n[JOGADOR] {parts[2]}")
                    last_in_size = current
            except Exception:
                pass
            time.sleep(0.5)

    t = threading.Thread(target=monitor_in, daemon=True)
    t.start()

    print("[BRIDGE] Modo conversa ativo. Digite sua resposta ou 'sair' para encerrar.")
    print("[BRIDGE] Mensagens do jogo aparecerao automaticamente.")
    try:
        while True:
            msg = input("> ").strip()
            if msg.lower() in ("sair", "exit", "quit"):
                break
            if msg:
                send_out(msg)
    except (KeyboardInterrupt, EOFError):
        print("\n[BRIDGE] Conversa encerrada")


def main():
    ensure_files()
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "chat":
        cmd_chat()
    elif cmd == "send":
        cmd_send()
    elif cmd == "listen":
        cmd_listen()
    elif cmd == "tail":
        cmd_tail()
    else:
        print(f"[ERRO] Comando desconhecido: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
