import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

from pathlib import Path
from mcr.discriminador_anatomia import avaliar_sprite

OUT_DIR = Path(_ROOT) / 'poc_output' / 'itens_gerados'
CAT_DIR = Path(_ROOT) / 'poc_output' / 'sprites_categorizados'

print('=== Sprites Gerados ===')
for cat_dir in sorted(OUT_DIR.iterdir()):
    if not cat_dir.is_dir():
        continue
    sprites = sorted(cat_dir.glob('*.png'))[:3]
    scores = []
    for sp in sprites:
        r = avaliar_sprite(str(sp))
        scores.append(r['score'])
    media = sum(scores) / len(scores) if scores else 0
    n = len(list(cat_dir.glob('*.png')))
    print('  %s: %.3f (%d sprites)' % (cat_dir.name, media, n))

print()
print('=== Sprites Reais (referencia) ===')
for cat_dir in sorted(CAT_DIR.iterdir()):
    if not cat_dir.is_dir():
        continue
    sprites = sorted(cat_dir.glob('*.png'))[:5]
    scores = []
    for sp in sprites:
        r = avaliar_sprite(str(sp))
        scores.append(r['score'])
    media = sum(scores) / len(scores) if scores else 0
    print('  %s: %.3f' % (cat_dir.name, media))
