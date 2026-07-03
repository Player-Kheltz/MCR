#!/usr/bin/env python3
"""
info.py — Consulta e extracao de informacao do MCR

Uso:
    python scripts/info.py search "termo"             # Busca em CATALOG.md qual doc fal do assunto
    python scripts/info.py doc "caminho" --section N   # Extrai secao especifica de um doc
    python scripts/info.py doc "caminho" --grep "texto" # Grep em doc com contexto
    python scripts/info.py grep "padrao" --server       # Grep no codigo do servidor
    python scripts/info.py grep "padrao" --client       # Grep no codigo do cliente
    python scripts/info.py index "caminho"              # Mostra estrutura de secoes do doc
    python scripts/info.py tree "caminho/pasta"         # Lista arvore de diretorio
    python scripts/info.py session                      # Mostra session.json
    python scripts/info.py status                       # Resumo do projeto (session + pendencias)
"""

import os
import sys
import json
import re
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
INST_DIR = os.path.join(DOCS_DIR, "MCR - Instruções")
CATALOG_PATH = os.path.join(DOCS_DIR, "CATALOG.md")
SESSION_PATH = os.path.join(DOCS_DIR, "session.json")
PENDENCIAS_PATH = os.path.join(INST_DIR, "DevLog", "Pendências.md")

SERVER_DIRS = [
    os.path.join(BASE_DIR, "Canary", "src"),
    os.path.join(BASE_DIR, "Canary", "data-canary", "scripts"),
]
CLIENT_DIRS = [
    os.path.join(BASE_DIR, "OTClient", "src"),
    os.path.join(BASE_DIR, "OTClient", "modules"),
]


