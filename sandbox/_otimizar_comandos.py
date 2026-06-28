#!/usr/bin/env python
"""Otimiza os 25 comandos extraidos para usar kg/ia do kernel."""
import os, re

COMANDOS = r'E:\Projeto MCR\scripts\mcr_devia\comandos'
PULOS = {'cmd_status', 'cmd_ensinar', 'cmd_grep', 'cmd_fast', 'cmd_aprender_conceito',
         'cmd_refresh', 'cmd_perguntar', 'cmd_read', 'cmd_todo'}

for f in sorted(os.listdir(COMANDOS)):
    if not f.endswith('.py') or f.startswith('__'): continue
    if f[:-3] in PULOS: continue
    
    fpath = os.path.join(COMANDOS, f)
    with open(fpath, 'r', encoding='utf-8') as fh:
        content = fh.read()
    
    changes = []
    
    # Substitui referencias a funcoes globais
    if 'fast(' in content and 'from modulos.util import fast' in content:
        changes.append('fast() ok (importado de util)')
    
    # Substitui print("[MCR-DevIA]" por print("[Comando]"
    old_print = content.count('print(f\'[MCR-DevIA]')
    if old_print:
        content = content.replace("print(f'[MCR-DevIA]", "print(f'[Comando]")
        changes.append(f'{old_print} prints atualizados')
    
    # Substitui referencias a self.kg por kg (parametro)
    if 'self.kg' in content:
        content = content.replace('self.kg', 'kg')
        changes.append('self.kg -> kg')
    if 'self.ia' in content:
        content = content.replace('self.ia', 'ia')
        changes.append('self.ia -> ia')
    
    # Remove 'self,' de assinaturas de funcoes internas se houver
    content = re.sub(r'def \w+\(self,', lambda m: m.group(0).replace('self, ', ''), content)
    
    with open(fpath, 'w', encoding='utf-8') as fh:
        fh.write(content)
    
    print(f'{f}: {"; ".join(changes) if changes else "sem alteracoes"}')

print('\nOtimizacao concluida!')
