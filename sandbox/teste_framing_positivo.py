"""Teste final: verificar se MCR_IDENTITY sem negacao resolve 'Minecraft'."""
import json, subprocess, sys, time

cmd = {'cmd': 'perguntar', 'args': ['O que e .lua no projeto MCR?']}
with open('E:/Projeto MCR/sandbox/.mcr_cmd.json', 'w') as f:
    json.dump(cmd, f)

t0 = time.time()
r = subprocess.run([sys.executable, 'E:/Projeto MCR/scripts/mcr_devia/MCR_DevIA-Kernel.py',
    '--json', 'E:/Projeto MCR/sandbox/.mcr_cmd.json'],
    capture_output=True, text=True, timeout=300)

# Linhas relevantes
for l in r.stdout.split(chr(10)):
    ls = l.strip()
    if 'Enricher' in ls or 'CR instrucao' in ls:
        print(ls[:150])

# Resposta final
try:
    resp = open('E:/Projeto MCR/sandbox/.mcr_resposta.txt', 'r').read()
    has_minecraft = 'minecraft' in resp.lower()
    has_tibia = 'tibia' in resp.lower()
    utils = 'scripts' in resp.lower() and 'mcr_devia' in resp.lower()
    
    print()
    print('RESPOSTA (' + str(len(resp)) + ' chars):')
    print(resp[:800])
    print()
    print('RESULTADO:')
    print('  Minecraft mencionado: ' + ('❌ SIM' if has_minecraft else '✅ NAO'))
    print('  Tibia mencionado: ' + ('✅ SIM' if has_tibia else '❌ NAO'))
    print('  Dados tecnicos usados: ' + ('✅ SIM' if utils else '⚠️ PARCIAL'))
except Exception as e:
    print('ERRO ao ler resposta:', e)

print(f'Tempo: {round(time.time()-t0,1)}s')
