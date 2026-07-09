#!/usr/bin/env python3
"""mcr.mcr_radar — Busca por ondas de similaridade.
Transplantado do prototipo_radar.py original.
Expande o raio de busca gradualmente ate encontrar conexoes."""
import math
import re
from typing import List, Dict, Optional, Callable


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
