#!/usr/bin/env python3
"""
find_example.py — Smart Example Finder v1.0
Dado um tipo de tarefa, encontra os melhores arquivos de exemplo no projeto.

Uso: python scripts/find_example.py "criar NPC" --project .
      python scripts/find_example.py "OTUI layout" --project .
      python scripts/find_example.py "SHC habilidade" --project .
"""
import os, sys, json, re, argparse
from pathlib import Path

# Mapa de conhecimento: tipo de tarefa → padrões de busca
TASK_PATTERNS = {
    # === MCR/TIBIA ===
    "npc": {
        "keywords": ["npc", "vendedor", "shop", "trader", "selfSay", "NPCHandler"],
        "extensions": [".lua"],
        "priority_dirs": ["data/npc", "data/scripts/npc", "data-canary/scripts/npc"],
        "description": "NPC scripts for Canary server"
    },
    "talkaction": {
        "keywords": ["talkaction", "onSay", "TalkAction"],
        "extensions": [".lua"],
        "priority_dirs": ["data/scripts/talkactions", "data-canary/scripts/MCR"],
        "description": "TalkAction commands"
    },
    "otui": {
        "keywords": ["UIWidget", "anchors", "margin", "padding"],
        "extensions": [".otui"],
        "priority_dirs": ["modules"],
        "description": "OTClient UI layouts"
    },
    "shc_hability": {
        "keywords": ["HABILIDADES[", "efeitoConfig", "postura", "niveis", "sinergias"],
        "extensions": [".lua"],
        "priority_dirs": ["Canary/data-canary/scripts/MCR/SPA/habilidades"],
        "description": "SHC ability definitions (ex: fogo.lua, gelo.lua, terra.lua)"
    },
    "spa_domain": {
        "keywords": ["SPA.registerDomain", "DOMINIO_", "dominio"],
        "extensions": [".lua"],
        "priority_dirs": ["data-canary/scripts/MCR/SPA/core"],
        "description": "SPA domain registration"
    },
    "quest_sqh": {
        "keywords": ["quest", "stage", "SQH", "mission", "reward"],
        "extensions": [".lua"],
        "priority_dirs": ["data-canary/scripts/MCR/quests", "data/scripts/quests"],
        "description": "Quest system (SQH)"
    },
    "database_schema": {
        "keywords": ["CREATE TABLE", "schema", "mysql"],
        "extensions": [".sql", ".lua"],
        "priority_dirs": ["data/migrations", "data/database"],
        "description": "Database schemas"
    },
    "item": {
        "keywords": ["ItemType", "items.xml", "itemid"],
        "extensions": [".xml", ".lua"],
        "priority_dirs": ["data/items", "data-canary/items"],
        "description": "Item definitions"
    },
    "monster": {
        "keywords": ["monster", "creature", "MonsterType"],
        "extensions": [".xml", ".lua"],
        "priority_dirs": ["data/monster", "data-canary/monster"],
        "description": "Monster definitions"
    },
    "cplusplus_class": {
        "keywords": ["class", "public:", "private:", "virtual"],
        "extensions": [".h", ".hpp", ".cpp"],
        "priority_dirs": ["src"],
        "description": "C++ class definitions"
    },
    "cmake_build": {
        "keywords": ["cmake_minimum_required", "project", "add_library", "add_executable"],
        "extensions": ["CMakeLists.txt"],
        "priority_dirs": ["."],
        "description": "CMake build files"
    },
    "python_script": {
        "keywords": ["def ", "import ", "class ", "#!/usr/bin"],
        "extensions": [".py"],
        "priority_dirs": ["scripts", "."],
        "description": "Python scripts"
    },
    "windows_powershell": {
        "keywords": ["Write-Output", "Get-ChildItem", "New-Item", "param("],
        "extensions": [".ps1", ".bat", ".cmd"],
        "priority_dirs": ["scripts", "."],
        "description": "Windows PowerShell scripts"
    },
}

