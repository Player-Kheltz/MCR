"""Teste rapido Deepseek R1 - raw=false, num_predict=8192"""
import json, urllib.request

payload = json.dumps({
    'model': 'deepseek-r1:7b',
    'prompt': 'Say hello in 5 words.',
    'stream': False,
    'options': {'temperature': 0.1, 'num_predict': 8192}
}).encode()

req = urllib.request.Request(
    'http://localhost:11434/api/generate',
    data=payload,
    headers={'Content-Type': 'application/json'}
)
resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
r = resp.get('response', '')
print(f'Tokens: {resp.get("eval_count",0)}')
print(f'Chars: {len(r)}')
print(f'Tempo: {resp.get("eval_duration",0)/1e9:.1f}s')
print('---RESPOSTA BRUTA---')
print(r[:500])
if '<' in r and '>' in r:
    print('\n--- TEM TAGS DE THINKING ---')
else:
    print('\n--- SEM TAGS - RESPOSTA DIRETA ---')
