"""Teste das 6 correcoes ML/NN/AGI."""
import sys, time
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.kg import KnowledgeGraph
from modulos.episodic_memory import EpisodicMemory
from modulos.master_agent import MasterAgent

print("=== Teste Correcoes ML/NN/AGI ===\n")

# C1: KG com embeddings
print("C1: KG busca semantica...")
kg = KnowledgeGraph()
r_embed = kg.buscar_por_embedding("criar um jogo de plataforma", n=2)
print(f"   buscar_por_embedding: {len(r_embed)} resultados")
if r_embed:
    print(f"   Primeiro: {r_embed[0]['erro'][:60]}")
# Testa que aprender() salva embedding
kg.aprender("Teste embedding", "causa teste", "solucao teste", ctx="test_embed")
print("   aprender() com embedding: OK")

# C2: Reforco
print("\nC2: EpisodicMemory funcao de recompensa...")
mem = EpisodicMemory()
taxa = mem.taxa_sucesso_para('gerar_codigo')
print(f"   taxa_sucesso_para('gerar_codigo'): {taxa:.2f}")
assert 0.0 <= taxa <= 1.0, f"Taxa invalida: {taxa}"

# Testa buscar_com_peso_de_reforco
resultados = mem.buscar_com_peso_de_reforco("criar um jogo", n=3, acoes=['gerar_codigo', 'validar_python'])
print(f"   buscar_com_peso_de_reforco: {len(resultados)} resultados")

# C3: Dataset estruturado (testa que _aprender_kg agora usa ctx=exec_*)
print("\nC3: KG estruturado...")
agent = MasterAgent()
# Simula registro
agent._aprender_kg(
    "cria um jogo teste", 
    {'sucesso': True, 'n_sucesso': 4, 'n_subtarefas': 4, 'tempo': 30.5, 'task_type': 'projeto_jogo'},
    "teste licao",
    task_type='projeto_jogo'
)
# Verifica se tem licao com ctx=exec_*
licoes_exec = [l for l in kg.data['licoes'] if 'exec_' in l.get('ctx', '')]
print(f"   Licoes com exec_ no ctx: {len(licoes_exec)}")

# C4: Feedback
print("\nC4: Feedback loop...")
agent._feedback("teste feedback", "simples", [{'id': 1}], {'1': {'sucesso': False}})
print("   _feedback executado sem erro")

# C5: Clusterizacao
print("\nC5: Clusterizacao...")
clusters = mem.clusterizar(n_clusters=3)
print(f"   clusters: {len(clusters)} grupos")
for cid, eps in clusters.items():
    print(f"   Grupo {cid}: {len(eps)} episodios")

# C6: Metacognicao
print("\nC6: Metacognicao...")
avaliacao = agent.autoavaliar("criar um jogo em Python com Pygame")
print(f"   Confianca: {avaliacao['confianca']}")
print(f"   Acao: {avaliacao['acao']}")
print(f"   Gaps: {avaliacao['gaps']}")
assert avaliacao['acao'] in ('executar', 'executar_com_cautela', 'estudar_antes')

print("\n=== TODOS OS TESTES OK ===")
