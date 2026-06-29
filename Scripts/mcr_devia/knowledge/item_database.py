"""ItemDatabase — Wrapper completo sobre items.xml do Canary.

Fornece:
- Busca por nome (fuzzy parcial)
- Busca por ID
- Busca por categoria (primarytype)
- Cache LRU integrado
- Preco medio por categoria baseado em NPCs reais (quando disponivel)

Uso:
    from knowledge.item_database import ItemDatabase
    db = ItemDatabase()
    itens = db.buscar_por_categoria('sword weapons')
    item = db.buscar_por_id(20341)
    itens = db.buscar_por_nome('espada')
"""
from __future__ import annotations
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field
from functools import lru_cache
import re, os, json
from collections import defaultdict

# Path do items.xml: knowledge/ -> mcr_devia/ -> Scripts/ -> Projeto MCR/
_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
ITEMS_XML = os.path.join(_BASE, 'Canary', 'data', 'items', 'items.xml')


# ============================================================
# DATACLASS ITEM
# ============================================================

@dataclass
class Item:
    """Representacao de um item do Tibia."""
    id: int
    nome: str
    categoria: str = ""
    artigo: str = ""
    plural: str = ""
    peso: float = 0.0
    tipo: str = ""                    # "weapon", "armor", "container", etc
    atributos: Dict[str, str] = field(default_factory=dict)
    
    # Metadados de NPC (preenchidos pelo CanaryIndexer)
    preco_compra: Optional[int] = None
    preco_venda: Optional[int] = None
    
    @property
    def nome_normalizado(self) -> str:
        """Nome em lowercase sem acentos."""
        n = self.nome.lower()
        replacements = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
            'é': 'e', 'ê': 'e', 'í': 'i', 'ó': 'o', 'ô': 'o', 'õ': 'o',
            'ú': 'u', 'ü': 'u', 'ç': 'c',
        }
        for old, new in replacements.items():
            n = n.replace(old, new)
        return n
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'nome': self.nome,
            'categoria': self.categoria,
            'peso': self.peso,
            'preco_compra': self.preco_compra,
            'preco_venda': self.preco_venda,
        }


# ============================================================
# MAPA DE CATEGORIAS PARA SHOP
# ============================================================

# Mapa: profissao -> (categorias_items, descricao, tipo_npc)
MAPA_PROFISSAO_CATEGORIA = {
    'ferreiro': {
        'categorias': ['sword weapons', 'axe weapons', 'club weapons',
                       'armors', 'shields', 'helmets', 'legs', 'boots',
                       'fist weapons'],
        'descricao': 'Ferreiro que vende armas e armaduras',
        'tipo_itens': 'weapons and armors',
    },
    'alquimista': {
        'categorias': ['potions', 'liquids', 'creature products', 'magical items'],
        'descricao': 'Alquimista que vende pocoes e ingredientes',
        'tipo_itens': 'potions and ingredients',
    },
    'mercador': {
        'categorias': ['valuables', 'containers', 'tools', 'tools (objects)',
                       'light sources', 'documents and papers'],
        'descricao': 'Mercador de itens diversos',
        'tipo_itens': 'general goods',
    },
    'bibliotecario': {
        'categorias': ['books', 'spellbooks', 'documents and papers', 'magical items'],
        'descricao': 'Bibliotecario que vende livros e pergaminhos',
        'tipo_itens': 'books and scrolls',
    },
    'guarda': {
        'categorias': ['sword weapons', 'shields', 'armors', 'helmets'],
        'descricao': 'Guarda que vende equipamento militar',
        'tipo_itens': 'military equipment',
    },
    'mago': {
        'categorias': ['wands', 'rods', 'spellbooks', 'magical items',
                       'attack runes', 'support runes', 'healing runes', 'amulets and necklaces'],
        'descricao': 'Mago que vende itens magicos',
        'tipo_itens': 'magical items',
    },
    'druida': {
        'categorias': ['wands', 'rods', 'healing runes', 'support runes',
                       'creature products', 'plants and herbs', 'flowers', 'mushrooms'],
        'descricao': 'Druida que vende itens naturais e runas',
        'tipo_itens': 'natural remedies',
    },
    'paladino': {
        'categorias': ['distance weapons', 'ammunition', 'armors', 'shields',
                       'sword weapons', 'boots', 'quivers'],
        'descricao': 'Paladino que vende equipamento de combate a distancia',
        'tipo_itens': 'distance combat gear',
    },
    'random': {
        'categorias': ['valuables', 'containers', 'food', 'drinks', 'tools'],
        'descricao': 'Vendedor de itens diversos',
        'tipo_itens': 'miscellaneous',
    },
}


