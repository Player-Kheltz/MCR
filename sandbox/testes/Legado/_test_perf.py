"""Teste de Performance do MCR-DevIA - Metricas de cada componente."""
import sys, os, time, json
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')

from modulos.decider import Decider
from modulos.kg import KnowledgeGraph
from modulos.episodic_memory import EpisodicMemory
from modulos.ia import IA
from modulos.tool_orchestrator import ToolOrchestrator
from modulos.task_planner import TaskPlanner

ia = IA()
decider = Decider(ia)
kg = KnowledgeGraph()
mem = EpisodicMemory()
tools = ToolOrchestrator()
planner = TaskPlanner(tools_orchestrator=tools, ia=ia)

print("=" * 70)
print("  TESTE DE PERFORMANCE - MCR-DevIA")
print("=" * 70)

resultados = {}

# ============================================================
# 1. DECIDER
# ============================================================
print("\n--- 1. DECIDER ---")

exemplos_lc = [
    ("O que e SPA no MCR?", "local"),
    ("pesquise python 3.13", "cloud"),
]

# Classificar (com cache)
for nome, consulta in [("MCR (local)", "O que e SPA no MCR?"), 
                        ("Web (cloud)", "pesquise python 3.13"),
                        ("Repetido (cache)", "O que e SPA no MCR?")]:
    t0 = time.time()
    r = decider.classificar(consulta, ['local', 'cloud'], exemplos=exemplos_lc)
    tempo = time.time() - t0
    resultados[f'decider_{nome}'] = round(tempo, 3)
    print(f"  [{nome:20s}] -> {r:6s} em {tempo:.3f}s")

# Extrair JSON
t0 = time.time()
dados = decider.extrair_json("Cria um jogo de plataforma em Python", 
                              {'nome': '', 'linguagem': ''},
                              exemplos=[("Cria um jogo em Python", {"nome": "jogo", "linguagem": "python"})])
tempo = time.time() - t0
resultados['decider_extrair_json'] = round(tempo, 3)
print(f"  [extrair_json         ] -> {dados.get('linguagem','?')} em {tempo:.3f}s")

# ============================================================
# 2. KNOWLEDGE GRAPH
# ============================================================
print("\n--- 2. KNOWLEDGE GRAPH ---")

# Busca por keyword
t0 = time.time()
r = kg.buscar("criar jogo", max_r=5)
tempo = time.time() - t0
resultados['kg_buscar_keyword'] = round(tempo, 3)
print(f"  [buscar keyword       ] -> {len(r)} resultados em {tempo:.4f}s")

# Busca por embedding
t0 = time.time()
r2 = kg.buscar_por_embedding("criar um jogo de plataforma", n=5)
tempo = time.time() - t0
resultados['kg_buscar_embedding'] = round(tempo, 3)
print(f"  [buscar embedding     ] -> {len(r2)} resultados em {tempo:.3f}s")

# Aprender
t0 = time.time()
kg.aprender("Teste perf", "teste", "teste", ctx="perf_test")
tempo = time.time() - t0
resultados['kg_aprender'] = round(tempo, 4)
print(f"  [aprender             ] -> em {tempo:.4f}s")

# ============================================================
# 3. EPISODIC MEMORY
# ============================================================
print("\n--- 3. EPISODIC MEMORY ---")

t0 = time.time()
r = mem.buscar("criar jogo", n=3)
tempo = time.time() - t0
resultados['mem_buscar'] = round(tempo, 4)
print(f"  [buscar               ] -> {len(r)} resultados em {tempo:.4f}s")

t0 = time.time()
taxa = mem.taxa_sucesso_para('gerar_codigo')
tempo = time.time() - t0
resultados['mem_taxa_sucesso'] = round(tempo, 4)
print(f"  [taxa_sucesso_para    ] -> {taxa:.2f} em {tempo:.4f}s")

t0 = time.time()
r = mem.buscar_com_peso_de_reforco("criar jogo", n=3, acoes=['gerar_codigo'])
tempo = time.time() - t0
resultados['mem_buscar_reforco'] = round(tempo, 4)
print(f"  [buscar_com_reforco   ] -> {len(r)} resultados em {tempo:.4f}s")

