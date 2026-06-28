"""Benchmark COMPLETO do qwen14b AGORA NA GPU, vs todos os modelos atuais.
Testa: pesado, code, texto, conceito, analisar - 5 cenarios reais.
"""
import json, urllib.request, time, os, subprocess, re

OLLAMA = 'http://localhost:11434/api/generate'
BASE = 'E:/Projeto MCR'

def chamar(modelo, prompt, temp=0.3, max_tokens=3072, timeout=180, forcar_gpu=False):
    t0 = time.time()
    try:
        opts = {'temperature': temp, 'num_ctx': 4096, 'num_predict': max_tokens}
        if forcar_gpu:
            opts['main_gpu'] = 0
            opts['num_gpu'] = 99
        body = {'model': modelo, 'prompt': prompt, 'stream': False, 'options': opts}
        if 'deepseek' in modelo:
            body['raw'] = False
        d = json.dumps(body).encode()
        req = urllib.request.Request(OLLAMA, data=d, headers={'Content-Type': 'application/json'})
        resp = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        texto = (resp.get('response') or '').strip()
        tempo = round(time.time() - t0, 1)
        r = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used',
            '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=5)
        return texto, tempo, r.stdout.strip()
    except Exception as e:
        return f'[ERRO] {e}', 0, '?'

def medir(modelo, nome_teste, prompt, label, forcar_gpu=False):
    """Roda teste e retorna metricas."""
    print(f'  >> {nome_teste}...', end=' ', flush=True)
    texto, tempo, gpu = chamar(modelo, prompt, forcar_gpu=forcar_gpu)
    print(f'{tempo}s | {len(texto)}c | GPU:{gpu[:10]}')
    
    # Metricas
    metricas = {
        'modelo': modelo,
        'teste': nome_teste,
        'tempo': tempo,
        'tamanho': len(texto),
        'gpu_util': gpu,
        'nomes': len(set(re.findall(r'\b[A-Z][a-z]{2,}\b', texto))),
        'linhas_citadas': texto.count('LINHA'),
        'tem_codigo': 1 if any(m in texto for m in ['```lua', '```python', '```cpp', 'local function', 'def ']) else 0,
    }
    
    # Salva texto
    fname = modelo.replace(':', '_').replace('.', '_').replace('-', '_')
    path = f'{BASE}/sandbox/bench_{nome_teste}_{fname}.txt'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(texto)
    
    return metricas

# Carrega Oraculo.lua para testes de codigo
with open(f'{BASE}/Canary/data-canary/scripts/MCR/oraculo.lua', 'r', encoding='utf-8', errors='replace') as f:
    oraculo = f.read()[:6000]

print('=' * 70)
print('BENCHMARK COMPLETO - qwen14b GPU vs modelos atuais')
print('=' * 70)

resultados = []

# ============================================================
# TESTE 1: PESADO (Lore Eridanus)
# ============================================================
print('\n--- TESTE 1: PESADO (Lore Eridanus) ---')
prompt_lore = """Crie uma lore detalhada para a cidade inicial Eridanus do projeto MCR (servidor de Tibia baseado em Canary).
Inclua nomes proprios de personagens, lugares e artefatos em portugues.
Responda em PT-BR."""

resultados.append(medir('qwen2.5-coder:7b', 'lore_qwen7b', prompt_lore, 'Qwen7b'))
resultados.append(medir('qwen2.5-coder:14b', 'lore_qwen14b', prompt_lore, 'Qwen14b', forcar_gpu=True))
resultados.append(medir('llama3.1:8b', 'lore_llama8b', prompt_lore, 'Llama8b'))

# ============================================================
# TESTE 2: CODE (Gerar codigo Lua)
# ============================================================
print('\n--- TESTE 2: CODE (Gerar NPC Lua) ---')
prompt_code = """Crie um NPC em Lua para o servidor Canary (OTServ) que:
- Seja um ferreiro chamado Mestre Borin
- Venda armas e armorias
- Tenha pelo menos 5 itens no estoque
- Use o sistema KeywordHandler
- Responda em portugues

Codigo completo em Lua:"""

resultados.append(medir('qwen2.5-coder:7b', 'code_qwen7b', prompt_code, 'Qwen7b'))
resultados.append(medir('qwen2.5-coder:14b', 'code_qwen14b', prompt_code, 'Qwen14b', forcar_gpu=True))

# ============================================================
# TESTE 3: TEXTO (Descricao PT-BR)
# ============================================================
print('\n--- TESTE 3: TEXTO (Descricao PT-BR) ---')
prompt_texto = """Descreva a Sala do Trono de Eridanus, o castelo real do projeto MCR.
Use linguagem descritiva, nomes proprios, e mencione elementos decorativos.
Responda em portugues brasileiro."""

