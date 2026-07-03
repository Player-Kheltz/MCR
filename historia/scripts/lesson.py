#!/usr/bin/env python3
"""
lesson.py — Cria licoes aprendidas automaticamente.

Uso interativo:
    python scripts/lesson.py

Uso direto:
    python scripts/lesson.py "Titulo" "Decisao" "Motivo" "Alternativas"
"""
import os, sys, datetime, glob, json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LESSONS_DIR = os.path.join(BASE_DIR, "docs", "lessons")


def ensure_dir():
    os.makedirs(LESSONS_DIR, exist_ok=True)


def list_lessons():
    files = sorted(glob.glob(os.path.join(LESSONS_DIR, "*.md")))
    for f in files:
        name = os.path.basename(f)
        if name in ("README.md", "recentes.md"):
            continue
        with open(f, "r", encoding="utf-8") as fh:
            first = fh.readline().strip().lstrip("# ")
        print(f"  {name}")
        print(f"    {first}")


def create_lesson(titulo, decisao, motivo, alternativas="", referencias=""):
    data = datetime.date.today().strftime("%Y-%m-%d")
    slug = titulo.lower().replace(" ", "-").replace("--", "-")[:40]
    filename = f"{data}_{slug}.md"
    filepath = os.path.join(LESSONS_DIR, filename)

    if os.path.exists(filepath):
        print(f"[AVISO] {filename} ja existe.")
        return

    alt_text = alternativas if alternativas else "(nenhuma informada)"
    ref_text = referencias if referencias else "(a adicionar)"

    content = f"""# {data} — {titulo}

## Decisao
{decisao}

## Motivo
{motivo}

## Alternativas rejeitadas
{alt_text}

## Referencias
{ref_text}
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    # Atualiza README.md
    readme_path = os.path.join(LESSONS_DIR, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            readme = f.read()
        insert = f"- [{data} — {titulo}]({filename})\n"
        if insert not in readme:
            # Insere depois do titulo ## Indice
            marker = "## Indice\n"
            if marker in readme:
                readme = readme.replace(marker, marker + insert)
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(readme)

    # Atualiza recentes.md (topo, mantendo as 5 mais recentes)
    recentes_path = os.path.join(LESSONS_DIR, "recentes.md")
    entries = []
    if os.path.exists(recentes_path):
        with open(recentes_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line.startswith("## "):
                entries.append(line)
    entries.insert(0, f"## {data} — {titulo}")
    entries = entries[:6]  # mantem titulo + 5 recentes

    recentes_content = "# Licoes Recentes\n\n" + "\n\n".join(entries) + "\n"
    with open(recentes_path, "w", encoding="utf-8") as f:
        f.write(recentes_content)

    print(f"[OK] Licao criada: {filename}")


def interactive():
    print("=== Criar Licao Aprendida ===\n")
    titulo = input("Titulo: ").strip()
    if not titulo:
        print("Cancelado.")
        return
    decisao = input("Decisao (1-2 frases): ").strip()
    motivo = input("Motivo da escolha: ").strip()
    print("Alternativas rejeitadas (pule se nao houver):")
    alt = input("> ").strip()
    print("Referencias (arquivos, opcional):")
    ref = input("> ").strip()
    create_lesson(titulo, decisao, motivo, alt, ref)


def main():
    ensure_dir()
    if len(sys.argv) >= 4:
        create_lesson(sys.argv[1], sys.argv[2], sys.argv[3],
                      sys.argv[4] if len(sys.argv) > 4 else "",
                      sys.argv[5] if len(sys.argv) > 5 else "")
    elif "--list" in sys.argv:
        list_lessons()
    else:
        interactive()


if __name__ == "__main__":
    main()
