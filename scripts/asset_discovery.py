"""Asset Discovery — mapeia ferramentas do MCR-DevIA com descricao funcional."""
import os, re, json

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

def analisar_arquivo(caminho):
    """Extrai classes, funcoes e descricao funcional de um .py."""
    try:
        with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
            conteudo = f.read()
    except Exception:
        return None
    
    linhas = conteudo.split('\n')
    
    # Classes e metodos publicos
    classes = []
    for linha in linhas:
        m = re.match(r'^class\s+(\w+)', linha)
        if m and not m.group(1).startswith('_'):
            classes.append(m.group(1))
    
    # Funcoes publicas top-level
    funcoes = []
    for linha in linhas:
        m = re.match(r'^def\s+(\w+)', linha)
        if m and not m.group(1).startswith('_'):
            funcoes.append(m.group(1))
    
    # Descricao da primeira docstring
    descricao = ''
    for i, linha in enumerate(linhas[:5]):
        if '"""' in linha:
            for j in range(i+1, min(i+5, len(linhas))):
                descricao += linhas[j].strip() + ' '
                if '"""' in linhas[j]:
                    break
            break
    
    # Categorizacao por padroes
    categorias = []
    patterns = {
        'analise_codigo': ['tree-sitter', 'AST', 'parse', 'code_analyzer', 'linter', 'token'],
        'kg_memoria': ['KnowledgeGraph', 'EpisodicMemory', 'kg.py', 'lesson', 'memoria'],
        'rag_vector': ['RAG', 'ChromaDB', 'embedding', 'vetor', 'busca'],
        'watcher': ['watchdog', 'monitor', 'FileObserver', 'LogWatcher', 'observer'],
        'auto_calibracao': ['AutoEvolution', 'SelfHeal', 'calibrar', 'threshold', 'AutoLoop'],
        'geracao_template': ['Template', 'Filler', 'Generator', 'Preencher', 'Builder'],
        'markov_decisao': ['MarkovRouter', 'MarkovDecider', 'MCR(', 'markov', 'Decisor'],
        'validacao': ['Validator', 'validar', 'check', 'verificar', 'lint'],
        'ferramentas': ['cmd_', 'comando', 'tool_', 'Tool', 'execute'],
    }
    
    for cat, padroes in patterns.items():
        if any(p in conteudo for p in padroes):
            categorias.append(cat)
    
    return {
        'classes': classes,
        'funcoes': funcoes,
        'descricao': descricao[:120].strip(),
        'categorias': categorias,
        'tamanho': len(conteudo),
        'linhas': len(linhas),
    }


def scan_dir(diretorio):
    """Escaneia diretorio e retorna dados consolidados."""
    resultados = []
    for f in sorted(os.listdir(diretorio)):
        if not f.endswith('.py') or f in ('__init__.py',):
            continue
        if 'test' in f.lower() and f.startswith('test'):
            continue
        caminho = os.path.join(diretorio, f)
        dados = analisar_arquivo(caminho)
        if dados:
            dados['arquivo'] = f
            dados['caminho'] = caminho
            resultados.append(dados)
    return resultados


# ─── SCAN ─────────────────────────────────────────────────────
print("=" * 110)
print("  MANIFESTO DE CAPACIDADES — MCR-DevIA Revived")
print("=" * 110)

diretorios = [
    (_BASE, "NUCLEO"),
    (os.path.join(_BASE, "devia", "kernel"), "KERNEL"),
    (os.path.join(_BASE, "mcr"), "MCR"),
]

for diretorio, rotulo in diretorios:
    items = scan_dir(diretorio)
    
    if not items:
        continue
    
    print(f"\n{'='*110}")
    print(f"  📁 {rotulo}")
    print(f"{'='*110}")
    
    for item in items:
        classes = ', '.join(item['classes'][:4]) if item['classes'] else '-'
        cats = ', '.join(item['categorias']) if item['categorias'] else '-'
        desc = item['descricao'][:100] if item['descricao'] else '-'
        
        print(f"\n  📄 {item['arquivo']:<35s} {item['tamanho']/1000:6.1f}KB {item['linhas']:4d}L")
        print(f"     Classes:  {classes}")
        print(f"     Categoria: {cats}")
        print(f"     Descricao: {desc}")

# ─── RESUMO POR CATEGORIA ─────────────────────────────────────
print(f"\n\n{'='*110}")
print("  RESUMO — FERRAMENTAS POR CATEGORIA")
print(f"{'='*110}")

todos = []
 for d, _ in diretorios:
    todos.extend(scan_dir(d))

categorias = {
    'analise_codigo': 'Analise de Codigo',
    'kg_memoria': 'KG / Memoria',
    'rag_vector': 'RAG / Busca Vetorial',
    'watcher': 'Watchers / Monitoramento',
    'auto_calibracao': 'Auto-Calibracao',
    'geracao_template': 'Geracao / Template',
    'markov_decisao': 'Markov / Decisao',
    'validacao': 'Validacao / Lint',
    'ferramentas': 'Ferramentas / Comandos',
}

for cat_slug, cat_nome in categorias.items():
    encontrados = [i for i in todos if cat_slug in i['categorias']]
    if not encontrados:
        continue
    print(f"\n  🔧 {cat_nome} ({len(encontrados)}):")
    for item in encontrados:
        classes = ', '.join(item['classes'][:3]) if item['classes'] else '-'
        print(f"     - {item['arquivo']:<30s} {classes}")
