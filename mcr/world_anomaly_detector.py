#!/usr/bin/env python3
"""world_anomaly_detector.py — Guardião de Coerência de Mundo.

Detecta termos anacrônicos comparando cada token contra o corpus
do mundo. O limiar de anomalia é adaptativo: emerge da entropia
do próprio corpus (Ponte Ótima).

Quanto mais diverso o mundo, menor o limiar (mais tolerante).
Quanto menor a entropia, maior o limiar (mais rigoroso).
Nenhum número mágico. Nenhuma lista fixa.
"""
import os, re, math, json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from collections import Counter

from devia.kernel.mcr_kernel.signature import raw_token_set


def _entropia_shannon(tokens: Set[str]) -> float:
    """Entropia de Shannon de um conjunto de tokens.
    
    Quanto mais distribuido o vocabulario, maior a entropia.
    Quanto menor a entropia, mais repetitivo/previsivel.
    
    Returns:
        valor entre 0 e log2(N) normalizado para [0, 1]
    """
    if not tokens:
        return 0.0
    n = len(tokens)
    if n < 2:
        return 0.0
    # entropia maxima = log2(n) para distribuicao uniforme
    # usamos uma aproximacao: assumimos distribuicao uniforme
    # H_max = log2(n), H_real ~ H_max para corpus grande
    h = math.log2(n)
    h_max = math.log2(max(n, 2))
    return h / h_max if h_max > 0 else 0.0


