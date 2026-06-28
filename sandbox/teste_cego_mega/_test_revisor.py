import os, sys
sys.path.insert(0, r"E:\Projeto MCR\scripts\mcr_devia")
os.chdir(r"E:\Projeto MCR\scripts\mcr_devia")

from modulos.auto_revisor import AutoRevisor, escanear_classes

# Suprime stdout
import contextlib
with open(os.devnull, 'w') as devnull:
    old = sys.stdout
    sys.stdout = devnull
    try:
        escanear_classes()
    finally:
        sys.stdout = old

r = AutoRevisor()
teste = "A classe DataLoader processa os dados. DataLake e StreamSimulator sao classes reais do projeto."
res = r.revisar(teste, {"DataLake", "StreamSimulator"})
print("Alucinacoes: " + str(res["total"]))
for c, ctx in res["alucinacoes"]:
    print("  " + c)

corrigido, _ = r.auto_corrigir(teste, {"DataLake", "StreamSimulator"})
print("Corrigido: " + corrigido)
