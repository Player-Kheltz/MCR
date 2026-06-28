"""Investiga modelo qwen14b e VRAM."""
import json, urllib.request, subprocess

# 1. Ver detalhes do modelo
print('=== Detalhes do qwen2.5-coder:14b ===')
try:
    req = urllib.request.Request('http://localhost:11434/api/show',
        data=json.dumps({'model': 'qwen2.5-coder:14b'}).encode(),
        headers={'Content-Type': 'application/json'})
    r = urllib.request.urlopen(req, timeout=15)
    info = json.loads(r.read())
    print(f'  Formato: {info.get("file_type", "?")}')
    print(f'  Parametros: {info.get("num_parameters", "?")}')
    print(f'  Quantizacao: {info.get("quantization_level", "?")}')
    print(f'  Required VRAM: {info.get("required_vram", "?")}')
    mod_info = info.get('model_info', info.get('details', {}))
    print(f'  Info: {json.dumps(mod_info, indent=2)[:500]}')
except Exception as e:
    print(f'  ERRO: {e}')

# 2. Ver GPU
print('\n=== GPU Status ===')
r = subprocess.run(['nvidia-smi', '--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu',
    '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=10)
print(f'  {r.stdout.strip()}')

# 3. VRAM disponivel
# Parse e calcula
for line in r.stdout.strip().split('\n'):
    parts = [p.strip() for p in line.split(',')]
    if len(parts) >= 5:
        total_mb = int(parts[2])
        used_mb = int(parts[3])
        free_mb = int(parts[4])
        print(f'\n  GPU {parts[0]}: {parts[1]}')
        print(f'  VRAM: {used_mb}MB usados / {total_mb}MB total ({free_mb}MB livres)')
        # qwen14b Q4_K_M ~ 8.5GB = 8700MB
        if free_mb > 9000:
            print(f'  ✅ {free_mb}MB livres - qwen14b (8.7GB) cabe TRANQUILAMENTE')
        elif free_mb > 8700:
            print(f'  ✅ {free_mb}MB livres - qwen14b cabe com margem')
        elif free_mb > 8000:
            print(f'  ⚠️ {free_mb}MB livres - qwen14b cabe APERTADO (8.7GB)')
        else:
            print(f'  ❌ {free_mb}MB livres - qwen14b NAO cabe sem quantizacao')

# 4. Ver modelos em memoria
print('\n=== Modelos no Ollama (ps) ===')
try:
    r2 = urllib.request.urlopen('http://localhost:11434/api/ps', timeout=5)
    ps = json.loads(r2.read())
    for m in ps.get('models', []):
        print(f'  {m["name"]} - VRAM: {m.get("size_vram", 0)//1024//1024}MB / size: {m["size"]//1024//1024}MB')
except Exception as e:
    print(f'  ERRO: {e}')

# 5. Listar quantizacoes disponiveis
print('\n=== Quantizacoes disponiveis (tags) ===')
try:
    r3 = urllib.request.urlopen('http://localhost:11434/api/tags', timeout=10)
    tags = json.loads(r3.read())
    qwen_tags = [m for m in tags.get('models', []) if 'qwen2.5' in m['name'] and '14b' in m['name']]
    for m in qwen_tags:
        print(f'  {m["name"]} - {m["size"]//1024//1024}MB')
except Exception as e:
    print(f'  ERRO: {e}')
