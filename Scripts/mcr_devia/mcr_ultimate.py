#!/usr/bin/env python3
"""
MCR-DevIA ULTIMATE — Orquestrador Universal
==============================================
Nao duplica templates. CHAMA os scripts certos.

Uso: python mcr_ultimate.py npc Nome fala 101 50
     python mcr_ultimate.py monster Nome hp atk def loot_id chance
     python mcr_ultimate.py quest Nome desc obj xp
     python mcr_ultimate.py item Nome id tipo atk def peso
     python mcr_ultimate.py spell Nome elem dano mana cd
"""

import sys, os, subprocess

BASE = r'E:\Projeto MCR'
DEVIA = os.path.join(BASE, 'scripts', 'mcr_devia')

COMANDOS = {
    'npc':     f'python "{{DEVIA}}"/mcr_devia.py gerar npc',
    'monster': f'python "{{DEVIA}}"/mcr_devia.py gerar monster',
    'quest':   f'python "{{DEVIA}}"/mcr_devia.py gerar quest',
    'item':    f'python "{{DEVIA}}"/mcr_devia.py gerar item',
    'spell':   f'python "{{DEVIA}}"/mcr_devia.py gerar spell',
    'lore':    f'python "{{DEVIA}}"/mcr_devia.py lore',
    'ensinar': f'python "{{DEVIA}}"/mcr_devia.py ensinar',
    'status':  f'python "{{DEVIA}}"/mcr_devia.py status',
    'chat':    f'python "{{DEVIA}}"/mcr_chat.py',
    'compilar':f'python "{{DEVIA}}"/mcr_autobuild.py',
}

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in COMANDOS:
        print('MCR-DevIA Ultimate - Orquestrador')
        print(f'\nComandos: {", ".join(COMANDOS.keys())}')
        print(f'\nEx: python {sys.argv[0]} npc Ferreiro "Ola" 101 50')
        sys.exit(1)
    
    cmd = sys.argv[1]
    args = sys.argv[2:]
    
    template = COMANDOS[cmd].format(DEVIA=DEVIA)
    comando = template + ' ' + ' '.join(f'"{a}"' if ' ' in a else a for a in args)
    
    print(f'[ULTIMATE] Executando: {cmd}')
    subprocess.run(comando, shell=True)
