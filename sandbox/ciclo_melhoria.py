"""MCR-DevIA — Ciclo de Melhoria: Correcao + Geracao
1. Detecta arquivos inconsistentes (Monster em vez do tipo certo)
2. Corrige usando LearningScan + KG
3. Regenera conteudo com templates corretos
4. Valida""" 
import os, sys, json, re, shutil, subprocess

SANDBOX = r"E:\Projeto MCR\sandbox"
LEARNING_PATH = os.path.join(SANDBOX, ".mcr_learning_scan.json")
KG_PATH = os.path.join(SANDBOX, ".mcr_devia", "knowledge.json")
MCR_DEVIA = r"E:\Projeto MCR\scripts\mcr_devia\mcr_devia.py"

# ============================================================
# 1. CARREGAR PADROES REAIS DO LEARNINGSCAN
# ============================================================
padroes_reais = {}
if os.path.exists(LEARNING_PATH):
    with open(LEARNING_PATH, encoding="utf-8") as f:
        data = json.load(f)
    padroes_reais = data.get("padroes", {})

print("=" * 70)
print("  CICLO DE MELHORIA — CORRECAO + GERACAO")
print("=" * 70)

# Mapa de correcao: nome do tipo -> construtor correto
CONSTRUTORES = {
    "monster": "Monster",
    "item": "Item",
    "npc": "NPC",
    "spell": "Spell",
    "quest": "Quest",
}

# Mapa reverso: construtor -> tipo
CONSTRUTOR_PARA_TIPO = {v: k for k, v in CONSTRUTORES.items()}

# ============================================================
# 2. CORRIGIR ARQUIVOS INCONSISTENTES
# ============================================================
print("\n--- FASE 1: Corrigindo arquivos inconsistentes ---")

corrigidos = 0
for fname in os.listdir(SANDBOX):
    if not fname.endswith(".lua") or ".bak" in fname:
        continue
    path = os.path.join(SANDBOX, fname)
    
    with open(path, encoding="utf-8") as f:
        conteudo = f.read()
    
    # Detecta o tipo esperado pelo nome do arquivo
    tipo_esperado = None
    for tipo in CONSTRUTORES:
        if tipo in fname.lower():
            tipo_esperado = tipo
            break
    
    if not tipo_esperado:
        continue
    
    construtor_esperado = CONSTRUTORES[tipo_esperado]
    conteudo_novo = conteudo
    
    # Verifica se esta usando o construtor ERRADO
    for construtor_errado, tipo_errado in CONSTRUTOR_PARA_TIPO.items():
        if construtor_errado == construtor_esperado:
            continue  # Esta usando o certo
        
        # Procura por `Monster("Nome")` quando deveria ser `Item("Nome")`
        padrao_errado = construtor_errado + "("
        if padrao_errado in conteudo:
            # Substitui pelo construtor correto
            conteudo_novo = conteudo_novo.replace(padrao_errado, construtor_esperado + "(")
            print(f"  Corrigido: {fname}: {construtor_errado} -> {construtor_esperado}")
            corrigidos += 1
            
            # Se tem funcoes do LearningScan, adiciona
            funcoes_tipo = padroes_reais.get(tipo_esperado, {})
            funcoes_confirmadas = [f for f, c in funcoes_tipo.items() if c >= 2]
            if funcoes_confirmadas and "set" in conteudo_novo.split("--")[-1]:
                # Ja tem funcoes set*, nao precisa adicionar
                pass
            elif funcoes_confirmadas:
                # Adiciona funcoes reais no final
                for func in funcoes_confirmadas[:3]:
                    if func.startswith("set"):
                        conteudo_novo += f"\n{tipo_esperado}:{func}(valor)"
                print(f"    Funcoes adicionadas: {funcoes_confirmadas[:3]}")
    
    if conteudo_novo != conteudo:
        with open(path, "w", encoding="utf-8") as f:
            f.write(conteudo_novo)

print(f"\n  Total corrigidos: {corrigidos}")

# ============================================================
# 3. REGENERAR CONTEUDO COM LEARNINGSCAN
# ============================================================
print("\n--- FASE 2: Regenerando conteudo com LearningScan ---")

# Gera novos arquivos usando o Gerador do MCR-DevIA
tipos_para_gerar = [
    ("monster", "DragaoFogo"),
    ("monster", "GolemPedra"), 
    ("item", "EspadaFlamejante"),
    ("item", "ArmaduraGelo"),
    ("npc", "FerrageiroNovo"),
    ("npc", "BibliotecarioNovo"),
    ("spell", "BolaFogo"),
    ("spell", "CuraDivina"),
    ("quest", "ForjaPerdida"),
]

for tipo, nome in tipos_para_gerar:
    print(f"  Gerando {tipo}: {nome}...")
    r = subprocess.run(
        [sys.executable, MCR_DEVIA, "gerar", tipo, nome],
        capture_output=True, text=True, timeout=120
    )
    stdout = (r.stdout or "")[-200:]
    stderr = (r.stderr or "")[:200]
    if r.returncode == 0:
        print(f"    [OK] {stdout.split(chr(10))[-3:-1]}")
    else:
        print(f"    [FALHA] {stderr}")

# ============================================================
# 4. VALIDAR
# ============================================================
print("\n--- FASE 3: Validando ---")

# Scanner
print("  Scanner mestre...")
r = subprocess.run([sys.executable, r"E:\Projeto MCR\sandbox\scanner_mestre.py"],
    capture_output=True, text=True, timeout=60)
for line in (r.stdout or "").split("\n"):
    if "SCAN FINAL:" in line:
        print(f"    {line.strip()}")

# Consistencia
print("  Detector de consistencia...")
r = subprocess.run([sys.executable, r"E:\Projeto MCR\sandbox\detector_consistencia.py"],
    capture_output=True, text=True, timeout=30)
for line in (r.stdout or "").split("\n"):
    if "Resultado:" in line:
        print(f"    {line.strip()}")

# ============================================================
# 5. REGISTRAR APRENDIZADO
# ============================================================
print("\n--- FASE 4: Registrando aprendizado ---")

kg = {"lessons": []}
if os.path.exists(KG_PATH):
    with open(KG_PATH, encoding="utf-8") as f:
        kg = json.load(f)

kg.setdefault("lessons", []).append({
    "context": "ciclo_melhoria",
    "tipo": "correcao_geracao",
    "corrigidos": corrigidos,
    "gerados": len(tipos_para_gerar),
    "aprendizado": "arquivos inconsistentes podem ser auto-corrigidos mapeando construtor -> tipo"
})

with open(KG_PATH, "w", encoding="utf-8") as f:
    json.dump(kg, f, indent=2, ensure_ascii=False)

print("  KG atualizado!")

print(f"\n{'='*70}")
print(f"  CICLO CONCLUIDO!")
print(f"  Corrigidos: {corrigidos} arquivos")
print(f"  Gerados: {len(tipos_para_gerar)} novos arquivos")
print(f"  Aprendizado registrado no KG")
print(f"{'='*70}")
