#!/usr/bin/env python3
"""mcr.pattern_miner — Minerador de padroes estruturais via AST (tree-sitter).
FASE 1: Varre codigo-fonte do Canary (Lua e C++) e extrai assinaturas para o KG."""
import json
import os
import time
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Optional

from tree_sitter import Language, Parser

import tree_sitter_lua
import tree_sitter_cpp

from mcr.paths import CANARY_SCRIPTS_DIR, CANARY_NPC_DIR, CANARY_SRC_DIR, KG_DIR
from mcr.encoding import read_file

# ─── Init parsers (uma vez) ────────────────────────────────────
_LUA_LANG = Language(tree_sitter_lua.language())
_CPP_LANG = Language(tree_sitter_cpp.language())
_LUA_PARSER = Parser(_LUA_LANG)
_CPP_PARSER = Parser(_CPP_LANG)

# Extensoes por linguagem
_EXT_LUA = {'.lua'}
_EXT_CPP = {'.cpp', '.h', '.hpp', '.cc', '.cxx'}

# ─── Utilitarios AST ───────────────────────────────────────────

def _node_text(node) -> str:
    """Retorna o texto de um node AST com seguranca."""
    try:
        return node.text.decode('utf-8', errors='replace')
    except Exception:
        return ''


def _extrair_chamadas(node, resultados: set, prefixo: str = ''):
    """Extrai chamadas de funcao da AST: `foo()` e `obj:method()`."""
    if node.type == 'function_call':
        # Tenta extrair o nome completo (ex: Game.createNpcType)
        nome = _extrair_nome_chamada(node)
        if nome:
            resultados.add(nome)
    for child in node.children:
        _extrair_chamadas(child, resultados)


def _extrair_nome_chamada(node) -> Optional[str]:
    """De um node function_call, extrai 'Game.createNpcType' ou 'npcType:register'."""
    if node.type != 'function_call':
        return None
    # Primeiro filho costuma ser o nome
    for child in node.children:
        if child.type in ('identifier', 'dot_index_expression', 'method_index_expression'):
            return _node_text(child).strip()
    return None


def _extrair_variaveis(node, resultados: set):
    """Extrai declaracoes de variaveis: `local x = ...` ou `x = ...`."""
    if node.type == 'assignment_statement':
        # Variavel do lado esquerdo
        for child in node.children:
            if child.type == 'variable_list':
                for var_node in child.children:
                    if var_node.type == 'identifier':
                        resultados.add(_node_text(var_node).strip())
    if node.type == 'variable_declaration':
        # local x, local x = ...
        for child in node.children:
            if child.type == 'variable_list':
                for var_node in child.children:
                    if var_node.type == 'identifier':
                        resultados.add(_node_text(var_node).strip())
    for child in node.children:
        _extrair_variaveis(child, resultados)


def _extrair_funcoes_definidas(node, resultados: list, arquivo: str):
    """Extrai definicoes de funcoes: `function onSay(...)` e suas chamadas internas."""
    if node.type == 'function_definition':
        nome = ''
        chamadas_internas = set()
        for child in node.children:
            if child.type in ('identifier', 'dot_index_expression', 'method_index_expression'):
                nome = _node_text(child).strip()
        _extrair_chamadas(node, chamadas_internas)
        if nome:
            resultados.append({
                'tipo': 'function',
                'nome': nome,
                'arquivo': arquivo,
                'chamadas_internas': list(chamadas_internas),
            })
    for child in node.children:
        _extrair_funcoes_definidas(child, resultados, arquivo)


def _extrair_tabelas(node, resultados: list, arquivo: str):
    """Extrai construcoes de tabela: `npcConfig = { ... }` e suas chaves."""
    if node.type == 'table_constructor':
        # Tenta encontrar a variavel associada
        # Sobe na arvore para achar o assignment_statement
        parent = node.parent
        variavel = ''
        if parent and parent.type == 'assignment_statement':
            for child in parent.children:
                if child.type in ('variable_list', 'identifier'):
                    variavel = _node_text(child).strip()
        chaves = set()
        for child in node.children:
            if child.type == 'field':
                for field_child in child.children:
                    if field_child.type in ('identifier', 'string', 'dot_index_expression'):
                        chaves.add(_node_text(field_child).strip())
                    elif field_child.type == 'expression_list' and field_child.child_count == 0:
                        pass  # skip
        if variavel:
            resultados.append({
                'tipo': 'table',
                'variavel': variavel,
                'arquivo': arquivo,
                'chaves': list(chaves),
            })
    for child in node.children:
        _extrair_tabelas(child, resultados, arquivo)


