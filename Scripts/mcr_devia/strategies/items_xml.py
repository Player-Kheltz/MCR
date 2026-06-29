# EXPERIMENTAL — Use agent_loop como pipeline principal.
# ItemDatabase (knowledge/item_database.py) e a versao
# mantida deste conceito. Usar ItemDatabase diretamente.
"""Estrategia B — Items XML (dados catalogados do items.xml).

Usa o ItemDatabase para buscar itens por nome, ID, categoria.
Complementa a estrategia Local quando nao encontra NPCs reais.

Prioridade: 2 (dados catalogados, mas sem contexto de NPC)
"""
from __future__ import annotations
from typing import Dict, Any, List
import os, sys

from strategies.base import BaseStrategy, StrategyResult
from engine.gap_detector import Gap, GapType


class ItemsXMLStrategy(BaseStrategy):
    """Estrategia que usa o items.xml como fonte."""
    
    def __init__(self):
        super().__init__()
        self.nome = "items_xml"
        self.prioridade = 2
        self._db = None
    
    @property
    def db(self):
        if self._db is None:
            sys.path.insert(0, os.path.join(
                os.path.dirname(__file__), '..', '..', 'Scripts', 'mcr_devia'))
            from knowledge.item_database import ItemDatabase
            self._db = ItemDatabase()
        return self._db
    
    def pode_preencher(self, gap: Gap) -> bool:
        return gap.tipo_lacuna in {
            GapType.ITEM_NOME, GapType.ITEM_ID, GapType.PRECO,
            GapType.TIPO_ITENS,
        }
    
    def preencher(self, gap: Gap, contexto: Dict[str, Any]) -> StrategyResult:
        try:
            if gap.tipo_lacuna == GapType.ITEM_NOME:
                return self._buscar_item_nome(gap, contexto)
            elif gap.tipo_lacuna == GapType.ITEM_ID:
                return self._buscar_item_id(gap, contexto)
            elif gap.tipo_lacuna == GapType.PRECO:
                return self._estimar_preco(gap, contexto)
            elif gap.tipo_lacuna == GapType.TIPO_ITENS:
                return self._sugerir_tipo(gap, contexto)
            
            return StrategyResult(False, None, 0.0, "items_xml",
                                 "Tipo nao suportado pelo ItemsXML")
        except Exception as e:
            return StrategyResult(False, str(e), 0.0, "items_xml",
                                 f"Erro: {e}")
    
    def _buscar_item_nome(self, gap: Gap, contexto: Dict) -> StrategyResult:
        """Busca nome de item no items.xml."""
        # Tenta buscar por palavra-chave do contexto
        keywords = contexto.get('palavras_chave', [])
        profissao = contexto.get('profissao', '')
        
        # Buscar itens da profissao
        itens = self.db.sugerir_itens_para_shop(profissao, n_itens=20)
        
        if itens:
            # Encontrar indice correto
            idx = 0
            if '2' in gap.campo:
                idx = min(1, len(itens) - 1)
            elif '3' in gap.campo:
                idx = min(2, len(itens) - 1)
            
            item = itens[idx] if idx < len(itens) else itens[-1]
            
            # Verificar se o nome parece real
            nome = item['nome']
            if nome and not nome.startswith('RESERVED'):
                return StrategyResult(True, nome, 0.70, "items_xml",
                                     f"Item do items.xml: {nome}")
        
        # Fallback: buscar por palavra-chave
        for kw in keywords[:3]:
            resultados = self.db.buscar_por_nome(kw, limite=3)
            if resultados:
                return StrategyResult(True, resultados[0].nome, 0.60, "items_xml",
                                     f"Item encontrado por '{kw}'")
        
        return StrategyResult(False, None, 0.0, "items_xml",
                             "Nenhum item encontrado")
    
    def _buscar_item_id(self, gap: Gap, contexto: Dict) -> StrategyResult:
        """Busca ID de item para um nome conhecido."""
        # Se o contexto tem nome_item, busca o ID
        nome_item = None
        for k, v in contexto.items():
            if k.endswith('_nome') and 'item' in k:
                nome_item = v
                break
        
        if nome_item:
            resultados = self.db.buscar_por_nome(nome_item, limite=1)
            if resultados:
                return StrategyResult(True, resultados[0].id, 0.85, "items_xml",
                                     f"ID {resultados[0].id} para '{nome_item}'")
        
        # Fallback: itens da profissao
        itens = self.db.sugerir_itens_para_shop(
            contexto.get('profissao', ''), n_itens=10)
        if itens:
            idx = len([k for k in contexto.keys() if k.endswith('_id')]) - 1
            idx = max(0, min(idx, len(itens) - 1))
            return StrategyResult(True, itens[idx]['id'], 0.65, "items_xml",
                                 f"ID {itens[idx]['id']} do items.xml")
        
        return StrategyResult(False, None, 0.0, "items_xml",
                             "Nenhum ID encontrado")
    
    def _estimar_preco(self, gap: Gap, contexto: Dict) -> StrategyResult:
        """Estima preco baseado em items.xml e categoria."""
        profissao = contexto.get('profissao', '')
        
        itens = self.db.sugerir_itens_para_shop(profissao, n_itens=10)
        if itens:
            idx = len([k for k in contexto.keys() if k.endswith('_preco')]) - 1
            idx = max(0, min(idx, len(itens) - 1))
            preco = itens[idx]['preco_sugerido']
            return StrategyResult(True, preco, 0.50, "items_xml",
                                 f"Preco estimado: {preco}")
        
        return StrategyResult(True, 100, 0.30, "items_xml", "Preco padrao: 100")
    
    def _sugerir_tipo(self, gap: Gap, contexto: Dict) -> StrategyResult:
        """Sugere tipo de itens baseado na profissao."""
        from knowledge.item_database import MAPA_PROFISSAO_CATEGORIA
        config = MAPA_PROFISSAO_CATEGORIA.get(contexto.get('profissao', '').lower())
        if config:
            return StrategyResult(True, config['tipo_itens'], 0.65, "items_xml",
                                 f"Tipo '{config['tipo_itens']}' para {contexto.get('profissao','')}")
        return StrategyResult(True, "equipment", 0.35, "items_xml", "Tipo generico")
    
    def validar(self, gap: Gap, valor: Any) -> StrategyResult:
        """Valida se um item existe no items.xml."""
        if gap.tipo_lacuna == GapType.ITEM_ID:
            if isinstance(valor, int):
                item = self.db.buscar_por_id(valor)
                if item:
                    return StrategyResult(True, valor, 0.90, "items_xml",
                                         f"ID {valor} validado: {item.nome}")
                return StrategyResult(False, valor, 0.0, "items_xml",
                                     f"ID {valor} NAO existe no items.xml")
        
        if gap.tipo_lacuna == GapType.ITEM_NOME:
            if isinstance(valor, str):
                resultados = self.db.buscar_por_nome(valor, limite=1)
                if resultados:
                    return StrategyResult(True, valor, 0.80, "items_xml",
                                         f"'{valor}' existe no items.xml")
                return StrategyResult(False, valor, 0.0, "items_xml",
                                     f"'{valor}' NAO encontrado no items.xml")
        
        return StrategyResult(True, valor, 0.50, "items_xml", "Validacao padrao")


from strategies.base import registrar_estrategia
registrar_estrategia(ItemsXMLStrategy())
