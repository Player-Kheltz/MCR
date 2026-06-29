"""Migracao unica: converte knowledge.json (mono-arquivo) para kg/ (multi-arquivo).
Cria pasta kg/ com um arquivo por contexto + atualiza knowledge.json como master index.

Uso:
    python sandbox/_migrar_kg.py
"""
import os, sys, json, shutil
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Scripts', 'mcr_devia'))

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SANDBOX = os.path.join(BASE, 'sandbox')
MCR_DEVIA = os.path.join(SANDBOX, '.mcr_devia')
LEGACY_PATH = os.path.join(MCR_DEVIA, 'knowledge.json')
KG_DIR = os.path.join(MCR_DEVIA, 'kg')

print('=== Migracao KG: mono-arquivo -> multi-arquivo ===')
print()

if not os.path.exists(LEGACY_PATH):
    print('[ERRO] knowledge.json nao encontrado em:', LEGACY_PATH)
    sys.exit(1)

# Le o legado
with open(LEGACY_PATH, 'r', encoding='utf-8') as f:
    dados = json.load(f)

licoes = dados.get('licoes', [])
print(f'Encontradas {len(licoes)} lessons no knowledge.json')
print()

# Cria pasta kg/
os.makedirs(KG_DIR, exist_ok=True)

# Agrupa por ctx
ctx_groups = {}
for l in licoes:
    ctx = l.get('ctx', 'geral')
    ctx_groups.setdefault(ctx, []).append(l)

print(f'Contextos encontrados: {len(ctx_groups)}')
for ctx, lessons in sorted(ctx_groups.items(), key=lambda x: -len(x[1])):
    print(f'  {ctx}: {len(lessons)} lessons')

print()
print('Salvando ctx files...')

# Salva um arquivo por ctx
for ctx, lessons in ctx_groups.items():
    ctx_path = os.path.join(KG_DIR, f'{ctx}.json')
    with open(ctx_path, 'w', encoding='utf-8') as f:
        json.dump({'ctx': ctx, 'licoes': lessons}, f, ensure_ascii=False, indent=2)
    print(f'  [OK] {ctx}.json ({len(lessons)} lessons)')

# Salva master index (substitui knowledge.json)
master = {
    'versoes': dados.get('versoes', 1),
    'metricas': dados.get('metricas', {'licoes': len(licoes)}),
    'index': dados.get('index', {}),
}
with open(LEGACY_PATH, 'w', encoding='utf-8') as f:
    json.dump(master, f, ensure_ascii=False, indent=2)

print()
print(f'[OK] Migracao concluida!')
print(f'  {len(ctx_groups)} ctx files em: {KG_DIR}')
print(f'  Master index em: {LEGACY_PATH}')
print()
print('Estrutura final:')
print(f'  .mcr_devia/')
print(f'    knowledge.json  ← master index ({"%.1f" % (os.path.getsize(LEGACY_PATH)/1024)} KB)')
print(f'    kg/')
for ctx in sorted(ctx_groups.keys()):
    fpath = os.path.join(KG_DIR, f'{ctx}.json')
    size_kb = os.path.getsize(fpath)/1024
    print(f'      {ctx}.json  ({"%.1f" % size_kb} KB)')