# ─── Mineradores Especificos ───────────────────────────────────

def _detectar_tipo_lua(api_calls: set, variables: set) -> str:
    """Detecta o tipo de arquivo Lua (npc, monster, action, spell, quest, generic)."""
    api_str = ' '.join(api_calls).lower()
    var_str = ' '.join(variables).lower()

    if 'createmonstertype' in api_str or 'monsterconfig' in var_str:
        return 'monster'
    if 'createnpctype' in api_str or 'npcconfig' in var_str or 'npchandler' in api_str:
        return 'npc'
    if 'action' in api_str and ('onuse' in api_str or 'uid' in api_str):
        return 'action'
    if 'spell' in api_str or 'instantspell' in api_str:
        return 'spell'
    if 'creatureevent' in api_str:
        return 'creatureevent'
    if 'globalevent' in api_str:
        return 'globalevent'
    if 'quest' in var_str:
        return 'quest'
    if 'habilidades[' in api_str or 'efeitoconfig' in var_str:
        return 'spa_skill'
    return 'generic'


# ─── API Publica ───────────────────────────────────────────────

def minerar_codigo(codigo: str, acao: str = '') -> List[Dict]:
    """Minera padroes de uma string de codigo (sem arquivo)."""
    if not codigo or len(codigo) < 20:
        return []
    try:
        tree = _LUA_PARSER.parse(bytes(codigo, 'utf-8'))
    except Exception:
        return []
    root = tree.root_node
    api_calls = set()
    variables = set()
    funcoes = []
    tabelas = []
    _extrair_chamadas(root, api_calls)
    _extrair_variaveis(root, variables)
    _extrair_funcoes_definidas(root, funcoes, '<inline>')
    _extrair_tabelas(root, tabelas, '<inline>')
    tipo = _detectar_tipo_lua(api_calls, variables)
    return [{
        'arquivo': f'<execucao:{acao}>',
        'linguagem': 'lua',
        'tipo': tipo,
        'api_calls': sorted(api_calls),
        'variaveis': sorted(variables),
        'funcoes': funcoes,
        'tabelas': tabelas,
        'tamanho_linhas': codigo.count('\n') + 1,
    }]


def miner_arquivo_lua(caminho: Path) -> Optional[Dict]:
    """Minera um unico arquivo .lua e retorna seu padrao estrutural."""
    try:
        codigo = read_file(caminho)
    except Exception:
        return None

    try:
        tree = _LUA_PARSER.parse(bytes(codigo, 'utf-8'))
    except Exception:
        return None

    root = tree.root_node

    api_calls = set()
    variables = set()
    funcoes = []
    tabelas = []

    _extrair_chamadas(root, api_calls)
    _extrair_variaveis(root, variables)
    _extrair_funcoes_definidas(root, funcoes, str(caminho))
    _extrair_tabelas(root, tabelas, str(caminho))

    tipo = _detectar_tipo_lua(api_calls, variables)

    return {
        'arquivo': str(caminho),
        'linguagem': 'lua',
        'tipo': tipo,
        'api_calls': sorted(api_calls),
        'variaveis': sorted(variables),
        'funcoes': funcoes,
        'tabelas': tabelas,
        'tamanho_linhas': codigo.count('\n') + 1,
    }


def miner_lua_files(diretorio: Path) -> List[Dict]:
    """Varre um diretorio em busca de .lua e extrai padroes estruturais."""
    padroes = []
    if not diretorio.exists():
        print(f'[PatternMiner] Diretorio nao encontrado: {diretorio}')
        return padroes

    arquivos = list(diretorio.rglob('*.lua'))
    print(f'[PatternMiner] Varrendo {len(arquivos)} arquivos .lua em {diretorio}')

    t0 = time.time()
    for i, fpath in enumerate(arquivos):
        padrao = miner_arquivo_lua(fpath)
        if padrao:
            padroes.append(padrao)
        if (i + 1) % 100 == 0:
            print(f'  Processados {i+1}/{len(arquivos)}...')
    t1 = time.time()

    print(f'[PatternMiner] Lua: {len(padroes)} padroes em {t1-t0:.1f}s ({len(padroes)/max(t1-t0,0.1):.0f} arqs/s)')
    return padroes


