"""mcr.sanity_validator_sql — Valida codigo SQL contra padroes conhecidos.

MESMA interface do SanityValidator (Lua) e SanityValidatorCS (C#) para que o
SignatureAnalyzer opere sem adaptacoes — zero hardcode de dominio.

Diferenca: usa raw_token_set() universal (sem tree-sitter) para tokenizar.
Isto reforca o Teorema 1 (Genericidade Parametrica): se o mesmo tokenizador
burro que parseia function...end e public class... clusteriza SELECT...FROM,
a genericidade e do kernel, nao do parser.
"""
import json
import os
import re
from pathlib import Path
from collections import Counter
from typing import Dict, List, Optional, Set

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


_SQL_KEYWORDS: Set[str] = {
    'select', 'from', 'where', 'join', 'left', 'right', 'inner', 'outer',
    'on', 'and', 'or', 'not', 'in', 'like', 'between', 'is', 'null',
    'as', 'order', 'by', 'group', 'having', 'limit', 'offset',
    'create', 'table', 'alter', 'drop', 'add', 'column', 'constraint',
    'primary', 'key', 'foreign', 'references', 'unique', 'index',
    'insert', 'into', 'values', 'update', 'set', 'delete', 'from',
    'exists', 'distinct', 'count', 'sum', 'avg', 'min', 'max',
    'asc', 'desc', 'union', 'all', 'case', 'when', 'then', 'else', 'end',
    'begin', 'commit', 'rollback', 'transaction',
    'grant', 'revoke', 'view', 'materialized', 'temporary',
    'if', 'replace', 'ignore', 'default', 'auto_increment',
    'integer', 'text', 'real', 'blob', 'boolean', 'date', 'datetime',
    'varchar', 'char', 'float', 'double', 'decimal', 'numeric',
    'true', 'false', 'check', 'cast', 'coalesce', 'nullif',
    'type', 'function', 'procedure', 'trigger', 'event', 'schema',
    'database', 'use', 'show', 'describe', 'explain', 'analyze',
    'natural', 'cross', 'using', 'except', 'intersect',
    'some', 'any', 'all',
}

_SQL_STMT_PATTERNS = [
    (re.compile(r'\bselect\b.*\bfrom\b', re.I), 'stmt:select'),
    (re.compile(r'\bcreate\s+table\b', re.I), 'stmt:create_table'),
    (re.compile(r'\binsert\s+into\b', re.I), 'stmt:insert'),
    (re.compile(r'\bupdate\b.*\bset\b', re.I), 'stmt:update'),
    (re.compile(r'\bdelete\s+from\b', re.I), 'stmt:delete'),
    (re.compile(r'\bcreate\s+index\b', re.I), 'stmt:create_index'),
    (re.compile(r'\balter\s+table\b', re.I), 'stmt:alter_table'),
    (re.compile(r'\bdrop\s+table\b', re.I), 'stmt:drop_table'),
    (re.compile(r'\bcreate\s+view\b', re.I), 'stmt:create_view'),
    (re.compile(r'\bjoin\b', re.I), 'stmt:join'),
    (re.compile(r'\bgroup\s+by\b', re.I), 'stmt:group_by'),
    (re.compile(r'\border\s+by\b', re.I), 'stmt:order_by'),
]


def _tokenizar_sql(codigo: str) -> List[str]:
    """Tokeniza SQL usando delimitadores universais + tratamento de strings."""
    from mcr.signature import _DELIMITADORES_UNIVERSAIS
    return _DELIMITADORES_UNIVERSAIS.split(codigo)


def _extrair_identificadores(tokens: List[str]) -> Set[str]:
    """Extrai identificadores (tokens que nao sao SQL keywords nem numeros)."""
    ids: Set[str] = set()
    for t in tokens:
        t_clean = t.strip().lower()
        if not t_clean or len(t_clean) < 1:
            continue
        if t_clean in _SQL_KEYWORDS:
            continue
        if t_clean.replace('.', '').isdigit():
            continue
        if t_clean.startswith("'") or t_clean.startswith('"'):
            continue
        ids.add(t_clean)
    return ids


