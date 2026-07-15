"""
treinar_esfera_visual.py — Treina a Esfera Posicional com regiões cromáticas.

1. Extrai regiões CIELAB dos 4 orcs
2. Alimenta MCRCoupling via VisualCoupling
3. Usa a Esfera para predizer disposições anatômicas
4. Gera novos sprites baseados nas predições
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

from pathlib import Path
import json
import math
from collections import Counter, defaultdict

from PIL import Image
import numpy as np

from mcr.regioes_anatomicas import extrair_regioes_cromaticas
from mcr.visual_coupling import VisualCoupling, _discretizar_cor, _discretizar_geometria, _discretizar_posicao
from mcr.coupling import MCRCoupling

ORC_DIR = Path(_ROOT) / 'poc_output'
SHIELD_DIR = ORC_DIR
ORCS = [
    ORC_DIR / 'orc_hue_ref_0.png',
    ORC_DIR / 'orc_nitido_ref.png',
    ORC_DIR / 'orc_mcr_ref.png',
    ORC_DIR / 'orc_final_ref.png',
    ORC_DIR / 'orc_hue_ref_1.png',
]

def carregar_imagem(caminho):
    img = Image.open(caminho).convert('RGB')
    return np.array(img)

def extrair_todas_regioes():
    """Extrai regiões de todos os orcs e shields."""
    regioes_por_orc = {}
    
    # Orcs
    for caminho in ORCS:
        if not caminho.exists():
            print(f"  [SKIP] {caminho.name} não encontrado")
            continue
        img = carregar_imagem(caminho)
        regioes = extrair_regioes_cromaticas(img)
        regioes_por_orc[caminho.name] = regioes
        print(f"  {caminho.name}: {len(regioes)} regiões")
        for i, r in enumerate(regioes):
            L, a, b = r['cor_media_lab']
            print(f"    R{i}: area={r['area']}, "
                  f"lab=({L:.0f},{a:.0f},{b:.0f}), "
                  f"excc={r['excentricidade']:.2f}, "
                  f"centroide=({r['centroide'][0]:.0f},{r['centroide'][1]:.0f})")
    
    # Shields (para mais dados de treinamento)
    for i in range(9):
        caminho = SHIELD_DIR / f'shield_ref_{i}.png'
        if not caminho.exists():
            continue
        img = carregar_imagem(caminho)
        regioes = extrair_regioes_cromaticas(img)
        regioes_por_orc[caminho.name] = regioes
        print(f"  {caminho.name}: {len(regioes)} regiões")
    
    return regioes_por_orc

def treinar_esfera(regioes_por_orc):
    """Treina MCRCoupling + Esfera com as regiões."""
    print("\n=== Treinando Esfera Posicional ===")
    
    coupling = MCRCoupling()
    vc = VisualCoupling(coupling)
    
    # Alimentar com todas as regiões
    for nome_orc, regioes in regioes_por_orc.items():
        print(f"\nAlimentando {nome_orc} ({len(regioes)} regiões)...")
        vc.alimentar_sprite(regioes)
    
    print(f"\nTotal de co-ocorrências registradas: {coupling.total_cooc}")
    print(f"Total na Esfera: {coupling.esfera.total}")
    
    # Recalcular
    coupling.recalcular()
    print(f"Após recalcular: {coupling.total_cooc} co-ocorrências")
    
    # Mostrar correlações aprendidas
    print("\n=== Correlações Aprendidas (top 15) ===")
    top = sorted(coupling.esfera.cross.get('cor_media', {}).items(),
                 key=lambda x: sum(x[1].get(n, {}).get(v, 0)
                                   for n, vs in x[1].items()
                                   for v in vs),
                 reverse=True)[:15]
    for valor_a, niveis in top:
        total_a = coupling.esfera.freq_nivel.get('cor_media', {}).get(valor_a, 0)
        print(f"\n  cor_media='{valor_a}' (freq={total_a}):")
        for nivel_b, valores in niveis.items():
            top_vals = sorted(valores.items(), key=lambda x: -x[1])[:3]
            top_str = ", ".join(f"{v}({c})" for v, c in top_vals)
            print(f"    → {nivel_b}: {top_str}")
    
    return coupling

def predizer_nova_disposicao(coupling):
    """Usa a Esfera para predizer uma nova disposição anatômica."""
    print("\n=== Predizendo Nova Disposição Anatômica ===")
    
    # Predições cross-level
    predicoes = {}
    
    # 1. Predizer cores para regiões típicas
    print("\nCores preditas para regiões:")
    for pos in ['cent_mid', 'cent_sup', 'cent_inf']:
        try:
            resultado = coupling.esfera.predizer_cross('cor_media', bbox_pos=pos)
            predicoes[f'cor_em_{pos}'] = resultado
            print(f"  Em {pos}: {resultado}")
        except Exception as e:
            print(f"  Em {pos}: erro ({e})")
    
    # 2. Predizer geometria para cada cor
    print("\nGeometria predita para cada cor:")
    for cor in ['medio_verde', 'escuro_neutro', 'claro_amarelo', 'medio_neutro']:
        try:
            resultado = coupling.esfera.predizer_cross('geometria', cor_media=cor)
            predicoes[f'geom_{cor}'] = resultado
            print(f"  Cor {cor}: {resultado}")
        except Exception as e:
            print(f"  Cor {cor}: erro ({e})")
    
    # 3. Predizer posições para cada geometria
    print("\nPosições preditas para cada geometria:")
    for geom in ['grande_retangular_proporcional', 'pequeno_quadrado_proporcional']:
        try:
            resultado = coupling.esfera.predizer_cross('bbox_pos', geometria=geom)
            predicoes[f'pos_{geom}'] = resultado
            print(f"  Geom {geom}: {resultado}")
        except Exception as e:
            print(f"  Geom {geom}: erro ({e})")
    
    return predicoes

def gerar_sprite_novo(coupling, largura=32, altura=32):
    """Gera um sprite novo baseado nas predições da Esfera."""
    print(f"\n=== Gerando Sprite Novo ({largura}x{altura}) ===")
    
    # Consultar a Esfera para montar a anatomia
    # Para cada posição do grid 3x3, predizer cor e geometria
    grid = {}
    for lin in range(3):
        for col in range(3):
            pos = ['esq_sup', 'cent_sup', 'dir_sup',
                   'esq_mid', 'cent_mid', 'dir_mid',
                   'esq_inf', 'cent_inf', 'dir_inf'][lin * 3 + col]
            try:
                cor = coupling.esfera.predizer_cross('cor_media', bbox_pos=pos)
                if cor and 'valor' in cor:
                    grid[pos] = cor['valor']
                elif isinstance(cor, dict) and 'melhor' in cor:
                    grid[pos] = cor['melhor']
                else:
                    grid[pos] = str(cor)
            except Exception:
                grid[pos] = 'neutro'
    
    print("Grid de cores predito:")
    for lin in range(3):
        row = [grid[['esq_sup','cent_sup','dir_sup',
                      'esq_mid','cent_mid','dir_mid',
                      'esq_inf','cent_inf','dir_inf'][lin*3+c]] for c in range(3)]
        print(f"  {' | '.join(row)}")
    
    return grid

def main():
    print("=" * 60)
    print("TREINAMENTO DA ESFERA POSICIONAL COM REGIÕES CROMÁTICAS")
    print("=" * 60)
    
    # 1. Extrair regiões
    print("\n[1/5] Extraindo regiões dos 4 orcs...")
    regioes_por_orc = extrair_todas_regioes()
    
    if not regioes_por_orc:
        print("ERRO: Nenhum orc encontrado")
        return
    
    # 2. Treinar Esfera
    print("\n[2/5] Treinando Esfera...")
    coupling = treinar_esfera(regioes_por_orc)
    
    # 3. Predizer nova disposição
    print("\n[3/5] Predizendo nova disposição...")
    predicoes = predizer_nova_disposicao(coupling)
    
    # 4. Gerar sprite novo
    print("\n[4/5] Gerando sprite novo...")
    grid = gerar_sprite_novo(coupling)
    
    # 5. Salvar resultados
    print("\n[5/5] Salvando resultados...")
    resultado = {
        'n_orcs': len(regioes_por_orc),
        'total_regioes': sum(len(r) for r in regioes_por_orc.values()),
        'total_cooc': coupling.total_cooc,
        'total_esfera': coupling.esfera.total,
        'predicoes': {k: str(v) for k, v in predicoes.items()},
        'grid': grid,
    }
    
    out = Path(_ROOT) / 'poc_output' / 'esfera_visual_treinada.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"Salvo em: {out}")
    
    print("\n" + "=" * 60)
    print("TREINAMENTO CONCLUÍDO")
    print("=" * 60)

if __name__ == '__main__':
    main()
