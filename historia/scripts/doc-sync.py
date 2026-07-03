#!/usr/bin/env python3
"""
doc-sync.py — Sincroniza cabeçalhos >> CATALOG nos docs e regenera CATALOG.md

Uso:
    python scripts/doc-sync.py              # executa para valer
    python scripts/doc-sync.py --dry-run    # só mostra o que faria
    python scripts/doc-sync.py --headers    # só atualiza cabeçalhos
    python scripts/doc-sync.py --catalog    # só regenera CATALOG.md
"""

import os
import sys
import re
import glob
from datetime import date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs", "MCR - Instru\u00e7\u00f5es")
CATALOG_PATH = os.path.join(BASE_DIR, "docs", "CATALOG.md")

HEADER_RE = re.compile(r'^>> CATALOG tags=(?P<tags>.+?) updated=(?P<date>\S+)')


def find_all_docs():
    """Descobre todos os arquivos de doc no diretorio."""
    pattern = os.path.join(DOCS_DIR, "**", "*")
    all_files = []
    for f in glob.glob(pattern, recursive=True):
        if os.path.isfile(f) and not f.endswith(".py"):
            rel = os.path.relpath(f, DOCS_DIR)
            all_files.append(rel)
    return all_files


# Metadados associados por nome normalizado (lowercase, sem acentos)
def normalize_key(name):
    """Normaliza nome de arquivo para matching case-insensitive."""
    s = name.lower()
    s = s.replace("\u00e7", "c").replace("\u00e3", "a").replace("\u00f5", "o")
    s = s.replace("\u00e1", "a").replace("\u00e9", "e").replace("\u00ed", "i")
    s = s.replace("\u00f3", "o").replace("\u00fa", "u").replace("\u00e0", "a")
    s = s.replace("\u00f4", "o").replace("\u00ea", "e").replace("\u00ea", "e")
    s = s.replace("\u2013", "-").replace("\u2011", "-")
    return s


DOC_METADATA = {
    "[0] mcr - indice geral.txt": {
        "tags": "index, overview, geral",
        "summary": "Indice geral do projeto, pilares permanentes, estado da implementacao e indice de todos os guias",
    },
    "[1] mcr - guia de compilacao (servidor).txt": {
        "tags": "compilation, server, canary, build",
        "summary": "Compilacao do servidor Canary com SPA e sistema de perseguicao multi-piso",
    },
    "[2] mcr - guia de compilacao (cliente).txt": {
        "tags": "compilation, client, otclient, build",
        "summary": "Compilacao do OTClient com opcodes e mascara de Alma",
    },
    "[3] mcr - guia de configuracao (servidor e rede).txt": {
        "tags": "config, network, server",
        "summary": "Configuracao de portas, storages, opcodes e OTCFeatures",
    },
    "[4] mcr - guia do login server.txt": {
        "tags": "login-server, auth, api",
        "summary": "API REST do Login Server, endpoints, error codes e guest accounts",
    },
    "[5] mcr - guia de interface (otui e lua cliente).txt": {
        "tags": "interface, otui, lua-client",
        "summary": "Sintaxe OTUI, fontes, codificacao, opcodes visuais",
    },
    "[6] mcr - guia de narrativa e dialogos.txt": {
        "tags": "narrative, npc, dialogs",
        "summary": "Imersao narrativa, personalidade de NPCs, sistema de cores",
    },
    "[7] mcr - guia de quests (sistema hibrido sqh).txt": {
        "tags": "quests, sqh, missions",
        "summary": "Criacao de missoes com HUD, toasts e integracao SPA",
    },
    "[8] mcr - guia de criacao de conta e personagem.txt": {
        "tags": "account, character, oracle, alma",
        "summary": "Fluxo do Salao dos Destinos, Oráculo, Alma, pronomes",
    },
    "[9] mcr - guia de banco de dados e infraestrutura.txt": {
        "tags": "database, schema, infrastructure",
        "summary": "Schema do banco, tabelas do SPA, populacao inicial de dominios",
    },
    "[10] mcr - guia de traducao e localizacao (pt-br).txt": {
        "tags": "translation, localization, pt-br, encoding",
        "summary": "Codificacao por tipo de arquivo, error codes, pipeline de traducao",
    },
    "[11] mcr - guia de experiencia do jogador.txt": {
        "tags": "player-experience, journey, overview",
        "summary": "A jornada completa do jogador, do Alma ao heroi",
    },
    "[12] mcr - guia de conteudo inicial e tutorial.txt": {
        "tags": "tutorial, eridanus, new-player",
        "summary": "Tutorial de Eridanus, NPCs, missoes iniciais",
    },
    "[13] mcr - guia de criacao de habilidades.txt": {
        "tags": "skills, abilities, game-design",
        "summary": "Filosofia de design, estrutura por hierarquia, pacotes tematicos, processo de geracao",
    },
    "[documentacao] mcr - documentacao tecnica do motor spa.txt": {
        "tags": "spa, technical, api, progressao, dominios",
        "summary": "Documentacao tecnica completa de todas as APIs C++ do SPA, metodos e sistemas",
    },
    "[documentacao] mcr - filosofia do spa - sistema de progressao do aventureiro.txt": {
        "tags": "spa, philosophy, design, vision",
        "summary": "Visao filosofica e canonica do Sistema de Progressao do Aventureiro",
    },
    "[documentacao] mcr - sistema de montaria como summon (mountsummon).txt": {
        "tags": "mounts, summon, pet",
        "summary": "Sistema de montaria como summon persistente: eventos C++, Lua mount_summon.lua, PetSystem",
    },
    "[documentacao] mcr - sistema de perseguicao multi-piso.txt": {
        "tags": "multi-piso, pursuit, pathfinding, monster-ai, crowd-control",
        "summary": "Sistema de perseguicao multi-piso v8 com GlobalMonsterMap, cercamento, anti-ping-pong",
    },
    "[personalidade] mcr - personalidade e identidade de dominios.txt": {
        "tags": "domains, design, narrative, identity",
        "summary": "Guia universal de design narrativo e mecanico para criacao de dominios",
    },
    "[gabarito] habilidade gabarito.txt": {
        "tags": "skills, template, reference, game-design",
        "summary": "Referencia maxima de todos os campos e regras para criacao de habilidades",
    },
    "[aquivo complementar] lista de items uteis.txt": {
        "tags": "items, reference, list",
        "summary": "Lista com mais de 3000 itens traduzidos, IDs e atributos",
    },
    "devlog\\sistema multi-piso.md": {
        "tags": "multi-piso, los, battlelist, navigation, combat, monster-ai",
        "summary": "Decisoes e historico do sistema multi-piso: LOS, BattleList, perseguicao, navegacao do jogador",
    },
    "devlog\\sistema de montarias.md": {
        "tags": "mounts, summon, devlog",
        "summary": "Decisoes e historico do sistema MountSummon",
    },
    "devlog\\sistema de codificacao.md": {
        "tags": "encoding, utf-8, devlog",
        "summary": "Decisoes e historico sobre encoding e padronizacao UTF-8",
    },
    "devlog\\pendencias.md": {
        "tags": "todo, next-steps, roadmap, pendencias",
        "summary": "Estado atual do projeto, tarefas pendentes e decisoes em aberto",
    },
}


