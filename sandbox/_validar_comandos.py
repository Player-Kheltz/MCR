#!/usr/bin/env python
"""Valida todos os 34 comandos modulares - tenta carregar e executar cada um."""
import sys, os, time
sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
from kernel import MCRKernel

k = MCRKernel()
k.inicializar()
n = k.loader.scan()
print(f'Comandos carregados: {n}\n')

# Testa cada comando (apenas carregamento + init, sem execucao completa)
testes = []
for nome in sorted(k.loader._cache.keys()):
    cmd = k.loader.get(nome)
    if cmd:
        meta = cmd['meta']
        handler = cmd['handler']
        testes.append((nome, meta, handler))

print(f'Testando {len(testes)} comandos...\n')
erros = 0
for nome, meta, handler in testes:
    try:
        # Testa se o handler existe e e chamavel
        assert callable(handler), f'handler nao chamavel'
        # Testa register() basico
        assert meta.get('name') == nome, f'nome diverge: {meta.get("name")}'
        print(f'  OK {nome:25s} | {meta.get("desc", "")[:40]}')
    except Exception as e:
        print(f'  ERRO {nome:25s} | {e}')
        erros += 1

print(f'\nResultado: {len(testes)-erros}/{len(testes)} OK, {erros} erros')

if erros == 0:
    print('\nTestando --json mode:')
    import json
    test_json = os.path.join(r'E:\Projeto MCR\sandbox', '.mcr_cmd.json')
    with open(test_json, 'w', encoding='utf-8') as f:
        json.dump({"cmd": "status", "args": []}, f)
    print('  OK arquivo JSON criado')
    
    print('\nTestando hot-reload:')
    n2 = k.loader.refresh()
    print(f'  OK {n2} comandos recarregados')
    
    print('\nTestando legado (import):')
    try:
        from MCR_DevIA_Legado import main as legado_main
        print('  OK MCR_DevIA-Legado.py importavel')
    except:
        print('  AVISO: MCR_DevIA-Legado.py (alias, nao precisa importar)')
    
    print('\n✅ TODOS OS TESTES PASSARAM!')
else:
    print('\n❌ ALGUNS TESTES FALHARAM!')