def resolve_doc_path(rel_or_name):
    """Tenta encontrar o doc em varias locais."""
    candidates = [
        os.path.join(INST_DIR, rel_or_name),
        os.path.join(INST_DIR, rel_or_name + ".txt"),
        os.path.join(INST_DIR, rel_or_name + ".md"),
        os.path.join(DOCS_DIR, rel_or_name),
        os.path.join(DOCS_DIR, rel_or_name + ".txt"),
        os.path.join(DOCS_DIR, rel_or_name + ".md"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    # Se nada, tenta glob
    import glob
    pattern = os.path.join(INST_DIR, "**", "*" + rel_or_name + "*")
    matches = glob.glob(pattern, recursive=True)
    if matches:
        return matches[0]
    return None


def cmd_search(args):
    """Busca em CATALOG.md qual doc fal do assunto."""
    term = " ".join(args).lower()
    if not term:
        print("Termo de busca obrigatorio")
        return
    if not os.path.exists(CATALOG_PATH):
        print("CATALOG.md nao encontrado")
        return
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    results = []
    for line in lines:
        if term in line.lower():
            line_clean = line.strip().replace("|", "")
            if line_clean:
                results.append(line_clean)

    if results:
        print(f"Resultados para '{term}':\n")
        for r in results[:20]:
            try:
                print(f"  {r}")
            except UnicodeEncodeError:
                print(f"  {r.encode('cp1252', errors='replace').decode('cp1252')}")
    else:
        print(f"Nada encontrado para '{term}' no CATALOG.md")


def cmd_doc(args):
    """Extrai secao ou grep de um doc."""
    if not args:
        print("Uso: info.py doc \"caminho\" [--section N|--grep \"texto\"]")
        return

    doc_path = resolve_doc_path(args[0])
    if not doc_path:
        print(f"Doc nao encontrado: {args[0]}")
        return

    rest = args[1:]
    section_num = None
    grep_term = None
    for i, arg in enumerate(rest):
        if arg == "--section" and i + 1 < len(rest):
            section_num = rest[i + 1]
        elif arg == "--grep" and i + 1 < len(rest):
            grep_term = rest[i + 1]

    with open(doc_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if section_num:
        inside = False
        in_sub = False
        for line in lines:
            stripped = line.strip()
            if re.match(r"^#{1,3}\s+" + re.escape(str(section_num)) + r"\.", stripped):
                inside = True
                print(line, end="")
                continue
            if inside:
                if re.match(r"^#{1,3}\s+\d+\.", stripped):
                    # Proxima secao principal
                    if not in_sub:
                        break
                if re.match(r"^#{1,3}\s+", stripped):
                    in_sub = True
                print(line, end="")
                continue
    elif grep_term:
        for i, line in enumerate(lines):
            if grep_term.lower() in line.lower():
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                for j in range(start, end):
                    prefix = ">" if j == i else " "
                    print(f"{prefix} {j+1:4d}: {lines[j]}", end="")
                print()
    else:
        print(f"Doc: {doc_path} ({len(lines)} linhas)")
        print("Use --section N ou --grep \"texto\" para filtrar")


def cmd_grep(args):
    """Grep no codigo-fonte."""
    if not args:
        print("Uso: info.py grep \"padrao\" [--server|--client]")
        return

    pattern = args[0]
    target = "server"
    if "--client" in args:
        target = "client"
    if "--server" in args:
        target = "server"

    dirs = SERVER_DIRS if target == "server" else CLIENT_DIRS

    for d in dirs:
        if not os.path.exists(d):
            continue
        result = subprocess.run(
            ["findstr", "/s", "/n", "/i", pattern],
            capture_output=True, text=True, shell=True, cwd=d
        )
        if result.stdout:
            lines = result.stdout.strip().split("\n")
            print(f"--- {d} ---")
            for line in lines[:15]:
                print(f"  {line}")
            if len(lines) > 15:
                print(f"  ... e mais {len(lines) - 15} resultados")
            print()


def cmd_index(args):
    """Mostra estrutura de secoes de um doc."""
    if not args:
        print("Uso: info.py index \"caminho\"")
        return
    doc_path = resolve_doc_path(args[0])
    if not doc_path:
        print(f"Doc nao encontrado: {args[0]}")
        return

    with open(doc_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"Indice de: {doc_path}\n")
    for line in lines:
        stripped = line.strip()
        if re.match(r"^#{1,4}\s", stripped):
            level = len(re.match(r"^#+", stripped).group())
            prefix = "  " * (level - 1) + "-"
            title = stripped.lstrip("# ")
            print(f"{prefix} {title}")


def cmd_tree(args):
    """Lista arvore de diretorio."""
    path = " ".join(args) if args else "."
    full_path = os.path.join(BASE_DIR, path)
    if not os.path.exists(full_path):
        print(f"Caminho nao encontrado: {full_path}")
        return

    for root, dirs, files in os.walk(full_path):
        if ".git" in dirs:
            dirs.remove(".git")
        level = root.replace(full_path, "").count(os.sep)
        indent = "  " * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = "  " * (level + 1)
        for file in files[:10]:
            print(f"{subindent}{file}")
        if len(files) > 10:
            print(f"{subindent}... e mais {len(files) - 10} arquivos")


def cmd_session():
    if os.path.exists(SESSION_PATH):
        with open(SESSION_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("(session.json nao encontrado)")


def cmd_status():
    """Resumo do projeto: session + pendencias."""
    if os.path.exists(SESSION_PATH):
        with open(SESSION_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"Task atual: {data.get('task', 'N/A')}")
        print(f"Proximos passos:")
        for step in data.get("next_steps", []):
            print(f"  - {step}")
    print()
    if os.path.exists(PENDENCIAS_PATH):
        with open(PENDENCIAS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if "- [ ]" in line:
                    print(f"  Pend: {line.strip().lstrip('- [ ]')}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "search": cmd_search,
        "doc": cmd_doc,
        "grep": cmd_grep,
        "index": cmd_index,
        "tree": cmd_tree,
        "session": lambda a: cmd_session(),
        "status": lambda a: cmd_status(),
    }

    if cmd in commands:
        commands[cmd](args)
    else:
        print(f"[ERRO] Comando desconhecido: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
