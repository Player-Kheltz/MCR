# EXPERIMENTAL — Use agent_loop como pipeline principal.
# Quando agent_loop falha, o feedback vai para o humano via
# cmd_conselho ou cmd_perguntar. Mantido como referencia.
"""Estrategia D — Humano (pergunta ao usuario).

Ultimo recurso: quando nenhuma estrategia consegue preencher
um gap, pergunta ao usuario. NUNCA gera lixo silenciosamente.

Prioridade: 5 (ultimo recurso)
"""
from __future__ import annotations
from typing import Dict, Any

from strategies.base import BaseStrategy, StrategyResult
from engine.gap_detector import Gap, GapType


class HumanStrategy(BaseStrategy):
    """Estrategia que pergunta ao usuario."""
    
    def __init__(self):
        super().__init__()
        self.nome = "humano"
        self.prioridade = 5
        self._perguntas_pendentes = []
    
    def pode_preencher(self, gap: Gap) -> bool:
        """Humano pode preencher qualquer gap."""
        return True
    
    def preencher(self, gap: Gap, contexto: Dict[str, Any]) -> StrategyResult:
        """Pergunta ao usuario o valor para este gap."""
        pergunta = self._montar_pergunta(gap, contexto)
        
        print(f"\n[HumanStrategy] PERGUNTA: {pergunta}")
        print(f"[HumanStrategy] Informe um valor (ou 'pular' para usar default):")
        
        try:
            resposta = input(">> ").strip()
        except (EOFError, KeyboardInterrupt):
            resposta = ""
        
        if not resposta or resposta.lower() in ('pular', 'skip', ''):
            return StrategyResult(False, None, 0.0, "humano",
                                 "Usuario pulou a pergunta")
        
        return StrategyResult(True, resposta, 1.0, "humano",
                             f"Valor fornecido pelo usuario: {resposta[:50]}...")
    
    def _montar_pergunta(self, gap: Gap, contexto: Dict) -> str:
        """Monta pergunta clara para o usuario."""
        tipo_npc = contexto.get('tipo_npc', gap.tipo_npc)
        profissao = contexto.get('profissao', '')
        
        partes = []
        partes.append(f"Para criar o NPC")
        if profissao:
            partes.append(f" ({profissao})")
        partes.append(f" tipo '{tipo_npc}'")
        
        partes.append(f"\nPreciso de um valor para '{gap.campo}'")
        if gap.valor_atual:
            partes.append(f" (atual: '{gap.valor_atual}')")
        
        partes.append(":")
        
        return ' '.join(partes)


from strategies.base import registrar_estrategia
registrar_estrategia(HumanStrategy())
