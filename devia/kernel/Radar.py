"""Radar — detecta loops de ação no pipeline.

Se a mesma ação aparece 4+ vezes consecutivas, força alternativa.
Previne que o sistema fique preso repetindo a mesma operação sem progresso.
"""
from typing import List, Optional


class Radar:
    """Detector de loop para o pipeline de comandos."""
    
    def __init__(self, limite: int = 4):
        self.ultimas_acoes: List[str] = []
        self.limite = limite
        self.alternativas_forcadas = 0
    
    def alimentar(self, acao: str):
        """Registra uma ação executada."""
        self.ultimas_acoes.append(acao)
        # Mantém só as últimas 10 para memória
        if len(self.ultimas_acoes) > 10:
            self.ultimas_acoes = self.ultimas_acoes[-10:]
    
    def em_loop(self) -> bool:
        """Verifica se está em loop (mesma ação N+ vezes consecutivas)."""
        if len(self.ultimas_acoes) < self.limite:
            return False
        return len(set(self.ultimas_acoes[-self.limite:])) == 1
    
    def forcar_alternativa(self, acoes_disponiveis: List[str]) -> Optional[str]:
        """Retorna ação diferente da que está em loop."""
        if not self.em_loop():
            return None
        
        acao_loop = self.ultimas_acoes[-1]
        alternativas = [a for a in acoes_disponiveis if a != acao_loop]
        
        if alternativas:
            import random
            escolha = random.choice(alternativas)
            self.alternativas_forcadas += 1
            return escolha
        
        return None
    
    def estado(self) -> dict:
        return {
            "em_loop": self.em_loop(),
            "ultimas_acoes": self.ultimas_acoes[-5:],
            "alternativas_forcadas": self.alternativas_forcadas,
        }
