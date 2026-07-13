"""
mcr.visual_coupling — Ponte entre regiões cromáticas e a Esfera Posicional.

Registra níveis visuais (regiao_cromatica, cor_media, geometria, bbox_pos)
na matriz de acoplamento MCRCoupling, permitindo que a Esfera prediga
relações espaciais entre regiões de sprites.

Uso:
    vc = VisualCoupling(coupling)
    vc.alimentar_sprite(regioes)
    # Agora a Esfera pode predizer:
    #   esfera.predizer_cross('cor_media', regiao_cromatica='verde_pele')
    #   → qual cor provável dado que a região é pele?
"""
from typing import List, Dict


def _discretizar_cor(lab):
    """Discretiza cor Lab* em bucket textual para uso como valor na Esfera."""
    L, a, b = lab
    # Luminância
    if L < 30: lum = 'escuro'
    elif L < 60: lum = 'medio'
    elif L < 80: lum = 'claro'
    else: lum = 'muito_claro'
    # Matiz dominante
    if abs(a) < 10 and abs(b) < 10: matiz = 'neutro'
    elif a > 20 and b > 20: matiz = 'amarelo'
    elif a > 20 and b < -20: matiz = 'vermelho'
    elif a < -20 and b > 20: matiz = 'verde'
    elif a < -20 and b < -20: matiz = 'azul'
    elif a > 10: matiz = 'magenta'
    elif b > 10: matiz = 'ciano'
    else: matiz = 'outro'
    return f"{lum}_{matiz}"


def _discretizar_geometria(reg):
    """Discretiza propriedades geométricas em bucket textual."""
    area = reg['area']
    excc = reg['excentricidade']
    w = reg.get('largura', 1)
    h = reg.get('altura', 1)
    
    # Tamanho
    if area < 20: tam = 'minusculo'
    elif area < 50: tam = 'pequeno'
    elif area < 150: tam = 'medio'
    elif area < 400: tam = 'grande'
    else: tam = 'enorme'
    
    # Forma
    if excc < 1.2: forma = 'quadrado'
    elif excc < 2.0: forma = 'retangular'
    elif excc < 3.0: forma = 'alongado'
    else: forma = 'muito_alongado'
    
    # Proporção
    if w > h * 1.5: prop = 'horizontal'
    elif h > w * 1.5: prop = 'vertical'
    else: prop = 'proporcional'
    
    return f"{tam}_{forma}_{prop}"


def _discretizar_posicao(reg, largura_grid=32, altura_grid=32):
    """Discretiza posição da região em grid 3x3."""
    cx, cy = reg['centroide']
    col = min(int(cx / largura_grid * 3), 2)
    lin = min(int(cy / altura_grid * 3), 2)
    posicoes = ['esq_sup', 'cent_sup', 'dir_sup',
                'esq_mid', 'cent_mid', 'dir_mid',
                'esq_inf', 'cent_inf', 'dir_inf']
    return posicoes[lin * 3 + col]


class VisualCoupling:
    """Ponte entre regiões cromáticas e MCRCoupling/MCREsfera.
    
    Registra 4 níveis visuais:
      - regiao_cromatica: identidade da região (ex: 'grande_verde_pele')
      - cor_media: cor discretizada (ex: 'medio_verde')
      - geometria: forma e tamanho (ex: 'grande_retangular_proporcional')
      - bbox_pos: posição no grid 3x3 (ex: 'cent_mid')
    
    Alimenta o coupling com co-ocorrências entre regiões do mesmo sprite.
    """
    
    NIVEIS_VISUAIS = ['regiao_cromatica', 'cor_media', 'geometria', 'bbox_pos']
    
    def __init__(self, coupling=None):
        """
        Args:
            coupling: instância de MCRCoupling (de devia.kernel.MCR_legacy)
        """
        self.coupling = coupling
        if coupling is not None:
            for nivel in self.NIVEIS_VISUAIS:
                coupling.registrar_nivel(nivel)
    
    def alimentar_sprite(self, regioes: List[Dict]):
        """Alimenta o coupling com todas as regiões de um sprite.
        
        Para cada par de regiões (i, j) no sprite:
        - Registra co-ocorrência entre as propriedades visuais
        - Alimenta a Esfera com pares (nivel_visual, valor)
        """
        if len(regioes) < 2:
            return
        
        # Alimentar pares de regiões (acoplamento espacial)
        for i in range(len(regioes)):
            ri = regioes[i]
            val_cor_i = _discretizar_cor(ri['cor_media_lab'])
            val_geom_i = _discretizar_geometria(ri)
            val_pos_i = _discretizar_posicao(ri)
            
            # Alimentar intra-região (todas as propriedades juntas)
            self.coupling.alimentar(
                'regiao_cromatica', 'cor_media',
                f"r{i}_{val_cor_i}", val_cor_i
            )
            self.coupling.alimentar(
                'regiao_cromatica', 'geometria',
                f"r{i}_{val_cor_i}", val_geom_i
            )
            self.coupling.alimentar(
                'regiao_cromatica', 'bbox_pos',
                f"r{i}_{val_cor_i}", val_pos_i
            )
            
            # Alimentar pares de regiões (acoplamento inter-região)
            for j in range(i + 1, len(regioes)):
                rj = regioes[j]
                val_cor_j = _discretizar_cor(rj['cor_media_lab'])
                val_geom_j = _discretizar_geometria(rj)
                val_pos_j = _discretizar_posicao(rj)
                
                # Co-ocorrência de cores
                self.coupling.alimentar(
                    'cor_media', 'cor_media',
                    val_cor_i, val_cor_j
                )
                # Co-ocorrência de geometria
                self.coupling.alimentar(
                    'geometria', 'geometria',
                    val_geom_i, val_geom_j
                )
                # Co-ocorrência de posições
                self.coupling.alimentar(
                    'bbox_pos', 'bbox_pos',
                    val_pos_i, val_pos_j
                )
                # Co-ocorrência cruzada (cor ↔ geometria)
                self.coupling.alimentar(
                    'cor_media', 'geometria',
                    val_cor_i, val_geom_j
                )
    
    def alimentar_sprites(self, lista_regioes: List[List[Dict]]):
        """Alimenta com múltiplos sprites."""
        for regioes in lista_regioes:
            self.alimentar_sprite(regioes)
    
    def predizer_cor(self, regiao_cromatica: str):
        """Dado o nome de uma região, prediz sua cor mais provável."""
        resultado = self.coupling.esfera.predizer_cross(
            'cor_media', regiao_cromatica=regiao_cromatica
        )
        return resultado
    
    def predizer_posicao(self, cor_media: str):
        """Dada uma cor, prediz a posição mais provável."""
        resultado = self.coupling.esfera.predizer_cross(
            'bbox_pos', cor_media=cor_media
        )
        return resultado
    
    def predizer_geometria(self, cor_media: str):
        """Dada uma cor, prediz a geometria mais provável."""
        resultado = self.coupling.esfera.predizer_cross(
            'geometria', cor_media=cor_media
        )
        return resultado
