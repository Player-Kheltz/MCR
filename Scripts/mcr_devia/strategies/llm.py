# EXPERIMENTAL — Use agent_loop como pipeline principal.
# NPCGenerator ja usa LLM como fallback quando nao ha exemplos.
# Mantido como referencia.
"""Estrategia C — LLM (Ollama).

Usa modelo local (qwen14b/7b) para gerar valores criativos
(descricoes, textos, nomes) quando fontes locais e web falham.

Prioridade: 4 (geracao criativa, menos confiavel que dados reais)
"""
from __future__ import annotations
from typing import Dict, Any
import os, sys, json

from strategies.base import BaseStrategy, StrategyResult
from engine.gap_detector import Gap, GapType


class LLMStrategy(BaseStrategy):
    """Estrategia que usa LLM para gerar valores."""
    
    def __init__(self):
        super().__init__()
        self.nome = "llm"
        self.prioridade = 4
        self._ia = None
    
    @property
    def ia(self):
        if self._ia is None:
            sys.path.insert(0, os.path.join(
                os.path.dirname(__file__), '..', '..', 'Scripts', 'mcr_devia'))
            from modulos.ia import IA
            self._ia = IA()
        return self._ia
    
    def pode_preencher(self, gap: Gap) -> bool:
        return gap.tipo_lacuna in {
            GapType.NOME_NPC, GapType.DESCRICAO, GapType.SAUDACAO,
            GapType.TEXTO_MISSAO, GapType.TIPO_ITENS, GapType.NOME_BANCO,
            GapType.NOME_HABILIDADE,
        }
    
    def preencher(self, gap: Gap, contexto: Dict[str, Any]) -> StrategyResult:
        try:
            prompt = self._montar_prompt(gap, contexto)
            
            # Chamar LLM
            resposta = self.ia.fast(prompt, sistema="You are a Tibia NPC creator. Respond in Portuguese.")
            
            if resposta and len(resposta) > 5:
                # Limpar resposta
                valor = resposta.strip().strip('"').strip("'")
                return StrategyResult(True, valor, 0.50, "llm",
                                     f"Gerado por LLM: {valor[:80]}...")
            
            return StrategyResult(False, None, 0.0, "llm",
                                 "LLM retornou resposta vazia")
        
        except Exception as e:
            return StrategyResult(False, str(e), 0.0, "llm",
                                 f"Erro no LLM: {e}")
    
    def _montar_prompt(self, gap: Gap, contexto: Dict) -> str:
        """Monta prompt para o LLM baseado no gap."""
        tipo_npc = contexto.get('tipo_npc', gap.tipo_npc)
        profissao = contexto.get('profissao', '')
        local = contexto.get('local', '')
        nome = contexto.get('nome_npc', '')
        
        if gap.tipo_lacuna == GapType.NOME_NPC:
            return (f"Suggest a name for a {profissao} NPC in Tibia"
                    f"{' from ' + local if local else ''}."
                    f" Return ONLY the name, nothing else."
                    f" Use fantasy/medieval style.")
        
        if gap.tipo_lacuna == GapType.DESCRICAO:
            return (f"Write a one-line description for {nome or 'a'} {profissao} NPC"
                    f" in Tibia{'. Be concise.' if local else ' in ' + local + '.'}"
                    f" Return ONLY the description.")
        
        if gap.tipo_lacuna == GapType.SAUDACAO:
            return (f"Write a greeting message for {nome or 'a'} {profissao} NPC"
                    f" in Tibia. Return ONLY the greeting text.")
        
        if gap.tipo_lacuna == GapType.TEXTO_MISSAO:
            campo = gap.campo.replace('_', ' ')
            return (f"Write a {campo} for a {tipo_npc} NPC in Tibia"
                    f"{' (' + profissao + ')' if profissao else ''}."
                    f" Return ONLY the text, max 100 chars.")
        
        if gap.tipo_lacuna == GapType.TIPO_ITENS:
            return (f"What type of items does a {profissao} sell in Tibia?"
                    f" Return a short phrase like 'weapons and armors'.")
        
        if gap.tipo_lacuna == GapType.NOME_BANCO:
            return (f"Suggest a name for a bank in {'Tibia' + local if local else 'Tibia'}."
                    f" Return ONLY the name.")
        
        return (f"Generate a value for '{gap.campo}' for a {tipo_npc} NPC in Tibia."
                f" Return ONLY the value.")


from strategies.base import registrar_estrategia
registrar_estrategia(LLMStrategy())
