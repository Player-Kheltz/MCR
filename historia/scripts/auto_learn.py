#!/usr/bin/env python3
"""
auto_learn.py — Sistema de auto-aprendizado para o assistente local.
Mantem um banco de conhecimento que cresce com o tempo.

Funcoes:
- learn(tarefa, codigo_gerado): registra um aprendizado
- recall(tarefa): recupera exemplos similares do passado
- stats(): mostra estatisticas de aprendizado
"""
import os, json, time, hashlib, sys
from pathlib import Path

LEARN_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".learn_db")
os.makedirs(LEARN_DIR, exist_ok=True)

KNOWLEDGE_FILE = os.path.join(LEARN_DIR, "knowledge.json")
PATTERNS_FILE = os.path.join(LEARN_DIR, "patterns.json")

def _load_json(path, default=None):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default or {}
    return default or {}

def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def learn(tarefa, codigo_gerado, linguagem="lua", projeto="", tags=None):
    """Registra um aprendizado: o que foi gerado e como."""
    knowledge = _load_json(KNOWLEDGE_FILE, {})
    
    # Gera um ID unico baseado no conteudo
    content_hash = hashlib.md5((tarefa + codigo_gerado[:200]).encode()).hexdigest()[:12]
    
    entry = {
        "id": content_hash,
        "tarefa": tarefa,
        "linguagem": linguagem,
        "projeto": projeto,
        "tags": tags or [],
        "data": time.strftime("%Y-%m-%d %H:%M"),
        "timestamp": time.time(),
        "tamanho": len(codigo_gerado),
        "sucesso": True,
    }
    
    if content_hash not in knowledge:
        knowledge[content_hash] = entry
        _save_json(KNOWLEDGE_FILE, knowledge)
    
    # Atualiza padroes
    patterns = _load_json(PATTERNS_FILE, {})
    task_type = tarefa.split(":")[0].strip() if ":" in tarefa else tarefa[:30]
    
    if task_type not in patterns:
        patterns[task_type] = {"count": 0, "tags": set(), "linguagens": set(), "ultimo": ""}
    
    patterns[task_type]["count"] += 1
    patterns[task_type]["tags"].update(tags or [])
    patterns[task_type]["linguagens"].add(linguagem)
    patterns[task_type]["ultimo"] = time.strftime("%Y-%m-%d %H:%M")
    
    # Salva padroes (convertendo sets para listas)
    patterns_serializable = {}
    for k, v in patterns.items():
        patterns_serializable[k] = {
            "count": v["count"],
            "tags": list(v["tags"]),
            "linguagens": list(v["linguagens"]),
            "ultimo": v["ultimo"]
        }
    _save_json(PATTERNS_FILE, patterns_serializable)
    
    return content_hash


def recall(tarefa, top_k=3):
    """Recupera aprendizados similares do passado."""
    knowledge = _load_json(KNOWLEDGE_FILE, {})
    if not knowledge:
        return []
    
    tarefa_lower = tarefa.lower()
    words = set(tarefa_lower.split())
    
    scored = []
    for entry in knowledge.values():
        task_words = set(entry["tarefa"].lower().split())
        intersection = len(words & task_words)
        union = len(words | task_words)
        score = intersection / union if union > 0 else 0
        
        # Bonus para tags que correspondem
        tag_bonus = sum(1 for tag in entry.get("tags", []) if tag.lower() in tarefa_lower) * 0.1
        
        scored.append((score + tag_bonus, entry))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored[:top_k] if s[0] > 0]


def stats():
    """Mostra estatisticas de aprendizado."""
    knowledge = _load_json(KNOWLEDGE_FILE, {})
    patterns = _load_json(PATTERNS_FILE, {})
    
    total = len(knowledge)
    if total == 0:
        return "Nenhum aprendizado registrado ainda."
    
    lines = [
        f"Total de aprendizados: {total}",
        f"Padroes identificados: {len(patterns)}",
        "",
        "TOP PADROES:"
    ]
    
    sorted_patterns = sorted(patterns.items(), key=lambda x: x[1]["count"], reverse=True)
    for name, data in sorted_patterns[:10]:
        lines.append(f"  {name}: {data['count']}x | tags: {', '.join(data['tags'][:5])} | ultimo: {data['ultimo']}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"
    
    if cmd == "stats":
        print(stats())
    elif cmd == "learn" and len(sys.argv) >= 4:
        learn(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "unknown")
        print(f"Aprendizado registrado: {sys.argv[2][:50]}")
    elif cmd == "recall" and len(sys.argv) >= 3:
        results = recall(sys.argv[2])
        print(f"Encontrados {len(results)} aprendizados similares:")
        for r in results:
            print(f"  [{r['data']}] {r['tarefa'][:60]}")
    else:
        print("Uso: python scripts/auto_learn.py stats")
        print("     python scripts/auto_learn.py learn 'tarefa' 'codigo' 'linguagem'")
        print("     python scripts/auto_learn.py recall 'tarefa'")
