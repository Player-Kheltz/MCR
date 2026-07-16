"""mcr.sanity_validator — Valida se um script Lua chama apenas APIs existentes.
Usa tree-sitter para extrair chamadas e compara contra o Knowledge Graph.
NENHUMA API hardcoded — tudo e aprendido do fonte ou do KG em tempo real."""
import json
import re
import os
from pathlib import Path
from typing import List, Dict, Optional, Set

from tree_sitter import Language, Parser
import tree_sitter_lua

from mcr.paths import KG_DIR, SERVER_DIR
from mcr.encoding import read_file

_LUA_LANG = Language(tree_sitter_lua.language())
_LUA_PARSER = Parser(_LUA_LANG)

# Cache global de APIs (evita re-minerar a cada instancia)
_APIS_CACHE: Set[str] = set()
_APIS_CACHE_INICIALIZADO = False


class SanityValidator:
    """Valida scripts Lua contra as APIs conhecidas.
    
    APIs sao descobertas dinamicamente de:
    1. Fonte C++ do servidor (server/src/) — funcoes registradas no lua
    2. Knowledge Graph (devia/knowledge/patterns_*.json) — chamadas reais
    3. Scripts .lua existentes — chamadas adicionais
    
    Zero APIs hardcoded. Tudo aprendido do ambiente.
    """

    def __init__(self, kg_dir: Optional[Path] = None, server_src_dir: Optional[Path] = None):
        self.kg_dir = kg_dir or KG_DIR
        self.server_src_dir = server_src_dir or (SERVER_DIR / "src")
        self.api_conhecidas: Set[str] = set()
        self.padroes: List[Dict] = []
        self._carregar_apis()

    # ─── Mineracao de APIs do C++ ──────────────────────────

    @staticmethod
    def minerar_apis_do_cpp(src_dir: Path) -> Set[str]:
        """Extrai nomes de funcoes Lua registradas no codigo fonte C++.
        
        Busca padroes como:
        - g_lua.bindClassMemberFunction<Classe>("nome", ...)
        - g_lua.bindGlobalFunction("nome", ...)
        - lua_register(L, "nome", ...)
        - .register("nome")
        - registerMethod("nome")
        """
        apis: Set[str] = set()
        if not src_dir.exists():
            print(f'[SanityValidator] Diretorio C++ nao encontrado: {src_dir}')
            return apis

        padroes_cpp = [
            r'bindClassMemberFunction\w*\s*<\w+>\s*\(\s*"(\w+)"',
            r'bindGlobalFunction\s*\(\s*"(\w+)"',
            r'lua_register\s*\([^,]+,\s*"(\w+)"',
            r'registerMethod\s*\(\s*"(\w+)"',
            r'registerFunction\s*\(\s*"(\w+)"',
            r'\.register\s*\(\s*"(\w+)"',
            r'CLASS_DECLARE\w*\s*\(\s*(\w+)',
        ]

        for fpath in sorted(src_dir.rglob('*.cpp')) if src_dir.exists() else []:
            try:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    conteudo = f.read()
            except Exception:
                continue
            for padrao in padroes_cpp:
                for m in re.finditer(padrao, conteudo):
                    nome = m.group(1).lower()
                    if len(nome) > 2:
                        apis.add(nome)

        print(f'[SanityValidator] Mineradas {len(apis)} APIs do C++')
        return apis

    @staticmethod
    def minerar_apis_dos_scripts(diretorio: Path) -> Set[str]:
        """Extrai chamadas de funcao de todos os scripts .lua do diretorio."""
        apis: Set[str] = set()
        if not diretorio.exists():
            return apis
        for fpath in sorted(diretorio.rglob('*.lua'))[:500]:  # amostra 500
            try:
                codigo = read_file(fpath)
            except Exception:
                continue
            if not codigo or len(codigo) < 20:
                continue
            try:
                tree = _LUA_PARSER.parse(bytes(codigo, 'utf-8'))
            except Exception:
                continue

            def _visitar(node):
                if node.type == 'function_call':
                    for child in node.children:
                        if child.type in ('identifier', 'dot_index_expression',
                                          'method_index_expression'):
                            try:
                                nome = child.text.decode('utf-8', errors='replace').strip().lower()
                                if nome and len(nome) > 3 and ' ' not in nome:
                                    apis.add(nome)
                            except Exception:
                                pass
                for child in node.children:
                    _visitar(child)

            _visitar(tree.root_node)

        print(f'[SanityValidator] Mineradas {len(apis)} APIs dos scripts .lua')
        return apis

    @staticmethod
    def minerar_definicoes_globais(diretorio: Path) -> Set[str]:
        """Extrai definicoes de classes/funcoes globais Lua.
        Captura padroes como:
        - NpcHandler = {}  (variavel global = tabela)
        - function NpcHandler:new(...)  (metodo de classe)
        - function Game.createMonster(...)  (funcao em namespace)
        - keywordHandler = {  (handler global)
        """
        apis: Set[str] = set()
        if not diretorio.exists():
            return apis

        padroes_def = [
            r'^(\w+)\s*=\s*\{\s*$',               # NpcHandler = {
            r'^(\w+)\s*=\s*function\s*\(',         # NpcHandler = function(
            r'^function\s+(\w+)[\.:](\w+)',         # function NpcHandler:method(
            r'^(\w+)\s*=\s*\w+\.\w+\s*$',          # NpcHandler = some.module
        ]

        for fpath in sorted(diretorio.rglob('*.lua'))[:500]:
            try:
                codigo = read_file(fpath)
            except Exception:
                continue
            if not codigo:
                continue
            for lin in codigo.split('\n'):
                lin_strip = lin.strip()
                if not lin_strip or lin_strip.startswith('--'):
                    continue
                for padrao in padroes_def:
                    m = re.match(padrao, lin_strip)
                    if m:
                        nome = m.group(1).lower()
                        if nome and len(nome) > 2 and nome not in ('end', 'then', 'do', 'local', 'return', 'if', 'for', 'function'):
                            apis.add(nome)
                        if len(m.groups()) >= 2:
                            nome2 = f'{m.group(1).lower()}.{m.group(2).lower()}'
                            if nome2 and len(nome2) > 2:
                                apis.add(nome2)
                            nome3 = f'{m.group(1).lower()}:{m.group(2).lower()}'
                            if nome3 and len(nome3) > 2:
                                apis.add(nome3)
        print(f'[SanityValidator] Mineradas {len(apis)} definicoes globais')
        return apis

    def _carregar_apis(self):
        """Carrega APIs de TODAS as fontes: C++ + KG + scripts."""
        global _APIS_CACHE, _APIS_CACHE_INICIALIZADO

        # Se ja foi inicializado (cache), reusa
        if _APIS_CACHE_INICIALIZADO:
            self.api_conhecidas = set(_APIS_CACHE)
            return

        # 1. Mineracao do C++
        if self.server_src_dir and self.server_src_dir.exists():
            apis_cpp = self.minerar_apis_do_cpp(self.server_src_dir)
            _APIS_CACHE.update(apis_cpp)

        # 2. Knowledge Graph
        if self.kg_dir and self.kg_dir.exists():
            for fpath in sorted(self.kg_dir.glob('patterns_*.json')):
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                    items = dados.get('padroes', dados if isinstance(dados, list) else [])
                    self.padroes.extend(items)
                except Exception:
                    continue
            for p in self.padroes:
                for api in p.get('api_calls', []):
                    nome_limpo = api.split('(')[0].strip().lower()
                    if nome_limpo:
                        _APIS_CACHE.add(nome_limpo)

        # 3. Mineracao de scripts Lua existentes (TODOS os diretorios)
        data_dir = SERVER_DIR / 'data-otservbr-global'
        if data_dir.exists():
            for subdir in sorted(data_dir.iterdir()):
                if subdir.is_dir():
                    apis_scripts = self.minerar_apis_dos_scripts(subdir)
                    _APIS_CACHE.update(apis_scripts)
                    apis_defs = self.minerar_definicoes_globais(subdir)
                    _APIS_CACHE.update(apis_defs)

        # 4. Mineracao do ShadowCanary mock (definicoes de APIs Lua reais)
        try:
            from mcr.shadow_canary import _gerar_mock_lua
            mock_lua = _gerar_mock_lua()
            if mock_lua:
                tree = _LUA_PARSER.parse(bytes(mock_lua, 'utf-8'))
                def _visitar_mock(node):
                    if node.type == 'function_call':
                        for child in node.children:
                            if child.type in ('identifier', 'dot_index_expression',
                                              'method_index_expression'):
                                try:
                                    nome = child.text.decode('utf-8', errors='replace').strip()
                                    if nome and len(nome) > 2 and ' ' not in nome:
                                        _APIS_CACHE.add(nome.lower())
                                except Exception:
                                    pass
                    for child in node.children:
                        _visitar_mock(child)
                _visitar_mock(tree.root_node)
        except Exception:
            pass

        self.api_conhecidas = set(_APIS_CACHE)
        _APIS_CACHE_INICIALIZADO = True
        print(f'[SanityValidator] {len(self.api_conhecidas)} APIs conhecidas carregadas (zero hardcode)')

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
        """Valida um arquivo .lua contra as APIs conhecidas."""
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
            encontrou = False
            for api_kg in self.api_conhecidas:
                if ch_lower == api_kg:
                    encontrou = True
                    break
                if ':' in ch_lower:
                    metodo = ch_lower.split(':')[-1]
                    if metodo and (api_kg.endswith(':' + metodo) or api_kg.endswith('.' + metodo)):
                        encontrou = True
                        break
                if '.' in ch_lower or ':' in ch_lower:
                    ultima_parte = ch_lower.split('.')[-1].split(':')[-1]
                    if ultima_parte and len(ultima_parte) > 5 and api_kg.endswith(ultima_parte):
                        encontrou = True
                        break
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

    @staticmethod
    def resetar_cache():
        """Reseta o cache global de APIs (para cold start)."""
        global _APIS_CACHE, _APIS_CACHE_INICIALIZADO
        _APIS_CACHE = set()
        _APIS_CACHE_INICIALIZADO = False
