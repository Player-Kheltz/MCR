import json, os, re

# ================================================================
# 1. ANALISE DOS TESTES
# ================================================================
with open('E:\\Projeto MCR\\sandbox\\testes_extensivos\\relatorio_bateria.json', encoding='utf-8') as f:
    data = json.load(f)

results = data['resultados']
total_time = sum(r['tempo'] for r in results)
ia_tests = [r for r in results if r['tempo'] > 1]
v12_tests = [r for r in results if r['tempo'] <= 1]

print('=== RELATORIO DE PERFORMANCE DOS TESTES ===')
print(f'Total de testes: {len(results)}')
print(f'Tempo total: {total_time:.1f}s ({total_time/60:.1f} min)')
print(f'Tempo medio: {total_time/len(results):.1f}s')
print()
print(f'Testes V12 (<=1s): {len(v12_tests)} de {len(results)} ({len(v12_tests)*100//len(results)}%)')
if v12_tests:
    print(f'  Tempo medio V12: {sum(r["tempo"] for r in v12_tests)/len(v12_tests):.1f}s')
print()
print(f'Testes com IA (>1s): {len(ia_tests)} de {len(results)} ({len(ia_tests)*100//len(results)}%)')
if ia_tests:
    print(f'  Tempo medio com IA: {sum(r["tempo"] for r in ia_tests)/len(ia_tests):.1f}s')
    print(f'  Tempo TOTAL com IA: {sum(r["tempo"] for r in ia_tests):.1f}s')
print()

print('=== TOP 10 MAIS LENTOS ===')
sorted_results = sorted(results, key=lambda r: -r['tempo'])
for r in sorted_results[:10]:
    print(f'  {r["tempo"]:6.1f}s  {r["cmd"]:<15} {r["nome"][:45]}')

print()
print('=== DISTRIBUICAO DE TEMPO POR COMANDO ===')
cmd_stats = {}
for r in results:
    cmd = r['cmd']
    if cmd not in cmd_stats:
        cmd_stats[cmd] = {'count': 0, 'total_time': 0}
    cmd_stats[cmd]['count'] += 1
    cmd_stats[cmd]['total_time'] += r['tempo']
for cmd, s in sorted(cmd_stats.items(), key=lambda x: -x[1]['total_time']):
    pct = s['total_time'] * 100 / total_time
    print(f'  {cmd:<20} {s["total_time"]:6.1f}s total  ({s["count"]} testes, '
          f'media {s["total_time"]/s["count"]:.1f}s, {pct:.0f}%)')

# ================================================================
# 2. ANALISE DO CODIGO
# ================================================================
print()
print('=' * 60)
print('ANALISE ESTRUTURAL DO CODIGO')
print('=' * 60)

mcr_path = 'E:\\Projeto MCR\\scripts\\mcr_devia\\mcr_devia.py'
with open(mcr_path, encoding='utf-8') as f:
    codigo = f.read()

# Contar subprocess.run
subprocess_chamadas = len(re.findall(r'subprocess\.run\(', codigo))
print(f'subprocess.run em mcr_devia.py: {subprocess_chamadas}')

# Contar IA calls diretas
ia_gerar = len(re.findall(r'self\.ia\.gerar\(', codigo))
fast_calls = len(re.findall(r'\bfast\(', codigo))
ollama_direct = len(re.findall(r'OLLAMA_URL', codigo))
print(f'IA.gerar(): {ia_gerar}')
print(f'fast(): {fast_calls}')
print(f'refs a OLLAMA_URL: {ollama_direct}')

# Contar kg.buscar
kg_buscar = len(re.findall(r'kg\.buscar\(', codigo) or re.findall(r'self\.kg\.buscar\(', codigo))
print(f'kg.buscar(): {kg_buscar}')

# Comprimento main()
main_match = re.search(r'def main\(\).*', codigo)
if main_match:
    main_start = main_match.start()
    # Encontrar fim do main (proximo def no mesmo nivel ou if __name__)
    resto = codigo[main_start:]
    # Contar elifs
    elif_count = len(re.findall(r'elif cmd ==', codigo))
    if_count = len(re.findall(r'\bif\s+', codigo))
    print(f'elif cmd == na main(): {elif_count}')
    print(f'if statements total: {if_count}')

# ================================================================
# 3. ANALISE DO KG
# ================================================================
print()
print('=' * 60)
print('ANALISE DO KNOWLEDGE GRAPH')
print('=' * 60)

kg_path = 'E:\\Projeto MCR\\sandbox\\.mcr_devia\\knowledge.json'
with open(kg_path, encoding='utf-8') as f:
    kg = json.load(f)

licoes = kg.get('licoes', [])
ativos = sum(1 for l in licoes if not l.get('inactive', False))
inativos = sum(1 for l in licoes if l.get('inactive', False))

print(f'Total lessons: {len(licoes)}')
print(f'Ativas: {ativos}')
print(f'Inativas: {inativos}')

# Context distribution for ACTIVE only
ctx_dist = {}
for l in licoes:
    if l.get('inactive', False):
        continue
    ctx = l.get('ctx', 'unknown')
    ctx_dist[ctx] = ctx_dist.get(ctx, 0) + 1

print()
print('Distribuicao por contexto (ATIVAS):')
for ctx, count in sorted(ctx_dist.items(), key=lambda x: -x[1])[:20]:
    print(f'  {ctx:<20} {count:5d} lessons')

# Duplicates in active lessons
solucoes = [l.get('solucao', '')[:60] for l in licoes if not l.get('inactive', False)]
from collections import Counter
dup_counter = Counter(solucoes)
dups = {k: v for k, v in dup_counter.items() if v > 1}
print(f'\nPossiveis duplicatas (mesmo inicio de solucao): {len(dups)}')
if dups:
    for s, c in sorted(dups.items(), key=lambda x: -x[1])[:5]:
        print(f'  "{s[:50]}..." x{c}')

# Tamanho
kg_size = len(json.dumps(kg))
print(f'Tamanho do KG: {kg_size:,} bytes ({kg_size/1024:.0f} KB)')

# ================================================================
# 4. ARQUIVOS NO SANDBOX
# ================================================================
print()
print('=' * 60)
print('ANALISE DO SANDBOX')
print('=' * 60)
sandbox = 'E:\\Projeto MCR\\sandbox'
py_files = [f for f in os.listdir(sandbox) if f.endswith('.py')]
total_py_kb = sum(os.path.getsize(os.path.join(sandbox, f)) for f in py_files) / 1024
print(f'Scripts .py no sandbox: {len(py_files)} ({total_py_kb:.0f} KB)')

# Weblearn
weblearn_dir = 'E:\\Modelos IA\\weblearn\\fragments'
if os.path.exists(weblearn_dir):
    frag_count = sum(1 for _, _, files in os.walk(weblearn_dir) for f in files if f.endswith('.json'))
    print(f'Fragmentos Weblearn: ~{frag_count}')

print()
print('=== FIM DA ANALISE ===')
