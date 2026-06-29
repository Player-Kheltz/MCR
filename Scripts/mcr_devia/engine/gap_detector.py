# EXPERIMENTAL — Use agent_loop como pipeline principal.
# GapDetector pode ser util como ferramenta de validacao,
# mas nao como parte do pipeline principal. agent_loop ja
# tem LuaValidator para detectar problemas no codigo gerado.
"""GapDetector — Detecta lacunas em templates de criacao.

Analisa placeholders e identifica quais sao genericos/lixo
(ex: "example item", 3003) e classifica cada lacuna por tipo,
confianca e estrategia recomendada.

Uso:
    from engine.gap_detector import GapDetector
    gaps = GapDetector.analisar_placeholders(tipo_npc, placeholders)
    for gap in gaps:
        print(gap.campo, gap.tipo_lacuna, gap.confianca)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import re, os, sys, importlib


# ============================================================
# TIPOS DE LACUNA
# ============================================================

class GapType(Enum):
    ITEM_NOME = "item_nome"         # Nome de item (ex: "example item")
    ITEM_ID = "item_id"             # ID de item (ex: 3003, 3457)
    PRECO = "preco"                 # Preco de item (ex: 50, 10)
    NOME_NPC = "nome_npc"           # Nome de NPC (ex: "Vendedor Ferronius")
    DESCRICAO = "descricao"         # Descricao textual
    SAUDACAO = "saudacao"           # Mensagem de saudacao
    TEXTO_MISSAO = "texto_missao"   # Texto de quest/dialogo
    NIVEL = "nivel"                 # Nivel/level (ex: 20)
    STORAGE = "storage"             # Storage value
    NUMERO = "numero"               # Numero generico
    COR = "cor"                     # Cor (ex: lookHead, lookBody)
    LOOKTYPE = "looktype"           # Aparencia
    TIPO_ITENS = "tipo_itens"       # Categoria de itens
    NOME_BANCO = "nome_banco"       # Nome de banco
    NOME_HABILIDADE = "nome_habilidade"  # Nome de skill/spell
    TEXTO_GENERICO = "texto_generico"    # Texto placeholder
    DESCONHECIDO = "desconhecido"


# ============================================================
# PRIORIDADE DE PREENCHIMENTO
# ============================================================

PRIORIDADE_PREENCHIMENTO = {
    GapType.ITEM_ID: 1,      # Mais critico: sem ID, sem item
    GapType.ITEM_NOME: 1,    # Nome sem ID nao serve
    GapType.PRECO: 2,        # Preco errado quebra economia
    GapType.NOME_NPC: 2,     # Nome generico parece incompleto
    GapType.DESCRICAO: 3,    # Descritivo, menos critico
    GapType.NIVEL: 3,
    GapType.STORAGE: 3,
    GapType.TEXTO_MISSAO: 4, # Texto pode ser generico
    GapType.SAUDACAO: 4,
    GapType.TIPO_ITENS: 3,
    GapType.LOOKTYPE: 4,     # Looktype 130 eh generico mas funcional
    GapType.COR: 5,          # Cor 57/116/97/114 eh padrao funcional
    GapType.NOME_BANCO: 4,
    GapType.NOME_HABILIDADE: 3,
    GapType.TEXTO_GENERICO: 5,
}


# ============================================================
# ESTRATEGIAS PARA CADA TIPO
# ============================================================

ESTRATEGIAS_PREENCHIMENTO = {
    # (tipo_npc, gap_type) -> lista de estrategias
    ('shop', GapType.ITEM_NOME): ['local', 'web', 'llm', 'humano'],
    ('shop', GapType.ITEM_ID): ['items_xml', 'local', 'web', 'llm'],
    ('shop', GapType.PRECO): ['local', 'items_xml', 'web', 'llm'],
    ('shop', GapType.TIPO_ITENS): ['local', 'web', 'llm'],
    ('shop', GapType.NOME_NPC): ['local', 'web', 'llm'],
    ('quest', GapType.TEXTO_MISSAO): ['web', 'llm', 'humano'],
    ('quest', GapType.STORAGE): ['llm', 'humano'],
    ('quest', GapType.ITEM_ID): ['items_xml', 'local'],
    ('quest', GapType.ITEM_NOME): ['local', 'llm'],
    ('generic', GapType.DESCRICAO): ['llm', 'web'],
    ('generic', GapType.SAUDACAO): ['llm', 'web'],
    ('generic', GapType.TEXTO_GENERICO): ['llm', 'web'],
}


# ============================================================
# VALORES "LIXO" / GENÉRICOS
# ============================================================

# Padrões que indicam placeholder generico / nao preenchido
PADROES_LIXO = [
    r'^example\s', r'^another\s', r'^third\s', r'^sample\s',
    r'^generic\s', r'^test\s', r'^placeholder\s', r'^some\s',
    r'^item\d', r'^TODO', r'^todo', r'^\s*$',
    r'^insert\s', r'^your\s', r'^unknown\s',
]

ITENS_ID_LIXO = {3003, 3457, 2920, 3031, 1, 0, 9999, 100, 200, 500, 1000}
# 3031 = gold coin (valido mas usado como lixo padrao)

TEXTOS_LIXO = [
    'example item', 'another item', 'third item',
    'I need your help!', 'Have you completed the task yet?',
    'Thank you! Now go and complete the task.',
    'Well done! Here is your reward.',
    'You still need to bring me the required item.',
    'I can teach you a few things. What would you like to learn?',
    'Here are the spells I can teach you.',
    'A wise choice. Let me teach you.',
    'Excellent! Let us begin the training.',
    'You may pass.',
    'You need level %d to pass.',
    'I am just a humble traveler.',
    'Explore the world and you shall find what you seek.',
    'Safe travels!',
    'Just ask me for a trade to see my offers.',
    'Sorry, I need a specific amount.',
    'How much would you like to deposit?',
    'How much would you like to withdraw?',
    'Halt! State your business.',
    'Welcome, pupil! Ready to improve your skills?',
    'Hello there, traveler!',
]


# ============================================================
# DATACLASS GAP
# ============================================================

@dataclass
class Gap:
    """Uma lacuna identificada em um template."""
    campo: str                      # Nome do placeholder (ex: "item1_nome")
    valor_atual: Any                # Valor atual (ex: "example item")
    tipo_lacuna: GapType            # Tipo da lacuna
    confianca: float                # 0.0 a 1.0 (certeza que é lixo)
    prioridade: int                 # 1 (critico) a 5 (cosmetico)
    estrategias: List[str] = field(default_factory=list)  # Estrategias viaveis
    contexto: str = ""              # Contexto (ex: "item do shop")
    tipo_npc: str = "shop"          # Tipo de NPC
    resolvido: bool = False         # Se ja foi preenchido
    valor_final: Any = None         # Valor preenchido
    
    def to_dict(self) -> Dict:
        return {
            'campo': self.campo,
            'valor_atual': str(self.valor_atual)[:50],
            'tipo_lacuna': self.tipo_lacuna.value,
            'confianca': self.confianca,
            'prioridade': self.prioridade,
            'estrategias': self.estrategias,
            'contexto': self.contexto,
            'resolvido': self.resolvido,
        }


# ============================================================
# GAP DETECTOR
# ============================================================

class GapDetector:
    """Detecta lacunas em placeholders de templates."""
    
    # Mapa: placeholder -> (tipo_lacuna, contexto)
    MAPA_CAMPO_TIPO = {
        # Shop
        'item1_nome': (GapType.ITEM_NOME, 'Item #1 do shop'),
        'item1_id': (GapType.ITEM_ID, 'ID do Item #1'),
        'item1_preco': (GapType.PRECO, 'Preco de compra do Item #1'),
        'item2_nome': (GapType.ITEM_NOME, 'Item #2 do shop'),
        'item2_id': (GapType.ITEM_ID, 'ID do Item #2'),
        'item2_preco': (GapType.PRECO, 'Preco de venda do Item #2'),
        'item3_nome': (GapType.ITEM_NOME, 'Item #3 do shop'),
        'item3_id': (GapType.ITEM_ID, 'ID do Item #3'),
        'item3_preco': (GapType.PRECO, 'Preco de compra do Item #3'),
        'tipo_itens': (GapType.TIPO_ITENS, 'Categoria de itens vendidos'),
        
        # Nome/descricao
        'nome': (GapType.NOME_NPC, 'Nome do NPC'),
        'descricao': (GapType.DESCRICAO, 'Descricao do NPC'),
        'saudacao': (GapType.SAUDACAO, 'Mensagem de saudacao'),
        'looktype': (GapType.LOOKTYPE, 'ID da aparencia (outfit)'),
        'lookHead': (GapType.COR, 'Cor da cabeca'),
        'lookBody': (GapType.COR, 'Cor do corpo'),
        'lookLegs': (GapType.COR, 'Cor das pernas'),
        'lookFeet': (GapType.COR, 'Cor dos pes'),
        
        # Quest
        'quest_storage': (GapType.STORAGE, 'Storage da quest'),
        'quest_term': (GapType.TEXTO_MISSAO, 'Termo da quest'),
        'quest_start_text': (GapType.TEXTO_MISSAO, 'Texto inicial da quest'),
        'quest_progress_text': (GapType.TEXTO_MISSAO, 'Texto de progresso'),
        'quest_accept_text': (GapType.TEXTO_MISSAO, 'Texto ao aceitar quest'),
        'quest_complete_text': (GapType.TEXTO_MISSAO, 'Texto ao completar quest'),
        'quest_missing_item_text': (GapType.TEXTO_MISSAO, 'Texto de item faltante'),
        'reward_item_id': (GapType.ITEM_ID, 'ID do item de recompensa'),
        
        # Bank
        'bank_name': (GapType.NOME_BANCO, 'Nome do banco'),
        
        # Gate
        'gate_level': (GapType.NIVEL, 'Nivel minimo para passar'),
        'gate_open_text': (GapType.TEXTO_MISSAO, 'Texto ao liberar passagem'),
        'gate_blocked_text': (GapType.TEXTO_MISSAO, 'Texto ao bloquear passagem'),
        
        # Trainer
        'train_offer_text': (GapType.TEXTO_MISSAO, 'Texto de oferta de treino'),
        'train_spell_text': (GapType.TEXTO_MISSAO, 'Texto sobre spells'),
        'train_accept_text': (GapType.TEXTO_MISSAO, 'Texto ao aceitar treino'),
        'train_spell_accept_text': (GapType.TEXTO_MISSAO, 'Texto ao aceitar spell'),
        
        # Dialogue
        'job_text': (GapType.TEXTO_MISSAO, 'Texto sobre trabalho'),
        'name_text': (GapType.TEXTO_MISSAO, 'Texto sobre nome'),
        'hint_text': (GapType.TEXTO_MISSAO, 'Texto de dica'),
        'farewell_text': (GapType.TEXTO_MISSAO, 'Texto de despedida'),
    }
    
    @staticmethod
    def analisar_placeholders(tipo_npc: str, placeholders: Dict) -> List[Gap]:
        """Analisa placeholders e retorna lista de gaps detectados."""
        gaps = []
        
        for campo, valor in placeholders.items():
            # Pular campos que nao sao placeholders de texto
            if campo.startswith('_'):
                continue
            
            # Detectar tipo da lacuna
            tipo_info = GapDetector.MAPA_CAMPO_TIPO.get(
                campo, (GapType.DESCONHECIDO, 'Campo generico')
            )
            tipo_lacuna = tipo_info[0]
            contexto = tipo_info[1]
            
            # Calcular confianca
            confianca = GapDetector._calcular_confianca(campo, valor, tipo_lacuna)
            
            # Prioridade
            prioridade = PRIORIDADE_PREENCHIMENTO.get(tipo_lacuna, 5)
            
            # Estrategias
            estrategias = GapDetector._sugerir_estrategias(tipo_npc, tipo_lacuna)
            
            # So cria gap se confianca > 0.3 (ignora valores aparentemente reais)
            if confianca > 0.3:
                gaps.append(Gap(
                    campo=campo,
                    valor_atual=valor,
                    tipo_lacuna=tipo_lacuna,
                    confianca=round(confianca, 2),
                    prioridade=prioridade,
                    estrategias=estrategias,
                    contexto=contexto,
                    tipo_npc=tipo_npc,
                ))
        
        # Ordenar por prioridade (1 = mais critico)
        gaps.sort(key=lambda g: (g.prioridade, -g.confianca))
        
        return gaps
    
    @staticmethod
    def _calcular_confianca(campo: str, valor: Any, tipo_lacuna: GapType) -> float:
        """Calcula o nivel de confianca de que este placeholder e lixo."""
        confianca = 0.0
        
        if valor is None:
            return 0.9
        
        valor_str = str(valor).strip()
        if not valor_str:
            return 0.9
        
        valor_lower = valor_str.lower()
        
        # 1. Verificar padroes de lixo textual
        for padrao in PADROES_LIXO:
            if re.search(padrao, valor_lower):
                confianca = max(confianca, 0.85)
                break
        
        # 2. Verificar textos lixo conhecidos
        for texto_lixo in TEXTOS_LIXO:
            if texto_lixo.lower() in valor_lower or valor_lower in texto_lixo.lower():
                if len(valor_str) > 5:
                    confianca = max(confianca, 0.80)
                break
        
        # 3. Verificar IDs lixo
        if tipo_lacuna in (GapType.ITEM_ID, GapType.NUMERO):
            try:
                num = int(valor)
                if num in ITENS_ID_LIXO:
                    confianca = max(confianca, 0.75)
                elif num <= 10:
                    confianca = max(confianca, 0.40)
            except (ValueError, TypeError):
                if tipo_lacuna == GapType.ITEM_ID:
                    confianca = max(confianca, 0.90)  # ID nao numerico = certeza de lixo
                pass
        
        # 4. Verificar placeholders aninhados nao resolvidos
        if isinstance(valor, str) and '{' in valor and '}' in valor:
            confianca = max(confianca, 0.60)
        
        # 5. Verificar se parece nome real de NPC
        if tipo_lacuna == GapType.NOME_NPC:
            if ' ' in valor_str and len(valor_str) > 5:
                # "Vendedor Ferronius" - parece real
                confianca = min(confianca, 0.30)
            elif len(valor_str) > 8:
                confianca = min(confianca, 0.40)
            else:
                confianca = max(confianca, 0.50)
        
        # 6. Verificar tipo itens
        if tipo_lacuna == GapType.TIPO_ITENS:
            if valor_lower in ['equipment', 'weapons', 'armors', 'items', 'supplies']:
                confianca = min(confianca, 0.50)  # Generico mas aceitavel
            else:
                confianca = max(confianca, 0.30)
        
        # 7. Verificar looktypes
        if tipo_lacuna == GapType.LOOKTYPE:
            if isinstance(valor, int):
                if valor == 130:  # Looktype padrao generico
                    confianca = max(confianca, 0.40)
                elif valor > 0:
                    confianca = min(confianca, 0.20)  # Looktype especifico, provavelmente real
                else:
                    confianca = max(confianca, 0.60)
        
        # 8. Verificar nivel
        if tipo_lacuna == GapType.NIVEL:
            if isinstance(valor, int):
                if valor == 20:  # Level padrao generico
                    confianca = max(confianca, 0.40)
                elif 1 <= valor <= 9999:
                    confianca = min(confianca, 0.20)  # Nivel especifico
                else:
                    confianca = max(confianca, 0.50)
        
        # 9. Verificar storage
        if tipo_lacuna == GapType.STORAGE:
            if 'Quest.Custom.' in valor_str:
                confianca = max(confianca, 0.60)
        
        # 10. Verificar precos
        if tipo_lacuna == GapType.PRECO:
            try:
                preco = int(valor)
                if preco in [2, 10, 50]:  # Precos padrao do template
                    confianca = max(confianca, 0.65)
                elif preco <= 1:
                    confianca = max(confianca, 0.80)
            except (ValueError, TypeError):
                confianca = max(confianca, 0.60)
        
        return min(confianca, 0.98)
    
    @staticmethod
    def _sugerir_estrategias(tipo_npc: str, tipo_lacuna: GapType) -> List[str]:
        """Sugere estrategias de preenchimento para esta lacuna."""
        # Tenta match exato
        estrategias = ESTRATEGIAS_PREENCHIMENTO.get((tipo_npc, tipo_lacuna), None)
        if estrategias:
            return list(estrategias)
        
        # Tenta com 'generic'
        estrategias = ESTRATEGIAS_PREENCHIMENTO.get(('generic', tipo_lacuna), None)
        if estrategias:
            return list(estrategias)
        
        # Fallback: ordem padrao
        return ['local', 'items_xml', 'web', 'llm', 'humano']
    
    @staticmethod
    def analisar_codigo_fonte(codigo: str, tipo_npc: str = 'shop') -> List[str]:
        """Analisa codigo Lua e detecta placeholders nao resolvidos."""
        placeholders_encontrados = re.findall(r'\{(\w+)\}', codigo)
        if placeholders_encontrados:
            return list(set(placeholders_encontrados))
        return []
    
    @staticmethod
    def extrair_gaps_de_npc_generator(tipo_npc: str) -> List[Gap]:
        """Extrai gaps diretamente dos defaults do NPCGenerator.
        
        Usa o NPCGenerator para gerar placeholders e depois analisa.
        """
        try:
            from modulos.npc_generator import NPCGenerator
            gen = NPCGenerator()
            placeholders = gen._placeholders_por_tipo(tipo_npc, 'NPC generico', {'nome': 'NPC Exemplo'})
            # Adiciona placeholders base
            placeholders['nome'] = 'NPC Exemplo'
            placeholders['descricao'] = 'Shop NPC - NPC Exemplo'
            placeholders['saudacao'] = 'Welcome!'
            placeholders['looktype'] = 130
            return GapDetector.analisar_placeholders(tipo_npc, placeholders)
        except Exception as e:
            # Fallback: gaps manuais
            return GapDetector._gaps_fallback(tipo_npc)
    
    @staticmethod
    def _gaps_fallback(tipo_npc: str) -> List[Gap]:
        """Gaps manuais quando NPCGenerator nao esta disponivel."""
        gaps_manuais = {
            'shop': [
                Gap('item1_nome', 'example item', GapType.ITEM_NOME, 0.95, 1, ['local', 'items_xml']),
                Gap('item1_id', 3003, GapType.ITEM_ID, 0.85, 1, ['items_xml', 'local']),
                Gap('item1_preco', 50, GapType.PRECO, 0.75, 2, ['local', 'items_xml']),
                Gap('item2_nome', 'another item', GapType.ITEM_NOME, 0.95, 1, ['local', 'items_xml']),
                Gap('item2_id', 3457, GapType.ITEM_ID, 0.85, 1, ['items_xml', 'local']),
                Gap('item2_preco', 10, GapType.PRECO, 0.75, 2, ['local', 'items_xml']),
                Gap('item3_nome', 'third item', GapType.ITEM_NOME, 0.95, 1, ['local', 'items_xml']),
                Gap('item3_id', 2920, GapType.ITEM_ID, 0.85, 1, ['items_xml', 'local']),
                Gap('item3_preco', 2, GapType.PRECO, 0.75, 2, ['local', 'items_xml']),
                Gap('tipo_itens', 'equipment', GapType.TIPO_ITENS, 0.50, 3, ['local', 'llm']),
                Gap('nome', 'NPC', GapType.NOME_NPC, 0.70, 2, ['llm', 'local']),
            ],
            'quest': [
                Gap('quest_storage', 'Quest.Custom.NPC_EXEMPLO', GapType.STORAGE, 0.60, 3, ['llm']),
                Gap('quest_start_text', 'I need your help!', GapType.TEXTO_MISSAO, 0.80, 4, ['web', 'llm']),
                Gap('reward_item_id', 3031, GapType.ITEM_ID, 0.75, 1, ['items_xml', 'local']),
            ],
            'gate': [
                Gap('gate_level', 20, GapType.NIVEL, 0.40, 3, ['llm', 'web']),
                Gap('gate_open_text', 'You may pass.', GapType.TEXTO_MISSAO, 0.80, 4, ['llm']),
            ],
            'trainer': [
                Gap('train_offer_text', 'I can teach you...', GapType.TEXTO_MISSAO, 0.80, 4, ['llm', 'web']),
            ],
            'dialogue': [
                Gap('job_text', 'I am just a humble traveler.', GapType.TEXTO_MISSAO, 0.80, 4, ['llm']),
                Gap('name_text', 'My name is NPC Exemplo.', GapType.TEXTO_MISSAO, 0.80, 4, ['llm']),
            ],
            'bank': [],
        }
        return gaps_manuais.get(tipo_npc, [])


# ============================================================
# FUNCAO UNICA DE ENTRADA
# ============================================================

def detectar_gaps(tipo_npc: str, placeholders: Optional[Dict] = None) -> List[Gap]:
    """Funcao unica de entrada para deteccao de gaps.
    
    Se placeholders for None, extrai do NPCGenerator.
    """
    if placeholders:
        return GapDetector.analisar_placeholders(tipo_npc, placeholders)
    else:
        return GapDetector.extrair_gaps_de_npc_generator(tipo_npc)


# ============================================================
# TESTE
# ============================================================

if __name__ == '__main__':
    print("=== TESTE GAP DETECTOR ===\n")
    
    for tipo in ['shop', 'quest', 'gate', 'trainer', 'dialogue', 'bank']:
        print(f"\n--- NPC tipo: {tipo} ---")
        gaps = detectar_gaps(tipo)
        if not gaps:
            print("  Nenhum gap detectado")
            continue
        for g in gaps[:10]:
            print(f"  [{g.prioridade}] {g.campo} = '{g.valor_atual}'")
            print(f"       Tipo: {g.tipo_lacuna.value} (conf: {g.confianca})")
            print(f"       Estrategias: {g.estrategias}")
