"""Teste: pergunta MCR ESPECIFICA sobre SPA, dominios e estados da alma."""
import json, subprocess, sys, time

cmd = {'cmd': 'perguntar', 'args': ['Como funciona o gerenciamento de afinidade no SPA? Como ele e interligado com os dominios e os estados da Alma?']}
with open('E:/Projeto MCR/sandbox/.mcr_cmd.json', 'w') as f:
    json.dump(cmd, f, ensure_ascii=False)

t0 = time.time()
r = subprocess.run([sys.executable, 'E:/Projeto MCR/scripts/mcr_devia/MCR_DevIA-Kernel.py',
    '--json', 'E:/Projeto MCR/sandbox/.mcr_cmd.json'],
    capture_output=True, text=True, timeout=300)

for l in r.stdout.split(chr(10)):
    ls = l.strip()
    if 'Escopo' in ls or 'CR instrucao' in ls or 'Enricher' in ls or 'ToT' in ls or 'Pergunta FORCADA' in ls:
        print(ls[:160])

try:
    resp = open('E:/Projeto MCR/sandbox/.mcr_resposta.txt', 'r').read()
    print()
    print('RESPOSTA (' + str(len(resp)) + ' chars):')
    print(resp[:2000])
    if len(resp) > 2000:
        print('...')
    
    # Metricas
    print()
    print('--- METRICAS ---')
    print('  Tamanho:', len(resp), 'chars')
    print('  Citou afinidade:', 'afinidade' in resp.lower())
    print('  Citou dominios:', 'dominio' in resp.lower() or 'dominios' in resp.lower())
    print('  Citou estados da alma:', 'alma' in resp.lower())
    print('  Citou elementos (fogo/gelo/terra/energia):', any(e in resp.lower() for e in ['fogo', 'gelo', 'terra', 'energia']))
    print('  Citou numeros (niveis 0-25):', any(str(n) in resp for n in range(1, 26)))
except Exception as e:
    print('ERRO:', e)

print('Tempo:', round(time.time()-t0, 1), 's')
