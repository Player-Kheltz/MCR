#!/usr/bin/env python3
"""cache_hierarquico.py — Cache Hierarquico L1→L2→L3→LLM.

Elimina ~70-80% das chamadas ao LLM.

L1 (dict): Pergunta identica → resposta exata (0.0001s)
L2 (Markov): Pergunta similar (MarkovDecider) → resposta do cache (0.001s)
L3 (Fingerprint): Pergunta parafraseada (Jaccard) → resposta do cache (0.01s)
Fallback: LLM, entao cache.aprender()
"""
import os, json, time, hashlib
from typing import Dict, Optional


CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'devia', 'kernel', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)


class CacheHierarquico:
    """Cache de respostas com 3 niveis.
    
    Uso:
        cache = CacheHierarquico()
        
        # Buscar
        resposta = cache.buscar(pergunta)
        if resposta:
            return resposta  # Nivel encontrado, zero LLM
        
        # Se nao encontrou, chama LLM e depois:
        cache.aprender(pergunta, resposta_llm, classe)
    """

    def __init__(self, max_size: int = 2000):
        self._l1: Dict[str, dict] = {}  # pergunta normalizada → {resposta, classe, timestamp}
        self._max_size = max_size
        self._stats = {'l1_hit': 0, 'l2_hit': 0, 'l3_hit': 0, 'miss': 0, 'total': 0}
        self._carregar()
    
    # ─── API publica ─────────────────────────────────────
    
    def buscar(self, pergunta: str) -> Optional[str]:
        """Busca resposta em 3 niveis. Retorna string ou None."""
        self._stats['total'] += 1
        
        # L1: Match exato (normalizado)
        norm = self._normalizar(pergunta)
        if norm in self._l1:
            entry = self._l1[norm]
            # Verifica se nao expirou (24h)
            if time.time() - entry.get('ts', 0) < 86400:
                self._stats['l1_hit'] += 1
                return entry['resposta']
        
        # L2: MarkovDecider (similaridade de tokens)
        try:
            from mcr_devia_v2 import MarkovDecider
            md = MarkovDecider()
            classe, conf = md.classificar(pergunta)
            if conf > 0.3:
                from devia.kernel.mcr_kernel.signature import raw_token_set
                tokens_q = raw_token_set(pergunta)
                # Busca no cache L1 por classe similar + similaridade minima
                for k, v in self._l1.items():
                    if v.get('classe') != classe:
                        continue
                    if time.time() - v.get('ts', 0) >= 86400:
                        continue
                    # Verifica similaridade Jaccard minima (evita falsos positivos)
                    tokens_k = raw_token_set(k)
                    if tokens_q and tokens_k:
                        inter = tokens_q & tokens_k
                        uniao = tokens_q | tokens_k
                        sim = len(inter) / len(uniao) if uniao else 0
                        if sim >= 0.12:  # similaridade minima viavel
                            self._stats['l2_hit'] += 1
                            return v['resposta']
        except Exception:
            pass
        
        # L3: Fingerprint (Jaccard de tokens)
        try:
            from devia.kernel.mcr_kernel.signature import raw_token_set
            from devia.kernel.mcr_kernel.engine import MCR
            tokens_pergunta = raw_token_set(pergunta)
            if tokens_pergunta:
                melhor = None
                melhor_sim = 0.0
                for k, v in self._l1.items():
                    if time.time() - v.get('ts', 0) >= 86400:
                        continue
                    tokens_cache = raw_token_set(k)
                    if not tokens_cache:
                        continue
                    inter = tokens_pergunta & tokens_cache
                    uniao = tokens_pergunta | tokens_cache
                    sim = len(inter) / len(uniao) if uniao else 0
                    if sim > melhor_sim:
                        melhor_sim = sim
                        melhor = v
                if melhor and melhor_sim >= 0.15:
                    self._stats['l3_hit'] += 1
                    return melhor['resposta']
        except Exception:
            pass
        
        self._stats['miss'] += 1
        return None
    
    def aprender(self, pergunta: str, resposta: str, classe: str = ''):
        """Aprende nova pergunta→resposta no cache."""
        if not pergunta or not resposta:
            return
        
        norm = self._normalizar(pergunta)
        
        # Evita cache de mensagens de erro
        if resposta.startswith('[Erro') or resposta.startswith('[LLM'):
            return
        
        # Mantem tamanho maximo (LRU aproximado)
        if len(self._l1) >= self._max_size:
            # Remove o mais antigo
            mais_antigo = min(self._l1.keys(), key=lambda k: self._l1[k].get('ts', 0))
            del self._l1[mais_antigo]
        
        self._l1[norm] = {
            'resposta': resposta,
            'classe': classe,
            'ts': time.time(),
        }
        
        # Aprende tambem no MarkovDecider
        try:
            from mcr_devia_v2 import MarkovDecider
            md = MarkovDecider()
            md.aprender(pergunta, classe or 'desconhecido')
        except Exception:
            pass
        
        # Salva periodicamente (a cada 10 novas entradas)
        if len(self._l1) % 10 == 0:
            self._salvar()
    
    def estatisticas(self) -> dict:
        """Retorna estatisticas do cache."""
        total = max(self._stats['total'], 1)
        return {
            'l1_hit': self._stats['l1_hit'],
            'l2_hit': self._stats['l2_hit'],
            'l3_hit': self._stats['l3_hit'],
            'miss': self._stats['miss'],
            'total': self._stats['total'],
            'taxa_acerto': round((self._stats['l1_hit'] + self._stats['l2_hit'] + self._stats['l3_hit']) / total * 100, 1),
            'tamanho': len(self._l1),
        }
    
    # ─── Persistencia ────────────────────────────────────
    
    def _normalizar(self, texto: str) -> str:
        return texto.lower().strip()[:200]
    
    def _salvar(self):
        path = os.path.join(CACHE_DIR, 'cache_hierarquico.json')
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({'l1': self._l1}, f, ensure_ascii=False)
        except Exception:
            pass
    
    def _carregar(self):
        path = os.path.join(CACHE_DIR, 'cache_hierarquico.json')
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._l1 = data.get('l1', {})
            except Exception:
                self._l1 = {}
