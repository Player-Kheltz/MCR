"""
gerar_sprite_esfera_v2.py — Gera sprites usando correlações cross-level da Esfera.

Anatomia aprendida (das correlações):
- bbox_pos='esq_mid' → regiao='r0_medio_n' → cor='medio_neut' → geom='grande_ret'
- bbox_pos='esq_sup' → regiao='r2_claro_m' → cor='claro_mage' → geom='minusculo_'
- bbox_pos='cent_mid' → regiao='r0_escuro_' → cor='escuro_neu' → geom='enorme_qua'
- bbox_pos='dir_inf' → regiao='r1_medio_n' → cor='medio_neut' → geom='grande_ret'
- bbox_pos='cent_mid' → regiao='r1_medio_v' → cor='medio_verm' → geom='minusculo_'

O sprite resultante tem 5-7 regiões cromáticas com cores sólidas,
onde cada região ocupa uma posição coerente no grid 3x3.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

from pathlib import Path
import math
from PIL import Image
import numpy as np

from mcr.regioes_anatomicas import extrair_regioes_cromaticas
from mcr.visual_coupling import VisualCoupling
from devia.kernel.MCR_legacy import MCRCoupling

# MapaLab → RGB (cores DISTINTAS para cada região)
LAB_PARA_RGB = {
    'medio_neut': (90, 70, 50),    # marrom médio (corpo)
    'claro_mage': (200, 170, 130), # bege bem claro (pele/clara)
    'escuro_neu': (30, 20, 12),    # quase preto (sombra/cabelo)
    'medio_verm': (200, 60, 30),   # vermelho vivo (detalhe)
    'muito_clar': (160, 200, 220), # azul claro (olho/magia)
    'claro_verd': (40, 180, 40),   # verde vivo (detalhe)
}


def treinar():
    """Treina a Esfera com orcs e shields."""
    orc_dir = Path(_ROOT) / 'poc_output'
    orcs = sorted(orc_dir.glob('orc_*_ref.png'))[:10]
    shields = sorted(orc_dir.glob('shield_ref_*.png'))
    
    coupling = MCRCoupling()
    vc = VisualCoupling(coupling)
    
    for c in orcs + shields:
        if not c.exists(): continue
        img = np.array(Image.open(c).convert('RGB'))
        regioes = extrair_regioes_cromaticas(img)
        vc.alimentar_sprite(regioes)
    
    coupling.recalcular()
    return coupling


def anatomia_da_esfera(coupling):
    """Usa a Esfera para montar anatomia: lista de (pos, cor, geom, escala)."""
    from collections import defaultdict
    
    # Para cada posição do grid, seguir a cadeia de correlações
    posicoes = ['esq_sup', 'cent_sup', 'dir_sup',
                'esq_mid', 'cent_mid', 'dir_mid',
                'esq_inf', 'cent_inf', 'dir_inf']
    
    anatomia = []
    usados = set()
    
    for pos in posicoes:
        # Passo 1: predizer regiao_cromatica dado bbox_pos
        regiao, _ = coupling.esfera.predizer_cross('regiao_cromatica', bbox_pos=pos)
        if not regiao or regiao in usados:
            continue
        usados.add(regiao)
        
        # Passo 2: predizer cor_media dado regiao_cromatica
        cor, _ = coupling.esfera.predizer_cross('cor_media', regiao_cromatica=regiao)
        if not cor:
            cor = 'medio_neut'
        
        # Passo 3: predizer geometria dado regiao_cromatica
        geom, _ = coupling.esfera.predizer_cross('geometria', regiao_cromatica=regiao)
        
        # Extrair escala da geometria
        tam = geom.split('_')[0] if geom else 'medio'
        escala = {
            'minusculo': 0.15, 'pequeno': 0.22, 'medio': 0.30,
            'grande': 0.40, 'enorme': 0.48
        }.get(tam, 0.30)
        
        anatomia.append({
            'pos': pos,
            'regiao': regiao,
            'cor_nome': cor,
            'geom': geom,
            'escala': escala,
        })
    
    return anatomia


def renderizar_sprite(anatomia, largura=32, altura=32, seed=0):
    """Renderiza um sprite a partir da anatomia da Esfera."""
    import random
    random.seed(seed)
    
    sprite = np.zeros((altura, largura, 3), dtype=np.uint8)
    sprite[:] = [255, 0, 255]  # fundo magenta
    
    # Mapear posições do grid → coordenadas no sprite
    # Usar grid 4x4 para mais espaço entre regiões
    for reg in anatomia:
        pos = reg['pos']
        col = ['esq', 'cent', 'dir'].index(pos.split('_')[0])
        lin = ['sup', 'mid', 'inf'].index(pos.split('_')[1])
        
        # Centro com espaçamento maior
        cx = int((col + 0.5) * largura / 3)
        cy = int((lin + 0.5) * altura / 3)
        
        # Raio menor para evitar sobreposição
        raio = int(reg['escala'] * min(largura, altura) / 2.5)
        
        rgb = LAB_PARA_RGB.get(reg['cor_nome'], (100, 60, 40))
        
        # Renderizar círculo
        for y in range(max(0, cy - raio), min(altura, cy + raio)):
            for x in range(max(0, cx - raio), min(largura, cx + raio)):
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                if dist <= raio:
                    sprite[y, x] = rgb
    
    return sprite


def main():
    print("=" * 60)
    print("GERADOR DE SPRITES VIA ESFERA POSICIONAL")
    print("=" * 60)
    
    # 1. Treinar
    print("\n[1/3] Treinando Esfera...")
    coupling = treinar()
    print(f"  {coupling.esfera.total} correlações aprendidas")
    
    # 2. Extrair anatomia
    print("\n[2/3] Extraindo anatomia da Esfera...")
    anatomia = anatomia_da_esfera(coupling)
    print(f"  {len(anatomia)} regiões:")
    for r in anatomia:
        print(f"    {r['pos']}: {r['cor_nome']} ({r['geom']}, escala={r['escala']:.2f})")
    
    # 3. Gerar 10 sprites
    print("\n[3/3] Gerando sprites...")
    out_dir = Path(_ROOT) / 'poc_output' / 'sprites_esfera_v2'
    out_dir.mkdir(exist_ok=True)
    
    for seed in range(10):
        sprite = renderizar_sprite(anatomia, seed=seed)
        caminho = out_dir / f'esfera_v2_{seed}.png'
        Image.fromarray(sprite).save(caminho)
        print(f"  {caminho.name}")
    
    print(f"\nSalvo em: {out_dir}")
    print("=" * 60)


if __name__ == '__main__':
    main()
