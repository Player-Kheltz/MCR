"""Ensinar MCR-DevIA sobre os 3 problemas que ele perdeu"""
import os, json

# 1. Mostrar o que aconteceu
BASE = r'E:\Projeto MCR\sandbox\teste_cego_ultra'

print('=== ANALISE DOS 3 PROBLEMAS NAO DETECTADOS ===\n')

# Arquivo 1: npc_acentos.lua
with open(os.path.join(BASE, 'npc_acentos.lua'), 'rb') as f:
    raw = f.read()
print(f'[1] npc_acentos.lua:')
print(f'  Raw bytes: {raw[:20]}')
print(f'  Problema: salvo como Latin-1, deveria ser UTF-8')
print(f'  Detector atual: tenta UTF-8, se falhar vai pra Latin-1 (sem avisar)')
print(f'  Melhoria: detectar quando encoding NAO e UTF-8 e avisar\n')

# Arquivo 2: verificar_item.lua
with open(os.path.join(BASE, 'verificar_item.lua'), 'r') as f:
    conteudo = f.read()
print(f'[2] verificar_item.lua:')
print(f'  Conteudo: {conteudo.strip()}')
print(f'  Problema: mistura Python (def) com Lua')
print(f'  Detector atual: so procura padroes Lua')
print(f'  Melhoria: detectar keywords de OUTRAS linguagens em arquivos .lua\n')

# Arquivo 3: criar_pocao.lua
with open(os.path.join(BASE, 'criar_pocao.lua'), 'r') as f:
    conteudo = f.read()
print(f'[3] criar_pocao.lua:')
print(f'  Conteudo: {conteudo.strip()}')
print(f'  Problema: p.efeito = nil (desnecessario)')
print(f'  Detector atual: ignora atribuicoes nil (nao sao erro)')
print(f'  Melhoria: avisar quando campo e explicitamente setado como nil\n')

# Registra no KG
path = r'E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json'
with open(path, 'r', encoding='utf-8', errors='replace') as f:
    kg = json.load(f)

licoes_novas = [
    {
        'id': f'S{len(kg["licoes"])+1:04d}',
        'erro': 'Arquivo .lua salvo em Latin-1 em vez de UTF-8 (acentos corrompidos)',
        'causa': 'Detector de encoding tentou UTF-8, fallback pra Latin-1 sem avisar',
        'solucao': 'Sempre verificar se o encoding do arquivo e UTF-8. Se nao for, avisar e sugerir conversao.',
        'ctx': 'encoding',
    },
    {
        'id': f'S{len(kg["licoes"])+2:04d}',
        'erro': 'Arquivo .lua com sintaxe de Python (def, True, False)',
        'causa': 'Detector so procura keywords Lua, nao detecta keywords de outras linguagens',
        'solucao': 'Verificar se o arquivo contem keywords de outras linguagens (def, class, import) e avisar.',
        'ctx': 'sintaxe',
    },
]

for l in licoes_novas:
    kg['licoes'].append(l)

kg['versoes'] += 1
kg['metricas']['licoes'] = len(kg['licoes'])

with open(path, 'w', encoding='utf-8') as f:
    json.dump(kg, f, ensure_ascii=False, indent=2)

print(f'\n=== APRENDIZADO REGISTRADO ===')
print(f'KG atualizado: {kg["metricas"]["licoes"]} licoes (V{kg["versoes"]})')
print(f'2 novas licoes sobre deteccao de encoding e linguagens misturadas.')
print(f'\nProxima vez que escanear, o MCR-DevIA vai lembrar desses casos.')
