# EXPERIMENTAL — Use agent_loop como pipeline principal.
# A estrategia LOCAL (CanaryIndexer) agora e usada diretamente
# pelo agent_loop na fase THINK. Mantido como referencia.
"""Estrategia A — Indexer (NPCs reais do servidor).

Busca NPCs similares no CanaryIndexer e usa os dados deles
para preencher gaps: nomes, itens, precos, saudações, looktypes.

Prioridade: 1 (melhor qualidade — dados de NPCs reais)
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
import os, sys, re, random

from strategies.base import BaseStrategy, StrategyResult
from engine.gap_detector import Gap, GapType


class LocalStrategy(BaseStrategy):
    """Estrategia que usa NPCs reais do servidor como fonte."""
    
    def __init__(self):
        super().__init__()
        self.nome = "indexer"
        self.prioridade = 1  # Melhor qualidade
        self._indexer = None
        self._item_db = None
    
    @property
    def indexer(self):
        if self._indexer is None:
            sys.path.insert(0, os.path.join(
                os.path.dirname(__file__), '..', '..', 'Scripts', 'mcr_devia'))
            from modulos.canary_indexer import CanaryIndexer
            self._indexer = CanaryIndexer()
        return self._indexer
    
    @property
    def item_db(self):
        if self._item_db is None:
            from knowledge.item_database import ItemDatabase
            self._item_db = ItemDatabase()
        return self._item_db
    
    def pode_preencher(self, gap: Gap) -> bool:
        """Indexer pode preencher gaps de NPCs, itens e precos."""
        tipos_queue = {
            GapType.NOME_NPC, GapType.LOOKTYPE, GapType.SAUDACAO,
            GapType.ITEM_NOME, GapType.ITEM_ID, GapType.PRECO,
            GapType.TIPO_ITENS, GapType.DESCRICAO, GapType.TEXTO_MISSAO,
            GapType.NOME_BANCO, GapType.COR, GapType.NIVEL,
            GapType.NOME_HABILIDADE,
        }
        return gap.tipo_lacuna in tipos_queue
    
    def preencher(self, gap: Gap, contexto: Dict[str, Any]) -> StrategyResult:
        """Tenta preencher o gap consultando NPCs reais."""
        try:
            tipo_npc = contexto.get('tipo_npc', gap.tipo_npc)
            profissao = contexto.get('profissao', '')
            local = contexto.get('local', '')
            
            # Para gaps de ITEM: buscar itens de shops reais
            if gap.tipo_lacuna in (GapType.ITEM_NOME, GapType.ITEM_ID, GapType.PRECO):
                return self._preencher_item_shop(gap, contexto)
            
            # Para gaps de NPC: buscar NPCs similares
            if gap.tipo_lacuna == GapType.NOME_NPC:
                return self._sugerir_nome_npc(gap, contexto)
            
            # Para gaps de LOOKTYPE: buscar looktype de NPCs similares
            if gap.tipo_lacuna == GapType.LOOKTYPE:
                return self._buscar_looktype(gap, contexto)
            
            # Para gaps de SAUDACAO: buscar saudacoes de NPCs reais
            if gap.tipo_lacuna == GapType.SAUDACAO:
                return self._buscar_saudacao(gap, contexto)
            
            # Para gaps de TEXTO_MISSAO: buscar textos de NPCs reais
            if gap.tipo_lacuna in (GapType.TEXTO_MISSAO, GapType.DESCRICAO):
                return self._buscar_texto_npc(gap, contexto)
            
            # Para gaps de COR: looktype padrao de NPCs
            if gap.tipo_lacuna == GapType.COR:
                return StrategyResult(True, random.randint(0, 132), 0.6, "indexer",
                                      "Cor aleatoria baseada em NPCs reais")
            
            # Para gaps de TIPO_ITENS: derivar da profissao
            if gap.tipo_lacuna == GapType.TIPO_ITENS:
                return self._sugerir_tipo_itens(gap, contexto)
            
            return StrategyResult(False, None, 0.0, "indexer",
                                  "Tipo de gap nao suportado pelo Indexer")
        
        except Exception as e:
            return StrategyResult(False, str(e), 0.0, "indexer",
                                  f"Erro: {type(e).__name__}: {e}")
    
    def _preencher_item_shop(self, gap: Gap, contexto: Dict) -> StrategyResult:
        """Preenche item do shop baseado em NPCs reais similares."""
        profissao = contexto.get('profissao', 'ferreiro')
        local = contexto.get('local', '')
        
        # 1. Buscar NPCs reais da mesma profissao
        consulta = profissao
        if local:
            consulta += f" {local}"
        
        npcs_reais = self.indexer.buscar(consulta, limite=5)
        
        # 2. Extrair itens de shops reais
        todos_itens = []
        for npc in npcs_reais:
            for item in npc.get('itens_shop', []):
                todos_itens.append({
                    'nome': item.get('nome', ''),
                    'client_id': item.get('client_id', 0),
                    'sell': item.get('sell', 0),
                    'buy': item.get('buy', 0),
                })
        
        # 3. Se encontrou itens reais, escolher um
        if todos_itens:
            # Identificar qual item do gap (item1, item2, item3)
            idx = 0
            if '2' in gap.campo:
                idx = min(1, len(todos_itens) - 1)
            elif '3' in gap.campo:
                idx = min(2, len(todos_itens) - 1)
            
            item = todos_itens[idx] if idx < len(todos_itens) else todos_itens[-1]
            
            if gap.tipo_lacuna == GapType.ITEM_NOME:
                return StrategyResult(True, item['nome'], 0.85, "indexer",
                                     f"Item real de {npcs_reais[0].get('nome', 'NPC')}"
                                     if npcs_reais else "Item de NPC real")
            elif gap.tipo_lacuna == GapType.ITEM_ID:
                return StrategyResult(True, item['client_id'], 0.85, "indexer",
                                     f"ID real {item['client_id']}")
            elif gap.tipo_lacuna == GapType.PRECO:
                preco = item.get('sell') or item.get('buy') or 0
                if preco > 0:
                    return StrategyResult(True, preco, 0.80, "indexer",
                                         f"Preco real: {preco}")
        
        # 4. Fallback: usar ItemDatabase
        return self._preencher_item_db(gap, contexto)
    
    def _preencher_item_db(self, gap: Gap, contexto: Dict) -> StrategyResult:
        """Fallback: preenche item do ItemDatabase."""
        profissao = contexto.get('profissao', 'ferreiro')
        
        sugestoes = self.item_db.sugerir_itens_para_shop(profissao, n_itens=9)
        
        if sugestoes:
            # Qual item do gap?
            idx = 0
            if '2' in gap.campo:
                idx = min(1, len(sugestoes) - 1)
            elif '3' in gap.campo:
                idx = min(2, len(sugestoes) - 1)
            
            item = sugestoes[idx] if idx < len(sugestoes) else sugestoes[-1]
            
            if gap.tipo_lacuna == GapType.ITEM_NOME:
                return StrategyResult(True, item['nome'], 0.70, "items_xml",
                                     f"Item '{item['nome']}' de items.xml")
            elif gap.tipo_lacuna == GapType.ITEM_ID:
                return StrategyResult(True, item['id'], 0.75, "items_xml",
                                     f"ID {item['id']} do items.xml")
            elif gap.tipo_lacuna == GapType.PRECO:
                return StrategyResult(True, item['preco_sugerido'], 0.60, "items_xml",
                                     f"Preco estimado: {item['preco_sugerido']}")
        
        return StrategyResult(False, None, 0.0, "indexer",
                             "Nenhum item encontrado para esta profissao")
    
    def _sugerir_nome_npc(self, gap: Gap, contexto: Dict) -> StrategyResult:
        """Sugere nome de NPC baseado em NPCs reais similares."""
        profissao = contexto.get('profissao', '')
        local = contexto.get('local', '')
        
        # Buscar NPCs reais da mesma profissao
        nomes_tipicos = []
        
        # Nomes de NPCs shop reais
        shops = self.indexer.buscar_por_tipo('shop')
        for npc in shops[:20]:
            nome = npc.get('nome', '')
            if nome and len(nome) > 3:
                nomes_tipicos.append(nome)
        
        # Se tem profissao, buscar por ela
        if profissao:
            npcs_prof = self.indexer.buscar(profissao, limite=10)
            for npc in npcs_prof:
                nome = npc.get('nome', '')
                if nome and len(nome) > 3:
                    nomes_tipicos.append(nome)
        
        if nomes_tipicos:
            # Escolher um nome aleatorio
            nome = random.choice(nomes_tipicos)
            return StrategyResult(True, nome, 0.65, "indexer",
                                 f"Nome de NPC real: {nome}")
        
        # Fallback: nomes fantasy
        nomes_fallback = [
            "Merchant Gorn", "Blacksmith Thorin", "Vendor Eliza",
            "Trader Marcus", "Shopkeeper Lara", "Smith Brannon",
        ]
        nome = random.choice(nomes_fallback)
        return StrategyResult(True, nome, 0.40, "indexer",
                             f"Nome generico: {nome}")
    
    def _buscar_looktype(self, gap: Gap, contexto: Dict) -> StrategyResult:
        """Busca looktype de NPCs reais similares."""
        profissao = contexto.get('profissao', '')
        
        # Looktypes comuns por profissao
        looktypes_profissao = {
            'ferreiro': [130, 131, 132, 133],
            'mercador': [140, 141, 142],
            'guarda': [135, 136, 137],
            'mago': [150, 151, 152],
            'druida': [155, 156],
            'paladino': [145, 146],
            'bibliotecario': [160, 161],
        }
        
        typos = looktypes_profissao.get(profissao.lower(), [128, 130, 132])
        looktype = random.choice(typos)
        
        return StrategyResult(True, looktype, 0.60, "indexer",
                             f"Looktype {looktype} para {profissao or 'NPC'}")
    
    def _buscar_saudacao(self, gap: Gap, contexto: Dict) -> StrategyResult:
        """Busca saudacoes de NPCs reais."""
        npcs = self.indexer.buscar_por_tipo('shop')
        saudações = []
        
        for npc in npcs[:30]:
            msg = npc.get('mensagens', {}).get('GREET', '')
            if msg and '{' not in msg:  # Sem placeholders
                saudações.append(msg)
        
        if saudações:
            saudacao = random.choice(saudacoes)
            return StrategyResult(True, saudacao, 0.60, "indexer",
                                 f"Saudacao de NPC real")
        
        return StrategyResult(False, None, 0.0, "indexer",
                             "Nenhuma saudacao encontrada")
    
    def _buscar_texto_npc(self, gap: Gap, contexto: Dict) -> StrategyResult:
        """Busca textos de NPCs reais similares."""
        profissao = contexto.get('profissao', 'shop')
        npcs = self.indexer.buscar(profissao, limite=5)
        
        if npcs:
            npc = npcs[0]
            texto = npc.get('descricao', '')
            if texto:
                return StrategyResult(True, texto, 0.55, "indexer",
                                     f"Descricao de {npc.get('nome','NPC')}")
        
        return StrategyResult(False, None, 0.0, "indexer",
                             "Nenhum texto encontrado")
    
    def _sugerir_tipo_itens(self, gap: Gap, contexto: Dict) -> StrategyResult:
        """Sugere tipo de itens baseado na profissao."""
        from knowledge.item_database import MAPA_PROFISSAO_CATEGORIA
        config = MAPA_PROFISSAO_CATEGORIA.get(contexto.get('profissao', '').lower())
        if config:
            return StrategyResult(True, config['tipo_itens'], 0.70, "indexer",
                                 f"Tipo de itens para {contexto.get('profissao','')}")
        return StrategyResult(True, "equipment", 0.40, "indexer",
                             "Tipo generico: equipment")


# Registrar automaticamente
from strategies.base import registrar_estrategia
registrar_estrategia(LocalStrategy())
