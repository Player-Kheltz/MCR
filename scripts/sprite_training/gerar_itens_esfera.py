"""
gerar_itens_esfera.py — Gera novos itens usando anatomia da Esfera + cores reais.

Para cada categoria:
1. Calcula cores médias reais dos sprites da categoria
2. Usa anatomia predita pela Esfera
3. Renderiza sprite com cores reais + posições aprendidas
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

import json
import math
import random
from pathlib import Path
from PIL import Image
import numpy as np

from mcr.regioes_anatomicas import extrair_regioes_cromaticas

CAT_DIR = Path(_ROOT) / 'poc_output' / 'sprites_categorizados'
ESFERA_DIR = Path(_ROOT) / 'poc_output' / 'esfera_categorizada'
OUT_DIR = Path(_ROOT) / 'poc_output' / 'itens_gerados'


def cores_reais_categoria(cat_dir, max_sprites=30):
    """Calcula cores médias Lab* dos sprites de uma categoria."""
    sprites = sorted(cat_dir.glob('*.png'))[:max_sprites]
    todos_lab = []

    for sp in sprites:
        try:
            img = Image.open(sp).convert('RGBA')
            arr_rgba = np.array(img)
            mask = arr_rgba[:,:,3] > 0
            if np.sum(mask) < 10:
                continue
            rgb = np.array(Image.open(sp).convert('RGB'))
            regioes = extrair_regioes_cromaticas(rgb)
            for r in regioes:
                todos_lab.append(r['cor_media_lab'])
        except Exception:
            pass

    if not todos_lab:
        return {}

    # Agrupiar cores por similaridade (kmeans simplificado)
    from collections import defaultdict
    buckets = defaultdict(list)
    for L, a, b in todos_lab:
        # Discretizar
        key = (round(L/10)*10, round(a/10)*10, round(b/10)*10)
        buckets[key].append((L, a, b))

    # Top 5 buckets mais comuns
    cores = []
    for key, pixels in sorted(buckets.items(), key=lambda x: -len(x[1]))[:5]:
        L = np.mean([p[0] for p in pixels])
        a = np.mean([p[1] for p in pixels])
        b = np.mean([p[2] for p in pixels])
        freq = len(pixels)
        cores.append({'lab': (float(L), float(a), float(b)), 'freq': freq})

    return {'cores': cores, 'total_pixels': len(todos_lab)}


def lab_para_rgb(L, a, b):
    """Conversão Lab* → RGB simplificada."""
    y = (L + 16) / 116
    x = a / 500 + y
    z = y - b / 200
    def f(t):
        return t**3 if t > 6/29 else 3*(6/29)**2*(t-4/29)
    r = 3.2406*f(x) - 1.5372*f(y) - 0.4986*f(z)
    g = -0.9689*f(x) + 1.8758*f(y) + 0.0415*f(z)
    b_ = 0.0557*f(x) - 0.2040*f(y) + 1.0570*f(z)
    return (int(max(0,min(255,r*255))), int(max(0,min(255,g*255))), int(max(0,min(255,b_*255))))


def renderizar_anatomia(anatomia, cores_info, largura=32, altura=32, seed=0):
    """Renderiza sprite a partir de anatomia + cores reais."""
    random.seed(seed)
    sprite = np.zeros((altura, largura, 3), dtype=np.uint8)
    sprite[:] = [255, 0, 255]

    cores = cores_info.get('cores', [{'lab': (50, 0, 0)}])

    for i, reg in enumerate(anatomia):
        pos = reg['pos']
        col = ['esq', 'cent', 'dir'].index(pos.split('_')[0])
        lin = ['sup', 'mid', 'inf'].index(pos.split('_')[1])

        cx = int((col + 0.5) * largura / 3)
        cy = int((lin + 0.5) * altura / 3)
        raio = int(reg['escala'] * min(largura, altura) / 2)

        # Escolher cor da lista (ciclar)
        cor_info = cores[i % len(cores)]
        rgb = lab_para_rgb(*cor_info['lab'])

        for y in range(max(0, cy - raio), min(altura, cy + raio)):
            for x in range(max(0, cx - raio), min(largura, cx + raio)):
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                if dist <= raio:
                    sprite[y, x] = rgb

    return sprite


def main():
    print("=" * 60)
    print("GERAÇÃO DE NOVOS ITENS POR CATEGORIA")
    print("=" * 60)

    # Carregar anatomias da Esfera
    with open(ESFERA_DIR / 'resultados_rapido.json', 'r', encoding='utf-8') as f:
        resultados = json.load(f)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for cat_name, info in resultados.items():
        cat_dir = CAT_DIR / cat_name
        display = cat_name.replace('_', ' ')
        anatomia = info.get('anatomia', [])

        if not anatomia:
            print(f"  {display}: SEM ANATOMIA")
            continue

        cores_info = cores_reais_categoria(cat_dir)
        if not cores_info:
            print(f"  {display}: SEM CORES")
            continue

        n_cores = len(cores_info.get('cores', []))
        print(f"  {display}: {len(anatomia)} regiões, {n_cores} cores detectadas")

        cat_out = OUT_DIR / cat_name
        cat_out.mkdir(exist_ok=True)

        for seed in range(5):
            sprite = renderizar_anatomia(anatomia, cores_info, seed=seed)
            fname = f'novo_{seed}.png'
            Image.fromarray(sprite).save(cat_out / fname)

        print(f"    -> 5 sprites gerados em {cat_out}")

    print(f"\n{'='*60}")
    print(f"Todos os sprites gerados em: {OUT_DIR}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
