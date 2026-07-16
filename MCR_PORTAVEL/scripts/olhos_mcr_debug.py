#!/usr/bin/env python3
"""
olhos_mcr_debug.py -- Debug completo com ASCII rico para revisao.

Gera representacao ASCII multi-camada (papel, luminancia, matiz,
perfil colunar, diagnostico) para sprites reais e gerados.
"""
import os, sys, random
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcr.sprite_corpus import (
    carregar_categoria, extrair_grid_papel, POC_OUTPUT_DIR,
)
from mcr.olhos_mcr import (
    sprite_para_ascii_rich, sprite_para_ascii_compacto,
    categoria_para_ascii_rich,
)
from mcr.template_regiao import (
    treinar_templates, gerar_sprite,
    clusterizar_por_arquetipo, treinar_templates_por_arquetipo,
    gerar_sprite_por_arquetipo,
)

SEED = 42
random.seed(SEED)

CATEGORIAS = ['sword_weapons', 'shields', 'armors', 'helmets', 'food', 'boots']
N_MOSTRAR = 5
N_GERAR = 5


def gerar_debug():
    linhas = []
    linhas.append('=' * 70)
    linhas.append('OLHOS MCR -- ASCII RICO PARA ARQUITETOS')
    linhas.append('Seed: %d | Formato: PAPEL + LUMINANCE + MATIZ + PERFIL + DIAG' % SEED)
    linhas.append('=' * 70)
    linhas.append('')

    for cat in CATEGORIAS:
        linhas.append('#' * 70)
        linhas.append('# CATEGORIA: %s' % cat)
        linhas.append('#' * 70)
        linhas.append('')

        try:
            sprites_reais = carregar_categoria(cat, max_sprites=20)
        except Exception as e:
            linhas.append('ERRO: %s' % e)
            linhas.append('')
            continue

        grids_reais = []
        for s in sprites_reais[:20]:
            gp, gc = extrair_grid_papel(s)
            grids_reais.append((gp, gc))

        # --- REAIS ---
        linhas.append('--- REAIS (mostrando %d de %d) ---' % (N_MOSTRAR, len(grids_reais)))
        linhas.append('')
        for i in range(min(N_MOSTRAR, len(grids_reais))):
            gp, gc = grids_reais[i]
            linhas.append('=== %s REAL #%d ===' % (cat, i + 1))
            linhas.append(sprite_para_ascii_rich(gp, gc, nome='%s_real_%d' % (cat, i)))
            linhas.append('')

        # --- GERADOS ---
        linhas.append('--- GERADOS ---')
        linhas.append('')

        # Clusterizar
        grids_only = [gp for gp, gc in grids_reais]
        clusters = clusterizar_por_arquetipo(grids_only, min_cluster_size=3)
        n_clusters = len(clusters)
        tamanhos = [len(c) for c in clusters]
        linhas.append('Clusters: %d, tamanhos=%s' % (n_clusters, tamanhos))
        linhas.append('')

        if n_clusters == 0:
            treino = treinar_templates(grids_only)
            for i in range(N_GERAR):
                gp, info = gerar_sprite(treino)
                # Gerar grid_cor fake para visualizacao
                gc = _grid_cor_para_ascii_colors(gp)
                linhas.append('=== %s GERADO #%d (template unico) ===' % (cat, i + 1))
                linhas.append(sprite_para_ascii_rich(gp, gc, nome='%s_ger_%d' % (cat, i)))
                linhas.append('')
        else:
            templates = treinar_templates_por_arquetipo(grids_only, clusters)
            resultados = gerar_sprite_por_arquetipo(templates, clusters, total_gerados=N_GERAR)
            for i, (gp, _) in enumerate(resultados):
                gc = _grid_cor_para_ascii_colors(gp)
                linhas.append('=== %s GERADO #%d (arquetipo) ===' % (cat, i + 1))
                linhas.append(sprite_para_ascii_rich(gp, gc, nome='%s_ger_%d' % (cat, i)))
                linhas.append('')

        linhas.append('')

    linhas.append('=' * 70)
    linhas.append('FIM DO OLHOS MCR')
    linhas.append('=' * 70)
    return '\n'.join(linhas)


def _grid_cor_para_ascii_colors(grid_papel):
    """Gera grid_cor basico para visualizacao de sprites gerados.

    Usa preto para B e branco para L (neutro para luminancia/matiz).
    """
    h = len(grid_papel)
    w = len(grid_papel[0]) if h else 0
    grid_cor = [[(0, 0, 0) for _ in range(w)] for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if grid_papel[y][x] == 'B':
                grid_cor[y][x] = (30, 30, 30)
            elif grid_papel[y][x] == 'L':
                grid_cor[y][x] = (180, 180, 180)
    return grid_cor


def main():
    output = gerar_debug()

    out_path = POC_OUTPUT_DIR / 'olhos_mcr_debug.txt'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(output)

    n_lines = len(output.split('\n'))
    print('Salvo: %s (%d linhas)' % (out_path, n_lines))


if __name__ == '__main__':
    main()
