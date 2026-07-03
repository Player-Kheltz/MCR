"""Debug: AprendizDePadroes + salvar KG"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.kg import KnowledgeGraph
from modulos.aprendiz_de_padroes import AprendizDePadroes
from modulos.tool_orchestrator import ToolOrchestrator

print("[1] Iniciando...")
t0 = time.time()

print(f"[2] PE + KG ({time.time()-t0:.1f}s)")
pe = PatternEngine()
kg = KnowledgeGraph()

print(f"[3] Aprendiz ({time.time()-t0:.1f}s)")
ap = AprendizDePadroes(pe=pe, kg=kg)

print(f"[4] Testando estudar_dados com texto ({time.time()-t0:.1f}s)")
padroes = ap.estudar_dados("Crie um NPC ferreiro em Eridanus", "teste_texto")
print(f"[5] Padroes: {len(padroes)} ({time.time()-t0:.1f}s)")

print(f"[6] Testando salvar_kg ({time.time()-t0:.1f}s)")
salvos = ap.salvar_kg()
print(f"[7] Salvos: {salvos} ({time.time()-t0:.1f}s)")

print(f"[8] Testando estudar_tudo() ({time.time()-t0:.1f}s)")
resultados = ap.estudar_tudo()
print(f"[9] Fontes estudadas: {resultados} ({time.time()-t0:.1f}s)")

print(f"\n✅ OK em {time.time()-t0:.1f}s")
