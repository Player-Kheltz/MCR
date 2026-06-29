"""Comando: fix_excepts - Substitui except: por except Exception as e:"""
import os, re, shutil

def register():
    return {
        "name": "fix_excepts",
        "desc": "Corrige except: genericos. Uso: fix_excepts <path> [--force] [--preview]",
        "handler": execute,
        "args": [{"name": "path", "type": "str", "required": True}],
        "categoria": "util",
    }

def execute(kg, ia, args, ctx_crew=None):
    if not args:
        print('[Fix] Uso: fix_excepts <path> [--force] [--preview]')
        return True
    
    path = args[0]
    forcar = '--force' in args
    preview = '--preview' in args or not forcar  # preview por padrao
    
    if not os.path.exists(path):
        print(f'[Fix] Caminho nao encontrado: {path}')
        return True
    
    # Se for diretorio, pega todos .py
    if os.path.isdir(path):
        files = []
        for root, dirs, files_walk in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith(('.', '__pycache__', 'vcpkg', 'node_modules'))]
            for f in files_walk:
                if f.endswith('.py'):
                    files.append(os.path.join(root, f))
    else:
        files = [path] if path.endswith('.py') else []
    
    if not files:
        print('[Fix] Nenhum arquivo .py encontrado')
        return True
    
    total_fixes = 0
    total_arquivos = 0
    
    for fpath in files:
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            original = f.read()
        
        # Encontra except: genericos (mas nao except X: ou except Exception:)
        # Regex: "except:" (sozinho) ou "except :" (com espaço)
        pattern = re.compile(r'^(\s*)except\s*:\s*(.*)$', re.MULTILINE)
        
        modified = original
        fixes = 0
        
        for match in pattern.finditer(original):
            indent = match.group(1)
            resto = match.group(2).strip()
            
            # Se ja tem tratamento, nao mexe
            if 'Exception' in resto or 'pass' == resto:
                continue
            
            # Substitui
            old = match.group(0)
            if resto and resto != 'pass':
                new = f'{indent}except Exception as e:\n{indent}    print(f"[Fix] ERRO: {{e}}")'
            else:
                new = f'{indent}except Exception as e:\n{indent}    print(f"[Fix] ERRO: {{e}}")'
            
            modified = modified.replace(old, new, 1)
            fixes += 1
        
        if fixes > 0:
            rel = os.path.relpath(fpath, os.path.dirname(os.path.dirname(__file__)) + '/..')
            print(f'  {rel}: {fixes} correcoes')
            
            if preview:
                # Mostra diff
                orig_lines = original.split('\n')
                mod_lines = modified.split('\n')
                for i, (ol, nl) in enumerate(zip(orig_lines, mod_lines)):
                    if ol != nl:
                        print(f'    L{i+1}: - {ol[:60]}')
                        print(f'           + {nl[:60]}')
            
            if forcar:
                # Backup
                bak = fpath + '.bak'
                shutil.copy2(fpath, bak)
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(modified)
                print(f'    -> Aplicado (backup: {os.path.basename(bak)})')
            
            total_fixes += fixes
            total_arquivos += 1
    
    if total_fixes == 0:
        print('[Fix] Nenhum except: generico encontrado')
    else:
        print(f'\n[Fix] {total_fixes} correcoes em {total_arquivos} arquivos')
        if not forcar:
            print('[Fix] Use --force para aplicar as correcoes')
    
    return True
