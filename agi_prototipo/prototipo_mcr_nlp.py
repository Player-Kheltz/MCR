#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCRNLP — Processamento de Linguagem Natural por Fingerprint
=============================================================
Zero keyword matching. Zero if/elif.
Toda compreensao de linguagem e feita por similaridade de fingerprint.

Uso:
    MCRNLP.aprender("anda para direita", "andar_dir")
    MCRNLP.aprender("va para o leste", "andar_dir")
    MCRNLP.aprender("ataque o monstro", "atacar")
    
    acoes = MCRNLP.entender("vire a direita")  # → ["andar_dir"]
"""
import sys, os
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_mcr_config import C


class MCRNLP:
    """Entendimento de linguagem 100% por similaridade.
    
    Nao ha keywords. Nao ha if/elif para cada palavra.
    Usa Jaccard de bytes para matching de curtas frases
    e fingerprint para deteccao de dominios.
    """
    
    _exemplos: Dict[str, List[str]] = {}  # acao -> [frase, ...]
    _dominios: Dict[str, List[str]] = {}  # dominio -> [frase, ...]
    
    @classmethod
    def aprender(cls, frase: str, acao: str, dominio: str = "acao"):
        """Aprende que uma frase corresponde a uma acao."""
        cls._exemplos.setdefault(acao, []).append(frase.lower())
        if dominio != "acao":
            cls._dominios.setdefault(dominio, []).append(frase.lower())
    
    @classmethod
    def entender(cls, frase: str, dominio: str = "acao",
                 top_k: int = None) -> List[str]:
        """Encontra a(s) acao(es) mais similar(es) por Jaccard.
        
        Zero keywords. Zero if/elif. Similaridade pura.
        """
        top_k = top_k if top_k is not None else max(1, int(C("top_k")))
        conf_min = C("conf_alta")
        frase = frase.lower()
        
        scores = cls._pontuar_por_jaccard(frase)
        scores.sort(key=lambda x: -x[0])
        
        if not scores or scores[0][0] < conf_min:
            return []
        
        return [a for s, a in scores[:top_k] if s > conf_min]
    
    @classmethod
    def entender_com_confianca(cls, frase: str, dominio: str = "acao"
                                ) -> List[Tuple[str, float]]:
        """Como entender(), mas retorna (acao, confianca)."""
        scores = cls._pontuar_por_jaccard(frase.lower())
        scores.sort(key=lambda x: -x[0])
        return [(a, round(s, 3)) for s, a in scores[:C("top_k")] if s > C("conf_alta")]
    
    @classmethod
    def _pontuar_por_jaccard(cls, frase: str) -> List[Tuple[float, str]]:
        """Calcula scores por Jaccard de bytes entre frase e exemplos."""
        from prototipo_agi_completo import MCRByteUtils
        scores: Dict[str, float] = {}
        
        for acao, exemplos in cls._exemplos.items():
            melhor_j = 0.0
            for ex in exemplos:
                j = MCRByteUtils.jaccard_bytes(frase, ex)
                if j > melhor_j:
                    melhor_j = j
            if melhor_j > 0:
                scores[acao] = melhor_j
        
        return [(s, a) for a, s in scores.items()]
    
    @classmethod
    def detectar_dominio(cls, texto: str) -> str:
        """Detecta dominio por Jaccard. Zero keywords."""
        from prototipo_agi_completo import MCRByteUtils
        texto = texto.lower()
        
        if not cls._dominios:
            return "texto"
        
        melhor_dom = "texto"
        melhor_j = 0.0
        
        for dominio, frases in cls._dominios.items():
            for ex in frases:
                j = MCRByteUtils.jaccard_bytes(texto, ex)
                if j > melhor_j:
                    melhor_j = j
                    melhor_dom = dominio
        
        return melhor_dom if melhor_j > C("conf_alta") else "texto"
    
    @classmethod
    def traduzir_acao(cls, acao: str, contexto: str = "") -> str:
        """Traduz uma acao para descricao textual."""
        exemplos = cls._exemplos.get(acao, [])
        if exemplos:
            return max(exemplos, key=len)
        return acao
    
    @classmethod
    def estatisticas(cls) -> Dict:
        return {
            "exemplos": sum(len(v) for v in cls._exemplos.values()),
            "dominios": len(cls._dominios),
            "acoes": len([k for k in cls._exemplos if not isinstance(
                cls._exemplos[k], list) or len(cls._exemplos[k]) > 0]),
        }


# ═══════════════════════════════════════════════════════════════════
# EXEMPLOS PADRAO
# ═══════════════════════════════════════════════════════════════════

def _registrar_exemplos_padrao():
    """Registra exemplos de linguagem natural para acoes do grid."""
    
    # Movimento
    for frase in ["anda para cima", "suba", "norte", "ir para norte", "vai pra cima"]:
        MCRNLP.aprender(frase, "andar_cima")
    for frase in ["anda para baixo", "desca", "sul", "ir para sul", "vai pra baixo"]:
        MCRNLP.aprender(frase, "andar_baixo")
    for frase in ["anda para esquerda", "esquerda", "oeste", "ir para oeste", "vire a esquerda"]:
        MCRNLP.aprender(frase, "andar_esq")
    for frase in ["anda para direita", "direita", "leste", "ir para leste", "vire a direita"]:
        MCRNLP.aprender(frase, "andar_dir")
    
    # Combate
    for frase in ["ataque", "atacar o monstro", "bater", "lutar", "combater", "golpear"]:
        MCRNLP.aprender(frase, "atacar")
    
    # Interacao
    for frase in ["abrir", "abra o bau", "abrir porta", "destrancar"]:
        MCRNLP.aprender(frase, "abrir")
    for frase in ["empurrar", "empurre a pedra", "mover objeto", "arrastar"]:
        MCRNLP.aprender(frase, "empurrar")
    
    # Dominios
    for frase in ["heroi", "posicao", "grid", "andar", "bau", "monstro",
                    "heroi andou para direita", "bau fechado", "monstro ataca"]:
        MCRNLP._dominios.setdefault("grid", []).append(frase.lower())
    for frase in ["SPA", "SHC", "sistema", "progressao", "habilidade", "lore"]:
        MCRNLP._dominios.setdefault("texto", []).append(frase.lower())
    for frase in ["1 2 3", "fibonacci", "sequencia", "numero", "potencia"]:
        MCRNLP._dominios.setdefault("numerico", []).append(frase.lower())


_registrar_exemplos_padrao()
