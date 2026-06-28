"""Benchmark dos novos modelos 14b para MCR-DevIA.
Testa: qwen2.5-coder:14b, deepseek-r1:14b vs versoes 7b.
"""
import json, urllib.request, time, sys, os

OLLAMA = 'http://localhost:11434/api/generate'
BASE = 'E:/Projeto MCR'

def chamar(modelo, prompt, temp=0.3, max_tokens=1024, timeout=120):
    """Chama modelo e retorna (resposta, tempo)."""
    t0 = time.time()
    try:
        d = json.dumps({
            'model': modelo,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': temp,
                'num_ctx': 4096,
                'num_predict': max_tokens,
            }
        }).encode()
        req = urllib.request.Request(OLLAMA, data=d,
            headers={'Content-Type': 'application/json'})
        resp = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        texto = (resp.get('response') or '').strip()
        tempo = round(time.time() - t0, 1)
        return texto, tempo
    except Exception as e:
        return f'[ERRO] {e}', round(time.time() - t0, 1)

def contar_nomes(texto):
    """Conta palavras com inicial maiuscula (nomes proprios candidatos)."""
    import re
    # Ignora inicio de frases e palavras comuns
    nomes = re.findall(r'\b[A-Z][a-z]{2,}\b', texto)
    # Filtra palavras que normalmente sao inicio de frase
    stop_nomes = {'O', 'A', 'Os', 'As', 'Um', 'Uma', 'E', 'Mas', 'Por', 'Com',
                  'Sem', 'Para', 'Em', 'No', 'Na', 'Dos', 'Das', 'Se', 'Ele',
                  'Ela', 'Voce', 'Isso', 'Isto', 'Aquilo', 'Este', 'Essa',
                  'Muito', 'Todos', 'Cada', 'Algum', 'Outro', 'Mesmo', 'Entao'}
    return sum(1 for n in nomes if n not in stop_nomes)

def testar_modelo(modelo, label):
    """Executa bateria de testes em um modelo."""
    print(f'\n# {label}')
    print(f'  Modelo: {modelo}')
    print(f'  {"="*50}')
    
    resultados = []
    
    # Teste 1: SPA (sem contexto MCR)
    print(f'\n  --- Teste 1: SPA ---')
    prompt = 'O que significa SPA? Responda em portugues.'
    texto, tempo = chamar(modelo, prompt)
    spa_correto = 'sistema de progress' in texto.lower() or 'sistema de progressão' in texto.lower()
    spa_erro = 'single page' in texto.lower() or 'software as a serv' in texto.lower()
    print(f'  Tempo: {tempo}s | Tam: {len(texto)}c')
    print(f'  SPA correto: {"✅" if spa_correto else "❌"} | SPA errado: {"⚠️" if spa_erro else "✅"}')
    print(f'  {texto[:150]}...')
    resultados.append({
        'teste': 'SPA',
        'tempo': tempo,
        'tamanho': len(texto),
        'nomes': contar_nomes(texto),
        'spa_correto': spa_correto,
        'spa_erro': spa_erro,
    })
    
    # Teste 2: .lua
    print(f'\n  --- Teste 2: .lua ---')
    prompt = 'O que e .lua no projeto MCR? Responda em portugues.'
    texto, tempo = chamar(modelo, prompt)
    lua_correto = 'linguagem' in texto.lower() or 'programa' in texto.lower() or 'script' in texto.lower()
    lua_satelite = 'satelite' in texto.lower() or 'satélite' in texto.lower() or 'lua (mitologia)' in texto.lower()
    print(f'  Tempo: {tempo}s | Tam: {len(texto)}c')
    print(f'  .lua = linguagem: {"✅" if lua_correto else "❌"} | .lua = satelite: {"⚠️" if lua_satelite else "✅"}')
    print(f'  {texto[:150]}...')
    resultados.append({
        'teste': '.lua',
        'tempo': tempo,
        'tamanho': len(texto),
        'nomes': contar_nomes(texto),
        'lua_correto': lua_correto,
        'lua_satelite': lua_satelite,
    })
    
    # Teste 3: Lore Eridanus (criativo)
    print(f'\n  --- Teste 3: Lore Eridanus ---')
    prompt = 'Crie uma lore para a cidade inicial Eridanus do projeto MCR. Inclua nomes proprios de personagens, lugares e artefatos. Responda em portugues.'
    texto, tempo = chamar(modelo, prompt, max_tokens=1536)
    nomes = contar_nomes(texto)
    print(f'  Tempo: {tempo}s | Tam: {len(texto)}c | Nomes: {nomes}')
    print(f'  {texto[:200]}...')
    resultados.append({
        'teste': 'Lore',
        'tempo': tempo,
        'tamanho': len(texto),
        'nomes': nomes,
    })
    
    return resultados

