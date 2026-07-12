"""
mcr.pipeline_mcr_sprite — Pipeline MCR Universal para geração de sprites.

Decisao de Design #5: N1+N2 criativo, N0 só renderiza.

Fluxo:
  1. Carregar sprites reais da categoria (sprite_corpus)
  2. Tokenizar cada em grid_papel B/L/F + grid_cor RGB
  3. Treinar template N1+N2 (template_regiao)
  4. Gerar novos sprites via template (fixed + gap)
  5. Colorir via CIELAB rotation (paleta mediana)
  6. Medir metricas A/B vs baseline

Uso:
    python -m mcr.pipeline_mcr_sprite --categoria sword_weapons --n 20
"""
import os, sys, math, random, json
from collections import Counter, defaultdict
from pathlib import Path
from typing import List, Dict, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcr.sprite_corpus import (
    carregar_categoria, extrair_grid_papel, extrair_paleta_mediana,
    salvar_grid_como_png, POC_OUTPUT_DIR,
)
from mcr.template_regiao import treinar_templates, gerar_sprite, resumir_treino
from mcr.cielab import rgb_para_lab, lab_para_rgb
from mcr.tokenizador_hierarquico import (
    extrair_regioes, extrair_relacoes, ordenar_regioes, resumir_hierarquico,
)
from mcr.regioes_anatomicas import (
    extrair_regioes_cromaticas, fingerprint_cromatico, resumir_regioes,
)
from mcr.meus_olhos import MCRDiscriminador


# ─── Medidas de qualidade ──────────────────────────────────────


def medir_coerencia_estrutural(
    grids_gerados: List[List[List[str]]],
    n_regioes_real_media: float,
    n_regioes_real_dp: float,
) -> Dict:
    """Metrica 1: numero de regioes geradas vs real.
    
    Returns:
        dict com media, dp, dentro_dp (fração dentro de ±1dp)
    """
    contagens = []
    for grid in grids_gerados:
        regioes = extrair_regioes(grid)
        contagens.append(len(regioes))
    
    media = sum(contagens) / len(contagens) if contagens else 0
    dp = (sum((x - media)**2 for x in contagens) / max(len(contagens), 1)) ** 0.5
    
    dentro_dp = sum(
        1 for c in contagens 
        if abs(c - n_regioes_real_media) <= n_regioes_real_dp
    ) / max(len(contagens), 1)
    
    return {
        'media_regioes_geradas': round(media, 2),
        'dp_regioes_geradas': round(dp, 2),
        'media_regioes_real': round(n_regioes_real_media, 2),
        'dp_regioes_real': round(n_regioes_real_dp, 2),
        'dentro_dp': round(dentro_dp, 3),
        'n_gerados': len(contagens),
    }


def medir_diversidade(
    grids_gerados: List[List[List[str]]],
) -> Dict:
    """Metrica 2: variância de fingerprints cromáticos entre gerados.
    
    Returns:
        dict com n_fingerprints_unicos, ratio_diversidade
    """
    fingerprints = []
    for grid in grids_gerados:
        # Converter grid B/L/F para grid_cor fictício para fingerprint
        grid_cor = [[(0, 0, 0)] * 32 for _ in range(32)]
        for y in range(32):
            for x in range(32):
                t = grid[y][x]
                if t == 'B':
                    grid_cor[y][x] = (50, 30, 20)
                elif t == 'L':
                    grid_cor[y][x] = (150, 120, 100)
                elif t == 'D':
                    grid_cor[y][x] = (100, 80, 60)
        
        regioes = extrair_regioes_cromaticas(grid_cor, grid)
        if regioes:
            fp = fingerprint_cromatico(regioes[0])
            fingerprints.append(fp)
        else:
            fingerprints.append('empty')
    
    unicos = len(set(fingerprints))
    total = len(fingerprints)
    ratio = unicos / max(total, 1)
    
    return {
        'n_fingerprints_unicos': unicos,
        'n_total': total,
        'ratio_diversidade': round(ratio, 3),
    }


