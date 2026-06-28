"""Preparar terreno desconhecido: Hub do Lojista
Apenas amostras. LGPD seguro. Nao explicar o que e."""
import os, shutil, subprocess, json

HUB_DIR = r"E:\Hub do Lojista"
TERRENO = r"E:\Projeto MCR\sandbox\terreno_desconhecido"
KG_PATH = r"E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json"

# Limpa terreno anterior
if os.path.exists(TERRENO):
    shutil.rmtree(TERRENO)
os.makedirs(TERRENO)

# Arquivos SEGUROS para copiar (sem .env, .db, logs, tokens)
EXTENSOES_SEGURAS = (".py", ".js", ".ts", ".json", ".md", ".sql", ".yml", ".prisma")
EXCLUIR_PALAVRAS = (".env", ".db", ".log", ".npy", ".err", ".tmp", "secret", "token", "password", "credential")

copiados = 0
for root, dirs, files in os.walk(HUB_DIR):
    # Pula diretorios problematicos
    if any(p in root.lower() for p in ["node_modules", ".git", "build", "venv", "__pycache__", ".rag_db"]):
        continue
    for f in files:
        if not f.endswith(EXTENSOES_SEGURAS):
            continue
        if any(p in f.lower() for p in EXCLUIR_PALAVRAS):
            continue
        src = os.path.join(root, f)
        dst = os.path.join(TERRENO, f)
        try:
            shutil.copy2(src, dst)
            copiados += 1
        except:
            pass
        if copiados >= 50:  # Limite de amostras
            break
    if copiados >= 50:
        break

# Registra no KG que este terreno existe
kg = {"lessons": []}
if os.path.exists(KG_PATH):
    with open(KG_PATH, encoding="utf-8") as f:
        kg = json.load(f)

kg.setdefault("lessons", []).append({
    "context": "terreno_desconhecido",
    "origem": "Hub do Lojista",
    "arquivos": copiados,
    "descricao": "Terreno completamente desconhecido para MCR-DevIA aprender",
    "regras": "MCR-DevIA deve descobrir sozinho o que e esse projeto"
})

with open(KG_PATH, "w", encoding="utf-8") as f:
    json.dump(kg, f, indent=2, ensure_ascii=False)

print("=" * 70)
print("  TERRENO DESCONHECIDO CRIADO")
print(f"  Origem: Hub do Lojista")
print(f"  Amostras: {copiados} arquivos")
print(f"  Local: {TERRENO}")
print(f"  LGPD: seguro (sem .env, .db, logs, tokens)")
print(f"  Regra: MCR-DevIA descobre SOZINHO o que e")
print("=" * 70)
print("\n  Agora vou deixar o MCR-DevIA explorar...")
