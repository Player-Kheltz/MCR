#!/usr/bin/env python3
"""
Script: remover_level_items.py
Função: Remove TODAS as restrições de level dos itens do items.xml.
        Cria um backup automático do ficheiro original antes de modificar.
"""

import re
import shutil
import sys
from pathlib import Path

# Caminho para o items.xml (ajusta se necessário)
CAMINHO = Path("E:/Projeto MCR/Canary/data/items/items.xml")

def main():
    if not CAMINHO.exists():
        print(f"Erro: Ficheiro {CAMINHO} não encontrado.")
        sys.exit(1)

    # Cria backup
    backup = CAMINHO.with_suffix(".xml.bak")
    shutil.copy2(CAMINHO, backup)
    print(f"Backup criado: {backup}")

    # Lê o conteúdo do ficheiro
    with open(CAMINHO, "r", encoding="utf-8") as f:
        conteudo = f.read()

    # Remove qualquer <attribute key="level" value="..." /> (com ou sem espaços)
    # A regex captura a tag inteira e substitui por vazio
    padrao = re.compile(r'<attribute\s+key="level"\s+value="[^"]*"\s*/>')
    novo_conteudo = padrao.sub("", conteudo)

    # Remove linhas em branco extras (opcional)
    while "\n\n\n" in novo_conteudo:
        novo_conteudo = novo_conteudo.replace("\n\n\n", "\n\n")

    # Escreve o ficheiro modificado
    with open(CAMINHO, "w", encoding="utf-8") as f:
        f.write(novo_conteudo)

    print("Restrições de level removidas com sucesso!")

if __name__ == "__main__":
    main()