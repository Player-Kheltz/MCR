"""
treinar_esfera_rapido.py — Treina Esfera por categoria (versão otimizada).

Usa amostragem: max 30 sprites por categoria para treinamento rápido.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

import json
import time
from pathlib import Path
from collections import defaultdict
from PIL import Image
import numpy as np

from mcr.regioes_anatomicas import extrair_regioes_cromaticas
from mcr.visual_coupling import VisualCoupling
from devia.kernel.MCR_legacy import MCRCoupling

CAT_DIR = Path(_ROOT) / 'poc_output' / 'sprites_categorizados'
OUT_DIR = Path(_ROOT) / 'poc_output' / 'esfera_categorizada'

MAX_POR_CAT = 30


def extrair_regioes_rapido(caminho):
    """Extrai regiões com limiar fixo (mais rápido)."""
    img = Image.open(caminho).convert('RGBA')
    arr_rgba = np.array(img)
    mask = arr_rgba[:,:,3] > 0
    if np.sum(mask) < 20:
        return []
    rgb = np.array(Image.open(caminho).convert('RGB'))
    return extrair_regioes_cromaticas(rgb)


def treinar_categoria(cat_dir):
    sprites = sorted(cat_dir.glob('*.png'))[:MAX_POR_CAT]
    if not sprites:
        return None

    coupling = MCRCoupling()
    vc = VisualCoupling(coupling)

    for sp in sprites:
        regioes = extrair_regioes_rapido(sp)
        if regioes:
            vc.alimentar_sprite(regioes)

    coupling.recalcular()
    return coupling


def anatomia_da_esfera(coupling):
    posicoes = ['esq_sup', 'cent_sup', 'dir_sup',
                'esq_mid', 'cent_mid', 'dir_mid',
                'esq_inf', 'cent_inf', 'dir_inf']
    anatomia = []
    usados = set()
    for pos in posicoes:
        try:
            regiao, _ = coupling.esfera.predizer_cross('regiao_cromatica', bbox_pos=pos)
            if not regiao or regiao in usados:
                continue
            usados.add(regiao)
            cor, _ = coupling.esfera.predizer_cross('cor_media', regiao_cromatica=regiao)
            geom, _ = coupling.esfera.predizer_cross('geometria', regiao_cromatica=regiao)
            tam = geom.split('_')[0] if geom else 'medio'
            escala = {
                'minusculo': 0.12, 'pequeno': 0.20, 'medio': 0.30,
                'grande': 0.40, 'enorme': 0.50, 'muito': 0.55
            }.get(tam, 0.30)
            anatomia.append({
                'pos': pos, 'regiao': regiao,
                'cor': cor or 'medio_neut', 'geom': geom or 'medio_quad',
                'escala': escala,
            })
        except Exception:
            pass
    return anatomia


def main():
    print("=" * 60)
    print("TREINAMENTO RÁPIDO DA ESFERA POR CATEGORIA")
    print("=" * 60)

    categorias = sorted([d.name for d in CAT_DIR.iterdir() if d.is_dir()])
    print(f"{len(categorias)} categorias, max {MAX_POR_CAT} sprites cada\n")

    resultados = {}
    t0 = time.time()

    for cat_name in categorias:
        cat_dir = CAT_DIR / cat_name
        display = cat_name.replace('_', ' ')

        t1 = time.time()
        coupling = treinar_categoria(cat_dir)
        dt = time.time() - t1

        if not coupling:
            print(f"  {display}: SEM DADOS")
            continue

        anatomia = anatomia_da_esfera(coupling)
        n_sprites = len(sorted(cat_dir.glob('*.png'))[:MAX_POR_CAT])

        resultados[cat_name] = {
            'n_sprites': n_sprites,
            'n_correlacoes': coupling.esfera.total,
            'anatomia': anatomia,
        }

        reg_str = ', '.join(f"{r['cor'][:10]}({r['geom'][:6]})" for r in anatomia)
        print(f"  {display}: {n_sprites} sprites, {coupling.esfera.total} corr, "
              f"{len(anatomia)} reg [{reg_str}] ({dt:.1f}s)")

    dt_total = time.time() - t0
    print(f"\n{'='*60}")
    print(f"Treinamento concluído em {dt_total:.1f}s")
    print(f"{'='*60}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / 'resultados_rapido.json', 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False, default=str)
    print(f"Salvo em: {OUT_DIR / 'resultados_rapido.json'}")


if __name__ == '__main__':
    main()