resultados.append(medir('llama3.1:8b', 'texto_llama8b', prompt_texto, 'Llama8b'))
resultados.append(medir('qwen2.5-coder:14b', 'texto_qwen14b', prompt_texto, 'Qwen14b', forcar_gpu=True))

# ============================================================
# TESTE 4: CONCEITO (Explicar conceito)
# ============================================================
print('\n--- TESTE 4: CONCEITO (Explicar SPA vs SHC) ---')
prompt_conceito = """Explique a diferenca entre SPA (Sistema de Progressao do Aventureiro) e SHC (Sistema de Habilidades Contextuais) no MCR.
Seja detalhado e cite exemplos. Responda em PT-BR."""

resultados.append(medir('deepseek-r1:7b', 'conceito_ds7b', prompt_conceito, 'Deepseek7b'))
resultados.append(medir('qwen2.5-coder:14b', 'conceito_qwen14b', prompt_conceito, 'Qwen14b', forcar_gpu=True))

# ============================================================
# TESTE 5: ANALISAR (Analisar codigo Oraculo)
# ============================================================
print('\n--- TESTE 5: ANALISAR (Analisar Oraculo.lua) ---')
prompt_analisar = f"""Analise o codigo Lua abaixo. Encontre bugs e problemas de seguranca.
Responda em PT-BR, citando LINHAS ESPECIFICAS.

```lua
{oraculo}
```"""

resultados.append(medir('deepseek-r1:7b', 'analisar_ds7b', prompt_analisar, 'Deepseek7b'))
resultados.append(medir('qwen2.5-coder:14b', 'analisar_qwen14b', prompt_analisar, 'Qwen14b', forcar_gpu=True))

# ============================================================
# RELATORIO
# ============================================================
print('\n\n' + '=' * 70)
print('RELATORIO FINAL - qwen14b GPU vs Modelos Atuais')
print('=' * 70)

# Agrupa por teste
testes_agrupados = {}
for r in resultados:
    test_name = r['teste'].split('_')[0]
    if test_name not in testes_agrupados:
        testes_agrupados[test_name] = []
    testes_agrupados[test_name].append(r)

for test_name, items in testes_agrupados.items():
    print(f'\n{test_name.upper()}:')
    print(f'  {"Modelo":25s} {"Tempo":>7s} {"Tam":>6s} {"Nomes":>6s} {"Codigo":>7s} {"GPU":>12s}')
    print(f'  {"-"*63}')
    for r in items:
        modelo_curto = r['modelo'].split(':')[0][:20] + ':' + r['modelo'].split(':')[-1][:5]
        gpu_percent = r['gpu_util'].split(',')[0] if r['gpu_util'] != '?' else '?'
        print(f'  {modelo_curto:25s} {r["tempo"]:>6.1f}s {r["tamanho"]:>6d} {r["nomes"]:>6d} {r["tem_codigo"]:>7d} {gpu_percent:>6s}%')

# Decisoes
print('\n\n=== RECOMENDACOES ===')
print(f'{"Rota":15s} {"Atual":15s} {"Candidato":15s} {"Veredito":15s}')
print(f'{"-"*60}')
for test_name in ['lore', 'code', 'texto', 'conceito', 'analisar']:
    items = testes_agrupados.get(test_name, [])
    if not items:
        continue
    melhor = max(items, key=lambda x: (x['nomes'] + x['tem_codigo']*10, -x['tempo']))
    pior = min(items, key=lambda x: (x['nomes'] + x['tem_codigo']*10, -x['tempo']))
    # Encontra o modelo atual (7b, deepseek, llama)
    atual = [i for i in items if '7b' in i['modelo'] or 'llama' in i['modelo'] or 'deepseek' in i['modelo']]
    candidato = [i for i in items if '14b' in i['modelo']]
    
    atual_name = atual[0]['modelo'].split(':')[0][:10] if atual else '?'
    cand_name = candidato[0]['modelo'].split(':')[0][:10] if candidato else '?'
    
    # Decide
    if candidato and atual:
        c = candidato[0]
        a = atual[0]
        # Qualidade: nomes + tem_codigo*10
        qual_c = c['nomes'] + c['tem_codigo']*10
        qual_a = a['nomes'] + a['tem_codigo']*10
        if qual_c > qual_a:
            voto = f'✅ Subir 14b'
        elif qual_c == qual_a and c['tempo'] < a['tempo'] * 2:
            voto = '⚠️ Empate'
        else:
            voto = f'❌ Manter'
        print(f'{test_name:15s} {atual_name:15s} {cand_name:15s} {voto:15s}')

print('\n' + '=' * 70)