# ============================================================
# EXECUTAR TODOS OS TESTES
# ============================================================
relatorio = {
    'qwen2.5-coder:7b': [],
    'qwen2.5-coder:14b': [],
    'deepseek-r1:7b': [],
    'deepseek-r1:14b': [],
}

# Testa qwen modelos (geracao)
relatorio['qwen2.5-coder:7b'] = testar_modelo('qwen2.5-coder:7b', 'QWEN2.5-CODER:7b (ATUAL)')
relatorio['qwen2.5-coder:14b'] = testar_modelo('qwen2.5-coder:14b', 'QWEN2.5-CODER:14b (NOVO)')

# Testa deepseek modelos (analise)
relatorio['deepseek-r1:7b'] = testar_modelo('deepseek-r1:7b', 'DEEPSEEK-R1:7b (ATUAL)')
relatorio['deepseek-r1:14b'] = testar_modelo('deepseek-r1:14b', 'DEEPSEEK-R1:14b (NOVO)')

# ============================================================
# RELATORIO COMPARATIVO
# ============================================================
print('\n\n')
print('=' * 70)
print('RELATORIO FINAL DE BENCHMARK')
print('=' * 70)

print('\n--- RESUMO POR TESTE ---')
testes_nomes = ['SPA', '.lua', 'Lore']
metricas = ['tempo', 'tamanho', 'nomes']

for i, tn in enumerate(testes_nomes):
    print(f'\n{tn}:')
    print(f'  {"Modelo":25s} {"Tempo":>8s} {"Tamanho":>8s} {"Nomes":>8s} {"Acerto":>10s}')
    print(f'  {"-"*59}')
    for modelo in ['qwen2.5-coder:7b', 'qwen2.5-coder:14b', 'deepseek-r1:7b', 'deepseek-r1:14b']:
        if i < len(relatorio[modelo]):
            r = relatorio[modelo][i]
            acerto = ''
            if tn == 'SPA':
                acerto = '✅' if r.get('spa_correto') else '❌'
            elif tn == '.lua':
                acerto = '✅' if r.get('lua_correto') else '❌'
            else:
                acerto = f'{r["nomes"]}n'
            print(f'  {modelo:25s} {r["tempo"]:>7.1f}s {r["tamanho"]:>8d} {r["nomes"]:>8d} {acerto:>10s}')

print('\n--- VENCEDORES ---')
vencedores = {}
for i, tn in enumerate(testes_nomes):
    melhor_tempo = min(relatorio['qwen2.5-coder:7b'][i]['tempo'],
                       relatorio['qwen2.5-coder:14b'][i]['tempo'],
                       relatorio['deepseek-r1:7b'][i]['tempo'],
                       relatorio['deepseek-r1:14b'][i]['tempo'])
    melhor_nomes = max(relatorio['qwen2.5-coder:7b'][i]['nomes'],
                       relatorio['qwen2.5-coder:14b'][i]['nomes'],
                       relatorio['deepseek-r1:7b'][i]['nomes'],
                       relatorio['deepseek-r1:14b'][i]['nomes'])
    for modelo in ['qwen2.5-coder:7b', 'qwen2.5-coder:14b', 'deepseek-r1:7b', 'deepseek-r1:14b']:
        r = relatorio[modelo][i]
        if r['tempo'] == melhor_tempo:
            print(f'  {tn} - Rapidez: {modelo} ({melhor_tempo}s)')
        if r['nomes'] == melhor_nomes:
            print(f'  {tn} - Riqueza: {modelo} ({melhor_nomes} nomes)')

# Salva relatorio
path = os.path.join(BASE, 'sandbox', 'benchmark_14b.json')
with open(path, 'w', encoding='utf-8') as f:
    json.dump(relatorio, f, ensure_ascii=False, indent=2)
print(f'\nRelatorio salvo em: {path}')
print('=' * 70)
