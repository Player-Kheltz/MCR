#!/usr/bin/env python3
"""Amostragem densa: busca grupos de sprites com mesma máscara em sheets consecutivas."""
import sys, os, json
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcr.sprite_extractor import SpriteExtractor
from PIL import Image

def obter_mascara(img):
    px = img.load()
    bits = []
    for y in range(32):
        for x in range(32):
            r, g, b, a = px[x, y]
            bits.append('1' if a > 128 and (r, g, b) != (255, 0, 255) else '0')
    return ''.join(bits)

ext = SpriteExtractor()

# Amostrar DENSAMENTE as primeiras 10 sheets (sprites 0 a 1439)
# Cada sheet tem 144 sprites (384/32 * 384/32 = 12*12 = 144)
print('Buscando grupos com mesma máscara em sprites 0-1439...')

grupos = defaultdict(list)
for sid in range(0, 1500):
    try:
        sprite = ext.get_sprite(sid, 32, 32)
        if sprite and len(sprite.pixels) >= 32*32*4:
            img = Image.frombytes('RGBA', (32, 32), sprite.pixels)
            mask = obter_mascara(img)
            opacos = mask.count('1')
            if opacos > 10:  # Ignorar quase vazios
                grupos[mask].append({'id': sid, 'img': img, 'opacos': opacos})
    except Exception as e:
        pass

# Filtrar grupos com 3+
grupos_3 = {k: v for k, v in grupos.items() if len(v) >= 3}
print(f'Total sprites: {sum(len(v) for v in grupos.values())}')
print(f'Mascaras unicas: {len(grupos)}')
print(f'Grupos com 3+: {len(grupos_3)}')

if grupos_3:
    maiores = sorted(grupos_3.items(), key=lambda x: -len(x[1]))[:20]
    for mask, members in maiores:
        op = mask.count('1')
        ids_str = ', '.join(str(m['id']) for m in members[:8])
        print(f'  {len(members)} sprites, {op} opacos: [{ids_str}{",..." if len(members) > 8 else ""}]')
else:
    print('Nenhum grupo com 3+ encontrado!')
    # Mostrar grupos com 2
    grupos_2 = {k: v for k, v in grupos.items() if len(v) == 2}
    print(f'Grupos com 2: {len(grupos_2)}')
    if grupos_2:
        for mask, members in list(grupos_2.items())[:10]:
            op = mask.count('1')
            print(f'  2 sprites, {op} opacos: IDs {members[0]["id"]}, {members[1]["id"]}')