t0 = time.time()
clusters = mem.clusterizar(n_clusters=3)
tempo = time.time() - t0
resultados['mem_clusterizar'] = round(tempo, 3)
total_eps = sum(len(v) for v in clusters.values())
print(f"  [clusterizar (3 grp)  ] -> {total_eps} episodios em {tempo:.3f}s")

# ============================================================
# 4. TOOL ORCHESTRATOR
# ============================================================
print("\n--- 4. TOOL ORCHESTRATOR ---")

t0 = time.time()
lista = tools.listar()
tempo = time.time() - t0
resultados['tools_listar'] = round(tempo, 4)
print(f"  [listar ferramentas   ] -> {len(lista)} ferramentas em {tempo:.4f}s")

# Validar codigo
t0 = time.time()
r = tools.executar('validar_codigo', {'codigo': 'x = 1; print(x)'})
tempo = time.time() - t0
valido = r.get('resultado', {}).get('valido', False)
print(f"  [validar_codigo Python ] -> valido={valido} em {tempo:.3f}s")
resultados['tools_validar_python'] = round(tempo, 3)

t0 = time.time()
r = tools.executar('validar_codigo', {'codigo': '{"nome":"Joao"}'})
tempo = time.time() - t0
valido = r.get('resultado', {}).get('valido', False)
print(f"  [validar_codigo JSON  ] -> valido={valido} em {tempo:.3f}s")
resultados['tools_validar_json'] = round(tempo, 3)

t0 = time.time()
r = tools.executar('validar_codigo', {'codigo': 'const x=1;'})
tempo = time.time() - t0
valido = r.get('resultado', {}).get('valido', False)
print(f"  [validar_codigo JS    ] -> valido={valido} em {tempo:.3f}s")
resultados['tools_validar_js'] = round(tempo, 3)

# ============================================================
# 5. TASK PLANNER
# ============================================================
print("\n--- 5. TASK PLANNER ---")

t0 = time.time()
plano = planner.planejar("Cria um script python que imprime hello")
tempo = time.time() - t0
resultados['planner_criar_codigo'] = round(tempo, 3)
print(f"  [planejar criar_codigo] -> {len(plano)} passos em {tempo:.3f}s")

t0 = time.time()
plano = planner.planejar("Cria um jogo de plataforma em Python com 3 fases")
tempo = time.time() - t0
resultados['planner_projeto_jogo'] = round(tempo, 3)
print(f"  [planejar projeto_jogo] -> {len(plano)} passos em {tempo:.3f}s")

# ============================================================
# RELATORIO FINAL
# ============================================================
print("\n" + "=" * 70)
print("  RELATORIO DE PERFORMANCE")
print("=" * 70)
print(f"\n  {'Componente':35s} {'Tempo':>10s}")
print(f"  {'-'*35} {'-'*10}")
categorias = {
    'DECIDER': [k for k in resultados if k.startswith('decider')],
    'KNOWLEDGE GRAPH': [k for k in resultados if k.startswith('kg_')],
    'EPISODIC MEMORY': [k for k in resultados if k.startswith('mem_')],
    'TOOL ORCHESTRATOR': [k for k in resultados if k.startswith('tools_')],
    'TASK PLANNER': [k for k in resultados if k.startswith('planner_')],
}
for cat, keys in categorias.items():
    print(f"\n  [{cat}]")
    for k in keys:
        print(f"    {k[10:] if k.startswith('tools_') else k[5:] if k.startswith('planner_') else k.split('_',1)[1] if '_' in k else k:33s} {resultados[k]:>8.3f}s")
    total = sum(resultados[k] for k in keys)
    print(f"    {'TOTAL':33s} {total:>8.3f}s")

total_geral = sum(resultados.values())
print(f"\n  {'TOTAL GERAL':33s} {total_geral:>8.3f}s")

# Salva resultados
relatorio = {
    'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
    'resultados': resultados,
    'total_geral': round(total_geral, 3),
}
path = os.path.join('E:/Projeto MCR/sandbox', '.mcr_perf_report.json')
with open(path, 'w', encoding='utf-8') as f:
    json.dump(relatorio, f, ensure_ascii=False, indent=2)
print(f"\n[Relatorio salvo em .mcr_perf_report.json]")
