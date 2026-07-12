"""
mcr.discriminador_anatomia — Avalia anatomia de sprites gerados.

Diferente do discriminador textural (meus_olhos.py), este avalia:
- Número de regiões (3-8 ideal)
- Distribuição de tamanhos (deve haver região dominante)
- Coerência espacial (regiões não podem ser muito dispersas)
- Diversidade cromática (2-4 cores distintas)
- Proporção fundo/foreground (foreground deve ser >30%)

Score > 0.6 = anatomia aceitável.
"""
import math
from collections import Counter
from typing import List, Dict, Tuple
from mcr.regioes_anatomicas import extrair_regioes_cromaticas


class DiscriminadorAnatomia:
    """Avalia qualidade anatômica de sprites (regiões cromáticas)."""
    
    def __init__(self):
        # Estatísticas de sprites reais (aprendidas na validação)
        self.faixa_regioes = (2, 8)      # mínimo, máximo de regiões
        self.faixa_cores = (2, 5)         # mínimo, máximo de cores
        self.min_foreground = 0.30        # mínimo de pixels foreground
        self.max_excentricidade = 4.0     # excentricidade máxima aceitável
    
    def avaliar(self, img_array) -> Dict:
        """Avalia a anatomia de um sprite.
        
        Args:
            img_array: numpy array (H, W, 3) RGB
        
        Returns:
            dict com score, breakdown, ok
        """
        regioes = extrair_regioes_cromaticas(img_array)
        
        if not regioes:
            return {'score': 0.0, 'ok': False, 'motivo': 'sem_regioes'}
        
        scores = {}
        
        # 1. Número de regiões (penaliza muito poucas ou muitas)
        n = len(regioes)
        min_r, max_r = self.faixa_regioes
        if n < min_r:
            scores['n_regioes'] = n / min_r
        elif n > max_r:
            scores['n_regioes'] = max_r / n
        else:
            scores['n_regioes'] = 1.0
        
        # 2. Região dominante (maior região deve ser >20% do total)
        areas = [r['area'] for r in regioes]
        total_area = sum(areas)
        maior_area = max(areas)
        dominancia = maior_area / total_area if total_area > 0 else 0
        scores['dominancia'] = min(dominancia / 0.20, 1.0)
        
        # 3. Coerência espacial (centroides não podem ser muito dispersas)
        centroides = [r['centroide'] for r in regioes]
        if len(centroides) >= 2:
            # Calcular distância média entre centroides
            dists = []
            for i in range(len(centroides)):
                for j in range(i+1, len(centroides)):
                    dx = centroides[i][0] - centroides[j][0]
                    dy = centroides[i][1] - centroides[j][1]
                    dists.append(math.sqrt(dx**2 + dy**2))
            dist_media = sum(dists) / len(dists)
            # Normalizar: distância média ideal = 10-15 pixels em sprite 32x32
            scores['coerencia'] = max(0, 1.0 - abs(dist_media - 12) / 20)
        else:
            scores['coerencia'] = 0.5
        
        # 4. Diversidade cromática (cores Lab* distintas)
        cores_lab = [r['cor_media_lab'] for r in regioes]
        # Discretizar cores (simplificado)
        cores_disc = set()
        for L, a, b in cores_lab:
            if L < 30: c = 'esc'
            elif L < 60: c = 'med'
            else: c = 'cla'
            if abs(a) > 20: c += '_a'
            if abs(b) > 20: c += '_b'
            cores_disc.add(c)
        
        n_cores = len(cores_disc)
        min_c, max_c = self.faixa_cores
        if n_cores < min_c:
            scores['diversidade'] = n_cores / min_c
        elif n_cores > max_c:
            scores['diversidade'] = max_c / n_cores
        else:
            scores['diversidade'] = 1.0
        
        # 5. Proporção foreground (regiões devem cobrir >30% do sprite)
        h, w = img_array.shape[:2]
        total_pixels = h * w
        foreground = sum(r['area'] for r in regioes)
        prop_fg = foreground / total_pixels
        scores['foreground'] = min(prop_fg / self.min_foreground, 1.0)
        
        # 6. Excentricidade (nenhuma região pode ser extremamente alongada)
        exccs = [r['excentricidade'] for r in regioes]
        max_excc = max(exccs) if exccs else 1.0
        scores['proporcao'] = min(self.max_excentricidade / max(max_excc, 0.1), 1.0)
        
        # Score final (média ponderada)
        pesos = {
            'n_regioes': 0.20,
            'dominancia': 0.20,
            'coerencia': 0.15,
            'diversidade': 0.20,
            'foreground': 0.15,
            'proporcao': 0.10,
        }
        
        score_final = sum(scores[k] * pesos[k] for k in pesos)
        
        return {
            'score': round(score_final, 3),
            'ok': score_final > 0.6,
            'n_regioes': n,
            'n_cores': n_cores,
            'dominancia': round(dominancia, 3),
            'prop_fg': round(prop_fg, 3),
            'breakdown': {k: round(v, 3) for k, v in scores.items()},
        }
    
    def diagnostico(self, resultado: Dict) -> str:
        """Diagnóstico textual."""
        s = resultado['score']
        if s > 0.8: txt = 'EXCELENTE'
        elif s > 0.6: txt = 'BOM'
        elif s > 0.4: txt = 'ACEITAVEL'
        else: txt = 'FRACO'
        
        linhas = [
            f"Score: {s:.3f} ({txt})",
            f"Regiões: {resultado.get('n_regioes', '?')}",
            f"Cores: {resultado.get('n_cores', '?')}",
            f"Dominância: {resultado.get('dominancia', '?')}",
            f"Foreground: {resultado.get('prop_fg', '?')}",
        ]
        
        bk = resultado.get('breakdown', {})
        for k, v in bk.items():
            linhas.append(f"  {k}: {v:.3f}")
        
        return '\n'.join(linhas)


def avaliar_sprite(img_path: str) -> Dict:
    """Função conveniência para avaliar um sprite de arquivo."""
    from PIL import Image
    import numpy as np
    
    img = Image.open(img_path).convert('RGB')
    arr = np.array(img)
    
    disc = DiscriminadorAnatomia()
    return disc.avaliar(arr)


def avaliar_diretorio(dir_path: str) -> Dict:
    """Avalia todos os sprites de um diretório."""
    from pathlib import Path
    
    resultados = []
    for fpath in sorted(Path(dir_path).glob('*.png')):
        r = avaliar_sprite(str(fpath))
        r['arquivo'] = fpath.name
        resultados.append(r)
    
    if not resultados:
        return {'media': 0.0, 'n': 0}
    
    scores = [r['score'] for r in resultados]
    return {
        'media': sum(scores) / len(scores),
        'min': min(scores),
        'max': max(scores),
        'n': len(resultados),
        'resultados': resultados,
    }
