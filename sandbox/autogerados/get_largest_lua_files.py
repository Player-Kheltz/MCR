#!/usr/bin/env python3
# listar arquivos .lua no diretorio MCR scripts e mostrar os 5 maiores
# Criado pelo MCR-DevIA
import os

def get_largest_lua_files(directory, num_files=5):
    lua_files = [(f, os.path.getsize(os.path.join(directory, f))) for f in os.listdir(directory) if f.endswith('.lua')]
    largest_files = sorted(lua_files, key=lambda x: x[1], reverse=True)[:num_files]
    return largest_files

directory_path = 'MCR/scripts'
largest_lua_files = get_largest_lua_files(directory_path)

for file, size in largest_lua_files:
    print(f'{file}: {size} bytes')