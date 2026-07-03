"""Teste da regex de extração de itens shop."""
import re

texto = open('Canary/data-otservbr-global/npc/al_dee.lua', encoding='utf-8').read()

# Regex usada no indexador
matches = re.findall(r'\{\s*itemName\s*=\s*"([^"]*)"\s*,\s*clientId\s*=\s*(\d+)([^}]*)\}', texto)
print('Encontrados via regex:', len(matches))
for m in matches[:5]:
    print('  - nome=%s, clientId=%s, resto=%s' % (m[0], m[1], m[2][:50]))

# Também testa se o bloco de shop está sendo encontrado
m = re.search(r'npcConfig\.shop\s*=', texto)
if m:
    pos = m.start()
    print('\nnpcConfig.shop encontrado na posicao', pos)
    print('Contexto:', repr(texto[pos:pos+200]))
