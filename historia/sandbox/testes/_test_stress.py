"""TESTE DE ESTRESSE — Leva cada componente ao limite para entender gargalos."""
import sys, os, time, json, random, threading, tempfile
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
sys.path.insert(0, 'E:/Projeto MCR')

from context_infinity import SessionCache
from modulos.decider import Decider
from modulos.kg import KnowledgeGraph
from modulos.episodic_memory import EpisodicMemory
from modulos.ia import IA
from modulos.tool_orchestrator import ToolOrchestrator
from modulos.task_planner import TaskPlanner
from modulos.master_agent import MasterAgent
from modulos.util import extrair_codigo_puro, extrair_nome_projeto

ia = IA()
decider = Decider(ia)
kg = KnowledgeGraph()
mem = EpisodicMemory()
tools = ToolOrchestrator()
planner = TaskPlanner(tools_orchestrator=tools, ia=ia)

print("=" * 70)
print("  TESTE DE ESTRESSE — MCR-DevIA")
print("  Descubrindo os LIMITES do sistema")
print("=" * 70)

resultados = {}
falhas = []

# ============================================================
# 1. SESSIONCACHE — Cap. de absorcao + tempo de pesca
# ============================================================
print("\n--- 1. SESSIONCACHE: CAPACIDADE DE ABSORCAO ---")

cache = SessionCache()
for batch in [100, 1000, 5000, 10000]:
    t0 = time.time()
    for i in range(batch):
        cache.absorver(f'stress_{batch}_{i}', 
                       f'fragmento de teste numero {i} com conteudo variavel ' * 5,
                       'texto', tags=['stress', f'batch_{batch}'])
    tempo = time.time() - t0
    resultados[f'sessioncache_absorver_{batch}'] = round(tempo, 3)
    print(f"  Absorver {batch:6d} fragmentos: {tempo:.3f}s ({batch/tempo:.0f} frag/s)")

# Limpeza para teste de pesca
print("\n  Teste de PESCA em lote grande...")
t0 = time.time()
for _ in range(100):
    r = cache.pescar(pergunta='teste numero stress', tipos=['texto'], max_tokens=2000, n=10)
tempo = time.time() - t0
resultados['sessioncache_pescar_100x'] = round(tempo, 3)
print(f"  100 pescas em {tempo:.3f}s ({(100/tempo):.0f} pescas/s)")

t0 = time.time()
estado = cache.reconstruir(max_chars=5000)
tempo = time.time() - t0
resultados['sessioncache_reconstruir'] = round(tempo, 3)
print(f"  Reconstruir estado (5k chars): {tempo:.4f}s")

m = cache.metricas()
print(f"  Metricas finais: {m['fragmentos']} frags, {m['termos_indexados']} termos, {m['tokens_total']} tokens")

# ============================================================
# 2. DECIDER — Classificacoes rapidas em lote
# ============================================================
print("\n--- 2. DECIDER: CLASSIFICACOES EM LOTE ---")

exemplos_lc = [("O que e SPA no MCR?", "local"), ("pesquise python", "cloud")]
consultas = [
    "O que e SPA no MCR?",
    "pesquise python 3.13",
    "cria um jogo em Python",
    "noticias de hoje",
    "como funciona um loop",
    "quem foi einstein?",
    "cria um script lua",
    "explique o SHC",
]

# Primeira vez (sem cache)
t0 = time.time()
for q in consultas:
    r = decider.classificar(q, ['local', 'cloud'], exemplos=exemplos_lc)
tempo = time.time() - t0
resultados['decider_8_classificacoes_1a_vez'] = round(tempo, 3)
print(f"  8 classificacoes (1a vez): {tempo:.3f}s ({(tempo/8*1000):.0f}ms cada)")

# Segunda vez (com cache)
t0 = time.time()
for q in consultas:
    r = decider.classificar(q, ['local', 'cloud'], exemplos=exemplos_lc)
tempo = time.time() - t0
resultados['decider_8_classificacoes_cache'] = round(tempo, 3)
print(f"  8 classificacoes (cache):  {tempo:.3f}s ({(tempo/8*1000):.1f}ms cada)")

# ============================================================
# 3. KG — Aprender + buscar em lote
# ============================================================
print("\n--- 3. KG: APRENDER + BUSCAR EM LOTE ---")

t0 = time.time()
for i in range(50):
    kg.aprender(f"Erro de teste {i}", f"Causa do erro {i}", 
                f"Solucao para o erro {i} com detalhes tecnicos", 
                ctx='stress_test')
