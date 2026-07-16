#!/usr/bin/env python3
"""
rodar_refatoracao.py — Mede pipeline refatorado com jaccard_silhueta.

Gera 20 sprites por categoria, mede:
- Coerencia estrutural (regioes vs real ±1 dp)
- Jaccard entre gerados (diversidade morfologica)
- Jaccard gerados vs reais (realismo de silhueta)
- Diversidade cromatica (variancia de fingerprints)
"""
import os, sys, json, random
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcr.sprite_corpus import (
    carregar_categoria, extrair_grid_papel, extrair_paleta_mediana,
    jaccard_silhueta, jaccard_gerados_vs_reais, POC_OUTPUT_DIR,
)
from mcr.template_regiao import treinar_templates, gerar_sprite, resumir_treino
from mcr.paths import ROOT_DIR

SEED = 42
random.seed(SEED)

CATEGORIAS = ['sword_weapons', 'shields', 'armors', 'helmets', 'food', 'boots']
N_TREINO = 20
N_GERAR = 20


def medir_categoria(cat):
    """Treina, gera e mede uma categoria."""
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
    
    # Treinar template
    treino = treinar_templates(grids_reais)
    print(f'  Treino: {resumir_treino(treino)}')
    
    # Gerar sprites
    grids_gerados = []
    for i in range(N_GERAR):
        gp, info = gerar_sprite(treino)
        grids_gerados.append(gp)
    
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
        'jaccard_reais': round(j_reais, 4),
        'jaccard_gerados': round(j_gerados, 4),
        'jaccard_vs_reais': round(j_vs_reais, 4),
        'opacos_reais_media': round(media_reais, 1),
        'opacos_reais_dp': round(dp_reais, 1),
        'opacos_gerados_media': round(media_gerados, 1),
        'opacos_gerados_dp': round(dp_gerados, 1),
        'treino': resumir_treino(treino),
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
    out_path = POC_OUTPUT_DIR / 'refatoracao_resultados.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    
    print(f'\nResultados salvos: {out_path}')
    
    # Tabela resumo
    print('\n=== TABELA RESUMO ===')
    print(f'{"Categoria":<22} | {"J Real":<8} | {"J Ger":<8} | {"J vs R":<8} | {"Opacos R (media±dp)":<20} | {"Opacos G (media±dp)":<20}')
    print('-' * 100)
    for cat, r in resultados.items():
        print(f'{cat:<22} | {r["jaccard_reais"]:<8.3f} | {r["jaccard_gerados"]:<8.3f} | {r["jaccard_vs_reais"]:<8.3f} | {r["opacos_reais_media"]:<8.0f} ± {r["opacos_reais_dp"]:<5.0f} | {r["opacos_gerados_media"]:<8.0f} ± {r["opacos_gerados_dp"]:<5.0f}')


if __name__ == '__main__':
    main()
