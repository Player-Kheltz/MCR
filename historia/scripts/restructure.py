#!/usr/bin/env python3
"""
restructure.py — Reorganiza a estrutura de docs/ do projeto MCR.

Uso:
    python scripts/restructure.py --dry-run    # Simula (nao altera nada)
    python scripts/restructure.py              # Executa

O que faz:
    1. Cria tools/ com scripts do Localizador
    2. Move assets/ para raiz (nao indexado pelo RAG)
    3. Reorganiza docs/ em guias/, tecnicas/, devlog/, referencia/
    4. Remove numeracao [] dos guias
    5. Atualiza CATALOG.md
    6. Usa git mv (preserva historico)
"""
import os, sys, shutil, subprocess, glob, re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRY_RUN = "--dry-run" in sys.argv

# Mapeamento: origem → destino (relativo ao BASE_DIR)
MOVES = []


def git_mv(src, dst):
    """Move arquivo preservando historico git."""
    src_full = os.path.join(BASE_DIR, src)
    dst_full = os.path.join(BASE_DIR, dst)
    os.makedirs(os.path.dirname(dst_full), exist_ok=True)
    if DRY_RUN:
        print(f"  mv {src} → {dst}")
    else:
        if os.path.exists(src_full):
            try:
                subprocess.run(["git", "mv", src, dst], cwd=BASE_DIR,
                               capture_output=True, text=True, timeout=30)
                print(f"  mv {src} → {dst}")
            except Exception as e:
                print(f"  ERRO ao mover {src}: {e}")


def create_dir(path):
    if DRY_RUN:
        print(f"  mkdir {path}")
    else:
        os.makedirs(os.path.join(BASE_DIR, path), exist_ok=True)


def remove_dir(path):
    if DRY_RUN:
        print(f"  rm -rf {path}")
    else:
        shutil.rmtree(os.path.join(BASE_DIR, path), ignore_errors=True)


def rename_guide(old_name):
    """Remove numeracao [] e converte para nome descritivo."""
    name = os.path.basename(old_name)
    # Remove [N] prefix
    name = re.sub(r'^\[\d+\]\s*', '', name)
    # Remove "MCR - " prefix
    name = re.sub(r'^MCR\s*-\s*', '', name)
    # Remove acentos e caracteres especiais
    name = name.replace('ç', 'c').replace('ã', 'a').replace('á', 'a')
    name = name.replace('é', 'e').replace('í', 'i').replace('ó', 'o')
    name = name.replace('ú', 'u').replace('ê', 'e').replace('õ', 'o')
    name = name.replace(' ', '-').replace('_', '-').lower()
    # Remove extensao, adiciona .md
    name = os.path.splitext(name)[0] + '.md'
    return name


