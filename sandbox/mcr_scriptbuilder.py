#!/usr/bin/env python3
"""MCR-DevIA Script Builder V12 puro"""
import sys, os, json, urllib.request, subprocess, re

OLLAMA_URL = 'http://localhost:11434/api/generate'
OUT_DIR = r'E:\Projeto MCR\sandbox\autogerados'
os.makedirs(OUT_DIR, exist_ok=True)

def ia(prompt):
    try:
        d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
            'options':{'temperature':0.5,'num_ctx':4096}}).encode()
        r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(r,timeout=120).read()).get('response','')
    except: return None

def construir(desc):
    print(f'\n[Builder] {desc[:60]}...')
    
    # IA gera APENAS o corpo da funcao (4-8 linhas de codigo)
    corpo = ia(f'Escreva 4-8 linhas de Python que: {desc}. Retorne APENAS o codigo, sem def, sem imports.')
    if not corpo:
        print('[ERRO] Falha')
        return None
    
    # Remove marcacoes
    corpo = re.sub(r'```.*?\n', '', corpo).strip()
    
    # Monta script completo (template FIXO, sem erros)
    codigo = f'''#!/usr/bin/env python3
# {desc}
import os, sys, json

def main():
    import os
{corpo}

if __name__ == '__main__':
    main()
'''
    
    # Tenta compilar com correcao
    for t in range(20):
        try:
            compile(codigo, 'script.py', 'exec')
            break
        except SyntaxError as e:
            linhas = codigo.split('\n')
            if e.lineno and 0 < e.lineno <= len(linhas):
                idx = e.lineno - 1
                if 'expected an indented block' in str(e):
                    linhas.insert(idx, '    pass')
                elif 'unexpected indent' in str(e):
                    linhas[idx] = linhas[idx].lstrip()
                else:
                    linhas[idx] = '#' + linhas[idx]
                codigo = '\n'.join(linhas)
            else:
                print(f'  [ERRO] {e.msg}')
                return None
    
    nome = re.sub(r'[^a-zA-Z]', '_', desc[:20]) + '.py'
    path = os.path.join(OUT_DIR, nome)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(codigo)
    print(f'  [OK] {path}')
    
    r = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=10)
    print(f'  [TESTE] {"OK" if r.returncode == 0 else "FALHOU"}: {r.stdout.strip()[:100] or r.stderr.strip()[:100]}')
    return path

if __name__ == '__main__':
    construir(' '.join(sys.argv[1:]))
