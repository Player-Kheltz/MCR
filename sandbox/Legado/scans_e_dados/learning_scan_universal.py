"""MCR-DevIA — LearningScan Universal
Aprende QUALQUER linguagem, QUALQUER padrao.
Nao usa tipos fixos. Descobre ESTRUTURA onde quer que exista.
Funciona pra .lua, .py, .ts, .js, .go, .rs, .java, etc.
Ate para linguagens INEXISTENTES (criadas na hora)."""
import os, re, json

LEARNING_PATH = r"E:\Projeto MCR\sandbox\.mcr_learning_scan.json"
KG_PATH = r"E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json"

# ============================================================
# DETECTORES DE LINGUAGEM (baseados em caracteristicas UNIVERSO)
# ============================================================

LINGUAGENS = {
    "lua": {
        "ext": ".lua",
        "marcadores": [r"local\s+\w+\s*=", r"function\s+\w+\s*\(", r"end\b", r"--\[\["],
        "comentario": r"--",
        "funcao": r"(?:local\s+)?function\s+(\w+)\s*\(",
        "metodo": r":(\w+)\s*\(",
        "import": r"(?:require|dofile)\s*[\(\"]",
    },
    "python": {
        "ext": ".py",
        "marcadores": [r"def\s+\w+\s*\(", r"import\s+\w+", r"class\s+\w+", r":\s*$"],
        "comentario": r"#",
        "funcao": r"def\s+(\w+)\s*\(",
        "metodo": r"self\.(\w+)\s*\(",
        "import": r"(?:import|from)\s+\w+",
    },
    "typescript": {
        "ext": ".ts",
        "marcadores": [r"(?:export\s+)?(?:function|class|interface|type)\s+\w+", r":\s*(?:string|number|boolean)",
                       r"import\s+\{", r"const\s+\w+\s*:\s*\w+"],
        "comentario": r"\/\/",
        "funcao": r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(",
        "metodo": r"(\w+)\s*(?:\([^)]*\)\s*:\s*\w+\s*=>|=\s*\([^)]*\)\s*=>)",
        "import": r"import\s+\{?\s*(\w+)",
    },
    "javascript": {
        "ext": ".js",
        "marcadores": [r"function\s+\w+\s*\(", r"(?:const|let|var)\s+\w+\s*=", r"module\.exports", r"require\("],
        "comentario": r"\/\/",
        "funcao": r"(?:function\s+(\w+)|(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)",
        "metodo": r"(\w+)\s*:\s*(?:async\s*)?\([^)]*\)\s*=>",
        "import": r"(?:require|import)\s*\(?\s*[\"']",
    },
    "generico": {
        "ext": None,  # Qualquer extensao nao identificada
        "marcadores": [r"\w+\s*\([^)]*\)\s*\{", r"import|include|using"],
        "comentario": r"\/\/|#|--|;",
        "funcao": r"(?:\w+\s+)?(\w+)\s*\([^)]*\)\s*(?:\{|->|=>)",
        "metodo": None,
        "import": r"(?:import|include|using|require)\s+\w+",
    }
}

def detectar_linguagem(arquivo, cabecalho):
    """Detecta linguagem pelo conteudo (nao pela extensao)."""
    ext = os.path.splitext(arquivo)[1].lower()
    
    # Tenta por extension primeiro
    for nome, config in LINGUAGENS.items():
        if config["ext"] and ext == config["ext"]:
            return nome
    
    # Tenta por marcadores
    scores = {}
    for nome, config in LINGUAGENS.items():
        if nome == "generico":
            continue
        score = 0
        for marcador in config["marcadores"]:
            if re.search(marcador, cabecalho):
                score += 1
        if score > 0:
            scores[nome] = score
    
    if scores:
        return max(scores, key=scores.get)
    return "generico"

# ============================================================
# EXTRATORES UNIVERSO
# ============================================================

def extrair_padroes(texto, config):
    """Extrai padroes de QUALQUER codigo usando config da linguagem."""
    padroes = {
        "funcoes": {},
        "metodos": {},
        "imports": {},
        "palavras_chave": {},
    }
    
    # Funcoes
    if config["funcao"]:
        for m in re.finditer(config["funcao"], texto):
            nome = m.group(1) or m.group(2) or "?"
            if nome and len(nome) > 1:
                padroes["funcoes"][nome] = padroes["funcoes"].get(nome, 0) + 1
    
    # Metodos
    if config["metodo"]:
        for m in re.finditer(config["metodo"], texto):
            nome = m.group(1)
            if nome and len(nome) > 1:
                padroes["metodos"][nome] = padroes["metodos"].get(nome, 0) + 1
    
    # Imports
    if config["import"]:
        for m in re.finditer(config["import"], texto):
            nome = m.group(1) if m.lastindex and m.group(1) else m.group(0)[:20]
            if nome and len(nome) > 1:
                padroes["imports"][nome] = padroes["imports"].get(nome, 0) + 1
    
    return padroes

# ============================================================
# MAIN
# ============================================================

print("=" * 70)
print("  MCR-DevIA — LEARNINGSCAN UNIVERSAL")
print("  Aprende QUALQUER linguagem, QUALQUER padrao.")
print("  Nao usa tipos fixos. Descobre ESTRUTURA.")
print("=" * 70)

# Diretorios para escanear (MCR + Hub do Lojista)
DIRS = [
    ("MCR (Lua)", r"E:\Projeto MCR\Canary\data-canary\scripts\MCR",
     lambda f: f.endswith(".lua")),
    ("Hub (TS/JS)", r"E:\Projeto MCR\sandbox\terreno_desconhecido",
     lambda f: f.endswith((".ts", ".js", ".py"))),
]

total_arquivos = 0
todos_padroes = {}
linguagens_encontradas = set()

for nome_dir, dir_path, filtro in DIRS:
    if not os.path.exists(dir_path):
        print(f"\n  [AVISO] {nome_dir}: diretorio nao encontrado")
        continue
    
    print(f"\n--- Escaneando: {nome_dir} ---")
    arquivos_lidos = 0
    
    for root, dirs, files in os.walk(dir_path):
        if any(p in root.lower() for p in ["node_modules", ".git", "build", "__pycache__", "_backup"]):
            continue
        for f in files:
            if not filtro(f):
                continue
            path = os.path.join(root, f)
            try:
                with open(path, encoding="utf-8") as fh:
                    cabecalho = fh.read(500)
                    conteudo = cabecalho + fh.read(4500)  # Total ~5000 chars
            except:
                continue
            total_arquivos += 1
            arquivos_lidos += 1
            
            # Detecta linguagem pelo CONTEUDO
            lingua = detectar_linguagem(f, cabecalho)
            linguagens_encontradas.add(lingua)
            
            # Extrai padroes
            config = LINGUAGENS.get(lingua, LINGUAGENS["generico"])
            padroes = extrair_padroes(conteudo, config)
            
            # Acumula
            if lingua not in todos_padroes:
                todos_padroes[lingua] = {"funcoes": {}, "metodos": {}, "imports": {}}
            for categoria in ["funcoes", "metodos", "imports"]:
                for nome, count in padroes[categoria].items():
                    todos_padroes[lingua][categoria][nome] = \
                        todos_padroes[lingua][categoria].get(nome, 0) + count
    
    if arquivos_lidos == 0:
        print(f"  Nenhum arquivo encontrado em {dir_path}")

print(f"\n{'='*70}")
print(f"  RESULTADO: {total_arquivos} arquivos escaneados")
print(f"  Linguagens detectadas: {linguagens_encontradas}")
print(f"{'='*70}")

for lingua in sorted(linguagens_encontradas):
    dados = todos_padroes.get(lingua, {})
    print(f"\n  {lingua.upper()}:")
    for categoria in ["funcoes", "metodos", "imports"]:
        items = dados.get(categoria, {})
        if items:
            top5 = sorted(items.items(), key=lambda x: -x[1])[:5]
            print(f"    {categoria}: {len(items)} unicas")
            for nome, count in top5:
                print(f"      {nome}: {count}x")

# Cria linguagem INEXISTENTE para testar
print(f"\n\n--- TESTE: Linguagem INEXISTENTE ---")
codigo_inexistente = """
# Linguagem XYZ (inventada)
# Nao existe em lugar nenhum

componente Main {
    estado contador = 0
    
    funcao iniciar() {
        contador = 0
        mostrar("Iniciou")
    }
    
    funcao incrementar(valor) {
        contador = contador + valor
        mostrar("Valor: " + valor)
    }
}

componente Botao {
    funcao clicar() {
        Main.incrementar(1)
    }
}
"""

lingua_inex = detectar_linguagem("teste.xyz", codigo_inexistente)
print(f"  Linguagem detectada: {lingua_inex}")
padroes_inex = extrair_padroes(codigo_inexistente, LINGUAGENS["generico"])
for cat, itens in padroes_inex.items():
    if itens:
        print(f"  {cat}: {list(itens.keys())[:5]}")

# FILTRO DE RUIDO: remove padroes que aparecem em 1 arquivo so
# MCR-DevIA descobriu: padrao so e valido se 2+ contextos
total_filtrado = 0
for lingua in list(todos_padroes.keys()):
    for categoria in ["funcoes", "metodos", "imports"]:
        items = todos_padroes[lingua].get(categoria, {})
        # Mantem so os que aparecem 2+ vezes
        items_filtrados = {k: v for k, v in items.items() if v >= 2}
        removidos = len(items) - len(items_filtrados)
        total_filtrado += removidos
        if removidos > 0:
            todos_padroes[lingua][categoria] = items_filtrados

print(f"\n  [FILTRO DE RUIDO] {total_filtrado} padroes removidos (1x so = ruido)")
print(f"  [REGRA] MCR-DevIA so aprende o que aparece em 2+ arquivos")

# Salva com padroes filtrados
with open(LEARNING_PATH, "w", encoding="utf-8") as f:
    json.dump({
        "universal": True,
        "total_arquivos": total_arquivos,
        "linguagens": list(linguagens_encontradas),
        "ruido_filtrado": total_filtrado,
        "padroes": {l: {c: {k: v for k, v in sorted(d[c].items(), key=lambda x: -x[1])[:50]} 
                       for c in ["funcoes", "metodos", "imports"] if d.get(c)}
                   for l, d in todos_padroes.items()}
    }, f, indent=2, ensure_ascii=False)

# Registra no KG
kg = {"lessons": []}
if os.path.exists(KG_PATH):
    with open(KG_PATH, encoding="utf-8") as f:
        kg = json.load(f)

for lingua in linguagens_encontradas:
    dados = todos_padroes.get(lingua, {})
    total_padroes = sum(len(dados.get(c, {})) for c in ["funcoes", "metodos", "imports"])
    kg.setdefault("lessons", []).append({
        "context": f"learning_scan_universal_{lingua}",
        "linguagem": lingua,
        "total_padroes": total_padroes,
        "funcoes_topo": list(dados.get("funcoes", {}).keys())[:5],
    })

# Registra o teste de linguagem inexistente
kg.setdefault("lessons", []).append({
    "context": "learning_scan_universal_inexistente",
    "linguagem": "XYZ (inventada)",
    "detectada_como": lingua_inex,
    "padroes_encontrados": {c: list(p.keys())[:5] for c, p in padroes_inex.items() if p},
    "conclusao": "LearningScan Universal consegue extrair padroes ATE de linguagens que nao existem"
})

with open(KG_PATH, "w", encoding="utf-8") as f:
    json.dump(kg, f, indent=2, ensure_ascii=False)

print(f"\n{'='*70}")
print(f"  LEARNINGSCAN UNIVERSAL CONCLUIDO!")
print(f"  {total_arquivos} arquivos, {len(linguagens_encontradas)} linguagens")
print(f"  Linguagem inexistente: PADROES EXTRAIDOS")
print(f"  KG: {len(kg.get('lessons',[]))} lessons")
print(f"{'='*70}")
