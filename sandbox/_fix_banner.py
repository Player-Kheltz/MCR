#!/usr/bin/env python3
"""Corrige a linha do banner com problemas de quote."""
path = r'E:\Projeto MCR\scripts\mcr_devia\kernel.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_line = "    print(f'[Cloud]     python -c \"import json,time; json.dump({\\\"role\\\":\\\"cloud\\\",\\\"msg\\\":\\\"...\\\",\\\"decisao\\\":\\\"...\\\",\\\"alternativas\\\":[...],\\\"ts\\\":time.time()}, open(r\\'E:\\\\Projeto MCR\\\\sandbox\\\\.mcr_conversa.jsonl\\',\\'a\\'), ensure_ascii=False)\"')"
new_line = "    print('[Cloud]     Use: python para escrever .mcr_conversa.jsonl com role=cloud, msg, alternativas, decisao, ts')"

if old_line in content:
    content = content.replace(old_line, new_line)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    try:
        compile(content, path, 'exec')
        print('OK')
    except SyntaxError as e:
        print('ERRO:', e)
else:
    print('old_line nao encontrada. Buscando...')
    for i, line in enumerate(content.split('\n')):
        if 'json.dump' in line:
            print(f'  L{i+1}: {line[:100]}')
