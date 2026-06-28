"""MCR-DevIA explora o terreno desconhecido SOZINHO."""
import os, json, re, sys

TERRENO = r"E:\Projeto MCR\sandbox\terreno_desconhecido"
KG_PATH = r"E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json"

print("=" * 70)
print("  MCR-DevIA — EXPLORANDO TERRENO DESCONHECIDO")
print(f"  Local: {TERRENO}")
print("=" * 70)

# 1. EXAMINAR: o que tem aqui?
print("\n--- FASE 1: Examinando o terreno ---")
extensoes = {}
total = 0
for f in os.listdir(TERRENO):
    path = os.path.join(TERRENO, f)
    if os.path.isfile(path):
        ext = os.path.splitext(f)[1]
        extensoes[ext] = extensoes.get(ext, 0) + 1
        total += 1

print(f"  Total de arquivos: {total}")
print(f"  Extensoes: {extensoes}")

# 2. DETECTAR: que tipo de projeto e esse?
print("\n--- FASE 2: Detectando tipo de projeto ---")
tipos_detectados = set()
for f in sorted(os.listdir(TERRENO)):
    path = os.path.join(TERRENO, f)
    if not os.path.isfile(path):
        continue
    try:
        with open(path, encoding="utf-8") as fh:
            cabecalho = fh.read(200)
    except:
        continue
    
    # Detecta tecnologias
    if "import React" in cabecalho or "from 'react'" in cabecalho:
        tipos_detectados.add("React/TypeScript")
    if "express" in cabecalho.lower() or "fastify" in cabecalho.lower():
        tipos_detectados.add("Backend (Express/Fastify)")
    if "prisma" in cabecalho.lower():
        tipos_detectados.add("Prisma ORM")
    if "drizzle" in cabecalho.lower():
        tipos_detectados.add("Drizzle ORM")
    if "router" in cabecalho.lower():
        tipos_detectados.add("Router (API)")
    if "createApp" in cabecalho or "app.listen" in cabecalho:
        tipos_detectados.add("Servidor HTTP")
    if "SELECT" in cabecalho or "INSERT INTO" in cabecalho:
        tipos_detectados.add("Banco de Dados SQL")

print(f"  Tecnologias detectadas: {tipos_detectados if tipos_detectados else 'Nao identificado'}")

# 3. EXTRAIR: padroes de codigo
print("\n--- FASE 3: Extraindo padroes de API ---")
funcoes_por_tipo = {}

for f in sorted(os.listdir(TERRENO)):
    path = os.path.join(TERRENO, f)
    if not os.path.isfile(path):
        continue
    try:
        with open(path, encoding="utf-8") as fh:
            conteudo = fh.read()
    except:
        continue
    
    # Detecta funcoes/metodos
    funcoes = set()
    for m in re.finditer(r'(?:async\s+)?(?:function\s+\w+|(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*(?:=>|{))', conteudo):
        funcoes.add(m.group(1) or m.group(0).split()[1] if 'function' in m.group(0) else m.group(1))
    if funcoes:
        tipo = os.path.splitext(f)[1]
        funcoes_por_tipo.setdefault(tipo, set()).update(funcoes)

for tipo, funcs in sorted(funcoes_por_tipo.items()):
    print(f"  {tipo}: {len(funcs)} funcoes")
    for f in sorted(funcs)[:5]:
        print(f"    - {f}")

# 4. REGISTRAR APRENDIZADO
print("\n--- FASE 4: Registrando aprendizado ---")
kg = {"lessons": []}
if os.path.exists(KG_PATH):
    with open(KG_PATH, encoding="utf-8") as f:
        kg = json.load(f)

kg.setdefault("lessons", []).append({
    "context": "exploracao_terreno_desconhecido",
    "tecnologias": list(tipos_detectados),
    "extensoes": extensoes,
    "total_arquivos": total,
    "funcoes_por_tipo": {t: list(f)[:10] for t, f in funcoes_por_tipo.items()},
    "conclusao": f"Projeto com {total} arquivos, tecnologias: {tipos_detectados}"
})

with open(KG_PATH, "w", encoding="utf-8") as f:
    json.dump(kg, f, indent=2, ensure_ascii=False)

print(f"  Aprendizado registrado no KG!")
print(f"  Total de lessons: {len(kg.get('lessons', []))}")

print(f"\n{'='*70}")
print(f"  EXPLORACAO CONCLUIDA!")
print(f"  MCR-DevIA examinou {total} arquivos e identificou:")
for t in tipos_detectados:
    print(f"    - {t}")
print(f"{'='*70}")
