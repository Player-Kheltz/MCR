"""Teste final: pergunta GERAL sem MCR."""
import json, subprocess, sys, time

cmd = {'cmd': 'perguntar', 'args': ['Explique o que e um buraco de minhoca (wormhole) em termos simples.']}
with open('E:/Projeto MCR/sandbox/.mcr_cmd.json', 'w') as f:
    json.dump(cmd, f, ensure_ascii=False)

t0 = time.time()
r = subprocess.run([sys.executable, 'E:/Projeto MCR/scripts/mcr_devia/MCR_DevIA-Kernel.py',
    '--json', 'E:/Projeto MCR/sandbox/.mcr_cmd.json'],
    capture_output=True, text=True, timeout=120)

for l in r.stdout.split(chr(10)):
    ls = l.strip()
    if 'Escopo' in ls or 'Pipeline] OK' in ls:
        print(ls[:150])

try:
    resp = open('E:/Projeto MCR/sandbox/.mcr_resposta.txt', 'r').read()
    mcr_terms = ['projeto mcr', 'tibia', 'canary', 'otserv', 'otclient', 'spa', 'shc', 'eridanus']
    found = [t for t in mcr_terms if t in resp.lower()]
    
    print()
    print('RESPOSTA (' + str(len(resp)) + ' chars):')
    print(resp[:800])
    print()
    if found:
        print('MCR VAZOU:', ', '.join(found))
    else:
        print('✅ RESPOSTA LIMPA - sem termos MCR')
except Exception as e:
    print('ERRO:', e)

print('Tempo:', round(time.time()-t0, 1), 's')
