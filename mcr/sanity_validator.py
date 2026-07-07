"""mcr.sanity_validator — Valida se um script Lua chama apenas APIs que existem no Canary.
Usa tree-sitter para extrair chamadas e compara contra o Knowledge Graph."""
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Set

from tree_sitter import Language, Parser
import tree_sitter_lua

from mcr.paths import KG_DIR
from mcr.encoding import read_file

# Parser Lua unico
_LUA_LANG = Language(tree_sitter_lua.language())
_LUA_PARSER = Parser(_LUA_LANG)


class SanityValidator:
    """Valida scripts Lua contra as APIs conhecidas no KG."""

    # APIs canonicas do Canary que sabemos que existem
    _API_BASE = {
        # Game
        'game.createnpctype', 'game.createmonstertype', 'game.createmonster',
        'game.createitem', 'game.getstoragevalue', 'game.setstoragevalue',
        # NpcType
        'npctype:register', 'npctype:register(keywordhandler)',
        # NpcHandler
        'npchandler:new', 'npchandler:addmodule',
        # KeywordHandler
        'keywordhandler:new',
        # Action
        'action', 'action:register', 'action:uid',
        # Player
        'player:sendtextmessage', 'player:additem', 'player:removeitem',
        'player:getstoragevalue', 'player:setstoragevalue', 'player:getname',
        'player:getposition', 'player:addmoney', 'player:removemoney',
        # Position
        'position',
        # Message constants
        'message_info_descr', 'message_event_advance', 'message_status_warning',
        'message_default', 'message_failure', 'message_trade',
        # FocusModule
        'focusmodule:new',
        # Item
        'item:remove', 'item:getid', 'item:gettype',
        # Container
        'container',
        # MonsterType
        'monstertype:register',
        # CreatureEvent
        'creatureevent',
        # GlobalEvent
        'globalevent',
        # TalkAction
        'talkaction',
        # MoveEvent
        'moveevent',
        # Spell
        'spell',
    }

    def __init__(self, kg_dir: Optional[Path] = None):
        self.kg_dir = kg_dir or KG_DIR
        self.api_conhecidas: Set[str] = set()
        self.padroes: List[Dict] = []
        self._carregar_kg()

    def _carregar_kg(self):
        """Carrega APIs conhecidas do KG + base canonicas."""
        # Comeca com as APIs canonicas
        self.api_conhecidas = set(self._API_BASE)

        if not self.kg_dir.exists():
            print(f'[SanityValidator] KG nao encontrado: {self.kg_dir}, usando {len(self.api_conhecidas)} APIs base')
            return

        for fpath in sorted(self.kg_dir.glob('patterns_*.json')):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                items = dados.get('padroes', dados if isinstance(dados, list) else [])
                self.padroes.extend(items)
            except Exception as e:
                print(f'[SanityValidator] Erro ao carregar {fpath.name}: {e}')

        for p in self.padroes:
            for api in p.get('api_calls', []):
                # Normaliza: remove argumentos, deixa so o nome
                nome_limpo = api.split('(')[0].strip()
                self.api_conhecidas.add(nome_limpo.lower())

        print(f'[SanityValidator] {len(self.api_conhecidas)} APIs conhecidas carregadas')

    # ─── Extracao de chamadas do script ────────────────────────

    def extrair_chamadas(self, codigo: str) -> List[str]:
        """Extrai todas as chamadas de funcao de um codigo Lua usando tree-sitter."""
        if not codigo or len(codigo) < 10:
            return []

        try:
            tree = _LUA_PARSER.parse(bytes(codigo, 'utf-8'))
        except Exception:
            return []

        chamadas = []

        def _visitar(node):
            if node.type == 'function_call':
                nome = self._extrair_nome_chamada(node)
                if nome:
                    chamadas.append(nome)
            for child in node.children:
                _visitar(child)

        _visitar(tree.root_node)
        return list(set(chamadas))

    @staticmethod
    def _extrair_nome_chamada(node) -> Optional[str]:
        """De um node function_call, extrai o nome completo (ex: Game.createNpcType)."""
        if node.type != 'function_call':
            return None
        for child in node.children:
            if child.type in ('identifier', 'dot_index_expression', 'method_index_expression'):
                try:
                    return child.text.decode('utf-8', errors='replace').strip()
                except Exception:
                    return None
        return None

    def validar_script(self, caminho: Path) -> Dict:
        """Valida um arquivo .lua contra as APIs conhecidas.
        
        Returns:
            dict com 'valido', 'apis_conhecidas', 'apis_desconhecidas', 'total_chamadas'
        """
        if not caminho.exists():
            return {'valido': False, 'erro': 'Arquivo nao encontrado', 'apis_conhecidas': [], 'apis_desconhecidas': []}

        try:
            codigo = read_file(caminho)
        except Exception as e:
            return {'valido': False, 'erro': str(e), 'apis_conhecidas': [], 'apis_desconhecidas': []}

        chamadas = self.extrair_chamadas(codigo)

        if not chamadas:
            return {'valido': True, 'apis_conhecidas': [], 'apis_desconhecidas': [], 'total_chamadas': 0}

        conhecidas = []
        desconhecidas = []

        for ch in chamadas:
            ch_lower = ch.lower()
            # Verifica se a API ou qualquer substring significativa dela e conhecida
            # Ex: "Game.createNpcType" -> procura "createNpcType", "game.createnpctype"
            encontrou = False
            for api_kg in self.api_conhecidas:
                # Caso 1: match exato (apos normalizar)
                if ch_lower == api_kg:
                    encontrou = True
                    break
                # Caso 2: a chamada usa um metodo que existe no KG como parte de objeto
                # Ex: ch='player:addItem' e api_kg contem ':addItem' 
                if ':' in ch_lower:
                    metodo = ch_lower.split(':')[-1]
                    if metodo and (api_kg.endswith(':' + metodo) or api_kg.endswith('.' + metodo)):
                        encontrou = True
                        break
                # Caso 3: match por metodo final (ex: ch='Game.createNpcType' e api_kg='createNpcType')
                if '.' in ch_lower or ':' in ch_lower:
                    ultima_parte = ch_lower.split('.')[-1].split(':')[-1]
                    if ultima_parte and len(ultima_parte) > 5 and api_kg.endswith(ultima_parte):
                        encontrou = True
                        break
                # Caso 4: match exato do nome da funcao (sem prefixo de objeto)
                if '.' not in ch_lower and ':' not in ch_lower:
                    if ch_lower == api_kg.split('.')[-1].split(':')[-1]:
                        encontrou = True
                        break

            if encontrou:
                conhecidas.append(ch)
            else:
                desconhecidas.append(ch)

        return {
            'valido': len(desconhecidas) == 0,
            'apis_conhecidas': conhecidas,
            'apis_desconhecidas': desconhecidas,
            'total_chamadas': len(chamadas),
        }

    def validar_codigo(self, codigo: str) -> Dict:
        """Valida uma string de codigo Lua diretamente."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.lua', mode='w', encoding='utf-8', delete=False) as f:
            f.write(codigo)
            tmp = f.name
        try:
            return self.validar_script(Path(tmp))
        finally:
            import os
            os.unlink(tmp)
