"""mcr.sanity_validator_cpp — Valida codigo C++ contra padroes conhecidos.

MESMA interface do SanityValidatorSQL, SanityValidatorCS, SanityValidator.
Usa raw_token_set() universal (sem tree-sitter) — reforca o Teorema 1.
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


_CPP_KEYWORDS: Set[str] = {
    'alignas', 'alignof', 'and', 'and_eq', 'asm', 'auto', 'bitand', 'bitor',
    'bool', 'break', 'case', 'catch', 'char', 'char8_t', 'char16_t', 'char32_t',
    'class', 'compl', 'concept', 'const', 'consteval', 'constexpr', 'constinit',
    'continue', 'co_await', 'co_return', 'co_yield', 'decltype', 'default',
    'delete', 'do', 'double', 'dynamic_cast', 'else', 'enum', 'explicit',
    'export', 'extern', 'false', 'float', 'for', 'friend', 'goto', 'if',
    'import', 'inline', 'int', 'long', 'module', 'mutable', 'namespace',
    'new', 'noexcept', 'not', 'not_eq', 'nullptr', 'operator', 'or', 'or_eq',
    'override', 'private', 'protected', 'public', 'register', 'reinterpret_cast',
    'requires', 'return', 'short', 'signed', 'sizeof', 'static', 'static_assert',
    'static_cast', 'struct', 'switch', 'template', 'this', 'throw', 'true',
    'try', 'typedef', 'typeid', 'typename', 'union', 'unsigned', 'using',
    'virtual', 'void', 'volatile', 'wchar_t', 'while', 'xor', 'xor_eq',
    'include', 'define', 'ifdef', 'ifndef', 'endif', 'pragma', 'undef',
    'once', 'std', 'string', 'vector', 'map', 'set', 'list', 'pair',
    'shared_ptr', 'unique_ptr', 'weak_ptr', 'make_shared', 'make_unique',
    'optional', 'variant', 'any', 'tuple', 'array', 'function', 'bind',
    'cout', 'cin', 'cerr', 'clog', 'endl', 'printf', 'scanf', 'size_t',
    'int8_t', 'int16_t', 'int32_t', 'int64_t', 'uint8_t', 'uint16_t',
    'uint32_t', 'uint64_t', 'nullptr_t',
}

_CPP_STMT_PATTERNS = [
    (re.compile(r'\bclass\s+\w+', re.I), 'stmt:class'),
    (re.compile(r'\bstruct\s+\w+', re.I), 'stmt:struct'),
    (re.compile(r'\benum\s+\w+', re.I), 'stmt:enum'),
    (re.compile(r'\btemplate\s*<', re.I), 'stmt:template'),
    (re.compile(r'#\s*include', re.I), 'stmt:include'),
    (re.compile(r'#\s*define', re.I), 'stmt:define'),
    (re.compile(r'\bnamespace\s+\w+', re.I), 'stmt:namespace'),
    (re.compile(r'\bvirtual\b', re.I), 'stmt:virtual'),
    (re.compile(r'\boverride\b', re.I), 'stmt:override'),
    (re.compile(r'\bconst\s+expr\b', re.I), 'stmt:constexpr'),
    (re.compile(r'\bauto\b', re.I), 'stmt:auto'),
    (re.compile(r'\blambda\b|\{\s*\[', re.I), 'stmt:lambda'),
    (re.compile(r'\b(?:int|void|bool|char|float|double|string|auto|size_t)\s+\w+\s*\(', re.I), 'stmt:function'),
    (re.compile(r'\b(?:class|struct|enum|union)\s+\w+\s*:', re.I), 'stmt:inheritance'),
]


def _tokenizar_cpp(codigo: str) -> List[str]:
    from devia.kernel.mcr_kernel.signature import _DELIMITADORES_UNIVERSAIS
    return _DELIMITADORES_UNIVERSAIS.split(codigo)


def _extrair_identificadores(tokens: List[str]) -> Set[str]:
    ids: Set[str] = set()
    for t in tokens:
        t_clean = t.strip().lower()
        if not t_clean or len(t_clean) < 1:
            continue
        if t_clean in _CPP_KEYWORDS:
            continue
        if t_clean.replace('.', '').isdigit():
            continue
        if t_clean.startswith('"') or t_clean.startswith("'"):
            continue
        ids.add(t_clean)
    return ids


def _detectar_tipos_cpp(tokens: Set[str]) -> List[str]:
    tipos = []
    if 'class' in tokens: tipos.append('cpp_class')
    if 'struct' in tokens: tipos.append('cpp_struct')
    if 'enum' in tokens: tipos.append('cpp_enum')
    if 'template' in tokens: tipos.append('cpp_template')
    if 'namespace' in tokens: tipos.append('cpp_namespace')
    if 'virtual' in tokens: tipos.append('cpp_virtual')
    if 'include' in tokens or 'define' in tokens: tipos.append('cpp_preprocessor')
    if 'override' in tokens: tipos.append('cpp_override')
    if 'auto' in tokens: tipos.append('cpp_auto')
    if 'constexpr' in tokens: tipos.append('cpp_constexpr')
    if 'using' in tokens: tipos.append('cpp_using')
    if 'friend' in tokens: tipos.append('cpp_friend')
    if 'operator' in tokens: tipos.append('cpp_operator')
    if 'template' in tokens: tipos.append('cpp_template')
    return tipos


def _extrair_classes(codigo: str) -> Set[str]:
    classes: Set[str] = set()
    for match in re.finditer(r'\b(?:class|struct)\s+(\w+)', codigo, re.I):
        nome = match.group(1).lower()
        if nome not in _CPP_KEYWORDS:
            classes.add(nome)
    return classes


def _extrair_funcoes(codigo: str) -> Set[str]:
    funcoes: Set[str] = set()
    for match in re.finditer(r'(?:[\w:]+\s+)?(\w+)\s*\([^)]*\)\s*(?:const|override|virtual|\{|;)', codigo):
        nome = match.group(1).lower()
        if nome not in _CPP_KEYWORDS and len(nome) > 1:
            funcoes.add(nome)
    return funcoes


def _extrair_namespaces(codigo: str) -> Set[str]:
    nss: Set[str] = set()
    for match in re.finditer(r'\bnamespace\s+(\w+)', codigo, re.I):
        nss.add(match.group(1).lower())
    return nss


def _extrair_macros(codigo: str) -> Set[str]:
    macros: Set[str] = set()
    for match in re.finditer(r'#\s*define\s+(\w+)', codigo, re.I):
        macros.add(match.group(1).lower())
    for match in re.finditer(r'#\s*include\s*[<"]([^>"]+)[>"]', codigo):
        macros.add('include:' + match.group(1).lower())
    return macros


_CPP_APIS_CACHE: Set[str] = set()
_CPP_CACHE_INICIALIZADO = False


class SanityValidatorCpp:
    """Valida codigo C++ contra padroes conhecidos.

    APIs descobertas dinamicamente de arquivos .cpp/.hpp.
    Zero hardcode alem das keywords C++ padrao.
    """

    def __init__(self):
        self.api_conhecidas: Set[str] = set()
        self.padroes: list = []
        self._carregar()

    @staticmethod
    def minerar_assinaturas(diretorio: Path) -> List[Dict]:
        """Extrai assinaturas de TODOS os arquivos .cpp/.hpp/.h do diretorio."""
        entidades = []
        if not diretorio.exists():
            print(f'[SanityValidatorCpp] Diretorio nao encontrado: {diretorio}')
            return entidades

        exts = ('*.cpp', '*.hpp', '*.h')
        cpp_files: List[Path] = []
        for ext in exts:
            cpp_files.extend(sorted(diretorio.rglob(ext)))

        print(f'[SanityValidatorCpp] Escaneando {len(cpp_files)} arquivos C++...')

        for fpath in cpp_files:
            if fpath.name == 'pch.h' or fpath.name == 'stdafx.h':
                continue
            try:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    codigo = f.read()
            except Exception:
                continue
            if not codigo or len(codigo) < 20:
                continue

            tokens = _tokenizar_cpp(codigo)
            tokens_clean = {t.strip().lower() for t in tokens if t.strip() and len(t.strip()) > 1}
            keywords_presentes = tokens_clean & _CPP_KEYWORDS
            identificadores = _extrair_identificadores(tokens)
            classes = _extrair_classes(codigo)
            funcoes = _extrair_funcoes(codigo)
            namespaces = _extrair_namespaces(codigo)
            macros = _extrair_macros(codigo)
            tipos = _detectar_tipos_cpp(tokens_clean)

            statements = []
            for pattern, label in _CPP_STMT_PATTERNS:
                if pattern.search(codigo):
                    statements.append(label)

            api_calls: Set[str] = set()
            for kw in keywords_presentes:
                api_calls.add(f'cpp:{kw}')
            for t in tipos:
                api_calls.add(f'tipo:{t}')
            for stmt in statements:
                api_calls.add(stmt)
            for cls in list(classes)[:15]:
                api_calls.add(f'class:{cls}')
            for fn in list(funcoes)[:20]:
                api_calls.add(f'func:{fn}')
            for ns in list(namespaces)[:10]:
                api_calls.add(f'ns:{ns}')
            for macro in list(macros)[:15]:
                api_calls.add(f'macro:{macro}')

            tipo_entidade = tipos[0] if tipos else (statements[0] if statements else 'cpp_generic')

            entidades.append({
                'arquivo': str(fpath),
                'tipo': tipo_entidade,
                'api_calls': list(api_calls),
                'tamanho_linhas': len(codigo.splitlines()),
                'keywords': list(keywords_presentes),
                'classes': list(classes),
                'funcoes': list(funcoes),
                'namespaces': list(namespaces),
                'macros': list(macros),
                'statements': statements,
                'tipos_cpp': tipos,
            })

        print(f'[SanityValidatorCpp] {len(entidades)} entidades extraidas')
        return entidades

    @staticmethod
    def _normalizar_api(nome: str) -> str:
        return nome.strip().lower()

    def _carregar(self):
        global _CPP_APIS_CACHE, _CPP_CACHE_INICIALIZADO
        if _CPP_CACHE_INICIALIZADO:
            self.api_conhecidas = set(_CPP_APIS_CACHE)
            return
        _CPP_APIS_CACHE = set(_CPP_KEYWORDS)
        _CPP_CACHE_INICIALIZADO = True
        self.api_conhecidas = set(_CPP_APIS_CACHE)
        print(f'[SanityValidatorCpp] Cache inicializado ({len(self.api_conhecidas)} keywords C++)')

    def extrair_chamadas(self, codigo: str) -> List[str]:
        """Extrai 'chamadas' (keywords + estruturas) de codigo C++."""
        if not codigo or len(codigo) < 10:
            return []
        tokens = _tokenizar_cpp(codigo)
        tokens_clean = {t.strip().lower() for t in tokens if t.strip() and len(t.strip()) > 1}
        chamadas: List[str] = []
        for kw in tokens_clean & _CPP_KEYWORDS:
            chamadas.append(f'cpp:{kw}')
        for pattern, label in _CPP_STMT_PATTERNS:
            if pattern.search(codigo):
                chamadas.append(label)
        return list(set(chamadas))

    def validar_codigo(self, codigo: str) -> Dict:
        chamadas = self.extrair_chamadas(codigo)
        if not chamadas:
            return {'valido': False, 'apis_conhecidas': [], 'apis_desconhecidas': ['no_cpp_keywords'], 'total_chamadas': 0}
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
        global _CPP_APIS_CACHE, _CPP_CACHE_INICIALIZADO
        _CPP_APIS_CACHE = set()
        _CPP_CACHE_INICIALIZADO = False


if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    val = SanityValidatorCpp()
    entidades = val.minerar_assinaturas(Path(_BASE) / 'server' / 'src')
    print(f'\nTotal entidades: {len(entidades)}')
    tipos = {}
    for e in entidades:
        t = e.get('tipo', 'unknown')
        tipos[t] = tipos.get(t, 0) + 1
    print(f'Distribuicao: {dict(sorted(tipos.items(), key=lambda x: -x[1])[:15])}')
    for e in entidades[:2]:
        print(f'\n  --- {e["tipo"]}: {Path(e["arquivo"]).name} ---')
        print(f'    Keywords: {e.get("keywords", [])[:10]}')
        print(f'    Classes: {e.get("classes", [])[:5]}')
        print(f'    Funcoes: {e.get("funcoes", [])[:5]}')