# Mapa de tipos de projeto
# Diretorios para EXCLUIR da busca (cache, backup, node_modules, etc)
EXCLUDE_DIRS = {"backup", "cache", "node_modules", ".git", "__pycache__", "build", ".rag_db",
                "vcpkg_installed", "packages", "Download", "downloads", "temp", "tmp"}

PROJECT_PROFILES = {
    "canary_tibia": {
        "name": "Canary TFS Server",
        "detect_files": ["Canary/vcproj/canary.vcxproj", "config.lua.dist"],
        "patterns": ["npc", "talkaction", "item", "monster", "quest_sqh",
                     "database_schema", "cplusplus_class", "cmake_build"]
    },
    "otclient": {
        "name": "OTClient",
        "detect_files": ["OTClient/vc17/otclient.vcxproj"],
        "patterns": ["otui", "cplusplus_class", "cmake_build"]
    },
    "mcr_spa": {
        "name": "MCR - SPA System",
        "detect_files": ["Canary/data-canary/scripts/MCR/SPA/core/0_init.lua"],
        "patterns": ["shc_hability", "spa_domain", "talkaction", "npc"]
    },
    "python_project": {
        "name": "Python Project",
        "detect_files": ["setup.py", "requirements.txt", "pyproject.toml"],
        "patterns": ["python_script"]
    },
    "generic": {
        "name": "Generic Project",
        "detect_files": [],
        "patterns": ["cplusplus_class", "python_script", "windows_powershell"]
    }
}


def detect_project_type(project_dir):
    """Detecta o tipo de projeto baseado em arquivos presentes."""
    for ptype, profile in PROJECT_PROFILES.items():
        for f in profile["detect_files"]:
            if os.path.exists(os.path.join(project_dir, f)):
                return ptype, profile
    return "generic", PROJECT_PROFILES["generic"]


def find_task_type(query):
    """Classifica a query em um tipo de tarefa conhecido."""
    query_lower = query.lower()
    
    # Mapeamento direto de palavras-chave para tipos
    keyword_map = {
        "npc": "npc", "vendedor": "npc", "shop": "npc", "trader": "npc",
        "talkaction": "talkaction", "comando": "talkaction", "!": "talkaction",
        "otui": "otui", "layout": "otui", "interface": "otui", "ui": "otui",
        "habilidade": "shc_hability", "ability": "shc_hability", "shc": "shc_hability",
        "dominio": "spa_domain", "domain": "spa_domain", "spa": "spa_domain",
        "quest": "quest_sqh", "missao": "quest_sqh", "mission": "quest_sqh",
        "sql": "database_schema", "mysql": "database_schema", "tabela": "database_schema",
        "item": "item", "item type": "item",
        "monstro": "monster", "monster": "monster", "creature": "monster",
        "class": "cplusplus_class", "header": "cplusplus_class", "hpp": "cplusplus_class",
        "cmake": "cmake_build", "build": "cmake_build", "compil": "cmake_build",
        "python": "python_script", "flask": "python_script",
        "powershell": "windows_powershell", "ps1": "windows_powershell", "batch": "windows_powershell",
    }
    
    for word in query_lower.split():
        if word in keyword_map:
            return keyword_map[word]
    
    # Fallback: fuzzy match
    scores = {}
    for ttype, pattern in TASK_PATTERNS.items():
        score = sum(1 for kw in pattern["keywords"] if kw.lower() in query_lower)
        if score > 0:
            scores[ttype] = score
    
    if scores:
        return max(scores, key=scores.get)
    return None


