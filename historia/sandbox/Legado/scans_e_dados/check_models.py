"""Verifica modelos disponiveis no Ollama."""
import urllib.request, json

r = urllib.request.urlopen('http://localhost:11434/api/tags', timeout=10)
models = json.loads(r.read())
print('Modelos disponiveis:')
print('=' * 70)
for m in models.get('models', []):
    name = m['name']
    size_gb = m['size'] / 1e9
    modified = m.get('modified_at', '?')[:10]
    print(f'  {name:30s} {size_gb:5.1f}GB  modificado: {modified}')
print('=' * 70)
print(f'Total: {len(models.get("models", []))} modelos')

# Analise dos modelos
print()
print('=== ANALISE POR CAPACIDADE ===')
modelos = models.get('models', [])
modelos.sort(key=lambda x: -x['size'])

# Categorias
categorias = {
    'Grande (70B+)': [],
    'Medio (10B-30B)': [],
    'Leve (7B-9B)': [],
    'Micro (<7B)': [],
    'Embedding': [],
}

for m in modelos:
    name = m['name']
    size_gb = m['size'] / 1e9
    if 'embed' in name.lower():
        categorias['Embedding'].append(f'  {name} ({size_gb:.1f}GB)')
    elif '70b' in name.lower() or '70B' in name:
        categorias['Grande (70B+)'].append(f'  {name} ({size_gb:.1f}GB)')
    elif size_gb > 10:
        categorias['Grande (70B+)'].append(f'  {name} ({size_gb:.1f}GB)')
    elif size_gb > 5:
        categorias['Medio (10B-30B)'].append(f'  {name} ({size_gb:.1f}GB)')
    elif size_gb > 2:
        categorias['Leve (7B-9B)'].append(f'  {name} ({size_gb:.1f}GB)')
    else:
        categorias['Micro (<7B)'].append(f'  {name} ({size_gb:.1f}GB)')

for cat, items in categorias.items():
    if items:
        print(f'\n{cat}:')
        for item in items:
            print(item)