def medir_paleta(
    grid_cor_real: List[List[tuple]],
    grid_papel_real: List[List[str]],
    paleta_gerada: Dict[str, Tuple[int, int, int]],
) -> Dict:
    """Mede quão bem a paleta gerada aproxima a real."""
    paleta_real = extrair_paleta_mediana(grid_cor_real, grid_papel_real)
    
    distancias = {}
    for papel in set(list(paleta_real.keys()) + list(paleta_gerada.keys())):
        if papel in paleta_real and papel in paleta_gerada:
            r1, g1, b1 = paleta_real[papel]
            r2, g2, b2 = paleta_gerada[papel]
            dist = ((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2) ** 0.5
            distancias[papel] = round(dist, 2)
        else:
            distancias[papel] = 999
    
    media_dist = sum(distancias.values()) / max(len(distancias), 1)
    
    return {
        'paleta_real': {k: list(v) for k, v in paleta_real.items()},
        'paleta_gerada': {k: list(v) for k, v in paleta_gerada.items()},
        'distancias_por_papel': distancias,
        'distancia_media': round(media_dist, 2),
    }


# ─── Pipeline principal ────────────────────────────────────────


def rodar_categoria(
    nome_categoria: str,
    n_gerados: int = 20,
    out_dir: str = None,
    max_sprites_treino: int = 0,
) -> Dict:
    """Roda pipeline completo em uma categoria.
    
    Args:
        nome_categoria: nome do diretorio da categoria
        n_gerados: numero de sprites a gerar
        out_dir: diretorio de saida (None = auto)
        max_sprites_treino: limite de sprites para treino (0 = todos)
    
    Returns:
        dict com resultados completos
    """
    if out_dir is None:
        out_dir = str(POC_OUTPUT_DIR / 'pipeline_mcr' / nome_categoria)
    os.makedirs(out_dir, exist_ok=True)
    
    print(f'\n{"=" * 50}')
    print(f'PIPELINE MCR SPRITE — {nome_categoria}')
    print(f'{"=" * 50}')
    
    # 1. Carregar sprites
    print('\n[1] Carregando sprites...')
    sprites_rgba = carregar_categoria(nome_categoria, max_sprites=max_sprites_treino)
    n_sprites = len(sprites_rgba)
    print(f'  Carregados: {n_sprites}')
    
    # 2. Tokenizar todos
    print('\n[2] Tokenizando...')
    grids_papel = []
    grids_cor = []
    for arr in sprites_rgba:
        gp, gc = extrair_grid_papel(arr)
        grids_papel.append(gp)
        grids_cor.append(gc)
    
    # Metricas reais
    opacos_reais = [sum(1 for row in gp for t in row if t != 'F') for gp in grids_papel]
    media_opacos_real = sum(opacos_reais) / len(opacos_reais)
    dp_opacos_real = (sum((x - media_opacos_real)**2 for x in opacos_reais) / len(opacos_reais)) ** 0.5
    
    regioes_reais = [len(extrair_regioes(gp)) for gp in grids_papel]
    media_regioes_real = sum(regioes_reais) / len(regioes_reais)
    dp_regioes_real = (sum((x - media_regioes_real)**2 for x in regioes_reais) / len(regioes_reais)) ** 0.5
    
    print(f'  Opacos real: {media_opacos_real:.1f} ± {dp_opacos_real:.1f}')
    print(f'  Regioes real: {media_regioes_real:.1f} ± {dp_regioes_real:.1f}')
    
    # 3. Treinar template
    print('\n[3] Treinando template N1+N2...')
    treino = treinar_templates(grids_papel)
    print(f'  {resumir_treino(treino)}')
    
    # 4. Paleta mediana
    print('\n[4] Extraindo paleta mediana...')
    paleta_mediana = extrair_paleta_mediana(grids_cor[0], grids_papel[0])
    
    # Calcular paleta mediana de TODOS os sprites (mais robusto)
    todas_cor = []
    todas_papel = []
    for i in range(n_sprites):
        for y in range(32):
            for x in range(32):
                if grids_papel[i][y][x] != 'F':
                    todas_cor.append(grids_cor[i][y][x])
                    todas_papel.append(grids_papel[i][y][x])
    
    por_papel = defaultdict(list)
    for i in range(len(todas_cor)):
        por_papel[todas_papel[i]].append(todas_cor[i])
    
    paleta_mediana = {}
    for papel, cores in por_papel.items():
        rs = sorted(c[0] for c in cores)
        gs = sorted(c[1] for c in cores)
        bs = sorted(c[2] for c in cores)
        n = len(rs)
        paleta_mediana[papel] = (rs[n//2], gs[n//2], bs[n//2])
    
    for papel, cor in sorted(paleta_mediana.items()):
        print(f'  {papel}: RGB({cor[0]}, {cor[1]}, {cor[2]})')
    
    # 5. Gerar sprites
    print(f'\n[5] Gerando {n_gerados} sprites...')
    random.seed(42)
    grids_gerados = []
    infos_geracao = []
    
    for g in range(n_gerados):
        grid_gerado, info = gerar_sprite(treino)
        grids_gerados.append(grid_gerado)
        infos_geracao.append(info)
        
        if g < 5 or g % 10 == 0:
            opacos = sum(1 for row in grid_gerado for t in row if t != 'F')
            print(f'  [{g}] opacos={opacos}, temp_n1={info["temperatura_n1"]}, temp_n2={info["temperatura_n2"]}')
    
    # 6. Colorir e salvar
    print('\n[6] Colorindo e salvando...')
    for g_idx, grid_gerado in enumerate(grids_gerados):
        angulo = random.random() * 2 * math.pi
        caminho = os.path.join(out_dir, f'sprite_{g_idx:03d}.png')
        salvar_grid_como_png(grid_gerado, paleta_mediana, caminho, angulo_hue=angulo, variacao=5)
    
    # Salvar referencia (primeiro sprite real)
    caminho_ref = os.path.join(out_dir, 'ref_real_000.png')
    salvar_grid_como_png(grids_papel[0], paleta_mediana, caminho_ref)
    
    # 7. Medir metricas
    print('\n[7] Medindo metricas A/B...')
    
    # Metrica 1: Coerencia estrutural
    m_coerencia = medir_coerencia_estrutural(
        grids_gerados, media_regioes_real, dp_regioes_real
    )
    print(f'  Coerencia: dentro_dp={m_coerencia["dentro_dp"]:.3f} '
          f'(geradas={m_coerencia["media_regioes_geradas"]:.1f}, real={m_coerencia["media_regioes_real"]:.1f})')
    
    # Metrica 2: Diversidade
    m_diversidade = medir_diversidade(grids_gerados)
    print(f'  Diversidade: {m_diversidade["n_fingerprints_unicos"]}/{m_diversidade["n_total"]} '
          f'({m_diversidade["ratio_diversidade"]:.3f})')
    
    # Discriminador
    disc = MCRDiscriminador()
    disc.treinar(grids_papel)
    scores_disc = []
    for grid in grids_gerados:
        resultado = disc.avaliar(grid)
        scores_disc.append(resultado['score'])
    media_disc = sum(scores_disc) / len(scores_disc) if scores_disc else 0
    print(f'  Disc score: {media_disc:.4f}')
    
    # 8. Salvar resultados
    resultados = {
        'categoria': nome_categoria,
        'n_sprites_treino': n_sprites,
        'n_gerados': n_gerados,
        'limiar_entropia': treino.get('limiar', 0),
        'n_regioes_alvo': treino.get('n_regioes_alvo', 0),
        'n1_fixed': treino.get('n1_fixed', 0),
        'n1_gap': treino.get('n1_gap', 0),
        'n2_fixed': treino.get('n2_fixed', 0),
        'n2_gap': treino.get('n2_gap', 0),
        'paleta_mediana': {k: list(v) for k, v in paleta_mediana.items()},
        'metricas': {
            'coerencia': m_coerencia,
            'diversidade': m_diversidade,
            'disc_score_medio': round(media_disc, 4),
        },
        'baseline': {
            'media_opacos_real': round(media_opacos_real, 1),
            'dp_opacos_real': round(dp_opacos_real, 1),
            'media_regioes_real': round(media_regioes_real, 1),
            'dp_regioes_real': round(dp_regioes_real, 1),
        },
    }
    
    json_path = os.path.join(out_dir, 'resultados.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False, default=str)
    
    print(f'\nResultados salvos em: {out_dir}')
    return resultados


# ─── Main ──────────────────────────────────────────────────────

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Pipeline MCR Universal para Sprites')
    parser.add_argument('--categoria', type=str, default='shields',
                       help='Nome da categoria (ex: sword_weapons, shields)')
    parser.add_argument('--n', type=int, default=20,
                       help='Numero de sprites a gerar')
    parser.add_argument('--max-treino', type=int, default=0,
                       help='Limite de sprites para treino (0 = todos)')
    
    args = parser.parse_args()
    
    resultados = rodar_categoria(
        args.categoria,
        n_gerados=args.n,
        max_sprites_treino=args.max_treino,
    )
    
    print('\n=== RESUMO FINAL ===')
    m = resultados['metricas']
    print(f'  Coerencia (dentro_dp): {m["coerencia"]["dentro_dp"]:.3f}')
    print(f'  Diversidade: {m["diversidade"]["ratio_diversidade"]:.3f}')
    print(f'  Disc score: {m["disc_score_medio"]:.4f}')
