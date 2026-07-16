#!/usr/bin/env python3
"""
rodar_sprint1.py — Executa pipeline_mcr_sprite nas 5 categorias de teste.
Mede metricas A/B vs baseline.
Salva sprint1_resultados.json.
"""
import os, sys, json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcr.pipeline_mcr_sprite import rodar_categoria, medir_coerencia_estrutural, medir_diversidade
from mcr.sprite_corpus import carregar_categoria, extrair_grid_papel
from mcr.tokenizador_hierarquico import extrair_regioes
from mcr.paths import POC_OUTPUT_DIR

TEST_CATEGORIES = ['sword_weapons', 'shields', 'armors', 'creature_products', 'helmets']
N_GERADOS = 20


def main():
    print('=' * 60)
    print('SPRITE1 COMPLETO — 5 Categorias de Teste')
    print('=' * 60)
    
    todos_resultados = {}
    
    for cat in TEST_CATEGORIES:
        try:
            resultado = rodar_categoria(cat, n_gerados=N_GERADOS)
            todos_resultados[cat] = resultado
        except Exception as e:
            print(f'ERRO em {cat}: {e}')
            import traceback; traceback.print_exc()
    
    # Salvar todos os resultados
    out_path = str(POC_OUTPUT_DIR / 'sprint1_resultados.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(todos_resultados, f, indent=2, ensure_ascii=False, default=str)
    
    print(f'\n{"=" * 60}')
    print('RESUMO COMPARATIVO')
    print(f'{"=" * 60}')
    
    print(f'\n{"Categoria":<20} {"Coerencia":>10} {"Diversidade":>12} {"Disc":>8} {"RegGer":>8} {"RegReal":>8}')
    print('-' * 78)
    
    for cat, r in todos_resultados.items():
        m = r.get('metricas', {})
        c = m.get('coerencia', {})
        d = m.get('diversidade', {})
        print(f'{cat:<20} '
              f'{c.get("dentro_dp", 0):>10.3f} '
              f'{d.get("ratio_diversidade", 0):>12.3f} '
              f'{m.get("disc_score_medio", 0):>8.4f} '
              f'{c.get("media_regioes_geradas", 0):>8.1f} '
              f'{c.get("media_regioes_real", 0):>8.1f}')
    
    # Carregar baseline para comparacao
    baseline_path = str(POC_OUTPUT_DIR / 'baseline_nitido' / 'baseline_pipeline_nitido.json')
    if os.path.exists(baseline_path):
        with open(baseline_path) as f:
            baseline = json.load(f)
        
        print(f'\n{"Baseline (pipeline_nitido):":<30}')
        print(f'{"Categoria":<20} {"Disc":>8} {"Opacos":>8}')
        print('-' * 40)
        for cat, b in baseline.items():
            print(f'{cat:<20} {b.get("disc_score_medio", 0):>8.4f} {b.get("media_opacos_gerados", 0):>8.1f}')
    
    print(f'\nResultados salvos em: {out_path}')


if __name__ == '__main__':
    main()