def miner_arquivo_cpp(caminho: Path) -> Optional[Dict]:
    """Minera um unico arquivo .cpp/.h e retorna seu padrao estrutural."""
    try:
        codigo = read_file(caminho)
    except Exception:
        return None

    if len(codigo) < 20:
        return None

    try:
        tree = _CPP_PARSER.parse(bytes(codigo, 'utf-8'))
    except Exception:
        return None

    root = tree.root_node

    classes = []
    funcoes = []
    includes = []

    def _visitar(node, nivel=0):
        if nivel > 50:
            return
        if node.type == 'class_specifier':
            nome = ''
            heranca = ''
            for child in node.children:
                if child.type == 'identifier':
                    nome = _node_text(child).strip()
                elif child.type == 'base_class_clause':
                    for base_child in child.children:
                        if base_child.type == 'type_identifier':
                            heranca = _node_text(base_child).strip()
            if nome:
                classes.append({'nome': nome, 'heranca': heranca})
        elif node.type == 'function_definition':
            nome = ''
            for child in node.children:
                if child.type == 'function_declarator':
                    for decl_child in child.children:
                        if decl_child.type == 'identifier':
                            nome = _node_text(decl_child).strip()
            if nome:
                funcoes.append(nome)
        elif node.type == 'preproc_include':
            texto = _node_text(node).strip()
            if texto:
                includes.append(texto)
        for child in node.children:
            _visitar(child, nivel + 1)

    _visitar(root)

    return {
        'arquivo': str(caminho),
        'linguagem': 'cpp',
        'classes': classes,
        'funcoes': funcoes,
        'includes': includes,
        'tamanho_linhas': codigo.count('\n') + 1,
    }


def miner_cpp_files(diretorio: Path) -> List[Dict]:
    """Varre um diretorio em busca de .cpp/.h e extrai padroes estruturais."""
    padroes = []
    if not diretorio.exists():
        print(f'[PatternMiner] Diretorio nao encontrado: {diretorio}')
        return padroes

    arquivos = []
    for ext in _EXT_CPP:
        arquivos.extend(diretorio.rglob(f'*{ext}'))

    print(f'[PatternMiner] Varrendo {len(arquivos)} arquivos C++ em {diretorio}')

    t0 = time.time()
    for i, fpath in enumerate(arquivos):
        padrao = miner_arquivo_cpp(fpath)
        if padrao:
            padroes.append(padrao)
        if (i + 1) % 50 == 0 and len(arquivos) > 100:
            print(f'  Processados {i+1}/{len(arquivos)}...')
    t1 = time.time()

    print(f'[PatternMiner] C++: {len(padroes)} padroes em {t1-t0:.1f}s ({len(padroes)/max(t1-t0,0.1):.0f} arqs/s)')
    return padroes


def save_patterns_to_kg(padroes: List[Dict], output_file: Optional[Path] = None) -> Path:
    """Salva padroes extraidos em JSON (KG provisorio)."""
    if output_file is None:
        KG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        output_file = KG_DIR / f'patterns_{timestamp}.json'

    # Estatisticas
    stats = defaultdict(int)
    for p in padroes:
        stats[p.get('tipo', 'generic')] += 1
        stats['total'] += 1

    dados = {
        'metadata': {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_padroes': len(padroes),
            'tipos': dict(stats),
        },
        'padroes': padroes,
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    print(f'[PatternMiner] KG salvo em: {output_file} ({len(padroes)} padroes, {os.path.getsize(output_file)/1024:.0f} KB)')
    return output_file


# ─── Ponto de entrada ──────────────────────────────────────────

if __name__ == '__main__':
    import sys

    print('=' * 55)
    print('  PATTERN MINER — FASE 1')
    print('=' * 55)

    t_global = time.time()

    # Lua — server/data/scripts/
    padroes_lua = miner_lua_files(CANARY_SCRIPTS_DIR)

    # Lua — server/data-otservbr-global/npc/ (1,076 scripts NPC)
    if CANARY_NPC_DIR.exists():
        padroes_npc = miner_lua_files(CANARY_NPC_DIR)
    else:
        print(f'[PatternMiner] NPC dir nao encontrado: {CANARY_NPC_DIR}')
        padroes_npc = []

    # C++ (opcional, pode pular se nao precisar)
    if '--cpp' in sys.argv or '--all' in sys.argv:
        padroes_cpp = miner_cpp_files(CANARY_SRC_DIR)
    else:
        print('[PatternMiner] C++: pulado (use --cpp ou --all para incluir)')
        padroes_cpp = []

    # Unifica
    todos_padroes = padroes_lua + padroes_npc + padroes_cpp

    # Salva
    if todos_padroes:
        output = save_patterns_to_kg(todos_padroes)
    else:
        print('[PatternMiner] Nenhum padrao encontrado')
        output = None

    t_final = time.time()
    print(f'\n[PatternMiner] Total: {len(todos_padroes)} padroes em {t_final-t_global:.1f}s')
    print(f'[PatternMiner] Pronto para FASE 2 (Metacognicao)')
