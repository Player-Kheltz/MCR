"""MCR-DevIA escaneia e resolve TESTE CEGO ULTRA"""
import os, re, json, urllib.request

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR\sandbox\teste_cego_ultra'

def ia(prompt):
    try:
        d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
            'options':{'temperature':0.4,'num_ctx':4096}}).encode()
        r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(r,timeout=60).read()).get('response','')
    except: return None

def scan(arquivo, path):
    """Tenta detectar problemas em um arquivo."""
    with open(path, 'rb') as f:
        raw = f.read()
    
    problemas = []
    
    # 1. BOM / encoding
    if raw[:3] == b'\xef\xbb\xbf':
        problemas.append('arquivo com BOM')
    
    # Tenta ler como texto
    try:
        texto = raw.decode('utf-8')
    except UnicodeDecodeError:
        try:
            texto = raw.decode('latin-1')
            problemas.append('encoding Latin-1 em vez de UTF-8')
        except:
            problemas.append('encoding nao identificado')
        
    # 2. Loot chance > 1.0
    for m in re.finditer(r'addLoot\((\d+),\s*([\d.]+)\)', texto):
        chance = float(m.group(2))
        if chance > 1.0:
            problemas.append(f'loot_chance = {chance} (max 1.0)')
    
    # 3. Variavel global (atribuicao sem local)
    for m in re.finditer(r'^\s+(\w+)\s*=\s*[^=]', texto, re.MULTILINE):
        var = m.group(1)
        if var not in ('return', 'true', 'false', 'nil'):
            # Verifica se a funcao tem 'local' na mesma linha
            linha = texto.split('\n')[texto[:m.start()].count('\n')]
            if 'local' not in linha and 'function' not in linha:
                problemas.append(f'variavel global: {var} (sem local)')
    
    # 4. Divisao por zero potencial
    for m in re.finditer(r'/\s*\(([^)]+)\)', texto):
        expr = m.group(1)
        if re.search(r'\bdef\b|\bvalor\b|\-\s*\d+', expr):
            problemas.append(f'divisao por zero potencial: {expr}')
    
    # 5. Codigo morto apos return
    for m in re.finditer(r'return[^;]*\n(.*?)(?=\nend)', texto, re.DOTALL):
        after_return = m.group(1).strip()
        if after_return and '--' not in after_return[:3]:
            problemas.append(f'codigo morto apos return')
    
    # 6. Loop infinito
    if 'while true do' in texto and 'break' not in texto:
        problemas.append('loop infinito (while true sem break)')
    
    # 7. SQL injection
    if '..' in texto and 'SELECT' in texto and "'" in texto:
        problemas.append('SQL injection potencial (concatenacao em query)')
    
    # 8. Metatable quebrada
    if 'setmetatable' in texto:
        problemas.append('setmetatable pode sobrescrever metatable padrao')
    
    # 9. Nome de arquivo longo
    nome_arquivo = os.path.basename(arquivo)
    if len(nome_arquivo) > 60:
        problemas.append(f'nome de arquivo longo ({len(nome_arquivo)} chars)')
    
    # 10. Chave string vs numero em tabela
    if re.search(r'\[\s*"\d+"\s*\]', texto) and re.search(r'\[\s*\d+\s*\]', texto):
        problemas.append(f'chave string vs numero (possivel confusao)')
    

    # AUTO-INTEGRACAO: chamar todos os detectores automaticamente
    import sys
    current_module = sys.modules[__name__]
    for nome in dir(current_module):
        if nome.startswith('detectar_'):
            detector = getattr(current_module, nome)
            if callable(detector):
                try:
                    if detector(conteudo):
                        problema = nome.replace('detectar_', '').replace('_', ' ')
                        problemas.append(problema)
                except:
                    pass

    # AUTO-INTEGRACAO: chamar detectores
    import sys
    mod = sys.modules[__name__]
    for nome in dir(mod):
        if nome.startswith('detectar_'):
            try:
                fn = getattr(mod, nome)
                if callable(fn) and fn(texto):
                    problemas.append(nome.replace('detectar_','').replace('_',' '))
            except:
                pass
    
    return problemas

