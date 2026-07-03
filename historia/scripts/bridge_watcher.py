#!/usr/bin/env python3
"""
bridge_watcher.py — Monitora chat_in.txt e escreve novas mensagens em bridge_output.txt
Uso: python scripts/bridge_watcher.py (deixa rodando em background)
"""
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAT_IN = os.path.join(BASE_DIR, "Canary", "data", "logs", "chat_in.txt")
OUTPUT = os.path.join(BASE_DIR, "bridge_output.txt")

last_size = 0
if os.path.exists(CHAT_IN):
    last_size = os.path.getsize(CHAT_IN)

while True:
    try:
        if os.path.exists(CHAT_IN):
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
                            msg = f"[{parts[1]}] {parts[2]}"
                        else:
                            msg = line
                        with open(OUTPUT, "a", encoding="utf-8") as out:
                            out.write(f"{int(time.time())}|{msg}\n")
                last_size = current_size
        time.sleep(1)
    except Exception as e:
        with open(OUTPUT, "a", encoding="utf-8") as out:
            out.write(f"[ERRO] {e}\n")
        time.sleep(5)
