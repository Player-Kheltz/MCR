#!/usr/bin/env python3
"""Busca ampla por grupos de sprite com mesma máscara em TODAS as sheets."""
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

# Amostrar DENSAMENTE as primeiras 5 sheets (sprites 0-719)
# Essas são tipicamente itens de inventário com variações de cor
print('Buscando em sprites 0-719...')

grupos = defaultdict(list)
batch_size = 5 * 144  # 5 sheets

for sid in range(0, batch_size):
    try:
        sprite = ext.get_sprite(sid, 32, 32)
        if sprite and len(sprite.pixels) >= 32*32*4:
            img = Image.frombytes('RGBA', (32, 32), sprite.pixels)
            mask = obter_mascara(img)
            opacos = mask.count('1')
            if opacos > 10:
                grupos[mask].append({'id': sid, 'img': img, 'opacos': opacos})
    except Exception:
        pass

# Mostrar grupos por tamanho
from collections import Counter
tamanhos = Counter(len(v) for v in grupos.values())
print(f'Distribuicao de grupos: {dict(sorted(tamanhos.items()))}')

grupos_3 = {k: v for k, v in grupos.items() if len(v) >= 3}
print(f'Grupos com 3+: {len(grupos_3)}')

if grupos_3:
    maiores = sorted(grupos_3.items(), key=lambda x: -len(x[1]))[:15]
    for mask, members in maiores:
        op = mask.count('1')
        ids = [m['id'] for m in members]
        print(f'  {len(members)} sprites, {op} opacos: IDs {ids}')
        
        # Mostrar exemplo de cores
        cores_exemplo = []
        for m in members[:5]:
            img = m['img']
            px = img.load()
            # Amostrar pixel central
            cx, cy = 16, 16
            r, g, b, a = px[cx, cy]
            if a > 128:
                cores_exemplo.append(f'({r},{g},{b})')
            else:
                # Procurar pixel opaco
                for y in range(32):
                    for x in range(32):
                        r, g, b, a = px[x, y]
                        if a > 128:
                            cores_exemplo.append(f'({r},{g},{b})')
                            break
                    if len(cores_exemplo) > len(ids):
                        break
        print(f'    Cores: {", ".join(cores_exemplo[:5])}')
else:
    print('Nenhum grupo com 3+ encontrado!')
    # Mostrar grupos com 2
    grupos_2 = {k: v for k, v in grupos.items() if len(v) == 2}
    print(f'Grupos com 2: {len(grupos_2)}')
    if grupos_2:
        # Verificar padrão de IDs
        for mask, members in list(grupos_2.items())[:3]:
            ids = [m['id'] for m in members]
            op = mask.count('1')
            diff = ids[1] - ids[0]
            print(f'  {op} opacos, IDs {ids}, diff={diff}')
        
        # Tentar encontrar triplas por similaridade de máscara (não identidade)
        print('\nBuscando máscaras similares (>90% match)...')
        masks_list = list(grupos_2.keys())
        for i in range(min(50, len(masks_list))):
            m1 = masks_list[i]
            for j in range(i+1, min(100, len(masks_list))):
                m2 = masks_list[j]
                same = sum(1 for a, b in zip(m1, m2) if a == b)
                total = max(len(m1), len(m2))
                if same / total > 0.90 and same / total < 1.0:
                    op1 = m1.count('1')
                    op2 = m2.count('1')
                    print(f'  Similar: {same/total:.0%} match, {op1}/{op2} opacos')
