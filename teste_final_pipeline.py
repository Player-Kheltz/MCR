import sys, time
sys.path.insert(0, r'E:\MCR')
from mcr_devia import processar

for pergunta in ['explique o que e SPA no Projeto MCR', 'traduza hello world']:
    t0 = time.time()
    r = processar(pergunta)
    t = time.time() - t0
    resp = r.get('resposta', '')
    print(f'> {pergunta}')
    print(f'  classe: {r["classe"]} tempo: {t:.1f}s')
    print(f'  resposta: {resp[:200]}')
    
    status = '?'
    if 'Progressao' in resp or 'Aventureiro' in resp:
        status = 'ACERTOU SPA'
    elif 'Single' in resp or 'pagina' in resp:
        status = 'ERROU (Single Page)'
    elif 'Ola Mundo' in resp or 'Ola' in resp:
        status = 'ACERTOU TRADUCAO'
    print(f'  STATUS: {status}')
