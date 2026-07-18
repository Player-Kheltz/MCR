#!/usr/bin/env python3
"""mcr.mcr_radar — Busca por ondas de similaridade.

Radar Polimórfico: compara texto (Jaccard, fingerprint) E sprites (CIELAB, geometria).
Expande o raio de busca gradualmente até encontrar conexões."""
import math
import re
from collections import Counter
from typing import List, Dict, Optional, Callable

pytest.importorskip('mcr.cielab')
from mcr.cielab import delta_e76


class RadarMCR:
    """Radar que busca por ondas de similaridade.
    
    Funciona em 4 ondas:
    - Onda 1: match exato (threshold alto)
    - Onda 2: match parcial (threshold medio)
    - Onda 3: match por byte/fingerprint (threshold baixo)
    - Onda 4: expansao contextual (tenta qualquer conexao)
    """

    ONDAS = [
        {'nome': 'exata', 'threshold': 0.70, 'desc': 'Match exato de conteudo'},
        {'nome': 'parcial', 'threshold': 0.50, 'desc': 'Match parcial de conteudo'},
        {'nome': 'fingerprint', 'threshold': 0.30, 'desc': 'Similaridade de fingerprint'},
        {'nome': 'contextual', 'threshold': 0.10, 'desc': 'Expansao contextual'},
    ]

    def __init__(self):
        self._cache = {}

    def buscar(self, consulta: str, candidatos: List[Dict],
               funcao_similaridade: Optional[Callable] = None) -> List[Dict]:
        """Busca em ondas de similaridade.
        
        Args:
            consulta: texto de consulta.
            candidatos: lista de dicts com 'texto' e 'id'.
            funcao_similaridade: funcao que recebe (texto_a, texto_b) -> float.
                                 Se None, usa Jaccard.
        
        Returns:
            lista de candidatos com 'score' e 'onda' adicionados.
        """
        if funcao_similaridade is None:
            funcao_similaridade = self._jaccard_sim

        resultados = []
        visitados = set()

        for onda in self.ONDAS:
            for cand in candidatos:
                if cand.get('id', '') in visitados:
                    continue

                score = funcao_similaridade(consulta, cand.get('texto', ''))
                if score >= onda['threshold']:
                    cand['score'] = round(score, 3)
                    cand['onda'] = onda['nome']
                    resultados.append(cand)
                    visitados.add(cand.get('id', ''))

        resultados.sort(key=lambda x: -x['score'])
        return resultados

    @staticmethod
    def _jaccard_sim(a: str, b: str) -> float:
        """Jaccard entre conjuntos de palavras."""
        set_a = set(re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', a.lower()))
        set_b = set(re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', b.lower()))
        inter = set_a & set_b
        uniao = set_a | set_b
        return len(inter) / len(uniao) if uniao else 0.0

    @staticmethod
    def fingerprint_sim(a: str, b: str) -> float:
        """Similaridade por fingerprint de tipos de caractere (8D)."""
        def _fp(texto):
            buckets = [0.0] * 8
            for char in texto:
                code = ord(char)
                if 97 <= code <= 122: buckets[0] += 1  # a-z
                elif 65 <= code <= 90: buckets[1] += 1  # A-Z
                elif 48 <= code <= 57: buckets[2] += 1  # 0-9
                elif code == 32: buckets[3] += 1        # espaco
                elif code in (33, 44, 46, 58, 59, 63): buckets[4] += 1  # pontuacao
                elif code < 65: buckets[5] += 1         # special
                elif code > 122: buckets[6] += 1        # high ascii
                else: buckets[7] += 1
            total = sum(buckets) or 1
            return [round(b / total * 10, 3) for b in buckets]

        fa = _fp(a)
        fb = _fp(b)
        dot = sum(x * y for x, y in zip(fa, fb))
        na = math.sqrt(sum(x * x for x in fa))
        nb = math.sqrt(sum(y * y for y in fb))
        return dot / (na * nb) if na * nb else 0.0

    def expandir_consulta(self, consulta: str, candidatos: List[Dict],
                          resultados_iniciais: List[Dict]) -> List[Dict]:
        """Expande a consulta com base nos resultados iniciais e busca novamente."""
        if not resultados_iniciais:
            return []

        # Extrai palavras dos melhores resultados
        palavras_extra = set()
        for r in resultados_iniciais[:3]:
            palavras_extra.update(
                re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', r.get('texto', '').lower())
            )

        consulta_expandida = consulta + ' ' + ' '.join(palavras_extra)
        return self.buscar(consulta_expandida, candidatos)

    # ─── Comparação Visual (C2 — Radar Polimórfico) ──────────

    @staticmethod
    def similaridade_visual(regioes_a: List[Dict], regioes_b: List[Dict]) -> float:
        """Compara dois sprites por regiões cromáticas.
        
        Métricas combinadas:
        1. Histograma de cores Lab* (distribuição de clusters)
        2. Geometria (distribuição de áreas e excentricidades)
        3. Distância entre centróides globais
        
        Args:
            regioes_a: lista de regiões do sprite A (saída de extrair_regioes_cromaticas)
            regioes_b: lista de regiões do sprite B
        
        Returns:
            score 0-1 (1 = idêntico visualmente)
        """
        if not regioes_a or not regioes_b:
            return 0.0

        # 1. Histograma de cores Lab* (bins de L, a, b)
        def _hist_lab(regioes, n_bins=8):
            labs = [r['cor_media_lab'] for r in regioes]
            if not labs:
                return [0] * (n_bins ** 3)
            # Normalizar L para [0, n_bins-1], a e b para [0, n_bins-1]
            hist = [0] * (n_bins ** 3)
            for L, a, b in labs:
                l_bin = min(int(L / 100 * n_bins), n_bins - 1)
                a_bin = min(int((a + 128) / 255 * n_bins), n_bins - 1)
                b_bin = min(int((b + 128) / 255 * n_bins), n_bins - 1)
                idx = l_bin * n_bins * n_bins + a_bin * n_bins + b_bin
                hist[idx] += 1
            total = sum(hist) or 1
            return [h / total for h in hist]

        hist_a = _hist_lab(regioes_a)
        hist_b = _hist_lab(regioes_b)

        # Cosine similarity entre histogramas
        dot = sum(x * y for x, y in zip(hist_a, hist_b))
        na = math.sqrt(sum(x * x for x in hist_a))
        nb = math.sqrt(sum(y * y for y in hist_b))
        sim_cor = dot / (na * nb) if na * nb else 0.0

        # 2. Geometria (distribuição de áreas e excentricidades)
        def _geo_vector(regioes):
            if not regioes:
                return [0.0, 0.0, 0.0, 0.0]
            areas = sorted([r['area'] for r in regioes])
            exccs = sorted([r['excentricidade'] for r in regioes])
            return [
                sum(areas) / len(areas),           # área média
                max(areas) / max(sum(areas), 1),   # fração da maior
                sum(exccs) / len(exccs),           # excentricidade média
                len(regioes),                       # número de regiões
            ]

        geo_a = _geo_vector(regioes_a)
        geo_b = _geo_vector(regioes_b)

        # Normalizar e calcular distância
        max_vals = [max(abs(a), abs(b), 1) for a, b in zip(geo_a, geo_b)]
        d_geo = sum(abs(a - b) / m for a, b, m in zip(geo_a, geo_b, max_vals)) / len(geo_a)
        sim_geo = max(0.0, 1.0 - d_geo)

        # 3. Distância entre centróides globais
        def _centroide_global(regioes):
            total_area = sum(r['area'] for r in regioes)
            if total_area == 0:
                return (0.0, 0.0)
            cx = sum(r['centroide'][0] * r['area'] for r in regioes) / total_area
            cy = sum(r['centroide'][1] * r['area'] for r in regioes) / total_area
            return (cx, cy)

        c_a = _centroide_global(regioes_a)
        c_b = _centroide_global(regioes_b)
        d_centro = math.sqrt((c_a[0] - c_b[0])**2 + (c_a[1] - c_b[1])**2)
        sim_pos = max(0.0, 1.0 - d_centro / 32.0)  # 32 = tamanho do sprite

        # Combinar: 50% cor + 30% geometria + 20% posição
        return sim_cor * 0.5 + sim_geo * 0.3 + sim_pos * 0.2

    def buscar_visual(self, regioes_query: List[Dict],
                      candidatos: List[Dict]) -> List[Dict]:
        """Busca visual por similaridade de regiões cromáticas.
        
        Args:
            regioes_query: regiões do sprite de consulta
            candidatos: lista de dicts com 'id', 'regioes' (lista de regiões)
        
        Returns:
            lista de candidatos com 'score' e 'onda' adicionados, ordenados por score
        """
        resultados = []
        visitados = set()

        for onda in self.ONDAS:
            for cand in candidatos:
                cand_id = cand.get('id', '')
                if cand_id in visitados:
                    continue

                cand_regioes = cand.get('regioes', [])
                if not cand_regioes:
                    continue

                score = self.similaridade_visual(regioes_query, cand_regioes)
                if score >= onda['threshold']:
                    resultados.append({
                        'id': cand_id,
                        'score': round(score, 3),
                        'onda': onda['nome'],
                        'n_regioes': len(cand_regioes),
                    })
                    visitados.add(cand_id)

        resultados.sort(key=lambda x: -x['score'])
        return resultados

    def fingerprint_visual(self, regioes: List[Dict]) -> List[float]:
        """Gera fingerprint visual 8D de um sprite a partir de suas regiões.
        
        Dimensões:
        0: número de regiões (normalizado)
        1: área total (normalizada)
        2: excentricidade média
        3: L* médio
        4: a* médio
        5: b* médio
        6: proporção de clusters diferentes
        7: entropia da distribuição de áreas
        """
        if not regioes:
            return [0.0] * 8

        n = len(regioes)
        areas = [r['area'] for r in regioes]
        exccs = [r['excentricidade'] for r in regioes]
        labs = [r['cor_media_lab'] for r in regioes]

        # Entropia da distribuição de áreas
        total_area = sum(areas) or 1
        probs = [a / total_area for a in areas]
        entropia = -sum(p * math.log2(p) for p in probs if p > 0)
        entropia_max = math.log2(max(n, 2))
        ent_norm = entropia / entropia_max if entropia_max > 0 else 0

        # Proporção de clusters diferentes
        clusters = set(r.get('cluster_id', 0) for r in regioes)
        prop_clusters = len(clusters) / max(n, 1)

        return [
            min(n / 10.0, 1.0),                    # 0: número de regiões
            min(sum(areas) / 1024.0, 1.0),          # 1: área total
            sum(exccs) / n / 5.0,                   # 2: excentricidade média
            sum(l[0] for l in labs) / n / 100.0,    # 3: L* médio
            (sum(l[1] for l in labs) / n + 128) / 255.0,  # 4: a* médio
            (sum(l[2] for l in labs) / n + 128) / 255.0,  # 5: b* médio
            prop_clusters,                           # 6: proporção de clusters
            ent_norm,                                # 7: entropia de áreas
        ]

    @staticmethod
    def fingerprint_visual_sim(fp_a: List[float], fp_b: List[float]) -> float:
        """Similaridade entre fingerprints visuais 8D (cosseno)."""
        dot = sum(x * y for x, y in zip(fp_a, fp_b))
        na = math.sqrt(sum(x * x for x in fp_a))
        nb = math.sqrt(sum(y * y for y in fp_b))
        return dot / (na * nb) if na * nb else 0.0