def _detectar_tipos_sql(tokens: Set[str]) -> List[str]:
    """Detecta tipos de SQL com base nas keywords presentes."""
    tipos = []
    if 'select' in tokens and 'from' in tokens:
        tipos.append('query_select')
    if 'create' in tokens and 'table' in tokens:
        tipos.append('ddl_create_table')
    if 'insert' in tokens and 'into' in tokens:
        tipos.append('dml_insert')
    if 'update' in tokens and 'set' in tokens:
        tipos.append('dml_update')
    if 'delete' in tokens and 'from' in tokens:
        tipos.append('dml_delete')
    if 'create' in tokens and 'index' in tokens:
        tipos.append('ddl_create_index')
    if 'alter' in tokens and 'table' in tokens:
        tipos.append('ddl_alter_table')
    if 'drop' in tokens and 'table' in tokens:
        tipos.append('ddl_drop_table')
    if 'join' in tokens:
        tipos.append('query_join')
    if 'group' in tokens and 'by' in tokens:
        tipos.append('query_group_by')
    if 'order' in tokens and 'by' in tokens:
        tipos.append('query_order_by')
    return tipos


def _extrair_tabelas(tokens: List[str], codigo: str) -> Set[str]:
    """Extrai nomes de tabelas.

    Heuristica: token apos FROM, JOIN, INTO, TABLE, REFERENCES, INDEX ON.
    """
    tabelas: Set[str] = set()
    consumir_proximo = False
    palavras_chave_tabela = {'from', 'into', 'table', 'references', 'index', 'update'}
    for token in tokens:
        t = token.strip().lower()
        if consumir_proximo and t and not t.startswith("'") and not t.replace('.', '').isdigit():
            if t not in _SQL_KEYWORDS:
                tabelas.add(t)
            consumir_proximo = False
        if t in palavras_chave_tabela:
            consumir_proximo = True
        elif t == 'join':
            consumir_proximo = True

    # Tambem detecta CREATE TABLE nome ou INSERT INTO nome
    for match in re.finditer(r'\b(?:create\s+table|insert\s+into|into|from|table|join|update)\s+(\w+)', codigo, re.I):
        nome = match.group(1).lower()
        if nome not in _SQL_KEYWORDS:
            tabelas.add(nome)

    return tabelas


def _extrair_colunas(codigo: str) -> Set[str]:
    """Extrai nomes de colunas apenas de definicoes CREATE TABLE."""
    colunas: Set[str] = set()
    # Só extrai colunas dentro de blocos CREATE TABLE (...)
    create_match = re.search(r'CREATE\s+TABLE\s+\w+\s*\((.*?)\);', codigo, re.I | re.DOTALL)
    if create_match:
        body = create_match.group(1)
        for match in re.finditer(r'(\w+)\s+(integer|text|real|boolean|datetime|varchar|float|double|decimal|blob|char|date|numeric|tinyint|bigint|smallint)', body, re.I):
            nome = match.group(1).lower()
            if nome not in _SQL_KEYWORDS:
                colunas.add(nome)
    return colunas


_SQL_APIS_CACHE: Set[str] = set()
_SQL_CACHE_INICIALIZADO = False


