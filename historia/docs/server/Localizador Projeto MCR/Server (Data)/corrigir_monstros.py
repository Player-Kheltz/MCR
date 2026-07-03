#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, re, os
from pathlib import Path

# Pastas a ignorar
FORBIDDEN_DIRS = {
    'lib', 'libs', 'migrations', 'vcproj', 'tests', 'src', 'cmake',
    '.github', 'docker', 'docs', 'metrics', 'npclib', 'scripts/lib',
    'MCR Scripts', 'modules', 'json', 'reports', 'logs', 'XML'
}
FORBIDDEN_FILES = {
    'config.lua', 'global.lua', 'core.lua', 'stages.lua', 'update.lua',
    'titles.lua', 'achievements.lua', 'badges.lua',
    'register_npc_type.lua', 'register_monster_type.lua'
}

def is_allowed(filepath):
    parts = filepath.parts
    for part in parts:
        if part in FORBIDDEN_DIRS:
            return False
    return filepath.name not in FORBIDDEN_FILES and filepath.suffix == '.lua'

def carregar_mapeamento(caminho):
    """Lê o arquivo de tradução e devolve EN -> PT (apenas Latin‑1 válidas)."""
    mapeamento = {}
    ignoradas = []
    with open(caminho, 'r', encoding='utf-8') as f:
        for num, linha in enumerate(f, 1):
            linha = linha.strip()
            if not linha or '=' not in linha:
                continue
            en, pt = linha.split('=', 1)
            en = en.strip()
            pt = pt.strip()
            try:
                pt.encode('latin-1')
            except UnicodeEncodeError:
                ignoradas.append(f"Linha {num}: '{pt}'")
                continue
            mapeamento[en] = pt
    if ignoradas:
        print("Aviso: traduções ignoradas (não são Latin‑1):")
        for msg in ignoradas:
            print("  -", msg)
        print()
    return mapeamento

def obter_nome_pt_esperado(nome_ficheiro, mapeamento):
    """
    Converte o nome base do ficheiro (ex.: shaburak_demon) numa chave inglesa
    e devolve a tradução correcta.
    """
    # Converte underscores para espaços e coloca em maiúsculas iniciais
    en_guess = nome_ficheiro.replace('_', ' ').title()
    # Procura no mapeamento (chave exacta)
    if en_guess in mapeamento:
        return mapeamento[en_guess]
    # Tenta outras combinações: com "The", "A", etc. (casos especiais)
    # Se não encontrar, retorna None
    return None

def corrigir_ficheiro(filepath, nome_correto):
    """Substitui o nome actual do monstro pelo correcto, se necessário."""
    try:
        with open(filepath, 'rb') as f:
            raw = f.read()
    except Exception as e:
        print(f"Erro ao ler {filepath}: {e}")
        return False

    conteudo = raw.decode('latin-1')

    # Extrair o nome actual do monstro (de Game.createMonsterType("..."))
    match = re.search(r'Game\.createMonsterType\("([^"]*)"\)', conteudo)
    if not match:
        print(f"Aviso: createMonsterType não encontrado em {filepath}")
        return False

    nome_atual = match.group(1)

    # Se já está correcto, não faz nada
    if nome_atual == nome_correto:
        return False

    # Substituir TODAS as ocorrências do nome actual pelo nome correcto
    # (aspas duplas, descrições, etc.)
    conteudo_novo = conteudo.replace(f'"{nome_atual}"', f'"{nome_correto}"')
    # Também substitui fora de aspas? (ex.: monster.description = "Um ...")
    # A substituição acima já cobre a descrição porque o nome aparece entre aspas.
    # Mas pode haver o nome sem aspas em comentários? Ignoramos.

    if conteudo_novo != conteudo:
        # Escreve em Latin‑1
        with open(filepath, 'wb') as f:
            f.write(conteudo_novo.encode('latin-1', errors='replace'))
        return True
    return False

def main():
    if len(sys.argv) != 3:
        print("Uso: python corrigir_monstros.py <mapeamento.txt> <raiz_monsters>")
        sys.exit(1)

    map_file = sys.argv[1]
    root = Path(sys.argv[2])

    print("A carregar mapeamento...")
    mapeamento = carregar_mapeamento(map_file)
    print(f"Total de traduções válidas: {len(mapeamento)}")

    corrigidos = 0
    erros = 0
    for fp in root.rglob('*.lua'):
        if not is_allowed(fp):
            continue

        # Obter o nome base do ficheiro (sem extensão)
        nome_base = fp.stem.lower()  # ex.: "shaburak_demon"
        nome_pt = obter_nome_pt_esperado(nome_base, mapeamento)
        if nome_pt is None:
            # Se não encontrou a tradução, ignora (pode ser um ficheiro não listado)
            continue

        if corrigir_ficheiro(fp, nome_pt):
            print(f"✔ Corrigido: {fp}")
            corrigidos += 1
        else:
            # Se não foi corrigido, verifica se o nome actual já é o esperado
            # (silencioso, está correcto)
            pass

    print(f"\nTotal de ficheiros corrigidos: {corrigidos}")

if __name__ == '__main__':
    main()