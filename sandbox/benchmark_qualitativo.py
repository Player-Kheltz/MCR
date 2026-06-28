"""Re-benchmark QUALITATIVO: compara a QUALIDADE real das respostas dos 4 modelos."""
import json, urllib.request, time

OLLAMA = 'http://localhost:11434/api/generate'
BASE = 'E:/Projeto MCR'

def chamar(modelo, prompt, temp=0.3, max_tokens=2048, timeout=180):
    t0 = time.time()
    try:
        d = json.dumps({
            'model': modelo,
            'prompt': prompt,
            'stream': False,
            'options': {'temperature': temp, 'num_ctx': 8192, 'num_predict': max_tokens}
        }).encode()
        req = urllib.request.Request(OLLAMA, data=d,
            headers={'Content-Type': 'application/json'})
        resp = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        texto = (resp.get('response') or '').strip()
        tempo = round(time.time() - t0, 1)
        return texto, tempo
    except Exception as e:
        return f'[ERRO] {e}', round(time.time() - t0, 3)

# AGORA com contexto MCR explicito no prompt!
print("=" * 60)
print("BENCHMARK QUALITATIVO - LORE ERIDANUS")
print("(com contexto MCR explicito no prompt)")
print("=" * 60)

prompt_lore = """CONTEXTO: MCR = servidor customizado de Tibia baseado em Canary (OTServ). SPA = Sistema de Progressao do Aventureiro. SHC = Sistema de Habilidades Contextuais. Eridanus = cidade inicial. Dominios elementais: Fogo, Gelo, Terra, Energia.

Crie uma lore DETALHADA para a cidade inicial Eridanus do projeto MCR (Tibia).
Inclua nomes proprios de personagens, lugares e artefatos em portugues.
Use a tematica de Tibia (medieval, magia, elementoals, masmorras).
Responda em PT-BR."""

for modelo in ['qwen2.5-coder:7b', 'qwen2.5-coder:14b', 'deepseek-r1:7b', 'deepseek-r1:14b']:
    print(f'\n{"=" * 60}')
    print(f'MODELO: {modelo}')
    print(f'{"=" * 60}')
    
    texto, tempo = chamar(modelo, prompt_lore, max_tokens=3072)
    
    # Salva
    fname = modelo.replace(':', '_').replace('.', '_')
    path = f'{BASE}/sandbox/lore_qualidade_{fname}.txt'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(texto)
    
    print(f'Tempo: {tempo}s')
    print(f'Tamanho: {len(texto)} chars')
    print()
    print(texto[:2500])
    print('\n...')

print("\n\nPRONTO. Respostas salvas em sandbox/lore_qualidade_*.txt")