class SanityValidatorSQL:
    """Valida codigo SQL contra padroes conhecidos.

    APIs (keywords/estruturas) descobertas dinamicamente de arquivos .sql.
    Zero hardcode alem das keywords SQL padrao.
    """

    def __init__(self):
        self.api_conhecidas: Set[str] = set()
        self.padroes: list = []
        self._carregar()

    @staticmethod
    def minerar_assinaturas(diretorio: Path) -> List[Dict]:
        """Extrai assinaturas de TODOS os arquivos .sql do diretorio.

        Para cada arquivo, extrai:
        - tipos: tipos de SQL detectados (query_select, ddl_create_table, etc.)
        - keywords: SQL keywords encontradas
        - tabelas: nomes de tabelas referenciadas
        - colunas: nomes de colunas definidas/usadas
        - statements: tipos de statement detectados (stmt:select, stmt:join, etc.)
        """
        entidades = []
        if not diretorio.exists():
            print(f'[SanityValidatorSQL] Diretorio nao encontrado: {diretorio}')
            return entidades

        sql_files = sorted(diretorio.rglob('*.sql'))
        print(f'[SanityValidatorSQL] Escaneando {len(sql_files)} arquivos .sql...')

        for fpath in sql_files:
            try:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    codigo = f.read()
            except Exception:
                continue
            if not codigo or len(codigo) < 10:
                continue

            tokens = _tokenizar_sql(codigo)
            tokens_clean = {t.strip().lower() for t in tokens if t.strip() and len(t.strip()) > 1}
            keywords_presentes = tokens_clean & _SQL_KEYWORDS
            identificadores = _extrair_identificadores(tokens)
            tabelas = _extrair_tabelas(tokens, codigo)
            colunas = _extrair_colunas(codigo)
            tipos = _detectar_tipos_sql(tokens_clean)

            statements = []
            for pattern, label in _SQL_STMT_PATTERNS:
                if pattern.search(codigo):
                    statements.append(label)

            api_calls: Set[str] = set()
            for kw in keywords_presentes:
                api_calls.add(f'sql:{kw}')
            for tipo in tipos:
                api_calls.add(f'tipo:{tipo}')
            for stmt in statements:
                api_calls.add(stmt)
            for tab in list(tabelas)[:15]:
                api_calls.add(f'table:{tab}')
            for col in list(colunas)[:20]:
                api_calls.add(f'column:{col}')

            tipo_entidade = tipos[0] if tipos else (statements[0] if statements else 'sql_generic')

            entidades.append({
                'arquivo': str(fpath),
                'tipo': tipo_entidade,
                'api_calls': list(api_calls),
                'tamanho_linhas': len(codigo.splitlines()),
                'keywords': list(keywords_presentes),
                'tabelas': list(tabelas),
                'colunas': list(colunas),
                'statements': statements,
                'tipos_sql': tipos,
            })

        print(f'[SanityValidatorSQL] {len(entidades)} entidades extraidas')
        return entidades

    @staticmethod
    def _normalizar_api(nome: str) -> str:
        return nome.strip().lower()

    def _carregar(self):
        global _SQL_APIS_CACHE, _SQL_CACHE_INICIALIZADO
        if _SQL_CACHE_INICIALIZADO:
            self.api_conhecidas = set(_SQL_APIS_CACHE)
            return
        _SQL_APIS_CACHE = set(_SQL_KEYWORDS)
        _SQL_CACHE_INICIALIZADO = True
        self.api_conhecidas = set(_SQL_APIS_CACHE)
        print(f'[SanityValidatorSQL] Cache inicializado ({len(self.api_conhecidas)} keywords SQL)')

    def extrair_chamadas(self, codigo: str) -> List[str]:
        """Extrai 'chamadas' SQL (keywords + identificadores de estrutura)."""
        if not codigo or len(codigo) < 10:
            return []
        tokens = _tokenizar_sql(codigo)
        tokens_clean = {t.strip().lower() for t in tokens if t.strip() and len(t.strip()) > 1}
        chamadas: List[str] = []
        for kw in tokens_clean & _SQL_KEYWORDS:
            chamadas.append(f'sql:{kw}')
        for pattern, label in _SQL_STMT_PATTERNS:
            if pattern.search(codigo):
                chamadas.append(label)
        return list(set(chamadas))

    def validar_codigo(self, codigo: str) -> Dict:
        """Valida uma string de codigo SQL contra keywords conhecidas."""
        chamadas = self.extrair_chamadas(codigo)
        if not chamadas:
            return {'valido': False, 'apis_conhecidas': [], 'apis_desconhecidas': ['no_sql_keywords'], 'total_chamadas': 0}

        conhecidas = []
        desconhecidas = []
        for ch in chamadas:
            ch_norm = self._normalizar_api(ch)
            if ch_norm in self.api_conhecidas or ch_norm.startswith('stmt:'):
                conhecidas.append(ch)
            else:
                desconhecidas.append(ch)

        return {
            'valido': len(desconhecidas) == 0 and len(conhecidas) > 0,
            'apis_conhecidas': conhecidas,
            'apis_desconhecidas': desconhecidas,
            'total_chamadas': len(chamadas),
        }

    @staticmethod
    def resetar_cache():
        global _SQL_APIS_CACHE, _SQL_CACHE_INICIALIZADO
        _SQL_APIS_CACHE = set()
        _SQL_CACHE_INICIALIZADO = False


if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    val = SanityValidatorSQL()
    entidades = val.minerar_assinaturas(Path(_BASE) / 'data' / 'generated' / 'sql_corpus')
    print(f'\nTotal entidades: {len(entidades)}')
    tipos = {}
    for e in entidades:
        t = e.get('tipo', 'unknown')
        tipos[t] = tipos.get(t, 0) + 1
    print(f'Distribuicao de tipos: {tipos}')
    for e in entidades[:3]:
        print(f'\n  --- {e["tipo"]}: {Path(e["arquivo"]).name} ---')
        print(f'    Keywords: {e.get("keywords", [])[:8]}')
        print(f'    Tabelas: {e.get("tabelas", [])[:5]}')
        print(f'    Statements: {e.get("statements", [])}')
