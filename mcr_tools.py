#!/usr/bin/env python3
"""mcr_tools.py — REPL pratico para geracao de conteudo do servidor Canary.
Comandos: /npc, /monster, /sair"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcr_server_toolset import criar_npc, criar_monstro

COMANDOS = {
    '/npc': ('Criar um NPC', criar_npc),
    '/monster': ('Criar um Monstro', criar_monstro),
    '/sair': ('Sair do toolset', None),
    '/help': ('Mostrar ajuda', None),
}

print("""
==================================================
  MCR-DevIA — Server Toolset v1.0
  Geracao de conteudo para Canary (Open Tibia)
==================================================
  Comandos:
    /npc <descricao>      Criar NPC valido
    /monster <descricao>  Criar Monstro valido
    /help                 Mostrar ajuda
    /sair                 Sair
==================================================
""")

while True:
    try:
        entrada = input('> ').strip()
    except (EOFError, KeyboardInterrupt):
        print()
        break

    if not entrada:
        continue

    if entrada == '/sair':
        print('[Toolset] Encerrando.')
        break

    if entrada == '/help':
        print('Comandos:')
        for cmd, (desc, _) in COMANDOS.items():
            print('  %s  %s' % (cmd.ljust(12), desc))
        print()
        print('Exemplos:')
        print('  /npc Crie um NPC chamado Guarda Real que vende espadas')
        print('  /monster Crie um monstro de fogo com 5000 HP')
        continue

    # Verifica se comecou com /
    if not entrada.startswith('/'):
        print('[Toolset] Use /npc, /monster ou /help para comecar.')
        continue

    # Extrai comando e descricao
    partes = entrada.split(' ', 1)
    cmd = partes[0].lower()
    descricao = partes[1] if len(partes) > 1 else ''

    if not descricao:
        print('[Toolset] Forneca uma descricao apos o comando.')
        print('  Ex: /npc Crie um ferreiro chamado Thorin')
        continue

    if cmd == '/npc':
        resultado = criar_npc(descricao)
    elif cmd == '/monster':
        resultado = criar_monstro(descricao)
    else:
        print('[Toolset] Comando desconhecido: %s' % cmd)
        continue

    print()
    print(resultado)
    print()
