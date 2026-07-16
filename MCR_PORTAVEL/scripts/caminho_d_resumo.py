#!/usr/bin/env python3
"""
caminho_d_resumo.py — Resumo ASCII para revisao do arquiteto.

Analise visual dos sprites gerados com Caminho D (multi-template por arquétipo).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

from mcr.sprite_corpus import carregar_categoria, extrair_grid_papel, sprite_para_ascii
from mcr.template_regiao import (
    clusterizar_por_arquetipo, treinar_templates_por_arquetipo,
    gerar_sprite_por_arquetipo, treinar_templates, gerar_sprite,
)
import random

SEED = 42
random.seed(SEED)

CATEGORIAS = ['sword_weapons', 'shields', 'armors', 'helmets', 'food', 'boots']

linhas = []
linhas.append('=' * 70)
linhas.append('CAMINHO D — RESUMO ASCII PARA ARQUITETO')
linhas.append('=' * 70)
linhas.append('')

for cat in CATEGORIAS:
    linhas.append('#' * 70)
    linhas.append('# %s' % cat)
    linhas.append('#' * 70)
    linhas.append('')
    
    sprites_reais = carregar_categoria(cat, max_sprites=20)
    grids_reais = [extrair_grid_papel(s)[0] for s in sprites_reais]
    
    # Clusterizar
    clusters = clusterizar_por_arquetipo(grids_reais, min_cluster_size=3)
    n_clusters = len(clusters)
    tamanhos = [len(c) for c in clusters]
    n_fora = len(grids_reais) - sum(tamanhos)
    
    linhas.append('Clusters: %d, tamanhos=%s, %d fora' % (n_clusters, tamanhos, n_fora))
    linhas.append('')
    
    # 3 reais
    linhas.append('--- 3 REAIS ---')
    for i in range(3):
        gp = grids_reais[i]
        ascii_art = sprite_para_ascii(gp)
        opacos = sum(1 for row in gp for t in row if t != 'F')
        linhas.append('REAL #%d (opacos=%d):' % (i+1, opacos))
        linhas.append(ascii_art)
        linhas.append('')
    
    # 5 gerados
    linhas.append('--- 5 GERADOS ---')
    if n_clusters == 0:
        treino = treinar_templates(grids_reais)
        linhas.append('(template unico)')
        for i in range(5):
            gp, _ = gerar_sprite(treino)
            ascii_art = sprite_para_ascii(gp)
            opacos = sum(1 for row in gp for t in row if t != 'F')
            linhas.append('GERADO #%d (opacos=%d):' % (i+1, opacos))
            linhas.append(ascii_art)
            linhas.append('')
    else:
        templates = treinar_templates_por_arquetipo(grids_reais, clusters)
        resultados = gerar_sprite_por_arquetipo(templates, clusters, total_gerados=5)
        for i, (gp, _) in enumerate(resultados):
            ascii_art = sprite_para_ascii(gp)
            opacos = sum(1 for row in gp for t in row if t != 'F')
            linhas.append('GERADO #%d (opacos=%d):' % (i+1, opacos))
            linhas.append(ascii_art)
            linhas.append('')
    
    linhas.append('')

linhas.append('=' * 70)
linhas.append('FIM DO RESUMO')
linhas.append('=' * 70)

output = '\n'.join(linhas)

# Salvar
from pathlib import Path
out_path = Path(_BASE) / 'poc_output' / 'caminho_d_resumo_ascii.txt'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(output)

print('Resumo salvo em: %s' % out_path)
print('Linhas: %d' % len(output.split('\n')))
