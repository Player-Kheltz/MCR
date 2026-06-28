"""Benchmark COMPLETO: code, texto, analisar.
Testa qwen7b vs qwen14b para código e análise,
deepseek7b para análise,
e qwen14b+tradução para texto.
"""
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

# ============================
# 1. BENCHMARK CODE
# ============================
print('=' * 60)
print('1. BENCHMARK: CODE (analise do Oraculo.lua)')
print('=' * 60)

# Pega um trecho de 100 linhas do Oraculo.lua para analise
with open(f'{BASE}/Canary/data-canary/scripts/MCR/oraculo.lua', 'r', encoding='utf-8', errors='replace') as f:
    codigo_oraculo = f.read()

trecho_codigo = codigo_oraculo[:5000]

prompt_code = f'''Analise o codigo Lua abaixo e responda:
1. Quais as principais funcoes e suas responsabilidades?
2. Ha bugs ou problemas de seguranca?
3. Sugestoes de melhoria.

Responda EM PORTUGUES, citando LINHAS ESPECIFICAS.

Codigo:
```lua
{trecho_codigo}
```'''

modelos_code = [
    ('qwen2.5-coder:7b', 'QWEN 7b (CODE)'),
    ('qwen2.5-coder:14b', 'QWEN 14b (CODE)'),
]

resultados_code = []
for modelo, label in modelos_code:
    print(f'\n  --- {label} ---')
    texto, tempo = chamar(modelo, prompt_code)
    print(f'  Tempo: {tempo}s | Tam: {len(texto)}c')
    print(f'  {texto[:300]}')
    resultados_code.append({'modelo': modelo, 'label': label, 'texto': texto, 'tempo': tempo, 'tamanho': len(texto)})

# ============================
# 2. BENCHMARK TEXTO (com tradutor)
# ============================
print('\n' + '=' * 60)
print('2. BENCHMARK: TEXTO (lore + tradutor)')
print('=' * 60)

prompt_texto = '''Crie uma descricao de um artefato magico chamado "Cristal de Eternidade" para o projeto MCR (Tibia). 
Descreva sua aparencia, origem, poderes e onde pode ser encontrado.
Use nomes proprios em portugues. Seja detalhado e criativo.'''

# Testa llama3.1:8b (atual)
print('\n  --- llama3.1:8b (TEXTO ATUAL) ---')
texto_llama, tempo_llama = chamar('llama3.1:8b', prompt_texto, max_tokens=2048)
print(f'  Tempo: {tempo_llama}s | Tam: {len(texto_llama)}c')
print(f'  {texto_llama[:300]}')

# Testa qwen2.5-coder:14b (candidato)
print('\n  --- qwen2.5-coder:14b (TEXTO CANDIDATO) ---')
texto_qwen14, tempo_qwen14 = chamar('qwen2.5-coder:14b', prompt_texto, max_tokens=2048)
print(f'  Tempo: {tempo_qwen14}s | Tam: {len(texto_qwen14)}c')
print(f'  {texto_qwen14[:300]}')

# Testa qwen14b + tradutor
print('\n  --- qwen2.5-coder:14b + TRADUTOR ---')
try:
    import sys
    sys.path.insert(0, f'{BASE}/scripts/mcr_devia')
    from modulos.tradutor import traduzir
    texto_qwen14_traduzido = traduzir(texto_qwen14)
    print(f'  Tam original: {len(texto_qwen14)}c | Tam traduzido: {len(texto_qwen14_traduzido)}c')
    print(f'  Original: {texto_qwen14[:200]}')
    print(f'  Traduzido: {texto_qwen14_traduzido[:200]}')
    # Verificou se o tradutor modificou algo
    if texto_qwen14 == texto_qwen14_traduzido:
        print('  ⚠️ Tradutor retornou IGUAL (texto ja em PT-BR)')
    else:
        print('  ✅ Tradutor modificou o texto')
