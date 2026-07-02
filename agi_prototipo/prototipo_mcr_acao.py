#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCRAcao — Sistema Universal de Acoes
======================================
Zero if/elif. Acoes sao REGISTRADAS, nao programadas.
Cada acao carrega: funcao, descricao, tags, alcance.
"""
import sys, os
from typing import Dict, List, Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_mcr_config import C


class MCRAcao:
    """Registro universal de acoes. Qualquer modulo pode registrar uma acao.
    
    Uso:
        MCRAcao.registrar("andar_dir", lambda e: mover(e, 1, 0),
                         descricao="move heroi para direita",
                         tags=["movimento", "basico"])
        
        MCRAcao.executar(estado, "andar_dir")
        MCRAcao.disponiveis()  # lista todas as acoes
    """
    
    _registro: Dict[str, Dict] = {}
    
    @classmethod
    def registrar(cls, nome: str, fn: Callable,
                  descricao: str = "",
                  tags: List[str] = None,
                  alcance: int = 1):
        """Registra uma nova acao."""
        cls._registro[nome] = {
            "fn": fn,
            "descricao": descricao,
            "tags": tags or [],
            "alcance": alcance,
        }
    
    @classmethod
    def executar(cls, estado, acao: str, **kw):
        """Executa uma acao registrada. Retorna estado.clone() se nao encontrada."""
        if acao not in cls._registro:
            return estado.clone() if hasattr(estado, "clone") else estado
        return cls._registro[acao]["fn"](estado, **kw)
    
    @classmethod
    def disponiveis(cls) -> List[str]:
        """Lista todas as acoes registradas."""
        return list(cls._registro.keys())
    
    @classmethod
    def descricao(cls, acao: str) -> str:
        """Descricao de uma acao."""
        info = cls._registro.get(acao)
        return info["descricao"] if info else acao
    
    @classmethod
    def por_tag(cls, tag: str) -> List[str]:
        """Filtra acoes por tag."""
        return [n for n, a in cls._registro.items() if tag in a["tags"]]
    
    @classmethod
    def tags_para(cls, acao: str) -> List[str]:
        """Tags de uma acao especifica."""
        info = cls._registro.get(acao)
        return list(info["tags"]) if info else []
    
    @classmethod
    def total(cls) -> int:
        return len(cls._registro)


class MCRAcaoRegistro:
    """Decorator para registrar acoes de forma declarativa."""
    
    @staticmethod
    def acao(nome: str = None, descricao: str = "", tags: List[str] = None):
        def decorator(fn):
            nome_acao = nome or fn.__name__
            MCRAcao.registrar(nome_acao, fn, descricao, tags)
            return fn
        return decorator


# ═══════════════════════════════════════════════════════════════════
# REGISTRO DAS ACOES PADRAO (grid world)
# ═══════════════════════════════════════════════════════════════════

def _registrar_acoes_padrao():
    """Registra as acoes do grid world. Chamado uma vez na importacao."""
    from prototipo_agi_completo import MotorFisica
    
    # Acoes de movimento
    MCRAcao.registrar("andar_cima",
        lambda e, **k: MotorFisica._mover(e, 0, -1) if hasattr(MotorFisica, "_mover") else e,
        descricao="move o heroi para cima (norte)",
        tags=["movimento"])
    MCRAcao.registrar("andar_baixo",
        lambda e, **k: MotorFisica._mover(e, 0, 1) if hasattr(MotorFisica, "_mover") else e,
        descricao="move o heroi para baixo (sul)",
        tags=["movimento"])
    MCRAcao.registrar("andar_esq",
        lambda e, **k: MotorFisica._mover(e, -1, 0) if hasattr(MotorFisica, "_mover") else e,
        descricao="move o heroi para esquerda (oeste)",
        tags=["movimento"])
    MCRAcao.registrar("andar_dir",
        lambda e, **k: MotorFisica._mover(e, 1, 0) if hasattr(MotorFisica, "_mover") else e,
        descricao="move o heroi para direita (leste)",
        tags=["movimento"])
    
    # Acoes de interacao
    MCRAcao.registrar("atacar",
        lambda e, **k: MotorFisica._interagir(e, "hp", -3) if hasattr(MotorFisica, "_interagir") else e,
        descricao="ataca entidade adjacente, reduz hp em 3",
        tags=["combate"])
    MCRAcao.registrar("abrir",
        lambda e, **k: MotorFisica._interagir(e, "aberto", True) if hasattr(MotorFisica, "_interagir") else e,
        descricao="abre baú ou porta adjacente",
        tags=["interacao"])
    MCRAcao.registrar("empurrar",
        lambda e, **k: MotorFisica._empurrar(e) if hasattr(MotorFisica, "_empurrar") else e,
        descricao="empurra objeto adjacente",
        tags=["interacao"])


# Registra automaticamente
_registrar_acoes_padrao()
