"""Teste: pergunta MCR deve ativar pipeline completo."""
import json, subprocess, sys, time

cmd = {'cmd': 'perguntar', 'args': ['Explique o que e SPA e SHC no projeto MCR']}
with open('E:/Projeto MCR/sandbox/.mcr_cmd.json', 'w') as f:
    json.dump(cmd, f, ensure_ascii=False)

t0 = time.time()
r = subprocess.run([sys.executable, 'E:/Projeto MCR/scripts/mcr_devia/MCR_DevIA-Kernel.py',
    '--json', 'E:/Projeto MCR/sandbox/.mcr_cmd.json'],
    capture_output=True, text=True, timeout=300)

for l in r.stdout.split(chr(10)):
    ls = l.strip()
    if 'Escopo' in ls or 'CR instrucao' in ls or 'Enricher OK' in ls or 'ToT' in ls:
        print(ls[:150])

try:
    resp = open('E:/Projeto MCR/sandbox/.mcr_resposta.txt', 'r').read()
    has_minecraft = 'minecraft' in resp.lower()
    spa_correto = 'progressao' in resp.lower() or 'progressão' in resp.lower()
    shc_correto = 'contextuais' in resp.lower()
    
    print()
    print('RESPOSTA (' + str(len(resp)) + ' chars):')
    print(resp[:800])
    print()
    print('Resultados:')
    print('  Escopo MCR ativado: ' + ('✅ SIM' if 'Escopo: MCR' in r.stdout else '❌'))
    print('  Minecraft: ' + ('❌ SIM' if has_minecraft else '✅ NAO'))
    print('  SPA = Progressao: ' + ('✅' if spa_correto else '❌'))
    print('  SHC = Contextuais: ' + ('✅' if shc_correto else '❌'))
except Exception as e:
    print('ERRO:', e)

print('Tempo:', round(time.time()-t0, 1), 's')
