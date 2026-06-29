# EXPERIMENTAL — Use agent_loop como pipeline principal.
# Mantido como referencia arquitetural de design patterns.
"""BaseStrategy — Classe base para todas as estrategias.

Cada estrategia:
  - Sabe preencher certos tipos de lacuna (GapType)
  - Retorna um ou mais valores com confianca
  - Pode validar resultados de outras estrategias
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import os, sys

_MCR_DEVIA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _MCR_DEVIA not in sys.path:
    sys.path.insert(0, _MCR_DEVIA)

from engine.gap_detector import Gap, GapType


# ============================================================
# RESULTADO DA ESTRATEGIA
# ============================================================

@dataclass
class StrategyResult:
    """Resultado de uma tentativa de preenchimento."""
    sucesso: bool
    valor: Any = None
    confianca: float = 0.0           # 0.0 a 1.0
    fonte: str = ""                   # "indexer", "items_xml", "web", "llm", "humano"
    detalhes: str = ""                # Explicacao do resultado
    multiplas_opcoes: List[Any] = field(default_factory=list)  # Alternativas
    
    def to_dict(self) -> Dict:
        return {
            'sucesso': self.sucesso,
            'valor': str(self.valor)[:100] if self.valor else None,
            'confianca': self.confianca,
            'fonte': self.fonte,
            'detalhes': self.detalhes[:200],
        }


# ============================================================
# CLASSE BASE
# ============================================================

class BaseStrategy(ABC):
    """Classe base para estrategias de preenchimento."""
    
    def __init__(self):
        self.nome = self.__class__.__name__
        self.prioridade = 5  # 1 (melhor) a 5 (pior)
    
    @abstractmethod
    def pode_preencher(self, gap: Gap) -> bool:
        """Verifica se esta estrategia pode preencher este gap."""
        pass
    
    @abstractmethod
    def preencher(self, gap: Gap, contexto: Dict[str, Any]) -> StrategyResult:
        """Tenta preencher o gap com o melhor valor possivel.
        
        Args:
            gap: O gap a ser preenchido
            contexto: Informacoes adicionais (profissao, local, etc)
        
        Returns:
            StrategyResult com sucesso=True se conseguiu preencher
        """
        pass
    
    def validar(self, gap: Gap, valor: Any) -> StrategyResult:
        """Valida se um valor preenchido por outra estrategia esta correto.
        
        Usado para validar resultados da web contra fontes locais.
        """
        # Por padrao, aceita qualquer valor
        return StrategyResult(
            sucesso=True,
            valor=valor,
            confianca=0.5,
            fonte=self.nome,
            detalhes="Validacao padrao: aceito",
        )


# ============================================================
# REGISTRY DE ESTRATEGIAS
# ============================================================

_registry: List[BaseStrategy] = []

def registrar_estrategia(estrategia: BaseStrategy):
    """Registra uma estrategia no registry global."""
    _registry.append(estrategia)
    _registry.sort(key=lambda e: e.prioridade)

def get_estrategias() -> List[BaseStrategy]:
    """Retorna todas as estrategias registradas."""
    return list(_registry)

def get_estrategias_para_gap(gap: Gap) -> List[BaseStrategy]:
    """Retorna estrategias que podem preencher um gap, ordenadas por prioridade."""
    return [e for e in _registry if e.pode_preencher(gap)]

def limpar_registry():
    """Limpa o registry (para testes)."""
    _registry.clear()
