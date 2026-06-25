"""Restaurar os 3 problemas para o estado original"""
import os

BASE = r'E:\Projeto MCR\sandbox\teste_cego_ultra'

# 1. npc_acentos.lua — Voltar pra Latin-1
with open(os.path.join(BASE, 'npc_acentos.lua'), 'w', encoding='latin-1') as f:
    f.write('-- NPC: S\xe1bio\nlocal npc = NPC("S\xe1bio")\nnpc:setSaudacao("Ol\xe1!")\n')
print('[RESTAURADO] npc_acentos.lua -> Latin-1')

# 2. verificar_item.lua — Voltar pra Python misturado
with open(os.path.join(BASE, 'verificar_item.lua'), 'w') as f:
    f.write('-- Verificador\ndef verificar(item):\n    if item["id"] == 123:\n        return True\n    return False\n')
print('[RESTAURADO] verificar_item.lua -> sintaxe Python')

# 3. criar_pocao.lua — Voltar nil desnecessario
with open(os.path.join(BASE, 'criar_pocao.lua'), 'w') as f:
    f.write('-- Pocao\nfunction criarPocao(tipo)\n    local p = {}\n    p.tipo = tipo\n    p.efeito = nil\n    return p\nend\n')
print('[RESTAURADO] criar_pocao.lua -> nil desnecessario')

print('\n3 arquivos restaurados. Agora deixe o MCR-DevIA tentar sozinho.')
print('Execute o loop ou o scan e veja se ele detecta e corrige.')
