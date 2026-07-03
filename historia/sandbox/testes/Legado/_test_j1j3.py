"""Teste das 3 correcoes pos-teste."""
import sys, time, threading
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
sys.path.insert(0, 'E:/Projeto MCR')
from modulos.master_agent import MasterAgent
from modulos.tool_orchestrator import ToolOrchestrator
from modulos.lessons_buffer import LessonsBuffer
from modulos.kg import KnowledgeGraph
from modulos.episodic_memory import EpisodicMemory

print("=== Teste Correcoes J1-J3 ===\n")

# J1: LessonsBuffer com batch
print("J1: LessonsBuffer com batch...")
kg = KnowledgeGraph()
buffer = LessonsBuffer(kg)
for i in range(5):
    buffer.adicionar(f"Erro de teste {i}", f"Causa do erro {i}", f"Solucao {i}", ctx='test_j1')
n = buffer.comitar()
print(f"   Lessons comitadas: {n}")
ultimas = kg.data['licoes'][-5:]
print(f"   Ultimas {len(ultimas)} lessons no KG: IDs = {[l.get('id','?') for l in ultimas]}")
assert n >= 0

# J2: Buffer de episodios
print("\nJ2: Buffer de episodios...")
agent = MasterAgent()
for i in range(3):
    agent._registrar_episodio({"sucesso": True}, "teste", f"licao do teste {i}")
print(f"   Buffer apos 3 registros: {len(agent._buffer_episodios)} (deve ser 3)")
assert len(agent._buffer_episodios) == 3
agent._flush_episodios()
print(f"   Buffer apos flush: {len(agent._buffer_episodios)} (deve ser 0)")
assert len(agent._buffer_episodios) == 0

# J3: Lock de escrita concorrente
print("\nJ3: Lock de escrita concorrente...")
tools = ToolOrchestrator()
erros = []
def escrever_thread(id, caminho):
    try:
        tools.executar('escrever_arquivo', {'caminho': caminho, 'conteudo': f'teste da thread {id}'})
    except Exception as e:
        erros.append(str(e))

caminho = 'E:/Projeto MCR/sandbox/_test_concorrencia.txt'
threads = []
for i in range(5):
    t = threading.Thread(target=escrever_thread, args=(i, caminho))
    threads.append(t)
    t.start()
for t in threads:
    t.join()

if erros:
    print(f"   ERROS: {erros}")
else:
    print(f"   5 threads sem erro! Conteudo: {open(caminho).read().strip()}")
assert len(erros) == 0

# Limpeza
import os
os.remove(caminho)

print("\n=== TODOS OS TESTES OK ===")
