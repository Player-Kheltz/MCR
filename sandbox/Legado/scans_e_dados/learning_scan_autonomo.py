"""MCR-DevIA — LearningScan Autonomo
SEM diretorios fixos. Ele EXPLORA e DESCOBRE.
Anda pelo projeto, encontra arquivos, decide o tipo pelo CONTEUDO,
agrupa, extrai padroes. Sozinho."""
import os, re, json, sys

BASE = r"E:\Projeto MCR\Canary"

# LGPD: arquivos que NAO devem ser escaneados (dados pessoais, segredos)
EXCLUIR_POR_NOME = [
    ".env", ".db", ".log", ".npy", ".err", ".tmp",
    "senha", "password", "token", "secret", "credential",
    "backup", "dump", "export",
]
EXCLUIR_POR_DIR = [
    "node_modules", ".git", "build", "_backup",
    "venv", "__pycache__",
]

def arquivo_lgpd_seguro(path):
    """Verifica se o arquivo pode ser escaneado sem violar LGPD."""
    nome = os.path.basename(path).lower()
    # Exclui por extensao/nome
    for padrao in EXCLUIR_POR_NOME:
        if padrao in nome:
            return False
    # Exclui por diretorio
    for parte in path.split(os.sep):
        if parte.lower() in EXCLUIR_POR_DIR:
            return False
    return True
# PONTO DE PARTIDA UNICO — o PROJETO MCR INTEIRO
SCAN_DIRS = [r"E:\Projeto MCR"]

LEARNING_PATH = r"E:\Projeto MCR\sandbox\.mcr_learning_scan.json"
KG_PATH = r"E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json"

# Palavras-chave para detectar tipo pelo CONTEUDO (nao pelo diretorio)
DETECTOR_TIPO = {
    "npc": [r"NPC\(", r"NpcHandler", r"KeywordHandler", r"setSaudacao", r"CALLBACK_GREET"],
    "monster": [r"Monster\(", r"setMaxHealth", r"setOutfit", r"addLoot"],
    "item": [r"Item\(", r"setAttribute", r"setDuration", r"setActionId"],
    "spell": [r"Spell\(", r"SpellData", r"setDamage", r"setManaCost"],
    "quest": [r"Quest\(", r"setDescricao", r"addObjetivo"],
    "talkaction": [r"TalkAction\(", r"talkAction"],
    "creaturescript": [r"CreatureEvent\(", r"onLogin", r"onAdvance"],
}

print("=" * 70)
print("  MCR-DevIA — LEARNINGSCAN AUTONOMO")
print("  SEM diretorios fixos. Descobre TUDO pelo conteudo.")
print("=" * 70)

def detectar_tipo_por_conteudo(texto):
    """Detecta o tipo do arquivo pelo CONTEUDO, nao pelo caminho."""
    scores = {}
    for tipo, padroes in DETECTOR_TIPO.items():
        score = 0
        for p in padroes:
            if re.search(p, texto):
                score += 1
        if score > 0:
            scores[tipo] = score
    if scores:
        return max(scores, key=scores.get)
    return None

# 1. EXPLORAR: varre TUDO, descobre tipos pelo conteudo
print("\n--- Explorando projeto ---")
arquivos_por_tipo = {}  # tipo -> [caminhos]

for scan_dir in SCAN_DIRS:
    if not os.path.exists(scan_dir):
        continue
    for root, dirs, files in os.walk(scan_dir):
        # Filtra diretorios LGPD sensiveis
        dirs[:] = [d for d in dirs if d.lower() not in EXCLUIR_POR_DIR]
        
        for f in files:
            if not f.endswith(".lua"):
                continue
            path = os.path.join(root, f)
            # LGPD: pula arquivos com dados sensiveis
            if not arquivo_lgpd_seguro(path):
                continue
            try:
                with open(path, encoding="utf-8") as fh:
                    cabecalho = fh.read(500)
            except:
                continue
            
            tipo = detectar_tipo_por_conteudo(cabecalho)
            if tipo:
                arquivos_por_tipo.setdefault(tipo, []).append(path)

print(f"\n  Tipos encontrados: {list(arquivos_por_tipo.keys())}")
for tipo, paths in sorted(arquivos_por_tipo.items()):
    print(f"    {tipo}: {len(paths)} arquivos")

# 2. APRENDER: extrai funcoes de cada tipo
print("\n--- Extraindo padroes ---")
padroes = {}  # tipo -> {funcao: contagem}

for tipo, paths in arquivos_por_tipo.items():
    funcoes = {}  # funcao -> contagem
    for path in paths:
        try:
            with open(path, encoding="utf-8") as f:
                conteudo = f.read()
        except:
            continue
        
        # Extrai funcoes "set*" e "get*" usadas no arquivo
        for m in re.finditer(r'[:.](\w+)\s*\(', conteudo):
            func = m.group(1)
            if func.startswith(("set", "get", "add", "is", "has")) and not func.startswith("setStorage"):
                funcoes[func] = funcoes.get(func, 0) + 1
    
    if funcoes:
        padroes[tipo] = funcoes
        confirmadas = {f: c for f, c in funcoes.items() if c >= 2}
        print(f"  {tipo}: {len(funcoes)} funcoes, {len(confirmadas)} confirmadas (2+ arquivos)")
        for f, c in sorted(confirmadas.items(), key=lambda x: -x[1])[:5]:
            print(f"    {f}: {c} arquivos")

# 3. REGISTRAR
print("\n--- Registrando aprendizado ---")

# Salva padroes
scan_data = {
    "padroes": padroes,
    "arquivos_por_tipo": {t: len(p) for t, p in arquivos_por_tipo.items()},
    "total_arquivos": sum(len(p) for p in arquivos_por_tipo.values())
}
with open(LEARNING_PATH, "w", encoding="utf-8") as f:
    json.dump(scan_data, f, indent=2, ensure_ascii=False)

# Atualiza KG
kg = {"lessons": []}
if os.path.exists(KG_PATH):
    with open(KG_PATH, encoding="utf-8") as f:
        kg = json.load(f)

for tipo, funcs in padroes.items():
    confirmadas = [f for f, c in funcs.items() if c >= 2]
    if confirmadas:
        kg.setdefault("lessons", []).append({
            "context": f"learning_scan_autonomo_{tipo}",
            "arquivos": len(arquivos_por_tipo.get(tipo, [])),
            "funcoes_confirmadas": confirmadas[:10],
            "descoberta": f"Tipo {tipo} usa principalmente {', '.join(confirmadas[:5])}"
        })

with open(KG_PATH, "w", encoding="utf-8") as f:
    json.dump(kg, f, indent=2, ensure_ascii=False)

print(f"\n  Padroes salvos em: {LEARNING_PATH}")
print(f"  KG atualizado: {len(kg.get('lessons', []))} lessons")
print(f"\n{'='*70}")
print(f"  LEARNINGSCAN AUTONOMO CONCLUIDO!")
print(f"  Descobriu {len(padroes)} tipos em {scan_data['total_arquivos']} arquivos")
print(f"{'='*70}")
