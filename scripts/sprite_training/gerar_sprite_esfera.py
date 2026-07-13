"""
gerar_sprite_esfera.py — Gera sprites usando a Esfera Posicional treinada.

A Esfera prediz:
1. Quais cores aparecem em cada posição do grid 3x3
2. Qual geometria (tamanho + forma) cada cor assume
3. O MCR renderiza cada região como bloco de cor sólida

O resultado é um sprite 32x32 onde cada região é uma cor sólida,
com a anatomia determinada pelas correlações aprendidas.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

from pathlib import Path
import json
import math
from collections import Counter
from PIL import Image
import numpy as np

from mcr.regioes_anatomicas import extrair_regioes_cromaticas
from mcr.visual_coupling import VisualCoupling, _discretizar_cor, _discretizar_geometria, _discretizar_posicao
from devia.kernel.MCR_legacy import MCRCoupling

# Cores Lab* → RGB aproximadas (dos dados dos orcs)
CORES_LAB = {
    'medio_neut': (42, 4, 3),      # marrom escuro (corpo orc)
    'claro_mage': (78, 12, 5),     # marrom claro (pele/clara)
    'muito_clar': (87, -104, 106), # ciano claro (olhos)
    'escuro_neu': (30, 2, 1),      # marrom muito escuro
    'claro_verd': (73, -192, 80),  # verde (detalhes)
}

def lab_para_rgb_aprox(L, a, b):
    """Conversão simplificada Lab* → RGB para geração."""
    # L 0-100, a -128..128, b -128..128
    y = (L + 16) / 116
    x = a / 500 + y
    z = y - b / 200
    
    def f(t):
        if t > 6/29:
            return t ** 3
        return 3 * (6/29)**2 * (t - 4/29)
    
    r = 3.2406 * f(x) - 1.5372 * f(y) - 0.4986 * f(z)
    g = -0.9689 * f(x) + 1.8758 * f(y) + 0.0415 * f(z)
    b_ = 0.0557 * f(x) - 0.2040 * f(y) + 1.0570 * f(z)
    
    r = int(max(0, min(255, r * 255)))
    g = int(max(0, min(255, g * 255)))
    b_ = int(max(0, min(255, b_ * 255)))
    return (r, g, b_)


def treinar_e_gerar():
    """Treina a Esfera e gera sprites novos."""
    orc_dir = Path(_ROOT) / 'poc_output'
    
    # Todos os orcs disponíveis
    orcs = sorted(orc_dir.glob('orc_*_ref.png'))[:10]
    shields = sorted(orc_dir.glob('shield_ref_*.png'))
    
    print(f"=== Treinando com {len(orcs)} orcs + {len(shields)} shields ===\n")
    
    coupling = MCRCoupling()
    vc = VisualCoupling(coupling)
    
    # Treinar com orcs
    for caminho in orcs:
        img = np.array(Image.open(caminho).convert('RGB'))
        regioes = extrair_regioes_cromaticas(img)
        vc.alimentar_sprite(regioes)
        print(f"  {caminho.name}: {len(regioes)} regiões")
    
    # Treinar com shields
    for caminho in shields:
        img = np.array(Image.open(caminho).convert('RGB'))
        regioes = extrair_regioes_cromaticas(img)
        vc.alimentar_sprite(regioes)
        print(f"  {caminho.name}: {len(regioes)} regiões")
    
    coupling.recalcular()
    
    print(f"\nEsfera treinada: {coupling.esfera.total} correlações")
    
    # Listar valores sobreviventes
    print("\n=== Valores aprendidos ===")
    for nivel in ['cor_media', 'geometria', 'bbox_pos']:
        vals = list(coupling.esfera.cross.get(nivel, {}).keys())
        print(f"  {nivel}: {vals}")
    
    # Gerar 5 sprites novos
    print("\n=== Gerando sprites ===")
    out_dir = Path(_ROOT) / 'poc_output' / 'sprites_esfera'
    out_dir.mkdir(exist_ok=True)
    
    for idx in range(5):
        sprite = gerar_sprite(coupling, idx)
        caminho = out_dir / f'esfera_{idx}.png'
        Image.fromarray(sprite).save(caminho)
        print(f"  Salvo: {caminho.name}")
    
    return coupling

def gerar_sprite(coupling, seed=0):
    """Gera um sprite 32x32 usando a Esfera treinada."""
    import random
    random.seed(seed)
    
    largura, altura = 32, 32
    sprite = np.zeros((altura, largura, 3), dtype=np.uint8)
    
    # Fundo magenta
    sprite[:] = [255, 0, 255]
    
    # 1. Consultar a Esfera: para cada posição, predizer a cor
    grid = {}
    for lin in range(3):
        for col in range(3):
            pos = ['esq_sup', 'cent_sup', 'dir_sup',
                   'esq_mid', 'cent_mid', 'dir_mid',
                   'esq_inf', 'cent_inf', 'dir_inf'][lin * 3 + col]
            
            # Tentar predizer cor para esta posição
            try:
                melhor, conf = coupling.esfera.predizer_cross('cor_media', bbox_pos=pos)
                if melhor:
                    grid[pos] = melhor
                else:
                    grid[pos] = 'medio_neut'
            except Exception:
                grid[pos] = 'medio_neut'
    
    print(f"\n  Grid seed={seed}:")
    for lin in range(3):
        row = [grid[['esq_sup','cent_sup','dir_sup',
                      'esq_mid','cent_mid','dir_mid',
                      'esq_inf','cent_inf','dir_inf'][lin*3+c]] for c in range(3)]
        print(f"    {' | '.join(row)}")
    
    # 2. Converter cores Lab* → RGB
    regioes = []
    for pos, cor_nome in grid.items():
        lab = CORES_LAB.get(cor_nome, (42, 4, 3))
        rgb = lab_para_rgb_aprox(*lab)
        
        # Predizer geometria para esta cor
        try:
            geom, _ = coupling.esfera.predizer_cross('geometria', cor_media=cor_nome)
        except Exception:
            geom = 'medio_quad'
        
        # Extrair tamanho da geometria
        tam = geom.split('_')[0] if geom else 'medio'
        escala = {'minusculo': 0.15, 'pequeno': 0.25, 'medio': 0.35, 'grande': 0.45, 'enorme': 0.55}.get(tam, 0.35)
        
        regioes.append({
            'pos': pos,
            'cor_nome': cor_nome,
            'rgb': rgb,
            'escala': escala,
        })
    
    # 3. Renderizar regiões no sprite
    # Mapear cada posição do grid para uma área no sprite 32x32
    for reg in regioes:
        pos = reg['pos']
        col = ['esq', 'cent', 'dir'].index(pos.split('_')[0])
        lin = ['sup', 'mid', 'inf'].index(pos.split('_')[1])
        
        # Centro da região
        cx = int((col + 0.5) * largura / 3)
        cy = int((lin + 0.5) * altura / 3)
        
        # Tamanho da região
        raio = int(reg['escala'] * min(largura, altura) / 2)
        
        # Preencher círculo/retângulo
        for y in range(max(0, cy - raio), min(altura, cy + raio)):
            for x in range(max(0, cx - raio), min(largura, cx + raio)):
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                if dist <= raio:
                    sprite[y, x] = reg['rgb']
    
    return sprite


if __name__ == '__main__':
    treinar_e_gerar()