except Exception as e:
    print(f'  ERRO tradutor: {e}')
    texto_qwen14_traduzido = texto_qwen14

# ============================
# 3. BENCHMARK ANALISAR (deepseek vs qwen14b)
# ============================
print('\n' + '=' * 60)
print('3. BENCHMARK: ANALISAR (deepseek7b vs qwen14b)')
print('=' * 60)

# Pega 200 linhas do codigo (mais para analise profunda)
trecho_analise = codigo_oraculo[:8000]

prompt_analisar = f'''Analise o codigo Lua abaixo e ENCONTRE BUGS E PROBLEMAS DE SEGURANCA.
Para cada problema, informe: LINHA X - tipo - descricao - gravidade (ALTA/MEDIA/BAIXA).

Responda em PORTUGUES.

Codigo:
```lua
{trecho_analise}
```'''

modelos_analisar = [
    ('deepseek-r1:7b', 'DEEPSEEK 7b (ANALISAR)'),
    ('qwen2.5-coder:14b', 'QWEN 14b (ANALISAR)'),
]

resultados_analisar = []
for modelo, label in modelos_analisar:
    print(f'\n  --- {label} ---')
    texto, tempo = chamar(modelo, prompt_analisar)
    print(f'  Tempo: {tempo}s | Tam: {len(texto)}c')
    print(f'  {texto[:400]}')
    resultados_analisar.append({
        'modelo': modelo, 'label': label, 'texto': texto,
        'tempo': tempo, 'tamanho': len(texto),
        'bugs_encontrados': texto.count('LINHA') + texto.count('ALTA') + texto.count('Erro')
    })

# ============================
# RELATORIO
# ============================
print('\n\n' + '=' * 60)
print('RELATORIO FINAL')
print('=' * 60)

print('\n--- CODE (analise do Oraculo.lua) ---')
for r in resultados_code:
    print(f'  {r["label"]:25s} {r["tempo"]:>6.1f}s {r["tamanho"]:>6d}c')

print('\n--- TEXTO (descricao de artefato) ---')
print(f'  llama3.1:8b:          {tempo_llama:6.1f}s {len(texto_llama):6d}c')
print(f'  qwen2.5-coder:14b:    {tempo_qwen14:6.1f}s {len(texto_qwen14):6d}c')
print(f'  qwen14b + tradutor:   {len(texto_qwen14_traduzido):6d}c (modificado: {"sim" if texto_qwen14 != texto_qwen14_traduzido else "nao"})')

print('\n--- ANALISAR (bugs no Oraculo.lua) ---')
for r in resultados_analisar:
    print(f'  {r["label"]:25s} {r["tempo"]:>6.1f}s {r["tamanho"]:>6d}c bugs_indicados: {r["bugs_encontrados"]}')

# Salva resultados
path = f'{BASE}/sandbox/benchmark_completo.json'
with open(path, 'w', encoding='utf-8') as f:
    # So salva metadados, nao textos completos (podem ser grandes)
    resumo = {
        'code': [{'modelo': r['modelo'], 'tempo': r['tempo'], 'tamanho': r['tamanho']} for r in resultados_code],
        'texto': {
            'llama3.1:8b': {'tempo': tempo_llama, 'tamanho': len(texto_llama)},
            'qwen2.5-coder:14b': {'tempo': tempo_qwen14, 'tamanho': len(texto_qwen14)},
            'qwen14b+tradutor': {'tempo': tempo_qwen14, 'tamanho': len(texto_qwen14_traduzido), 'modificado': texto_qwen14 != texto_qwen14_traduzido},
        },
        'analisar': [{'modelo': r['modelo'], 'tempo': r['tempo'], 'tamanho': r['tamanho'], 'bugs': r['bugs_encontrados']} for r in resultados_analisar],
    }
    json.dump(resumo, f, ensure_ascii=False, indent=2)
print(f'\nResumo salvo em: {path}')
print('=' * 60)
