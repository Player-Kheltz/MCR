"""Apenas a parte 3 (analisar) do benchmark completo."""
import json, urllib.request, time, os

OLLAMA = 'http://localhost:11434/api/generate'
BASE = 'E:/Projeto MCR'

def chamar(modelo, prompt, temp=0.3, max_tokens=4096, timeout=300):
    t0 = time.time()
    try:
        d = json.dumps({
            'model': modelo, 'prompt': prompt, 'stream': False,
            'options': {'temperature': temp, 'num_ctx': 8192, 'num_predict': max_tokens}
        }).encode()
        req = urllib.request.Request(OLLAMA, data=d,
            headers={'Content-Type': 'application/json'})
        resp = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        texto = (resp.get('response') or '').strip()
        tempo = round(time.time() - t0, 1)
        return texto, tempo
    except Exception as e:
        return f'[ERRO] {e}', round(time.time() - t0, 1)

print('3. BENCHMARK: ANALISAR (deepseek7b vs qwen14b)')
print('=' * 60)

with open(f'{BASE}/Canary/data-canary/scripts/MCR/oraculo.lua', 'r', encoding='utf-8', errors='replace') as f:
    codigo_oraculo = f.read()

trecho_analise = codigo_oraculo[:8000]

prompt_analisar = f'''Analise o codigo Lua abaixo e ENCONTRE BUGS E PROBLEMAS DE SEGURANCA.
Para cada problema, informe: LINHA X - tipo - descricao - gravidade (ALTA/MEDIA/BAIXA).

Responda em PORTUGUES.

Codigo:
```lua
{trecho_analise}
```'''

# Testa DEEPSEEK 7b (atual)
print('\n--- DEEPSEEK 7b (ANALISAR ATUAL) ---')
texto_ds, tempo_ds = chamar('deepseek-r1:7b', prompt_analisar)
print(f'Tempo: {tempo_ds}s | Tam: {len(texto_ds)}c')
# Salva resposta completa
with open(f'{BASE}/sandbox/analisar_deepseek7b.txt', 'w', encoding='utf-8') as f:
    f.write(texto_ds)
print(texto_ds[:600])

# Testa QWEN 14b (candidato)
print('\n--- QWEN 14b (ANALISAR CANDIDATO) ---')
texto_qwen14, tempo_qwen14 = chamar('qwen2.5-coder:14b', prompt_analisar)
print(f'Tempo: {tempo_qwen14}s | Tam: {len(texto_qwen14)}c')
with open(f'{BASE}/sandbox/analisar_qwen14b.txt', 'w', encoding='utf-8') as f:
    f.write(texto_qwen14)
print(texto_qwen14[:600])

# Comparacao QUALITATIVA
print('\n\n=== COMPARACAO QUALITATIVA ===')

# Conta indicadores de qualidade
import re
for nome, texto in [('DEEPSEEK 7b', texto_ds), ('QWEN 14b', texto_qwen14)]:
    linhas = texto.count('LINHA')
    altas = texto.count('ALTA')
    medias = texto.count('MEDIA')
    baixas = texto.count('BAIXA')
    bugs_especificos = len(re.findall(r'(?:bug|erro|problema|falha|risco|vulnerabilidade)', texto.lower()))
    print(f'\n{nome}:')
    print(f'  Tempo: {tempo_ds if "DS" in nome else tempo_qwen14}s')
    print(f'  Tamanho: {len(texto)} chars')
    print(f'  "LINHA" mencionado: {linhas}x')
    print(f'  Gravidade ALTA: {altas}x | MEDIA: {medias}x | BAIXA: {baixas}x')
    print(f'  Palavras de problema: {bugs_especificos}x')
    # Verifica se menciona SQL injection
    if 'sql' in texto.lower() or 'injection' in texto.lower():
        print(f'  ✅ Detectou SQL injection')
    if 'conta convidada' in texto.lower() or 'guest' in texto.lower():
        print(f'  ✅ Detectou problema de conta convidada')
    if 'db.storeQuery' in texto.lower() or 'storeQuery' in texto.lower():
        print(f'  ✅ Detectou problema em db.storeQuery')

print('\nRespostas completas salvas em:')
print('  sandbox/analisar_deepseek7b.txt')
print('  sandbox/analisar_qwen14b.txt')
