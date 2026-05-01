#!/usr/bin/env python3
"""
Remove blocos inteiros de ficheiros de dados (extraido/traduzido/reparado)
cujos caminhos correspondem a padrões proibidos (cabeçalhos, títulos, config).
Uso: python removedor.py arquivo1.txt arquivo2.txt ...
"""
import sys
from pathlib import Path

# Padrões de caminhos a excluir (verificados no nome do ficheiro ou no caminho completo)
FORBIDDEN_PATTERNS = [
    # Extensões de cabeçalho
    ".hpp",
    ".h",
    # Ficheiros de configuração que contêm identificadores sensíveis
    "configmanager.cpp",
    # Títulos e conquistas
    "player_title.cpp",
    "player_title.hpp",
    "titles.lua",
    "achievements.lua",
    "badges.lua",
    "title_data.lua",
    "achievement_data.lua",
    "player_titles.lua",
    "mount_titles.lua",
    # Ficheiros de binding Lua (muito sensíveis)
    "lua_functions_loader.cpp",
    "creature_functions.cpp",
    "player_functions.cpp",
    "monster_functions.cpp",
    "npc_functions.cpp",
    "game_functions.cpp",
    "global_functions.cpp",
    # Bloquear toda a pasta lua
    "/lua/",
]

def is_forbidden(filepath: str) -> bool:
    """Retorna True se o caminho corresponde a algum padrão proibido."""
    fp_lower = filepath.lower()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in fp_lower:
            return True
    # Bloquear qualquer arquivo que contenha 'title' ou 'achievement' no nome do ficheiro
    stem = Path(filepath).stem.lower()
    if 'title' in stem or 'achievement' in stem:
        return True
    return False

def process_file(data_file: str) -> int:
    """Remove seções proibidas do ficheiro de dados; retorna número de seções removidas."""
    with open(data_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    skip_section = False
    removed = 0

    for line in lines:
        stripped = line.strip()
        # Deteta início de secção: [caminho]
        if stripped.startswith('[') and stripped.endswith(']'):
            caminho = stripped[1:-1]
            skip_section = is_forbidden(caminho)
            if skip_section:
                removed += 1
                continue   # não escreve a linha de cabeçalho nem o bloco
            else:
                new_lines.append(line)
        else:
            if not skip_section:
                new_lines.append(line)
            # Se skip_section é True, simplesmente descarta a linha

    if removed > 0:
        with open(data_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"✔ {data_file}: {removed} seção(ões) removida(s).")
    else:
        print(f"ℹ️ {data_file}: nenhuma seção proibida encontrada.")
    return removed

def main():
    if len(sys.argv) < 2:
        print("Uso: python removedor.py <arquivo1> <arquivo2> ...")
        return

    for fname in sys.argv[1:]:
        process_file(fname)

if __name__ == '__main__':
    main()