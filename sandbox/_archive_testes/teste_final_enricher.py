"""Teste final da pipeline com Enricher."""
import json, subprocess, sys, time

cmd = {'cmd': 'perguntar', 'args': ['O que e .lua no projeto MCR?']}
with open('E:/Projeto MCR/sandbox/.mcr_cmd.json', 'w') as f:
    json.dump(cmd, f, ensure_ascii=False)

t0 = time.time()
r = subprocess.run([sys.executable, 'E:/Projeto MCR/scripts/mcr_devia/MCR_DevIA-Kernel.py',
    '--json', 'E:/Projeto MCR/sandbox/.mcr_cmd.json'],
    capture_output=True, text=True, timeout=300)

for l in r.stdout.split(chr(10)):
    ls = l.strip()
    if 'Enricher' in ls or 'ToT' in ls or 'Auto-Revisor' in ls:
        print(ls[:160])

try:
    resp = open('E:/Projeto MCR/sandbox/.mcr_resposta.txt', 'r').read()
    has_minecraft = 'minecraft' in resp.lower()
    print()
    print('RESPOSTA (' + str(len(resp)) + ' chars):')
    print(resp[:600])
    print()
    print('Minecraft: ' + ('SIM' if has_minecraft else 'NAO'))
except Exception as e:
    print('ERRO:', e)

print('Tempo:', round(time.time()-t0, 1), 's')