# ============================================================
# DATABASE
# ============================================================

class ItemDatabase:
    """Database de itens do Tibia, carregada do items.xml."""
    
    _instance = None
    _items_por_id: Dict[int, Item] = {}
    _items_por_categoria: Dict[str, List[Item]] = {}
    _items_todos: List[Item] = []
    _categorias: List[str] = []
    _carregado = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._carregado:
            self._carregar()
    
    def _carregar(self):
        """Carrega items do XML (uma vez)."""
        if self._carregado:
            return
        
        self._items_por_id = {}
        self._items_por_categoria = defaultdict(list)
        self._items_todos = []
        
        # Parse do XML
        import xml.etree.ElementTree as ET
        tree = ET.parse(ITEMS_XML)
        root = tree.getroot()
        
        for elem in root:
            if elem.tag != 'item':
                continue
            
            item_id = int(elem.get('id', '0'))
            item_nome = elem.get('name', 'Unknown')
            item_artigo = elem.get('article', '')
            item_plural = elem.get('plural', '')
            
            # Extrair atributos
            atributos = {}
            categoria = ''
            peso = 0.0
            
            for attr in elem:
                key = attr.get('key', '')
                value = attr.get('value', '')
                if key == 'primarytype':
                    categoria = value
                elif key == 'weight':
                    try:
                        peso = float(value)
                    except ValueError:
                        pass
                else:
                    atributos[key] = value
            
            item = Item(
                id=item_id,
                nome=item_nome,
                categoria=categoria,
                artigo=item_artigo,
                plural=item_plural,
                peso=peso,
                atributos=atributos,
            )
            
            self._items_por_id[item_id] = item
            self._items_todos.append(item)
            
            if categoria:
                self._items_por_categoria[categoria].append(item)
        
        self._categorias = list(self._items_por_categoria.keys())
        self._carregado = True
        
        print(f"[ItemDatabase] {len(self._items_todos)} itens carregados "
              f"de '{os.path.basename(ITEMS_XML)}' "
              f"({len(self._categorias)} categorias)")
    
    # --- BUSCAS ---
    
    @lru_cache(maxsize=128)
    def buscar_por_id(self, item_id: int) -> Optional[Item]:
        """Busca item por ID."""
        return self._items_por_id.get(item_id)
    
    def buscar_por_nome(self, termo: str, limite: int = 20) -> List[Item]:
        """Busca itens por nome (parcial, case-insensitive)."""
        termo = termo.lower().strip()
        if not termo:
            return []
        
        # Lista de matching items com score
        resultados = []
        
        for item in self._items_todos:
            nome = item.nome_normalizado
            
            # Match exato
            if nome == termo:
                score = 100
            # Match comeca com
            elif nome.startswith(termo):
                score = 80
            # Match em qualquer parte
            elif termo in nome:
                score = 50
            # Match de palavras (ex: "espada" encontra "espada de ferro")
            elif any(termo == p for p in nome.split()):
                score = 60
            elif any(termo in p for p in nome.split()):
                score = 30
            else:
                continue
            
            resultados.append((score, item))
        
        # Ordenar por score e nome
        resultados.sort(key=lambda x: (-x[0], x[1].nome))
        
        return [item for _, item in resultados[:limite]]
    
    def buscar_por_categoria(self, categoria: str, limite: int = 50) -> List[Item]:
        """Busca itens por categoria (primarytype)."""
        categoria_lower = categoria.lower().strip()
        
        # Match exato
        if categoria_lower in self._items_por_categoria:
            return self._items_por_categoria[categoria_lower][:limite]
        
        # Match parcial
        for cat, items in self._items_por_categoria.items():
            if categoria_lower in cat.lower():
                return items[:limite]
        
        return []
    
    def buscar_por_profissao(self, profissao: str, limite: int = 30) -> List[Item]:
        """Busca itens adequados para uma profissao (ex: ferreiro)."""
        profissao_lower = profissao.lower().strip()
        
        config = MAPA_PROFISSAO_CATEGORIA.get(profissao_lower)
        if not config:
            # Tenta match parcial
            for key, cfg in MAPA_PROFISSAO_CATEGORIA.items():
                if profissao_lower in key or key in profissao_lower:
                    config = cfg
                    break
        
        if not config:
            return []
        
        resultados = []
        for cat in config['categorias']:
            items = self._items_por_categoria.get(cat, [])
            resultados.extend(items[:limite // len(config['categorias']) + 1])
        
        return resultados[:limite]
    
    def sugerir_itens_para_shop(self, profissao: str, n_itens: int = 9) -> List[Dict]:
        """Sugere itens para um NPC shop com base na profissao.
        
        Retorna lista de dicts com nome, id, preco_sugerido.
        """
        config = MAPA_PROFISSAO_CATEGORIA.get(profissao.lower())
        if not config:
            return []
        
        candidatos = self.buscar_por_profissao(profissao, limite=n_itens * 3)
        
        # Filtrar itens com nome valido (sem RESERVED, sem placeholder)
        candidatos = [i for i in candidatos 
                      if not i.nome.startswith('RESERVED')
                      and i.nome != 'Unknown'
                      and i.peso > 0 or i.categoria != '']
        
        # Pegar os primeiros n_itens
        selecionados = candidatos[:n_itens]
        
        resultado = []
        for item in selecionados:
            # Preco sugerido baseado no tipo
            preco = self._estimar_preco(item)
            resultado.append({
                'nome': item.nome,
                'id': item.id,
                'categoria': item.categoria,
                'preco_sugerido': preco,
            })
        
        return resultado
    
    def _estimar_preco(self, item: Item) -> int:
        """Estima um preco para o item baseado no tipo."""
        # Se tem preco real de NPC, usa
        if item.preco_compra:
            return item.preco_compra
        
        # Estimativas por categoria
        precos_base = {
            'sword weapons': 500,
            'axe weapons': 450,
            'club weapons': 400,
            'armors': 800,
            'shields': 300,
            'helmets': 250,
            'legs': 200,
            'boots': 150,
            'distance weapons': 300,
            'ammunition': 5,
            'fist weapons': 100,
            'wands': 1000,
            'rods': 800,
            'spellbooks': 500,
            'amulets and necklaces': 1000,
            'rings': 500,
            'containers': 100,
            'potions': 50,
            'food': 15,
            'creature products': 100,
            'valuables': 200,
            'tools': 80,
            'light sources': 200,
            'magical items': 1500,
            'healing runes': 150,
            'attack runes': 200,
            'support runes': 100,
        }
        
        return precos_base.get(item.categoria, 100)
    
    @property
    def categorias(self) -> List[str]:
        """Lista de categorias disponiveis."""
        return sorted(self._categorias)
    
    @property
    def total_itens(self) -> int:
        return len(self._items_todos)
    
    def estatisticas(self) -> Dict:
        """Estatisticas da database."""
        from collections import Counter
        cats = Counter(i.categoria for i in self._items_todos if i.categoria)
        return {
            'total': self.total_itens,
            'categorias': len(self._categorias),
            'top_categorias': cats.most_common(20),
        }
    
    def recarregar(self):
        """Forca recarga do XML."""
        self._carregado = False
        self.buscar_por_id.cache_clear()
        self._carregar()


# ============================================================
# FUNCAO UNICA DE ENTRADA
# ============================================================

def get_db() -> ItemDatabase:
    """Retorna a instancia unica do ItemDatabase."""
    return ItemDatabase()


# ============================================================
# TESTE
# ============================================================

if __name__ == '__main__':
    import json
    
    print("=== TESTE ITEM DATABASE ===\n")
    db = get_db()
    
    print(f"Total de itens: {db.total_itens}")
    print(f"Categorias: {len(db.categorias)}")
    
    # Teste 1: Busca por ID
    item = db.buscar_por_id(20341)
    print(f"\n1. Busca por ID 20341: {item.nome if item else 'NAO ENCONTRADO'}")
    
    # Teste 2: Busca por nome
    print("\n2. Busca por 'espada':")
    for i in db.buscar_por_nome('espada')[:5]:
        print(f"   ID {i.id:5d}: {i.nome} ({i.categoria})")
    
    # Teste 3: Busca por categoria
    print("\n3. Itens 'sword weapons':")
    for i in db.buscar_por_categoria('sword weapons')[:5]:
        print(f"   ID {i.id:5d}: {i.nome}")
    
    # Teste 4: Sugerir para ferreiro
    print("\n4. Sugestoes para ferreiro:")
    sugestoes = db.sugerir_itens_para_shop('ferreiro', 9)
    for s in sugestoes[:9]:
        print(f"   ID {s['id']:5d}: {s['nome']} (preco: {s['preco_sugerido']})")
    
    # Teste 5: Categorias disponiveis para armeiro
    print("\n5. Categorias para 'ferreiro':")
    config = MAPA_PROFISSAO_CATEGORIA.get('ferreiro')
    if config:
        for cat in config['categorias']:
            count = len(db.buscar_por_categoria(cat))
            print(f"   {count:4d} itens em '{cat}'")
