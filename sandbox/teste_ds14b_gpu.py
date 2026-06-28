"""Testa deepseek-r1:14b com GPU forcing vs deepseek-r1:7b para analise de codigo."""
import json, urllib.request, time, os, subprocess

OLLAMA = 'http://localhost:11434/api/generate'
BASE = 'E:/Projeto MCR'
OLLAMA_URL = OLLAMA

def chamar(modelo, prompt, temp=0.3, max_tokens=4096, timeout=300, forcar_gpu=False):
    t0 = time.time()
    try:
        opts = {'temperature': temp, 'num_ctx': 4096, 'num_predict': max_tokens}
        if forcar_gpu:
            opts['main_gpu'] = 0
            opts['num_gpu'] = 99
        body = {
            'model': modelo, 'prompt': prompt, 'stream': False,
            'options': opts
        }
        # deepseek raw mode
        if 'deepseek' in modelo:
            body['raw'] = False
        d = json.dumps(body).encode()
        req = urllib.request.Request(OLLAMA_URL, data=d,
            headers={'Content-Type': 'application/json'})
        resp = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        texto = (resp.get('response') or '').strip()
        tempo = round(time.time() - t0, 1)
        
        # GPU stats
        r = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used',
            '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=5)
        gpu = r.stdout.strip()
        
        return texto, tempo, gpu
    except Exception as e:
        return f'[ERRO] {e}', round(time.time() - t0, 1), '?'

# Carrega o Oraculo.lua para analise
with open(f'{BASE}/Canary/data-canary/scripts/MCR/oraculo.lua', 'r', encoding='utf-8', errors='replace') as f:
    codigo = f.read()
trecho = codigo[:8000]

prompt = f'''Analise o codigo Lua abaixo e ENCONTRE BUGS E PROBLEMAS DE SEGURANCA.
Para cada problema, informe: LINHA X - tipo - descricao - gravidade (ALTA/MEDIA/BAIXA).
Responda em PORTUGUES.

Codigo:
```lua
{trecho}
```'''

print('=' * 60)
print('COMPARACAO: deepseek-r1:7b (GPU) vs deepseek-r1:14b (GPU forcada)')
print('=' * 60)

# 1. deepseek-r1:7b (sempre rodou na GPU)
print('\n--- deepseek-r1:7b (ATUAL - GPU natural) ---')
texto7, tempo7, gpu7 = chamar('deepseek-r1:7b', prompt)
print(f'Tempo: {tempo7}s | Tam: {len(texto7)}c | GPU: {gpu7}')
with open(f'{BASE}/sandbox/analisar_ds7b_gpu.txt', 'w', encoding='utf-8') as f:
    f.write(texto7)
print(texto7[:500])

# 2. deepseek-r1:14b COM GPU forcing
print('\n--- deepseek-r1:14b (COM GPU forcing) ---')
texto14, tempo14, gpu14 = chamar('deepseek-r1:14b', prompt, forcar_gpu=True)
print(f'Tempo: {tempo14}s | Tam: {len(texto14)}c | GPU: {gpu14}')
with open(f'{BASE}/sandbox/analisar_ds14b_gpu.txt', 'w', encoding='utf-8') as f:
    f.write(texto14)
print(texto14[:500])

# 3. Comparacao QUALITATIVA
print('\n\n=== COMPARACAO QUALITATIVA ===')
import re

for nome, texto, tempo in [
    ('deepseek-r1:7b', texto7, tempo7),
    ('deepseek-r1:14b (GPU)', texto14, tempo14)
]:
    linhas = texto.count('LINHA')
    altas = len(re.findall(r'ALTA', texto))
    medias = len(re.findall(r'MEDIA', texto))
    baixas = len(re.findall(r'BAIXA', texto))
    palavras_problema = len(re.findall(r'(?:bug|erro|problema|falha|risco|vulnerabilidade)', texto.lower()))
    
    # Deteccoes especificas
    detectou_sql = 'sql' in texto.lower() or 'injection' in texto.lower()
    detectou_encoding = 'encoding' in texto.lower() or 'codifica' in texto.lower()
    detectou_guest = 'guest' in texto.lower() or 'convidado' in texto.lower()
    
    print(f'\n{nome}:')
    print(f'  Tempo: {tempo}s')
    print(f'  Tamanho: {len(texto)} chars')
    print(f'  "LINHA X": {linhas}x')
    print(f'  Gravidade: ALTA {altas}x | MEDIA {medias}x | BAIXA {baixas}x')
    print(f'  Palavras de problema: {palavras_problema}x')
    print(f'  SQL injection: {"✅" if detectou_sql else "❌"}')
    print(f'  Encoding: {"✅" if detectou_encoding else "❌"}')
    print(f'  Guest account: {"✅" if detectou_guest else "❌"}')

print(f'\nRespostas salvas em:')
print(f'  sandbox/analisar_ds7b_gpu.txt')
print(f'  sandbox/analisar_ds14b_gpu.txt')