def get_header(tags, updated=None):
    if updated is None:
        updated = date.today().strftime("%Y-%m-%d")
    return f">> CATALOG tags={tags} updated={updated}"


def parse_existing_header(line):
    m = HEADER_RE.match(line.strip())
    if m:
        return m.group("tags"), m.group("date")
    return None, None


def match_metadata(relpath):
    """Procura metadados para um arquivo, ignorando case e acentos."""
    norm = normalize_key(relpath)
    for key, meta in DOC_METADATA.items():
        if normalize_key(key) == norm:
            return meta
    return None


def sync_headers(dry_run=False):
    """Adiciona ou atualiza cabecalhos >> CATALOG no topo de cada doc."""
    modified = []
    files_found = find_all_docs()

    for relpath in sorted(files_found):
        meta = match_metadata(relpath)
        if meta is None:
            continue

        abspath = os.path.join(DOCS_DIR, relpath)

        with open(abspath, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.splitlines()
        first_line = lines[0] if lines else ""
        existing_tags, existing_date = parse_existing_header(first_line)

        new_header = get_header(meta["tags"])

        if existing_tags is not None:
            if existing_tags == meta["tags"]:
                continue  # ja esta correto
            new_header = get_header(meta["tags"], updated=existing_date)
            new_content = "\n".join([new_header] + lines[1:])
        else:
            new_content = new_header + "\n" + content

        if not content.endswith("\n"):
            new_content += "\n"

        if not dry_run:
            with open(abspath, "w", encoding="utf-8") as f:
                f.write(new_content)

        status = "OK" if not dry_run else "DRY"
        tag_action = f"+tags: {meta['tags']}" if existing_tags is None else f"tags: {existing_tags} -> {meta['tags']}"
        safe_relpath = relpath.encode("cp1252", errors="replace").decode("cp1252", errors="replace")
        print(f"[{status}] {safe_relpath}  ({tag_action})")
        modified.append(relpath)

    return modified


def build_catalog_index(only_existing=True):
    rows = []
    all_files = find_all_docs() if only_existing else DOC_METADATA.keys()

    for relpath in sorted(all_files):
        meta = match_metadata(relpath)
        if meta is None:
            continue

        abspath = os.path.join(DOCS_DIR, relpath)
        if not os.path.exists(abspath):
            continue

        with open(abspath, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
        _, updated = parse_existing_header(first_line)
        if updated is None:
            updated = date.today().strftime("%Y-%m-%d")

        rows.append((relpath, meta["tags"], updated, meta["summary"]))
    return rows


def generate_catalog(dry_run=False):
    """Regenera CATALOG.md por completo."""
    today = date.today().strftime("%Y-%m-%d")
    index_rows = build_catalog_index()

    decision_map = [
        ("LOS, visao, BattleList, projeteis, multi-piso",
         "DevLog/Sistema Multi-Piso.md"),
        ("SPA, dominios, habilidades, progressao, Maestria",
         "[Documentacao] MCR - Documentacao Tecnica do Motor SPA.txt + [Documentacao] MCR - Filosofia do SPA...txt"),
        ("Montaria como summon, pets",
         "[Documentacao] MCR - Sistema de Montaria como Summon (MountSummon).txt + DevLog/Sistema de Montarias.md"),
        ("Perseguicao multi-piso, pathfinding, monster AI",
         "[Documentacao] MCR - Sistema de Perseguicao Multi-Piso.txt + DevLog/Sistema Multi-Piso.md"),
        ("Compilacao (servidor)",
         "AGENTS.md §8 + Guia [1]"),
        ("Compilacao (cliente)",
         "AGENTS.md §8 + Guia [2]"),
        ("Configuracao de servidor/rede",
         "Guia [3]"),
        ("Login Server, API REST, autenticacao",
         "Guia [4]"),
        ("Interface OTUI, Lua cliente",
         "Guia [5]"),
        ("Narrativa, dialogos, NPCs, cores",
         "Guia [6] + Guia [11]"),
        ("Quests, SQH, HUD, toasts",
         "Guia [7]"),
        ("Criacao de conta, personagem, Oráculo",
         "Guia [8]"),
        ("Banco de dados, schema MySQL",
         "Guia [9]"),
        ("Traducao, localizacao, encoding",
         "Guia [10] + DevLog/Sistema de Codificacao.md"),
        ("Criacao de habilidades, game design",
         "Guia [13] + [Gabarito] Habilidade Gabarito.txt"),
        ("Identidade de dominios, design narrativo",
         "[Personalidade] MCR - Personalidade e Identidade de Dominios.txt"),
        ("Lista de itens, IDs, atributos",
         "[Aquivo Complementar] Lista de Items Uteis.txt"),
        ("Visao geral do projeto, pilares, roadmap",
         "Guia [0] (Indice Geral)"),
        ("Tarefas pendentes, estado atual, planejamento",
         "DevLog/Pendencias.md"),
        ("Tutorial, Eridanus, novo jogador",
         "Guia [12]"),
    ]

    lines = []
    lines.append("# Catalogo de Documentacao MCR")
    lines.append("")
    lines.append(f"> Gerado por scripts/doc-sync.py em {today}")
    lines.append("> Leia este arquivo no inicio de toda conversa para saber quais docs carregar.")
    lines.append("")
    lines.append("## Tabela de Decisao Rapida")
    lines.append("")
    lines.append("| Sua tarefa envolve... | Leia |")
    lines.append("|---|---|")
    for task, docs_ref in decision_map:
        lines.append(f"| {task} | {docs_ref} |")
    lines.append("")
    lines.append("## Indice Completo")
    lines.append("")
    lines.append("| Arquivo | Tags | Atualizado | Resumo |")
    lines.append("|---|---|---|---|")
    for relpath, tags, updated, summary in index_rows:
        escaped_tags = tags.replace("|", "\\|")
        escaped_summary = summary.replace("|", "\\|")
        lines.append(f"| `{relpath}` | `{escaped_tags}` | {updated} | {escaped_summary} |")
    lines.append("")

    content = "\n".join(lines)

    if not dry_run:
        with open(CATALOG_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[OK] CATALOG.md regenerado -- {len(index_rows)} entradas")
    else:
        print(f"[DRY] CATALOG.md seria regenerado -- {len(index_rows)} entradas")
        print()
        # Mostra so as primeiras linhas no dry-run
        for line in lines[:20]:
            print(line)
        print("...")


def main():
    dry_run = "--dry-run" in sys.argv
    only_headers = "--headers" in sys.argv
    only_catalog = "--catalog" in sys.argv

    if not only_catalog:
        print("=== Sincronizando cabecalhos >> CATALOG ===")
        modified = sync_headers(dry_run)
        if not modified:
            print("Nenhum cabecalho precisa de atualizacao.")
        print()

    if not only_headers:
        print("=== Regenerando CATALOG.md ===")
        generate_catalog(dry_run)

    if dry_run:
        print("\n-- Modo --dry-run -- nada foi alterado.")
    else:
        print("\nConcluido.")


if __name__ == "__main__":
    main()
