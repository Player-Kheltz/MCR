#!/usr/bin/env python3
"""
MCR-DevIA Auto-Script — Cria scripts Python usando V12 + auto-correcao
========================================================================
"""
import sys, os, json, re, urllib.request, hashlib, datetime, ast

OLLAMA_URL = 'http://localhost:11434/api/generate'
SANDBOX = r'E:\Projeto MCR\sandbox'
OUT_DIR = os.path.join(SANDBOX, 'autogerados')
os.makedirs(OUT_DIR, exist_ok=True)

def ia(prompt):
    try:
        d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
            'options':{'temperature':0.6,'num_ctx':4096}}).encode()
        r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(r,timeout=180).read()).get('response','')
    except: return None

def criar_script(desc):
    print(f'\n[AutoScript] {desc[:80]}')
    
    # 1. IA gera o codigo
    prompt = f"Crie um script Python para: {desc}\nUse apenas bibliotecas padrao (os, sys, json, re).\nRetorne APENAS o codigo Python, sem explicacoes.\n\nCodigo:"
    codigo = ia(prompt)
    if not codigo: print('Falha na geracao'); return None
    
    # Limpa marcacoes ```python ... ```
    codigo = re.sub(r'```\w*\n?', '', codigo).strip()
    
    # Extrai nome do script
    nome_match = re.search(r'(?:def |class )?(\w+)(?:\(|:)', codigo)
    nome = nome_match.group(1) if nome_match else f'script_{datetime.datetime.now():%H%M%S}'
    
    # 2. Tenta compilar, se falhar, corrige
    for tentativa in range(10):
        try:
            ast.parse(codigo)
            # Salva!
            path = os.path.join(OUT_DIR, f'{nome}.py')
            with open(path,'w',encoding='utf-8') as f:
                f.write(f'#!/usr/bin/env python3\n# {desc}\n# Criado pelo MCR-DevIA\n{codigo}')
            print(f'  [OK] {path}')
            return path
        except SyntaxError as e:
            if tentativa == 0:
                print(f'  Corrigindo: {e.msg}')
            linhas = codigo.split('\n')
            if e.lineno and 0 < e.lineno <= len(linhas):
                idx = e.lineno - 1
                if 'expected an indented block' in str(e):
                    linhas.insert(idx, '    pass')
                elif 'unexpected indent' in str(e):
                    linhas[idx] = linhas[idx].lstrip()
                else:
                    linhas[idx] = '# ' + linhas[idx]
                codigo = '\n'.join(linhas)
            else:
                break
    
    print('  [FALHA] Nao foi possivel corrigir')
    return None

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f'Uso: {sys.argv[0]} "descricao do script"'); sys.exit(1)
    criar_script(' '.join(sys.argv[1:]))
