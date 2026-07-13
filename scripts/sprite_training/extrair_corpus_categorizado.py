"""
extrair_corpus_categorizado.py — Extrai sprites reais do Tibia por categoria.

Usa SpriteExtractor + item_sprite_map.json para extrair sprites
de categorias específicas (armas, armaduras, escudos, etc.).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

import json
from pathlib import Path
from collections import Counter, defaultdict
from PIL import Image
import numpy as np

from mcr.sprite_extractor import SpriteExtractor

MAP_PATH = Path('C:/Users/Kheltz/AppData/Local/Temp/item_sprite_map.json')
THINGS_DIR = Path(_ROOT) / 'client' / 'data' / 'things' / '1500'
OUT_DIR = Path(_ROOT) / 'poc_output' / 'sprites_categorizados'

CATEGORIAS_ALVO = {
    'sword weapons': 80,
    'axe weapons': 80,
    'club weapons': 80,
    'shields': 80,
    'armors': 80,
    'helmets': 80,
    'legs': 50,
    'boots': 50,
    'rings': 40,
    'amulets and necklaces': 40,
    'food': 60,
    'tools': 40,
    'spellbooks': 20,
    'wands': 20,
    'rods': 20,
    'distance weapons': 40,
    'ammunition': 30,
    'creature products': 60,
}


def carregar_mapa():
    with open(MAP_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    por_categoria = defaultdict(list)
    for item_id, info in data.items():
        cat = info.get('primarytype', '')
        if not cat:
            continue
        sprite_ids = info.get('sprite_ids', [])
        if sprite_ids:
            por_categoria[cat].append({
                'name': info.get('name', ''),
                'sprite_ids': sprite_ids,
            })
    return por_categoria


def extrair_categoria(extractor, categoria, itens, max_sprites, out_dir):
    cat_dir = out_dir / categoria.replace(' ', '_')
    cat_dir.mkdir(parents=True, exist_ok=True)
    extraidos = 0
    sprites_vistos = set()
    for item in itens:
        if extraidos >= max_sprites:
            break
        for sprite_id in item['sprite_ids']:
            if sprite_id in sprites_vistos:
                continue
            if extraidos >= max_sprites:
                break
            sprites_vistos.add(sprite_id)
            try:
                sprite = extractor.get_sprite(sprite_id)
                if sprite and sprite.pixels:
                    img = Image.frombytes('RGBA', (sprite.width, sprite.height), sprite.pixels)
                    arr = np.array(img)
                    opaque = np.sum(arr[:,:,3] > 0)
                    if opaque > 20:
                        fname = f"{item['name'].replace('/', '_').replace(' ', '_')}_{sprite_id}.png"
                        img.save(cat_dir / fname)
                        extraidos += 1
            except Exception:
                pass
    return extraidos


def main():
    print("=" * 60)
    print("EXTRAÇÃO MASSIVA DE SPRITES CATEGORIZADOS")
    print("=" * 60)

    print("\n[1/3] Carregando mapa item->sprite...")
    por_categoria = carregar_mapa()
    print(f"  {sum(len(v) for v in por_categoria.values())} itens com sprite_ids")
    print(f"  {len(por_categoria)} categorias")

    print("\n[2/3] Inicializando SpriteExtractor...")
    extractor = SpriteExtractor(str(THINGS_DIR))
    stats = extractor.stats()
    print(f"  {stats['total_sprites']} sprites disponiveis")

    print("\n[3/3] Extraindo sprites por categoria...")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    resumo = {}
    for cat, max_sprites in CATEGORIAS_ALVO.items():
        itens = por_categoria.get(cat, [])
        if not itens:
            print(f"  {cat}: SEM DADOS")
            continue
        n = extrair_categoria(extractor, cat, itens, max_sprites, OUT_DIR)
        resumo[cat] = n
        print(f"  {cat}: {n} sprites extraidos (de {len(itens)} itens)")

    with open(OUT_DIR / 'resumo.json', 'w', encoding='utf-8') as f:
        json.dump(resumo, f, indent=2, ensure_ascii=False)

    total = sum(resumo.values())
    print(f"\n{'='*60}")
    print(f"TOTAL: {total} sprites extraidos em {len(resumo)} categorias")
    print(f"Salvo em: {OUT_DIR}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
