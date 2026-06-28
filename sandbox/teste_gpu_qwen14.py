"""Testa qwen14b com config para caber na GPU (10GB VRAM)."""
import json, urllib.request, time, subprocess

OLLAMA = 'http://localhost:11434/api/generate'

def teste(descricao, options):
    print(f'\n=== {descricao} ===')
    t0 = time.time()
    prompt = 'Explique o que e SPA no projeto MCR em 3 frases curtas.'
    d = json.dumps({
        'model': 'qwen2.5-coder:14b',
        'prompt': prompt,
        'stream': False,
        'options': options
    }).encode()
    try:
        req = urllib.request.Request(OLLAMA, data=d,
            headers={'Content-Type': 'application/json'})
        resp = json.loads(urllib.request.urlopen(req, timeout=180).read())
        texto = (resp.get('response') or '').strip()
        tempo = round(time.time() - t0, 1)
        
        # Ver GPU usage
        r = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,utilization.memory,memory.used',
            '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=5)
        gpu_stats = r.stdout.strip()
        
        print(f'  Tempo: {tempo}s')
        print(f'  GPU: {gpu_stats}')
        print(f'  Tokens/s: {len(texto.split())/tempo:.1f}')
        print(f'  Resposta: {texto[:200]}')
        return {'tempo': tempo, 'texto': texto, 'gpu': gpu_stats}
    except Exception as e:
        print(f'  ERRO: {e}')
        return None

# GPU atual antes dos testes
print('=== GPU ANTES ===')
r = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.free',
    '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=5)
print(f'  {r.stdout.strip()}')

# Teste 1: qwen7b (atual, referencia)
teste('QWEN7b - config ATUAL (ctx=4096)', {
    'num_ctx': 4096, 'num_predict': 512, 'temperature': 0.3
})

# Teste 2: qwen14b com contexto 4096 (reduz KV cache)
teste('QWEN14b - ctx=4096 (reduzido)', {
    'num_ctx': 4096, 'num_predict': 512, 'temperature': 0.3
})

# Teste 3: qwen14b com contexto 2048 (minimo)
teste('QWEN14b - ctx=2048 (minimo)', {
    'num_ctx': 2048, 'num_predict': 256, 'temperature': 0.3
})

# Teste 4: qwen14b com contexto 4096 + num_gpu parcial
teste('QWEN14b - ctx=4096, main_gpu=0 (forcar GPU)', {
    'num_ctx': 4096, 'num_predict': 512, 'temperature': 0.3,
    'main_gpu': 0, 'num_gpu': 99
})

# GPU depois
print('\n=== GPU DEPOIS ===')
r = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.free',
    '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=5)
print(f'  {r.stdout.strip()}')