tempo = time.time() - t0
resultados['kg_aprender_50'] = round(tempo, 3)
print(f"  Aprender 50 licoes: {tempo:.3f}s")

t0 = time.time()
for i in range(20):
    r = kg.buscar(f"erro de teste {i}", max_r=3)
tempo = time.time() - t0
resultados['kg_buscar_keyword_20x'] = round(tempo, 3)
print(f"  20 buscas keyword: {tempo:.4f}s")

t0 = time.time()
for i in range(5):
    r = kg.buscar_por_embedding(f"erro de teste {i}", n=3)
tempo = time.time() - t0
resultados['kg_buscar_embedding_5x'] = round(tempo, 3)
print(f"  5 buscas embedding: {tempo:.3f}s ({tempo/5*1000:.0f}ms cada)")

# ============================================================
# 4. TOOL ORCHESTRATOR — Multiplas validacoes
# ============================================================
print("\n--- 4. TOOL ORCHESTRATOR: VALIDACOES EM LOTE ---")

codigos_teste = [
    ("Python valido", 'x = 1; print(x)', 'python'),
    ("Python invalido", 'x = ', 'python'),
    ("JSON valido", '{"nome": "Joao", "idade": 30}', 'json'),
    ("JSON invalido", '{nome: Joao}', 'json'),
    ("JavaScript", 'const x = 1; console.log(x);', 'javascript'),
    ("HTML", '<html><body>Oi</body></html>', 'html'),
    ("Lua", 'local x = 1; print(x)', 'lua'),
    ("Rust (sem validador)", 'fn main() { println!("hi"); }', 'rust'),
    ("Markdown + Python", '```python\nprint("oi")\n```', 'python'),
    ("Codigo vazio", '', 'invalido'),
]

t0 = time.time()
for nome, codigo, lang_esperada in codigos_teste:
    r = tools.executar('validar_codigo', {'codigo': codigo})
tempo = time.time() - t0
resultados['tools_validar_10_linguagens'] = round(tempo, 3)
print(f"  10 validacoes (diversas linguagens): {tempo:.3f}s ({(tempo/10*1000):.0f}ms cada)")

# ============================================================
# 5. EPISODIC MEMORY — Registro + busca + cluster
# ============================================================
print("\n--- 5. EPISODIC MEMORY: REGISTRO + BUSCA + CLUSTER ---")

# Registrar alguns episodios
t0 = time.time()
for i in range(10):
    mem.registrar(f"teste de estresse episodio {i}", 
                  {'sucesso': i % 2 == 0}, 
                  f"licao do episodio {i}")
tempo = time.time() - t0
resultados['mem_registrar_10'] = round(tempo, 3)
print(f"  Registrar 10 episodios: {tempo:.3f}s")

t0 = time.time()
for i in range(10):
    r = mem.buscar(f"teste de estresse", n=3)
tempo = time.time() - t0
resultados['mem_buscar_10x'] = round(tempo, 3)
print(f"  10 buscas: {tempo:.3f}s")

t0 = time.time()
taxa = mem.taxa_sucesso_para('gerar_codigo')
tempo = time.time() - t0
resultados['mem_taxa_sucesso'] = round(tempo, 4)
print(f"  taxa_sucesso_para(): {taxa:.2f} em {tempo:.4f}s")

t0 = time.time()
clusters = mem.clusterizar(n_clusters=5)
tempo = time.time() - t0
resultados['mem_clusterizar_5'] = round(tempo, 3)
total = sum(len(v) for v in clusters.values())
print(f"  clusterizar(5 grupos): {tempo:.3f}s ({total} episodios)")

# ============================================================
# 6. TASK PLANNER — Planejamento variado
# ============================================================
print("\n--- 6. TASK PLANNER: PLANEJAMENTO VARIADO ---")

requests_teste = [
    ("Script simples", "Cria um script python que imprime hello"),
    ("Jogo completo", "Cria um jogo de plataforma em Python com 3 fases"),
    ("Site", "Cria um site em HTML+CSS com 3 paginas"),
    ("Pergunta", "O que e SPA no MCR?"),
    ("Analise", "Analisa este codigo: x = 1"),
]

t0 = time.time()
for nome, req in requests_teste:
    try:
        plano = planner.planejar(req)
        result = f"{len(plano)} passos"
    except Exception as e:
        result = f"ERRO: {e}"
