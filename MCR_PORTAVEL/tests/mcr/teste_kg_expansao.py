#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'devia' / 'kernel'))

from mcr.sanity_validator import SanityValidator
SanityValidator.resetar_cache()
sv = SanityValidator()

print(f'APIs: {len(sv.api_conhecidas)}')

# Busca APIs com isPlayer ou similares
for api in sorted(sv.api_conhecidas):
    if 'is' in api.lower() and ('player' in api.lower() or 'monster' in api.lower() or 'npc' in api.lower()):
        print(f'  ENCONTRADO: {api}')
print('---')
# Busca doPlayerSendTextMessage variants
for api in sorted(sv.api_conhecidas):
    if 'sendtextmessage' in api.lower():
        print(f'  ENCONTRADO: {api}')
print('---')
# Busca onSay
for api in sorted(sv.api_conhecidas):
    if 'onsay' in api.lower():
        print(f'  ENCONTRADO: {api}')
print('---')
# Busca npc variants
for api in sorted(sv.api_conhecidas):
    if 'npchandler' in api.lower() or 'npc' in api.lower() and 'handler' in api.lower():
        print(f'  ENCONTRADO: {api}')
