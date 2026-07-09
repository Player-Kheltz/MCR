#!/usr/bin/env python3
"""setup_treesitter.py — Instalacao e teste do tree-sitter para FASE 1 (PatternMiner).
Verifica se as bibliotecas necessarias existem, instala se preciso, e valida com um parser Lua."""
import sys
import subprocess
import importlib.util
import platform

REQUISITOS = [
    'tree_sitter',
    'tree_sitter_languages',   # opcional (pode faltar em Python 3.14)
]

REQUISITOS_GRAMATICA = [
    'tree_sitter_lua',   # importa como tree_sitter_lua
    'tree_sitter_cpp',   # importa como tree_sitter_cpp
]

# Snippet Lua para teste do parser
TESTE_LUA = """
local internalNpcName = "Guarda"
local npcType = Game.createNpcType(internalNpcName)
local npcConfig = {}
npcConfig.name = internalNpcName
npcConfig.outfit = { lookType = 128 }
npcType:register(npcConfig)
"""


def _pip_install(pacote):
    """Instala um pacote via pip."""
    print(f"  Instalando {pacote}...")
    try:
        r = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', pacote],
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode == 0:
            print(f"  -> {pacote} instalado com sucesso")
            return True
        else:
            print(f"  -> ERRO ao instalar {pacote}:")
            print(f"     {r.stderr.strip()[-200:]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  -> TIMEOUT ao instalar {pacote}")
        return False
    except Exception as e:
        print(f"  -> ERRO: {e}")
        return False


def verificar_tree_sitter():
    """Verifica se tree-sitter esta funcional. Instala se necessario."""
    print("=" * 55)
    print("  SETUP TREE-SITTER — FASE 1 PatternMiner")
    print("=" * 55)

    # Verifica Python
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    print(f"\n[1] Python: {py_ver}")
    if sys.version_info < (3, 10):
        print("  AVISO: Python < 3.10 pode ter problemas com tree-sitter")

    # Verifica/Instala dependencias
    print(f"\n[2] Verificando dependencias...")
    todas_ok = True
    for req in REQUISITOS:
        spec = importlib.util.find_spec(req)
        if spec is not None:
            print(f"  {req}: OK ({spec.origin})")
        else:
            print(f"  {req}: NAO ENCONTRADO")
            # tree_sitter_languages e opcional
            if req != 'tree_sitter_languages':
                todas_ok = False

    for req in REQUISITOS_GRAMATICA:
        spec = importlib.util.find_spec(req)
        if spec is not None:
            print(f"  {req}: OK ({spec.origin})")
        else:
            print(f"  {req}: NAO ENCONTRADO")
            todas_ok = False

    if not todas_ok:
        print(f"\n[3] Instalando dependencias faltantes...")
        for req in REQUISITOS + REQUISITOS_GRAMATICA:
            spec = importlib.util.find_spec(req)
            if spec is None:
                # Converte nome de modulo para nome pip (tree_sitter_lua -> tree-sitter-lua)
                pip_name = req.replace('_', '-')
                _pip_install(pip_name)

    # Verifica novamente apos instalacao
    print(f"\n[4] Validando instalacao...")
    core_ok = True
    gramatica_ok = True
    for req in REQUISITOS:
        spec = importlib.util.find_spec(req)
        if spec is not None:
            print(f"  {req}: OK")
        elif req == 'tree_sitter_languages':
            print(f"  {req}: OPIONAL (indisponivel para Python 3.14)")
        else:
            print(f"  {req}: FALHA — tente manualmente: pip install {req}")
            core_ok = False

    for req in REQUISITOS_GRAMATICA:
        spec = importlib.util.find_spec(req)
        if spec is not None:
            print(f"  {req}: OK")
        else:
            print(f"  {req}: FALHA — tente manualmente: pip install {req.replace('_', '-')}")
            gramatica_ok = False

    if not core_ok:
        return False

    # Teste com parser Lua
    print(f"\n[5] Teste de parser Lua e C++...")
    try:
        from tree_sitter import Language, Parser

        # Lua parser
        import tree_sitter_lua
        lua_lang = Language(tree_sitter_lua.language())
        lua_parser = Parser(lua_lang)
        print(f"  Lua language: OK")
        print(f"  Lua parser: OK")

        # Parse do snippet Lua
        tree = lua_parser.parse(bytes(TESTE_LUA, 'utf-8'))
        root = tree.root_node
        print(f"  AST root: {root.type}")
        print(f"  Children: {root.child_count}")

        # Verifica se extraiu a funcao
        def _contar_tipos(node, tipos):
            tipo = node.type
            tipos[tipo] = tipos.get(tipo, 0) + 1
            for child in node.children:
                _contar_tipos(child, tipos)
            return tipos

        tipos = _contar_tipos(root, {})
        print(f"  Tipos encontrados: {list(tipos.keys())[:10]}...")
        print(f"  Parser Lua: FUNCIONAL")

        # C++ parser (se disponivel)
        try:
            import tree_sitter_cpp
            cpp_lang = Language(tree_sitter_cpp.language())
            cpp_parser = Parser(cpp_lang)
            print(f"  C++ language: OK")
            print(f"  C++ parser: OK")
        except ImportError:
            print(f"  C++ grammar: NAO INSTALADO (rode: pip install tree-sitter-cpp)")

        return True

    except ImportError as e:
        print(f"  ERRO: biblioteca nao encontrada: {e}")
        print(f"  Tente: pip install tree_sitter tree_sitter_languages")
        return False
    except Exception as e:
        print(f"  ERRO no teste de parser: {e}")
        print(f"  Possivel causa: falta de compilador C++ no sistema")
        print(f"  Solucao: instale 'Build Tools for Visual Studio' ou baixe o wheel pre-compilado")
        return False


if __name__ == '__main__':
    ok = verificar_tree_sitter()
    print()
    if ok:
        print("=" * 55)
        print("  SETUP CONCLUIDO — tree-sitter pronto para FASE 1")
        print("=" * 55)
        sys.exit(0)
    else:
        print("=" * 55)
        print("  SETUP FALHOU — veja as instrucoes acima")
        print("=" * 55)
        sys.exit(1)
