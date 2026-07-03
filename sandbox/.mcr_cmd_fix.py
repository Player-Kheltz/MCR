#!/usr/bin/env python3
"""Adiciona leitura de contexto .mcr_conversa.jsonl no kernel."""
import sys, os, json

# 1. Restaura kernel.py removendo duplicacao
kpath = r'E:\Projeto MCR\scripts\mcr_devia\kernel.py'
with open(kpath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove linhas corrompidas (L299-305 duplicadas)
# E substitui por uma funcao main_kernel() limpa
new_block = '''def main_kernel():
    """Entry point principal do kernel."""
    import json as _j_ctx
    
    # Le contexto da conversa
    try:
        _ctx_path = os.path.join(os.path.dirname(__file__), '..', 'sandbox', '.mcr_conversa.jsonl')
        if os.path.exists(_ctx_path):
            with open(_ctx_path, 'r', encoding='utf-8') as _f_ctx:
                _ctx_lines = _f_ctx.readlines()[-5:]  # Ultimas 5 linhas
            _ctx_texto = ' '.join(_j_ctx.loads(l).get('msg','') for l in _ctx_lines if l.strip())
            if _ctx_texto:
                print(f'[Contexto] {_ctx_texto[:200]}')
    except: pass
    
    # Processa --json antes de tudo
    if main_json():
        sys.exit(0)
    
    if len(sys.argv) < 2:
        print('MCR-DevIA Kernel v1')
        print('Uso: python kernel.py <comando> [args...]')
        print('     python kernel.py --json <arquivo.json>')
        print(f'Comandos em: {COMANDOS_DIR}')
        sys.exit(0)
    
    cmd = sys.argv[1]
    args = sys.argv[2:]
    
    k = MCRKernel()
    n = k.inicializar()
    
    if cmd == 'listar':
        print(f'Comandos carregados: {n}')
        for nome, desc in k.listar_comandos():
            print(f'  {nome:20s} | {desc}')
    elif cmd == 'refresh':
        n = k.loader.refresh()
        print(f'[Kernel] {n} comandos recarregados (hot-reload)')
    else:
        resultado = k.executar(cmd, args)
        if not resultado:
            print(f'[Kernel] Comando nao encontrado: {cmd}')

if __name__ == '__main__':
    main_kernel()
'''

# Encontra o primeiro 'def main_kernel' ou 'if __name__' e substitui ate o final
replace_start = None
for i, line in enumerate(lines):
    if 'def main_kernel' in line or "if __name__ == '__main__':" in line:
        replace_start = i
        break

if replace_start is not None:
    lines = lines[:replace_start] + [new_block]
    with open(kpath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    try:
        compile(''.join(lines), kpath, 'exec')
        print('OK - kernel.py limpo e com contexto')
    except SyntaxError as e:
        print(f'ERRO: {e}')
else:
    print('ERRO: bloco nao encontrado')

# 2. Cria .mcr_conversa.jsonl vazio se nao existe
conversa_path = r'E:\Projeto MCR\sandbox\.mcr_conversa.jsonl'
if not os.path.exists(conversa_path):
    with open(conversa_path, 'w', encoding='utf-8') as f:
        f.write('')
    print('OK - .mcr_conversa.jsonl criado')

# 3. Atualiza MCR_DevIA-Kernel.py
mpath = r'E:\Projeto MCR\scripts\mcr_devia\MCR_DevIA-Kernel.py'
with open(mpath, 'w', encoding='utf-8') as f:
    f.write('''#!/usr/bin/env python
"""MCR-DevIA Kernel - Entry point CLI.
Importa kernel.py e delega.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == '__main__':
    from kernel import main_kernel
    main_kernel()
''')
print('OK - MCR_DevIA-Kernel.py atualizado')

# 4. Testa
try:
    compile(open(mpath, encoding='utf-8').read(), mpath, 'exec')
    print('OK - MCR_DevIA-Kernel.py compila')
except SyntaxError as e:
    print(f'ERRO MCR_DevIA-Kernel.py: {e}')

print('\\nFeito!')