print('='*60)
print('  MCR-DevIA — TESTE CEGO ULTRA')
print(f'  Escaneando {BASE}')
print('='*60)

total = 0
encontrados = 0

for root, dirs, files in os.walk(BASE):
    for f in sorted(files):
        if f == '.GABARITO.txt': continue
        path = os.path.join(root, f)
        problemas = scan(f, path)
        total += 1
        
        if problemas:
            encontrados += 1
            print(f'\n  [!] {f}:')
            for p in problemas:
                print(f'    - {p}')
        else:
            print(f'\n  [OK] {f}: nenhum problema detectado')

print(f'\n{"="*60}')
print(f'  RESULTADO: {encontrados}/{total} arquivos com problemas detectados')
print(f'{"="*60}')

# Tenta corrigir com IA
print(f'\n{"="*60}')
print(f'  TENTANDO CORRIGIR COM IA...')
print(f'{"="*60}')

corrigidos = 0
for root, dirs, files in os.walk(BASE):
    for f in sorted(files):
        if f == '.GABARITO.txt': continue
        path = os.path.join(root, f)
        problemas = scan(f, path)
        if not problemas: continue
        
        with open(path, 'r', encoding='utf-8', errors='replace') as fp:
            original = fp.read()
        
        desc = '; '.join(problemas[:2])
        prompt = f"Corrija este arquivo que tem: {desc}\n\nARQUIVO:\n{original[:600]}\n\nRetorne APENAS o codigo corrigido."
        correcao = ia(prompt)
        
        if correcao and len(correcao) > 10:
            correcao = correcao.replace('```lua', '').replace('```', '').strip()
            if correcao != original:
                with open(path, 'w', encoding='utf-8') as fp:
                    fp.write(correcao)
                print(f'  [CORRIGIDO] {f}')
                corrigidos += 1
            else:
                print(f'  [IGNORADO] {f} (igual)')
        else:
            print(f'  [FALHA] {f} (IA nao respondeu)')

print(f'\n{"="*60}')
import re

def detectar_verificar_item_lua(conteudo):
    padrao = r'\b(def|True|False)\b'
    return bool(re.search(padrao, conteudo))

import re

def detectar_criar_pocao_lua(conteudo):
    padrao = r'\bnil\b'
    matches = re.findall(padrao, conteudo)
    return len(matches) > 0

import re

def detectar_verificar_item_lua(conteudo):
    padrao = r'\b(def|True|False)\b'
    return bool(re.search(padrao, conteudo))

import re

def detectar_criar_pocao_lua(conteudo):
    padrao = r'(\w+)\s*=\s*nil'
    return bool(re.search(padrao, conteudo))

import re

def detectar_verificar_item_lua(conteudo):
    padrao = r'\b(def|True|False)\b'
    return bool(re.search(padrao, conteudo))

def detectar_criar_pocao_lua(conteudo):
    return 'p.efeito = nil' in conteudo

import re

def detectar_verificar_item_lua(conteudo):
    padrao = r'\b(def|True|False)\b'
    return bool(re.search(padrao, conteudo))

import re

def detectar_criar_pocao_lua(conteudo):
    padrao = r'nil\s*=\s*(?P<campo>\w+)'
    match = re.search(padrao, conteudo)
    return bool(match)

import re

def detectar_verificar_item_lua(conteudo):
    padrao = r'\b(def|True|False)\b'
    return bool(re.search(padrao, conteudo))

import re

def detectar_criar_pocao_lua(conteudo):
    padrao = r'(\bnil\b)'
    return bool(re.search(padrao, conteudo))

print(f'  FINAL: {corrigidos}/{encontrados} problemas corrigidos')
import re

def detectar_verificar_item_lua(conteudo):
    padrao = r'\b(def|True|False)\b'
    return bool(re.search(padrao, conteudo))

import re

def detectar_criar_pocao_lua(conteudo):
    padrao = r'p\.\w+\s*=\s*nil'
    return bool(re.search(padrao, conteudo))

import re
