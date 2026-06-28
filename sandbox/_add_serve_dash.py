#!/usr/bin/env python3
"""Adiciona comandos --serve e --dashboard ao kernel.py."""
kpath = r'E:\Projeto MCR\scripts\mcr_devia\kernel.py'
with open(kpath, 'r', encoding='utf-8') as f:
    content = f.read()

old = (
    '    else:\n'
    '        resultado = k.executar(cmd, args)\n'
    '        if not resultado:\n'
    '            print(f\'[Kernel] Comando nao encontrado: {cmd}\')'
)

new = (
    '    elif cmd == "--serve":\n'
    '        from modulos.serve import Serve\n'
    '        Serve(k).loop()\n'
    '    elif cmd == "--dashboard":\n'
    '        from modulos.dashboard import Dashboard\n'
    '        Dashboard(k).iniciar()\n'
    '    else:\n'
    '        resultado = k.executar(cmd, args)\n'
    '        if not resultado:\n'
    '            print(f\'[Kernel] Comando nao encontrado: {cmd}\')'
)

if old in content:
    content = content.replace(old, new)
    with open(kpath, 'w', encoding='utf-8') as f:
        f.write(content)
    try:
        compile(content, kpath, 'exec')
        print('OK')
    except SyntaxError as e:
        print(f'ERRO: {e}')
else:
    print('old not found')
    for i, line in enumerate(open(kpath, encoding='utf-8')):
        if 'else:' in line and 'resultado' in line:
            print(f'L{i+1}: {line.rstrip()}')
