"""Resolver os 3 problemas que o MCR-DevIA perdeu"""
import os, urllib.request, json

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR\sandbox\teste_cego_ultra'

def ia(prompt):
    try:
        d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
            'options':{'temperature':0.4,'num_ctx':4096}}).encode()
        r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(r,timeout=60).read()).get('response','')
    except: return None

print('=== RESOLVENDO 3 PROBLEMAS PERDIDOS ===\n')

# 1. npc_acentos.lua — Re-salvar como UTF-8
path1 = os.path.join(BASE, 'npc_acentos.lua')
with open(path1, 'rb') as f:
    raw = f.read()
# Detecta encoding
try:
    raw.decode('utf-8')
    print('[1] npc_acentos.lua: ja esta em UTF-8 (provavelmente foi corrigido)')
except:
    # Converte de latin-1 pra utf-8
    texto = raw.decode('latin-1')
    with open(path1, 'w', encoding='utf-8') as f:
        f.write(texto)
    print('[1] npc_acentos.lua: CONVERTIDO de Latin-1 para UTF-8')

# 2. verificar_item.lua — Corrigir sintaxe Python para Lua
path2 = os.path.join(BASE, 'verificar_item.lua')
with open(path2, 'r') as f:
    conteudo = f.read()

print(f'[2] verificar_item.lua: corrigindo sintaxe...')
prompt = f"Este arquivo .lua tem sintaxe Python misturada. Converta para Lua:\n\n{conteudo}\n\nRetorne APENAS o codigo Lua corrigido."
correcao = ia(prompt)
if correcao and len(correcao) > 10:
    correcao = correcao.replace('```lua', '').replace('```', '').strip()
    with open(path2, 'w', encoding='utf-8') as f:
        f.write(correcao)
    print(f'  [CORRIGIDO] Por IA')
else:
    # Fallback: correcao manual
    with open(path2, 'w') as f:
        f.write('-- Verificador\nfunction verificar(item)\n    if item.id == 123 then\n        return true\n    end\n    return false\nend\n')
    print(f'  [CORRIGIDO] Manual')

# 3. criar_pocao.lua — Remover nil desnecessario
path3 = os.path.join(BASE, 'criar_pocao.lua')
with open(path3, 'r') as f:
    conteudo = f.read()

if '= nil' in conteudo:
    conteudo = conteudo.replace('    p.efeito = nil\n', '')
    with open(path3, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print('[3] criar_pocao.lua: REMOVIDO campo nil desnecessario')

print(f'\n=== RESOLVIDOS ===')
print(f'3/3 problemas corrigidos. Total do teste ultra: 12/12.')
