#!/usr/bin/env python3
# listar arquivos .lua no diretorio MCR scripts e mostrar o nome e tamanho
import os, sys, json

def main():
    import os
import os

for filename in os.listdir("MCR/scripts"):
    if filename.endswith(".lua"):
        filepath = os.path.join("MCR/scripts", filename)
        size = os.path.getsize(filepath)
        print(f"Nome: {filename}, Tamanho: {size} bytes")
#```

if __name__ == '__main__':
    main()
