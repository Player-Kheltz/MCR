#!/usr/bin/env python3
"""
rodar_caminho_d.py — Mede pipeline com multi-template por arquétipo (Caminho D).

Gera 20 sprites por categoria com arquétipos:
- Clusteriza sprites reais por Jaccard de silhueta
- Treina um template por cluster (arquétipo)
- Gera sprites proporcionalmente ao tamanho do cluster
"""
import os, sys, json, random
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcr.sprite_corpus import (
    carregar_categoria, extrair_grid_papel, extrair_paleta_mediana,
    jaccard_silhueta, jaccard_gerados_vs_reais, POC_OUTPUT_DIR,
)
from mcr.template_regiao import (
    treinar_templates, gerar_sprite, resumir_treino,
    clusterizar_por_arquetipo, treinar_templates_por_arquetipo,
    gerar_sprite_por_arquetipo,
)
from mcr.paths import ROOT_DIR

SEED = 42
random.seed(SEED)

CATEGORIAS = ['sword_weapons', 'shields', 'armors', 'helmets', 'food', 'boots']
N_TREINO = 20
N_GERAR = 20


def medir_categoria(cat):
    """Treina, gera e mede uma categoria com arquétipos."""
    print(f'\n--- {cat} ---')
    
    # Carregar sprites reais
    try:
        sprites_reais = carregar_categoria(cat, max_sprites=0)
    except Exception as e:
        print(f'  ERRO ao carregar: {e}')
        return None
    
    if len(sprites_reais) < N_TREINO:
        print(f'  Poucos sprites ({len(sprites_reais)}), usando todos')
        N = len(sprites_reais)
    else:
        N = N_TREINO
    
    # Extrair grids
    grids_reais = []
    for s in sprites_reais[:N]:
        gp, _ = extrair_grid_papel(s)
        grids_reais.append(gp)
    
    # Clusterizar por arquétipo
    clusters = clusterizar_por_arquetipo(grids_reais, min_cluster_size=3)
    n_clusters = len(clusters)
    tamanhos = [len(c) for c in clusters]
    n_fora = len(grids_reais) - sum(tamanhos)
    
    print(f'  Clusters: {n_clusters}, tamanhos={tamanhos}, {n_fora} fora')
    
    if n_clusters == 0:
        # Sem clusters: treinar template unico
        print(f'  Fallback: template unico')
        treino = treinar_templates(grids_reais)
        print(f'  Treino: {resumir_treino(treino)}')
        
        grids_gerados = []
        for i in range(N_GERAR):
            gp, info = gerar_sprite(treino)
            grids_gerados.append(gp)
    else:
        # Treinar template por arquétipo
        templates = treinar_templates_por_arquetipo(grids_reais, clusters)
        for i, (t, c) in enumerate(zip(templates, clusters)):
            print(f'  Arquétipo {i}: {len(c)} sprites, {resumir_treino(t)}')
        
        # Gerar sprites distribuidos entre arquétipos
        resultados_gerados = gerar_sprite_por_arquetipo(
            templates, clusters, total_gerados=N_GERAR
        )
        grids_gerados = [g for g, _ in resultados_gerados]
    
    # Medir
    j_reais = jaccard_silhueta(grids_reais)
    j_gerados = jaccard_silhueta(grids_gerados)
    j_vs_reais = jaccard_gerados_vs_reais(grids_gerados, grids_reais)
    
    # Coerencia: opacos media e dp
    opacos_reais = [sum(1 for row in g for t in row if t != 'F') for g in grids_reais]
    opacos_gerados = [sum(1 for row in g for t in row if t != 'F') for g in grids_gerados]
    media_reais = sum(opacos_reais) / len(opacos_reais) if opacos_reais else 0
    media_gerados = sum(opacos_gerados) / len(opacos_gerados) if opacos_gerados else 0
    dp_reais = (sum((x - media_reais)**2 for x in opacos_reais) / max(len(opacos_reais), 1)) ** 0.5
    dp_gerados = (sum((x - media_gerados)**2 for x in opacos_gerados) / max(len(opacos_gerados), 1)) ** 0.5
    
    resultado = {
        'categoria': cat,
        'n_reais': N,
        'n_clusters': n_clusters,
        'clusters_tamanhos': tamanhos,
        'n_fora': n_fora,
        'jaccard_reais': round(j_reais, 4),
        'jaccard_gerados': round(j_gerados, 4),
        'jaccard_vs_reais': round(j_vs_reais, 4),
        'opacos_reais_media': round(media_reais, 1),
        'opacos_reais_dp': round(dp_reais, 1),
        'opacos_gerados_media': round(media_gerados, 1),
        'opacos_gerados_dp': round(dp_gerados, 1),
    }
    
    print(f'  Jaccard reais: {j_reais:.3f}')
    print(f'  Jaccard gerados: {j_gerados:.3f}')
    print(f'  Jaccard vs reais: {j_vs_reais:.3f}')
    print(f'  Opacos: reais={media_reais:.0f}±{dp_reais:.0f}, gerados={media_gerados:.0f}±{dp_gerados:.0f}')
    
    return resultado


def main():
    resultados = {}
    for cat in CATEGORIAS:
        r = medir_categoria(cat)
        if r:
            resultados[cat] = r
    
    # Salvar resultados
    out_path = POC_OUTPUT_DIR / 'caminho_d_resultados.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    
    print(f'\nResultados salvos: {out_path}')
    
    # Tabela resumo
    print('\n=== TABELA RESUMO (Caminho D) ===')
    print(f'{"Categoria":<22} | {"Clusters":<8} | {"J Real":<8} | {"J Ger":<8} | {"J vs R":<8} | {"Opacos R (media±dp)":<20} | {"Opacos G (media±dp)":<20}')
    print('-' * 110)
    for cat, r in resultados.items():
        print(f'{cat:<22} | {r["n_clusters"]:<8} | {r["jaccard_reais"]:<8.3f} | {r["jaccard_gerados"]:<8.3f} | {r["jaccard_vs_reais"]:<8.3f} | {r["opacos_reais_media"]:<8.0f} ± {r["opacos_reais_dp"]:<5.0f} | {r["opacos_gerados_media"]:<8.0f} ± {r["opacos_gerados_dp"]:<5.0f}')


if __name__ == '__main__':
    main()