def main():
    print(f"{'[DRY-RUN]' if DRY_RUN else '[EXECUTANDO]'} Restruturacao\n")

    # 1. Criar diretorios alvo
    create_dir("tools/localizador-server/scripts")
    create_dir("tools/localizador-data/dicionarios")
    create_dir("tools/localizador-data/scripts")
    create_dir("tools/map-editor")
    create_dir("assets/habilidades-spa5")
    create_dir("assets/mapa-mcr")
    create_dir("docs/guias")
    create_dir("docs/tecnicas")
    create_dir("docs/devlog")
    create_dir("docs/referencia")

    # 2. Mover assets antigos
    print("\n--- Movendo assets ---")
    assets_dir = os.path.join(BASE_DIR, "docs", "assets")
    if os.path.exists(assets_dir):
        for item in os.listdir(assets_dir):
            item_path = os.path.join(assets_dir, item)
            if os.path.isdir(item_path):
                dest = os.path.join("assets", item)
            else:
                dest = os.path.join("assets", item)
            git_mv(f"docs/assets/{item}", dest)

    # 3. Mover Localizador → tools/
    print("\n--- Movendo ferramentas ---")
    localizador = os.path.join(BASE_DIR, "docs", "Localizador Projeto MCR")
    if os.path.exists(localizador):
        # Map Editor
        me_orig = "docs/Localizador Projeto MCR/Map Editor (CodigoFonte)"
        if os.path.exists(os.path.join(BASE_DIR, me_orig)):
            for f in os.listdir(os.path.join(BASE_DIR, me_orig)):
                git_mv(f"{me_orig}/{f}", f"tools/map-editor/{f}")

        # Server (CodigoFonte) → tools/localizador-server/scripts
        sc_orig = "docs/Localizador Projeto MCR/Server (CodigoFonte)"
        if os.path.exists(os.path.join(BASE_DIR, sc_orig)):
            for f in os.listdir(os.path.join(BASE_DIR, sc_orig)):
                git_mv(f"{sc_orig}/{f}", f"tools/localizador-server/scripts/{f}")

        # Server (Data) → tools/localizador-data
        sd_orig = "docs/Localizador Projeto MCR/Server (Data)"
        if os.path.exists(os.path.join(BASE_DIR, sd_orig)):
            for f in os.listdir(os.path.join(BASE_DIR, sd_orig)):
                ext = os.path.splitext(f)[1].lower()
                if ext in ('.py',):
                    git_mv(f"{sd_orig}/{f}", f"tools/localizador-data/scripts/{f}")
                elif ext in ('.json', '.txt', '.xml'):
                    git_mv(f"{sd_orig}/{f}", f"tools/localizador-data/dicionarios/{f}")
                elif ext == '.pyc':
                    continue  # skip __pycache__
                else:
                    git_mv(f"{sd_orig}/{f}", f"tools/localizador-data/{f}")

    # 4. Reorganizar guias [0]-[13]
    print("\n--- Reorganizando guias ---")
    instrucoes = os.path.join(BASE_DIR, "docs", "MCR - Instruções")
    if os.path.exists(instrucoes):
        for f in sorted(os.listdir(instrucoes)):
            if f.startswith("[") and (f.endswith(".txt") or f.endswith(".md")):
                new_name = rename_guide(f)
                # Classifica por conteudo
                if "Documentação" in f or any(x in f for x in ["SPA", "Persegui", "Montaria", "Filosofia"]):
                    git_mv(f"docs/MCR - Instruções/{f}", f"docs/tecnicas/{new_name}")
                elif "DevLog" in f:
                    git_mv(f"docs/MCR - Instruções/{f}", f"docs/devlog/{new_name}")
                elif "Gabarito" in f or "Personalidade" in f or "Indice" in f or "Lista" in f:
                    git_mv(f"docs/MCR - Instruções/{f}", f"docs/referencia/{new_name}")
                else:
                    git_mv(f"docs/MCR - Instruções/{f}", f"docs/guias/{new_name}")

        # DevLog subdir
        devlog_src = os.path.join(instrucoes, "DevLog")
        if os.path.exists(devlog_src):
            for f in os.listdir(devlog_src):
                git_mv(f"docs/MCR - Instruções/DevLog/{f}", f"docs/devlog/{f}")

    # 5. Atualizar CATALOG.md se existir
    catalog = os.path.join(BASE_DIR, "docs", "CATALOG.md")
    if os.path.exists(catalog) and not DRY_RUN:
        with open(catalog, "r", encoding="utf-8") as f:
            content = f.read()
        # Atualiza caminhos (simplificado)
        content = content.replace("docs/MCR - Instruções/", "docs/")
        content = content.replace("docs/assets/", "assets/")
        content = content.replace("docs/Localizador Projeto MCR/", "tools/")
        with open(catalog, "w", encoding="utf-8") as f:
            f.write(content)
        print("  CATALOG.md atualizado")

    # 6. Remover diretorios vazios antigos
    print("\n--- Limpando diretorios antigos ---")
    for d in ["docs/assets", "docs/Localizador Projeto MCR", "docs/MCR - Instruções/DevLog"]:
        full = os.path.join(BASE_DIR, d)
        if os.path.exists(full) and not os.listdir(full):
            if DRY_RUN:
                print(f"  rmdir {d}")
            else:
                try:
                    os.rmdir(full)
                    print(f"  rmdir {d}")
                except OSError:
                    pass

    print(f"\n{'[DRY-RUN]' if DRY_RUN else '[OK]'} Restruturacao concluida!")
    print("Execute 'python scripts/rag_indexer.py --force' para reindexar o RAG")


if __name__ == "__main__":
    main()