tempo = time.time() - t0
resultados['planner_5_requests'] = round(tempo, 3)
print(f"  5 planejamentos variados: {tempo:.3f}s ({(tempo/5*1000):.0f}ms cada)")

# ============================================================
# 7. MASTERAGENT — Execucao completa (limitada para nao demorar)
# ============================================================
print("\n--- 7. MASTERAGENT: EXECUCAO COMPLETA ---")

agent = MasterAgent()

t0 = time.time()
r = agent.executar("Cria um script python que imprime 'Hello World'")
tempo = time.time() - t0
resultados['masteragent_script_simples'] = round(tempo, 3)
print(f"  Script simples: {tempo:.1f}s — {r.get('n_sucesso',0)}/{r.get('n_subtarefas',0)} passos")

# Verifica SessionCache
n_frags = len(agent.ctx.fragmentos) if hasattr(agent, 'ctx') else 0
print(f"  Fragmentos no SessionCache: {n_frags}")

# ============================================================
# 8. EXECUCAO CONCORRENTE (2 threads)
# ============================================================
print("\n--- 8. EXECUCAO CONCORRENTE (2 threads) ---")

def executar_worker(id, request, results):
    try:
        ag = MasterAgent()
        t0 = time.time()
        r = ag.executar(request)
        t = time.time() - t0
        results[id] = {'tempo': round(t, 1), 'sucesso': r.get('sucesso'), 'passos': f"{r.get('n_sucesso',0)}/{r.get('n_subtarefas',0)}"}
    except Exception as e:
        results[id] = {'erro': str(e)}

threads = []
results_threads = {}
reqs = [
    ("T1", "Cria um script python que imprime 'teste 1'"),
    ("T2", "Cria um script python que imprime 'teste 2'"),
]

t0 = time.time()
for id_t, req_t in reqs:
    t = threading.Thread(target=executar_worker, args=(id_t, req_t, results_threads))
    threads.append(t)
    t.start()

for t in threads:
    t.join(timeout=180)

tempo = time.time() - t0
resultados['concorrencia_2_threads'] = round(tempo, 3)
for id_t, res in results_threads.items():
    print(f"  Thread {id_t}: {res}")

# ============================================================
# RELATORIO FINAL
# ============================================================
print("\n\n" + "=" * 70)
print("  RELATORIO DE ESTRESSE")
print("=" * 70)

categorias = {
    'SESSIONCACHE': [k for k in resultados if k.startswith('sessioncache')],
    'DECIDER': [k for k in resultados if k.startswith('decider')],
    'KNOWLEDGE GRAPH': [k for k in resultados if k.startswith('kg_')],
    'EPISODIC MEMORY': [k for k in resultados if k.startswith('mem_')],
    'TOOL ORCHESTRATOR': [k for k in resultados if k.startswith('tools_')],
    'TASK PLANNER': [k for k in resultados if k.startswith('planner_')],
    'MASTER AGENT': [k for k in resultados if k.startswith('masteragent_')],
    'CONCORRENCIA': [k for k in resultados if k.startswith('concorrencia_')],
}

for cat, keys in categorias.items():
    if not keys: continue
    total = sum(resultados[k] for k in keys)
    print(f"\n  [{cat}] Total: {total:.3f}s")
    for k in keys:
        nome_curto = k.replace('sessioncache_','').replace('decider_','').replace('kg_','').replace('mem_','').replace('tools_','').replace('planner_','').replace('masteragent_','').replace('concorrencia_','')
        print(f"    {nome_curto:40s} {resultados[k]:>8.3f}s")

tempo_total = sum(resultados.values())
print(f"\n  {'TEMPO TOTAL':50s} {tempo_total:>8.3f}s")
print(f"  {'FRAGMENTOS NO SESSIONCACHE':50s} {cache.metricas()['fragmentos']}")
print(f"  {'TERMOS INDEXADOS':50s} {cache.metricas()['termos_indexados']}")

# Salva relatorio
relatorio = {
    'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
    'resultados': resultados,
    'metricas_sessioncache': cache.metricas(),
    'tempo_total': round(tempo_total, 3),
}
path = os.path.join('E:/Projeto MCR/sandbox', '.mcr_stress_report.json')
with open(path, 'w', encoding='utf-8') as f:
    json.dump(relatorio, f, ensure_ascii=False, indent=2)
print(f"\n[Relatorio salvo em .mcr_stress_report.json]")