class WorldAnomalyDetector:
    """Guardião de coerência de mundo com limiar adaptativo.
    
    O limiar de anomalia emerge da entropia do corpus:
        limiar = 1.0 - entropia_normalizada
    
    A entropia e calculada sobre a distribuicao de FREQUENCIAS
    dos tokens (Counter), nao apenas sobre o conjunto.
    
    - Frequencias muito concentradas (entropia baixa) → limiar alto → rigoroso
    - Frequencias bem distribuidas (entropia alta) → limiar baixo → tolerante
    - Termo com frequencia zero no corpus → similaridade 0 → ANOMALIA para sempre
    """

    def __init__(self):
        self._freq: Counter = Counter()  # token -> frequencia no corpus
        self._corpus: Set[str] = set()    # tokens unicos
        self._entropia: float = 0.0

    # ─── Propriedade principal ─────────────────────────

    @property
    def corpus(self) -> Set[str]:
        """Tokens unicos do corpus (para calculo de Jaccard)."""
        return set(self._freq.keys())

    @property
    def limiar_anomalia(self) -> float:
        """Limiar adaptativo: inversamente proporcional a entropia do corpus.
        
        A entropia e calculada sobre as FREQUENCIAS dos tokens.
        - Se algumas palavras dominam (ex: 'function' aparece 1000x), 
          entropia baixa → limiar alto → sistema rigoroso.
        - Se as palavras sao bem distribuidas, entropia alta → limiar baixo.
        - Termos AUSENTES do corpus sempre serao anomalos (sim=0 < limiar).
        """
        return max(0.01, 1.0 - self._entropia)

    @property
    def entropia(self) -> float:
        return self._entropia

    # ─── Carregamento inicial ──────────────────────────

    def _add_tokens(self, texto: str):
        """Adiciona tokens ao corpus com frequencia."""
        tokens = raw_token_set(texto)
        for t in tokens:
            self._freq[t] += 1

    def carregar(self, scripts_dir: str = None, world_state_path: str = None,
                 chronicle_path: str = None, kg_dir: str = None):
        """Carrega o corpus inicial do mundo e calcula a entropia."""
        if scripts_dir and os.path.isdir(scripts_dir):
            count = 0
            for root, dirs, files in os.walk(scripts_dir):
                for fname in files:
                    if not fname.endswith('.lua'):
                        continue
                    try:
                        with open(os.path.join(root, fname), 'r',
                                  encoding='utf-8', errors='replace') as f:
                            self._add_tokens(f.read())
                        count += 1
                    except Exception:
                        pass
            print(f'[AnomalyDetector] {count} scripts lidos')

        if chronicle_path and os.path.exists(chronicle_path):
            try:
                with open(chronicle_path, 'r', encoding='utf-8') as f:
                    self._add_tokens(f.read())
            except Exception:
                pass

        if kg_dir and os.path.isdir(kg_dir):
            for fname in os.listdir(kg_dir):
                if not fname.endswith('.json'):
                    continue
                try:
                    with open(os.path.join(kg_dir, fname), 'r',
                              encoding='utf-8') as f:
                        data = json.load(f)
                    for lesson in data.get('licoes', []):
                        for campo in ('solucao', 'erro', 'causa'):
                            txt = lesson.get(campo, '')
                            if txt and isinstance(txt, str):
                                self._add_tokens(txt)
                except Exception:
                    pass

        if world_state_path and os.path.exists(world_state_path):
            try:
                with open(world_state_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                textos = []
                for chave in ('npcs', 'monstros', 'lores'):
                    for nome, dados in data.get(chave, {}).items():
                        textos.append(nome)
                        for v in dados.values():
                            if isinstance(v, str):
                                textos.append(v)
                for t in textos:
                    self._add_tokens(t)
            except Exception:
                pass

        self._recalcular_entropia()
        print(f'[AnomalyDetector] Corpus: {len(self.corpus)} tokens, '
              f'entropia: {self._entropia:.4f}, limiar: {self.limiar_anomalia:.4f}')

    # ─── Atualizacao a cada canonizacao ────────────────

    def atualizar(self, texto: str):
        """Expande o corpus com novo texto e recalcula entropia.
        
        Chamado apos cada NPC/lore canonizado com sucesso.
        """
        tokens = raw_token_set(texto)
        antes = len(self._freq)
        for t in tokens:
            self._freq[t] += 1
        depois = len(self._freq)
        if depois > antes:
            self._recalcular_entropia()

    def _recalcular_entropia(self):
        """Recalcula a entropia do corpus usando a distribuicao de frequencias."""
        if not self._freq:
            self._entropia = 0.0
            return
        total = sum(self._freq.values())
        if total == 0:
            self._entropia = 0.0
            return
        h = 0.0
        for count in self._freq.values():
            p = count / total
            if p > 0:
                h -= p * math.log2(p)
        n = len(self._freq)
        h_max = math.log2(max(n, 2))
        self._entropia = h / h_max if h_max > 0 else 0.0

    # ─── Deteccao ──────────────────────────────────────

    def detectar(self, texto: str) -> List[Dict]:
        """Detecta tokens anomalos em um texto gerado.
        
        Para cada token, calcula similaridade Jaccard com o corpus.
        Tokens com similaridade < limiar_anomalia sao anomalos.
        
        Args:
            texto: texto gerado (resposta do LLM)
        
        Returns:
            lista de anomalias: [{token, similaridade, contexto}]
        """
        if not texto:
            return []

        tokens_texto = raw_token_set(texto)
        if not tokens_texto:
            return []

        limiar = self.limiar_anomalia
        anomalias = []

        for token in tokens_texto:
            if len(token) < 4 or token.isdigit():
                continue
            sim = self._jaccard({token}, self.corpus)
            if sim < limiar:
                anomalias.append({
                    'token': token,
                    'similaridade': round(sim, 4),
                    'contexto': self._extrair_contexto(texto, token),
                })

        anomalias.sort(key=lambda a: a['similaridade'])
        return anomalias

    def validar(self, texto: str, max_tentativas: int = 2) -> Dict:
        """Valida texto e retorna instrucao de correcao se necessario.
        
        Returns:
            dict com 'valido', 'anomalias', 'instrucao', 'exige_regeneracao'
        """
        anomalias = self.detectar(texto)

        if not anomalias:
            return {
                'valido': True, 'anomalias': [], 'instrucao': '',
                'exige_regeneracao': False,
            }

        termos = list(set(a['token'] for a in anomalias[:5]))
        instrucao = (
            f"EVITE os seguintes conceitos no texto gerado, pois sao "
            f"incompativeis com o universo de fantasia medieval: "
            f"{', '.join(termos)}. "
            f"Mantenha-se fiel a um mundo de fantasia classico com magia, "
            f"espadas, castelos, florestas e dragoes. "
            f"NADA de tecnologia moderna."
        )

        return {
            'valido': False, 'anomalias': anomalias[:10],
            'instrucao': instrucao, 'exige_regeneracao': True,
        }

    # ─── Helpers ───────────────────────────────────────

    @staticmethod
    def _jaccard(a: set, b: set) -> float:
        inter = a & b
        uniao = a | b
        return len(inter) / len(uniao) if uniao else 0.0

    @staticmethod
    def _extrair_contexto(texto: str, token: str, pad: int = 40) -> str:
        idx = texto.lower().find(token.lower())
        if idx < 0:
            return token
        ini = max(0, idx - pad)
        fim = min(len(texto), idx + len(token) + pad)
        ctx = texto[ini:fim].replace('\n', ' ')
        return ('...' if ini > 0 else '') + ctx + ('...' if fim < len(texto) else '')
