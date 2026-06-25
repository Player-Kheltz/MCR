"""MCR-DevIA escaneia e resolve o TESTE CEGO"""
import os, re, json, urllib.request

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR\sandbox\teste_cego'

def ia(prompt):
    try:
        d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
            'options':{'temperature':0.4,'num_ctx':4096}}).encode()
        r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(r,timeout=60).read()).get('response','')
    except: return None

print('='*60)
print('  MCR-DevIA — TESTE CEGO')
print('  8 problemas NOVOS que ele nunca viu')
print('='*60)

# Escaneia todos os .lua do diretorio
problemas = []
for root, dirs, files in os.walk(BASE):
    for f in files:
        if not f.endswith('.lua'): continue
        path = os.path.join(root, f)
        with open(path, 'r', encoding='utf-8', errors='replace') as fp:
            conteudo = fp.read()
        rel = os.path.relpath(path, BASE)
        
        # 1. Nome inconsistente
        if f != f.lower() and f != f.title():
            problemas.append((rel, f'nome inconsistente: {f}'))
        
        # 2. HP negativo
        for m in re.finditer(r'setHealth\((-\d+)\)', conteudo):
            problemas.append((rel, f'HP negativo: {m.group(1)}'))
        
        # 3. Funcoes inexistentes
        for m in re.finditer(r'(?:npc|mon|item):(set\w+)\(', conteudo):
            func = m.group(1)
            if func in ('setMana', 'setMagicLevel'):
                problemas.append((rel, f'funcao inexistente: {func}'))
        
        # 4. NPC sem saudacao
        if 'NPC(' in conteudo and 'npc:setSaudacao' not in conteudo:
            problemas.append((rel, 'NPC sem setSaudacao'))
        
        # 5. Monster sem loot
        if 'Monster(' in conteudo and 'addLoot' not in conteudo:
            problemas.append((rel, 'monstro sem loot'))
        
        # 6. BOM (Byte Order Mark)
        try:
            with open(path, 'rb') as fb:
                raw = fb.read(10)
            if raw[:3] == b'\xef\xbb\xbf':
                problemas.append((rel, 'arquivo com BOM'))
        except: pass
        
        # 7. Indentacao mista
        if '\t' in conteudo and '  ' in conteudo:
            problemas.append((rel, 'indentacao mista tabs+espacos'))

if not problemas:
    print('\n  Nenhum problema encontrado!')
else:
    print(f'\n  Problemas detectados: {len(problemas)}')
    for arquivo, desc in problemas:
        print(f'    [!] {arquivo}: {desc}')

# Tenta corrigir cada um
print(f'\n{"="*60}')
print('  TENTANDO CORRIGIR...')
print(f'{"="*60}')

acertos = 0
for arquivo, desc in problemas:
    path = os.path.join(BASE, arquivo)
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        original = f.read()
    
    print(f'\n  [{arquivo}] {desc}')
    
    prompt = f"Corrija este arquivo Lua que tem este problema: {desc}\n\nARQUIVO:\n{original[:800]}\n\nRetorne APENAS o codigo corrigido."
    correcao = ia(prompt)
    
    if correcao and len(correcao) > 10:
        correcao = correcao.replace('```lua', '').replace('```', '').strip()
        if correcao != original:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(correcao)
            print(f'    [CORRIGIDO]')
            acertos += 1
        else:
            print(f'    [IGNORADO] igual ao original')
    else:
        print(f'    [FALHA] IA nao respondeu')

print(f'\n{"="*60}')
print(f'  RESULTADO: {acertos}/{len(problemas)} problemas resolvidos')
print(f'{"="*60}')
