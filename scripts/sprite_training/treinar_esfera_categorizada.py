"""
treinar_esfera_categorizada.py — Treina Esfera por categoria de item.

Para cada categoria (armas, escudos, etc.):
1. Extrai regiões cromáticas de todos os sprites
2. Alimenta a Esfera com correlações visuais
3. Extrai anatomia média da categoria
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

import json
import math
from pathlib import Path
from collections import Counter, defaultdict
from PIL import Image
import numpy as np

from mcr.regioes_anatomicas import extrair_regioes_cromaticas
from mcr.visual_coupling import VisualCoupling
from mcr.coupling import MCRCoupling

CAT_DIR = Path(_ROOT) / 'poc_output' / 'sprites_categorizados'
OUT_DIR = Path(_ROOT) / 'poc_output' / 'esfera_categorizada'

# Cores médias por tipo de item (aprendidas dos sprites reais)
CORES_POR_CATEGORIA = {}


def extrair_regioes_sprite(caminho):
    """Extrai regiões de um sprite RGBA."""
    img = Image.open(caminho).convert('RGB')
    arr = np.array(img)
    # Remover fundo magenta
    rgba = np.array(Image.open(caminho).convert('RGBA'))
    mask = rgba[:,:,3] > 0
    # Se maioria transparente, pulo
    if np.sum(mask) < 20:
        return []
    return extrair_regioes_cromaticas(arr)


def treinar_categoria(nome_categoria, sprites_dir):
    """Treina a Esfera com sprites de uma categoria."""
    sprites = list(sprites_dir.glob('*.png'))
    if not sprites:
        return None

    coupling = MCRCoupling()
    vc = VisualCoupling(coupling)

    n_regioes_total = 0
    todos_lab = []

    for sprite_path in sprites:
        regioes = extrair_regioes_sprite(sprite_path)
        if regioes:
            vc.alimentar_sprite(regioes)
            n_regioes_total += len(regioes)
            for r in regioes:
                todos_lab.append(r['cor_media_lab'])

    coupling.recalcular()

    # Calcular cores médias da categoria
    if todos_lab:
        L_medio = np.mean([l[0] for l in todos_lab])
        a_medio = np.mean([l[1] for l in todos_lab])
        b_medio = np.mean([l[2] for l in todos_lab])
        CORES_POR_CATEGORIA[nome_categoria] = (float(L_medio), float(a_medio), float(b_medio))

    # Extrair correlações aprendidas
    correlacoes = {}
    for nivel_a in coupling.esfera.cross:
        for valor_a in coupling.esfera.cross[nivel_a]:
            for nivel_b in coupling.esfera.cross[nivel_a][valor_a]:
                for valor_b, freq in coupling.esfera.cross[nivel_a][valor_a][nivel_b].items():
                    if freq >= 2:
                        chave = f"{nivel_a}={valor_a} -> {nivel_b}={valor_b}"
                        correlacoes[chave] = freq

    return {
        'n_sprites': len(sprites),
        'n_regioes_total': n_regioes_total,
        'n_correlacoes': len(correlacoes),
        'total_cooc': coupling.total_cooc,
        'total_esfera': coupling.esfera.total,
        'top_correlacoes': sorted(correlacoes.items(), key=lambda x: -x[1])[:20],
        'coupling': coupling,
    }


def anatomia_da_esfera(coupling):
    """Usa a Esfera para montar anatomia."""
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
                'pos': pos,
                'regiao': regiao,
                'cor_nome': cor or 'medio_neut',
                'geom': geom or 'medio_quad',
                'escala': escala,
            })
        except Exception:
            pass

    return anatomia


def main():
    print("=" * 60)
    print("TREINAMENTO DA ESFERA POR CATEGORIA")
    print("=" * 60)

    categorias = sorted([d.name for d in CAT_DIR.iterdir() if d.is_dir()])
    print(f"\n{len(categorias)} categorias encontradas")

    resultados = {}

    for cat_dir_name in categorias:
        cat_dir = CAT_DIR / cat_dir_name
        cat_display = cat_dir_name.replace('_', ' ')

        print(f"\n--- {cat_display} ---")
        resultado = treinar_categoria(cat_display, cat_dir)

        if not resultado:
            print("  Sem dados")
            continue

        print(f"  Sprites: {resultado['n_sprites']}")
        print(f"  Regioes total: {resultado['n_regioes_total']}")
        print(f"  Correlacoes: {resultado['n_correlacoes']}")
        print(f"  Co-ocorrencias: {resultado['total_cooc']}")

        # Extrair anatomia
        anatomia = anatomia_da_esfera(resultado['coupling'])
        resultado['anatomia'] = anatomia
        print(f"  Anatomia: {len(anatomia)} regioes")
        for r in anatomia:
            print(f"    {r['pos']}: {r['cor_nome']} ({r['geom']}, {r['escala']:.2f})")

        # Top correlações
        if resultado['top_correlacoes']:
            print("  Top correlacoes:")
            for chave, freq in resultado['top_correlacoes'][:5]:
                print(f"    {chave}: {freq}")

        resultados[cat_dir_name] = {
            'n_sprites': resultado['n_sprites'],
            'n_regioes': resultado['n_regioes_total'],
            'n_correlacoes': resultado['n_correlacoes'],
            'anatomia': anatomia,
            'top_correlacoes': [(k, v) for k, v in resultado['top_correlacoes'][:10]],
        }

    # Salvar resultados
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Salvar como JSON (sem coupling)
    with open(OUT_DIR / 'resultados.json', 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False, default=str)

    # Salvar cores médias
    with open(OUT_DIR / 'cores_por_categoria.json', 'w', encoding='utf-8') as f:
        json.dump(CORES_POR_CATEGORIA, f, indent=2, default=str)

    print(f"\n{'='*60}")
    print(f"Resultados salvos em: {OUT_DIR}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
