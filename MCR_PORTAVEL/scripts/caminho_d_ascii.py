#!/usr/bin/env python3
"""
caminho_d_ascii.py — ASCII debug para Caminho D (multi-template por arquétipo).

Gera representacao ASCII de sprites reais e gerados com arquétipos.
Usa random.seed(42) para reprodutibilidade.
"""
import os, sys, random
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcr.sprite_corpus import (
    carregar_categoria, extrair_grid_papel, sprite_para_ascii,
    POC_OUTPUT_DIR,
)
from mcr.template_regiao import (
    treinar_templates, gerar_sprite, resumir_treino,
    clusterizar_por_arquetipo, treinar_templates_por_arquetipo,
    gerar_sprite_por_arquetipo,
)
from mcr.tokenizador_hierarquico import extrair_regioes
from mcr.paths import ROOT_DIR

SEED = 42
random.seed(SEED)

CATEGORIAS = ['sword_weapons', 'shields', 'armors', 'helmets', 'food', 'boots']
N_EXEMPLOS = 10


def gerar_output_ascii():
    """Gera output ASCII completo para todas as categorias."""
    linhas = []
    linhas.append('=' * 70)
    linhas.append('CAMINHO D — ASCII DEBUG PARA ARQUITETOS')
    linhas.append('Seed: %d' % SEED)
    linhas.append('=' * 70)
    linhas.append('')
    
    for cat in CATEGORIAS:
        linhas.append('#' * 70)
        linhas.append('# CATEGORIA: %s' % cat)
        linhas.append('#' * 70)
        linhas.append('')
        
        # Carregar sprites reais
        try:
            sprites_reais = carregar_categoria(cat, max_sprites=0)
        except Exception as e:
            linhas.append('ERRO ao carregar %s: %s' % (cat, e))
            linhas.append('')
            continue
        
        # Selecionar N_EXEMPLOS aleatorios
        indices = random.sample(range(len(sprites_reais)), min(N_EXEMPLOS, len(sprites_reais)))
        
        linhas.append('--- REAIS (seed=%d, indices=%s) ---' % (SEED, indices))
        linhas.append('')
        
        for idx_i, idx in enumerate(indices):
            gp, gc = extrair_grid_papel(sprites_reais[idx])
            ascii_art = sprite_para_ascii(gp)
            opacos = sum(1 for row in gp for t in row if t != 'F')
            regioes = len(extrair_regioes(gp))
            
            linhas.append('=== %s REAL #%d (idx=%d, opacos=%d, regioes=%d) ===' % (
                cat, idx_i + 1, idx, opacos, regioes))
            linhas.append(ascii_art)
            linhas.append('')
        
        # Treinar com arquétipos
        grids_reais = []
        for s in sprites_reais[:20]:
            gp, _ = extrair_grid_papel(s)
            grids_reais.append(gp)
        
        clusters = clusterizar_por_arquetipo(grids_reais, min_cluster_size=3)
        n_clusters = len(clusters)
        tamanhos = [len(c) for c in clusters]
        
        linhas.append('--- CLUSTERIZACAO: %d clusters, tamanhos=%s ---' % (n_clusters, tamanhos))
        linhas.append('')
        
        if n_clusters == 0:
            # Fallback: template unico
            treino = treinar_templates(grids_reais)
            linhas.append('--- GERADOS (template unico, %s) ---' % resumir_treino(treino))
            linhas.append('')
            
            grids_gerados = []
            for i in range(N_EXEMPLOS):
                gp, info = gerar_sprite(treino)
                grids_gerados.append(gp)
        else:
            # Treinar por arquétipo
            templates = treinar_templates_por_arquetipo(grids_reais, clusters)
            
            linhas.append('--- GERADOS (%d arquétipos) ---' % n_clusters)
            linhas.append('')
            
            resultados = gerar_sprite_por_arquetipo(
                templates, clusters, total_gerados=N_EXEMPLOS
            )
            grids_gerados = [g for g, _ in resultados]
        
        for i, gp in enumerate(grids_gerados):
            ascii_art = sprite_para_ascii(gp)
            opacos = sum(1 for row in gp for t in row if t != 'F')
            regioes = len(extrair_regioes(gp))
            
            linhas.append('=== %s GERADO #%d (opacos=%d, regioes=%d) ===' % (
                cat, i + 1, opacos, regioes))
            linhas.append(ascii_art)
            linhas.append('')
        
        linhas.append('')
    
    linhas.append('FIM DO ASCII DEBUG')
    
    return '\n'.join(linhas)


def main():
    output = gerar_output_ascii()
    
    # Salvar arquivo
    out_path = POC_OUTPUT_DIR / 'caminho_d_ascii.txt'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print('ASCII debug salvo em: %s' % out_path)
    print('Linhas: %d' % len(output.split('\n')))


if __name__ == '__main__':
    main()
