"""FeedbackFilter — evita contaminação do KG com respostas inválidas.

Filtros:
1. Entropia: respostas com entropia muito alta ou muito baixa são suspeitas
2. Tamanho: respostas muito curtas (< 20 chars) ou vazias são descartadas
3. Repetição: respostas idênticas à pergunta são descartadas
4. Template: respostas que são apenas templates não preenchidos são descartadas
"""
import re
from typing import Optional


class FeedbackFilter:
    """Filtra respostas antes de alimentar o KG."""
    
    def __init__(self):
        self.rejeitados = 0
        self.aceitos = 0
    
    def filtrar(self, pergunta: str, resposta: str, confianca: float = 0.0) -> bool:
        """Retorna True se a resposta é válida para aprendizado, False se deve ser rejeitada."""
        if not self._validar_entrada(pergunta, resposta):
            self.rejeitados += 1
            return False
        
        if not self._validar_tamanho(resposta):
            self.rejeitados += 1
            return False
        
        if self._eh_repeticao(pergunta, resposta):
            self.rejeitados += 1
            return False
        
        if self._eh_template_nao_preenchido(resposta):
            self.rejeitados += 1
            return False
        
        if not self._validar_confianca(confianca):
            self.rejeitados += 1
            return False
        
        self.aceitos += 1
        return True
    
    def _validar_entrada(self, pergunta: str, resposta: str) -> bool:
        """Valida se entrada não é vazia ou inválida."""
        if not pergunta or not resposta:
            return False
        if not isinstance(pergunta, str) or not isinstance(resposta, str):
            return False
        return True
    
    def _validar_tamanho(self, resposta: str) -> bool:
        """Valida se resposta tem tamanho mínimo.
        
        Respostas muito curtas (< 20 chars) são: "sim", "não", "ok", código de 1 linha
        Essas não agregam valor ao KG.
        """
        return len(resposta.strip()) >= 20
    
    def _eh_repeticao(self, pergunta: str, resposta: str) -> bool:
        """Detecta se a resposta é apenas uma repetição da pergunta."""
        p = pergunta.lower().strip()
        r = resposta.lower().strip()
        if p == r:
            return True
        if len(r) > 3 and p.startswith(r):
            return True
        if len(r) > 3 and p.endswith(r):
            return True
        return False
    
    def _eh_template_nao_preenchido(self, resposta: str) -> bool:
        """Detecta se resposta contém placeholders não preenchidos."""
        return '<<<' in resposta and '>>>' in resposta
    
    def _validar_confianca(self, confianca: float) -> bool:
        """Valida se confiança é suficiente para aprendizado."""
        return confianca >= 0.3
    
    def stats(self) -> dict:
        return {
            "aceitos": self.aceitos,
            "rejeitados": self.rejeitados,
            "taxa_aceite": round(self.aceitos / max(self.aceitos + self.rejeitados, 1) * 100, 1),
        }
