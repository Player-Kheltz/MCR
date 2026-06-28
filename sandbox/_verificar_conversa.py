#!/usr/bin/env python3
import json
with open(r'E:\Projeto MCR\sandbox\.mcr_conversa.jsonl', 'r', encoding='utf-8') as f:
    lines = f.readlines()[-6:]
for l in lines:
    d = json.loads(l)
    role = d.get('role', '?')
    msg = str(d.get('msg', ''))[:80]
    print(f'[{role}]: {msg}')
