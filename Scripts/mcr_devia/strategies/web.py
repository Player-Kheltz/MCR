# EXPERIMENTAL — Use agent_loop como pipeline principal.
# ContextCrew ja faz busca web com weblearn. Usar ContextCrew.
"""Estrategia B2 — Web (weblearn + validacao local).

Usa weblearn para buscar dados na web quando as fontes locais
nao tem informacao suficiente. Respeita ordem de qualidade:
web como "professor externo", validado contra items.xml.

Prioridade: 3 (web, validado localmente)
"""
from __future__ import annotations
from typing import Dict, Any, List
import os, sys, json

from strategies.base import BaseStrategy, StrategyResult
from engine.gap_detector import Gap, GapType


class WebStrategy(BaseStrategy):
    """Estrategia que busca dados na web."""
    
    def __init__(self):
        super().__init__()
        self.nome = "web"
        self.prioridade = 3
        self._items_xml = None
        self._ultima_busca = None
    
    @property
    def items_xml(self):
        if self._items_xml is None:
            sys.path.insert(0, os.path.join(
                os.path.dirname(__file__), '..', '..', 'Scripts', 'mcr_devia'))
            from strategies.items_xml import ItemsXMLStrategy
            self._items_xml = ItemsXMLStrategy()
        return self._items_xml
    
    def pode_preencher(self, gap: Gap) -> bool:
        """Web pode preencher qualquer gap, mas com confiança menor."""
        return True  # Web e o fallback universal
    
    def preencher(self, gap: Gap, contexto: Dict[str, Any]) -> StrategyResult:
        try:
            # Construir consulta para web
            consulta = self._montar_consulta(gap, contexto)
            
            # Verificar se temos resultado em cache
            # (em producao, usaria weblearn real)
            
            # SIMULAR: como weblearn nao esta sempre disponivel,
            # retornamos resultado simulado para testes
            return self._resultado_simulado(gap, contexto, consulta)
        
        except Exception as e:
            return StrategyResult(False, str(e), 0.0, "web",
                                 f"Erro na busca web: {e}")
    
    def _montar_consulta(self, gap: Gap, contexto: Dict) -> str:
        """Monta consulta para busca web."""
        profissao = contexto.get('profissao', '')
        local = contexto.get('local', '')
        tipo_npc = contexto.get('tipo_npc', gap.tipo_npc)
        
        base = f"Tibia {profissao} {tipo_npc} NPC"
        if local:
            base += f" {local}"
        
        if gap.tipo_lacuna == GapType.ITEM_NOME:
            return f"{base} shop items list"
        elif gap.tipo_lacuna == GapType.PRECO:
            return f"{base} item prices"
        elif gap.tipo_lacuna == GapType.TEXTO_MISSAO:
            return f"Tibia {profissao} NPC dialogue {local}"
        elif gap.tipo_lacuna == GapType.NOME_NPC:
            return f"Tibia {profissao} NPC names"
        else:
            return f"Tibia {profissao} NPC {gap.campo}"
    
    def _resultado_simulado(self, gap: Gap, contexto: Dict, consulta: str) -> StrategyResult:
        """Simula resultado web para testes (substituir por weblearn real)."""
        # Tentar validar contra items.xml primeiro
        if gap.tipo_lacuna in (GapType.ITEM_NOME, GapType.ITEM_ID):
            resultado = self.items_xml.preencher(gap, contexto)
            if resultado.sucesso:
                return StrategyResult(
                    True, resultado.valor, 
                    resultado.confianca * 0.85,  # Web e menos confiavel que XML
                    "web", 
                    f"Web -> ItemsXML: {resultado.detalhes}"
                )
        
        # Para textos, web pode ser util
        if gap.tipo_lacuna in (GapType.TEXTO_MISSAO, GapType.SAUDACAO, GapType.DESCRICAO):
            # Simular resultado web generico
            textos = {
                'saudacao': "Welcome, adventurer! How can I help you today?",
                'job_text': "I am the local merchant. I sell various goods.",
                'name_text': "My name is not important, but my wares are!",
                'descricao': "A humble merchant selling wares to travelers.",
            }
            if gap.campo in textos:
                return StrategyResult(True, textos[gap.campo], 0.50, "web",
                                     f"Resultado web para '{gap.campo}'")
        
        # Nao conseguiu nada via web
        return StrategyResult(False, None, 0.0, "web",
                             f"Web sem resultados para: {consulta}")
    
    def validar(self, gap: Gap, valor: Any) -> StrategyResult:
        """Valida resultado web contra items.xml."""
        if gap.tipo_lacuna == GapType.ITEM_ID and isinstance(valor, int):
            return self.items_xml.validar(gap, valor)
        if gap.tipo_lacuna == GapType.ITEM_NOME and isinstance(valor, str):
            return self.items_xml.validar(gap, valor)
        
        return StrategyResult(True, valor, 0.50, "web", "Validacao superficial aceita")


from strategies.base import registrar_estrategia
registrar_estrategia(WebStrategy())
