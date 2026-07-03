"""memoria.py — Aprendizado continuo do MCR-Dev."""
import os, json, hashlib, time

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEARN_DIR = os.path.join(BASE, ".learn_db")
KNOWLEDGE_FILE = os.path.join(LEARN_DIR, "mcr_dev.json")
CONTEXT_FILE = os.path.join(LEARN_DIR, "contexto.json")
os.makedirs(LEARN_DIR, exist_ok=True)

MAX_HISTORY = 100  # max interacoes lembradas


def _load():
    if os.path.exists(KNOWLEDGE_FILE):
        try:
            with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"aprendizados": [], "estatisticas": {"total": 0, "tipos": {}}}
    return {"aprendizados": [], "estatisticas": {"total": 0, "tipos": {}}}


def _save(data):
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def learn(entrada, saida, tipo, arquivo_gerado=""):
    """Registra uma interacao para aprendizado futuro."""
    data = _load()
    
    entry = {
        "id": hashlib.md5((entrada + str(time.time())).encode()).hexdigest()[:8],
        "entrada": entrada[:100],
        "tipo": tipo,
        "arquivo": arquivo_gerado,
        "timestamp": time.time(),
        "data": time.strftime("%Y-%m-%d %H:%M"),
        "tamanho_saida": len(saida),
    }
    
    data["aprendizados"].append(entry)
    
    # Mantem so os ultimos MAX_HISTORY
    if len(data["aprendizados"]) > MAX_HISTORY:
        data["aprendizados"] = data["aprendizados"][-MAX_HISTORY:]
    
    # Estatisticas
    est = data["estatisticas"]
    est["total"] = len(data["aprendizados"])
    est["tipos"][tipo] = est["tipos"].get(tipo, 0) + 1
    
    _save(data)


def recall(entrada, top_k=3):
    """Recupera experiencias similares do passado."""
    data = _load()
    if not data["aprendizados"]:
        return []
    
    words = set(entrada.lower().split())
    scored = []
    
    for a in data["aprendizados"]:
        aw = set(a["entrada"].lower().split())
        inter = len(words & aw)
        union = len(words | aw)
        score = inter / union if union > 0 else 0
        
        # Bonus para mesmo tipo
        if a.get("tipo") and a["tipo"].lower() in entrada.lower():
            score += 0.2
        
        scored.append((score, a))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored[:top_k] if s[0] > 0.1]


def stats():
    """Estatisticas de uso."""
    data = _load()
    est = data["estatisticas"]
    
    lines = [
        f"  Total de tarefas: {est['total']}",
        f"  Por tipo:"
    ]
    for tipo, count in sorted(est["tipos"].items(), key=lambda x: x[1], reverse=True):
        lines.append(f"    {tipo}: {count}x")
    
    # Ultimas 5
    if data["aprendizados"]:
        lines.append(f"\n  Ultimas 5 tarefas:")
        for a in data["aprendizados"][-5:]:
            lines.append(f"    [{a['data']}] {a['entrada'][:50]}")
    
    return "\n".join(lines)