def find_examples(project_dir, query, top_k=3, max_chars=800):
    """Encontra exemplos relevantes para uma query."""
    task_type = find_task_type(query)
    if not task_type:
        return json.dumps({"error": "Nao foi possivel classificar a tarefa", "query": query})
    
    pattern = TASK_PATTERNS.get(task_type)
    if not pattern:
        return json.dumps({"error": f"Tipo de tarefa desconhecido: {task_type}"})
    
    project_type, project_profile = detect_project_type(project_dir)
    
    results = []
    searched_dirs = set()
    
    def _should_exclude(dirname):
        return dirname.lower() in EXCLUDE_DIRS or dirname.startswith(".")
    
    # Busca nos diretorios prioritarios
    for rel_dir in pattern["priority_dirs"]:
        search_path = os.path.join(project_dir, rel_dir)
        if not os.path.exists(search_path):
            continue
        searched_dirs.add(os.path.normpath(search_path))
        
        for root, dirs, files in os.walk(search_path):
            # Filtra diretorios excluidos (modifica dirs in-place para evitar os.walk entrar neles)
            dirs[:] = [d for d in dirs if not _should_exclude(d)]
            
            if len(results) >= top_k:
                break
            for fname in files:
                if len(results) >= top_k:
                    break
                ext = os.path.splitext(fname)[1].lower()
                if ext not in pattern["extensions"]:
                    continue
                
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read(max_chars)
                    
                    keyword_score = sum(1 for kw in pattern["keywords"] if kw.lower() in content.lower())
                    if keyword_score >= 1:
                        rel_path = os.path.relpath(fpath, project_dir)
                        results.append({
                            "path": rel_path,
                            "score": keyword_score,
                            "content": content[:max_chars],
                            "task_type": task_type,
                            "description": pattern["description"]
                        })
                except:
                    continue
    
    # Se nao achou nos prioritarios, busca ampla (excluindo Backup e system dirs)
    if not results:
        for ext in pattern["extensions"]:
            for root, dirs, files in os.walk(project_dir):
                dirs[:] = [d for d in dirs if not _should_exclude(d)]
                
                if len(results) >= top_k:
                    break
                norm_root = os.path.normpath(root)
                if norm_root in searched_dirs:
                    continue
                for fname in files:
                    if len(results) >= top_k:
                        break
                    if not fname.endswith(ext):
                        continue
                    
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read(max_chars)
                        
                        keyword_score = sum(1 for kw in pattern["keywords"] if kw.lower() in content.lower())
                        if keyword_score >= 2:
                            rel_path = os.path.relpath(fpath, project_dir)
                            results.append({
                                "path": rel_path,
                                "score": keyword_score,
                                "content": content[:max_chars],
                                "task_type": task_type,
                                "description": pattern["description"]
                            })
                    except:
                        continue
    
    # Ordena por score
    results.sort(key=lambda r: r["score"], reverse=True)
    
    output = {
        "query": query,
        "task_type": task_type,
        "project_type": project_type,
        "project_name": project_profile["name"],
        "total_examples": len(results),
        "examples": results[:top_k],
        "instruction": f"Use os exemplos acima como referencia para criar/implementar {query}. Siga o formato exato dos exemplos."
    }
    
    return json.dumps(output, ensure_ascii=False, indent=2)


def cmd(query, project_dir=None, top_k=3):
    """Funcao principal para ser chamada por agentes."""
    if not project_dir:
        project_dir = os.getcwd()
    
    result = find_examples(project_dir, query, top_k)
    data = json.loads(result)
    
    if "error" in data:
        print(f"[find_example] {data['error']}")
        return ""
    
    print(f"[find_example] Tipo: {data['task_type']} | Projeto: {data['project_name']}")
    print(f"[find_example] Encontrados {data['total_examples']} exemplos")
    
    output = []
    for ex in data["examples"]:
        output.append(f"=== EXEMPLO: {ex['path']} (score:{ex['score']}) ===")
        output.append(ex["content"])
        output.append("")
    
    return "\n".join(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart Example Finder")
    parser.add_argument("query", help="O que voce quer criar/implementar")
    parser.add_argument("--project", "-p", default=os.getcwd(), help="Diretorio do projeto")
    parser.add_argument("--top-k", "-k", type=int, default=3, help="Numero de exemplos")
    parser.add_argument("--json", action="store_true", help="Saida em JSON")
    
    args = parser.parse_args()
    
    if args.json:
        print(find_examples(args.project, args.query, args.top_k))
    else:
        print(cmd(args.query, args.project, args.top_k))
