#!/usr/bin/env python3
"""mcr.mcr_orchestrator — Orquestrador universal de perguntas.
Transplantado do MCR_Chat.py original (commit de7bcb1d).
Usa similaridade Jaccard + Equacao MCR para decidir acoes."""
import re
from typing import Optional

from mcr.equacao_mcr import _EQUACAO_ATUAL

# Ferramentas disponiveis (cada uma com nome, descricao, funcao)
_FERRAMENTAS = []


def registrar_ferramenta(nome: str, descricao: str, fn):
    """Registra uma ferramenta disponivel."""
    _FERRAMENTAS.append({'nome': nome, 'desc': descricao, 'fn': fn})


def _jaccard_sim(texto_a: str, texto_b: str) -> float:
    """Similaridade Jaccard entre dois textos."""
    set_a = set(texto_a.lower().split())
    set_b = set(texto_b.lower().split())
    inter = set_a & set_b
    uniao = set_a | set_b
    return len(inter) / len(uniao) if uniao else 0.0


def escolher_ferramenta(pergunta: str) -> Optional[dict]:
    """Equacao MCR escolhe a ferramenta sem if/else.
    
    Usa Jaccard + match de prefixo para selecionar a melhor ferramenta.
    """
    if not _FERRAMENTAS:
        return None
    
    pp = [w.lower().strip('?.,!') for w in pergunta.split()]
    melhor, melhor_score = None, 0.0
    
    for f in _FERRAMENTAS:
        j = _jaccard_sim(pergunta, f['desc'])
        pd = [w.lower() for w in f['desc'].split()]
        
        # Match exato
        exata = any(p1 == p2 for p1 in pp for p2 in pd)
        # Match por prefixo
        prefixo = any(
            len(p1) >= 3 and len(p2) >= 3 and (p1.startswith(p2) or p2.startswith(p1))
            for p1 in pp for p2 in pd
        )
        
        if not (exata or prefixo):
            continue
        
        score = (j + 
                 sum(1 for p1 in pp for p2 in pd if p1 == p2) * 0.2 +
                 sum(1 for p1 in pp for p2 in pd 
                     if len(p1) >= 3 and len(p2) >= 3 and 
                     (p1.startswith(p2) or p2.startswith(p1)) and p1 != p2) * 0.15)
        
        if score > melhor_score:
            melhor_score, melhor = score, f
    
    return melhor if melhor_score > 0.2 else None


def rotear(pergunta: str, contexto: dict = None) -> str:
    """Roteia uma pergunta para a melhor ferramenta ou retorna fallback."""
    ferramenta = escolher_ferramenta(pergunta)
    if ferramenta:
        try:
            return ferramenta['fn'](pergunta)
        except Exception:
            return "Erro ao executar ferramenta."
    return None


def fragmentar(texto: str) -> list:
    """Divide texto em partes por . ! ? , — universal, 0 hardcode."""
    partes = re.split(r'[,;.!?\n]+(?:\s+|$)', texto)
    return [p.strip() for p in partes if p.strip() and len(p.strip()) > 4]
