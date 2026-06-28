import os, sys
sys.path.insert(0, r"E:\Projeto MCR\scripts\mcr_devia")
os.chdir(r"E:\Projeto MCR\scripts\mcr_devia")

import contextlib
with open(os.devnull, 'w') as devnull:
    old = sys.stdout
    sys.stdout = devnull
    try:
        from modulos.auto_revisor import AutoRevisor
        from modulos.util import fast as _fast
    finally:
        sys.stdout = old

# Teste direto do FAST
print("Teste FAST direto:")
prompt = "Contexto: A classe FileProcessor processa arquivos de configuracao.\n\nA classe 'FileProcessor' mencionada acima:\nA) Existe no contexto do problema\nB) Foi inventada pelo modelo\n\nResponda apenas: A ou B"
resp = _fast(prompt, 0.1, "leve")
print(f"  FAST respondeu: '{resp}'")

prompt2 = "Contexto: A classe HyperNovaProcessor usa QuantumNeuralNetwork.\n\nA classe 'HyperNovaProcessor' mencionada acima:\nA) Existe no contexto\nB) Foi inventada\n\nResponda apenas: A ou B"
resp2 = _fast(prompt2, 0.1, "leve")
print(f"  FAST respondeu: '{resp2}'")

r = AutoRevisor()

# Teste 1: FileProcessor (classe real do problema - nao deveria ser alucinacao)
teste1 = "A classe FileProcessor processa arquivos de configuracao. Ela usa requests.get() para verificar servidores."
res1 = r.revisar(teste1)
print(f"Teste 1 - FileProcessor (deveria ser REAL):")
print(f"  Alucinacoes: {res1['total']}")
for c, ctx in res1['alucinacoes']:
    print(f"  FALSO POSITIVO: {c}")

# Teste 2: Classe realmente inventada  
teste2 = "A classe HyperNovaProcessor usa QuantumNeuralNetwork para processar dados."
res2 = r.revisar(teste2)
print(f"\nTeste 2 - HyperNovaProcessor (deveria ser ALUCINACAO):")
print(f"  Alucinacoes: {res2['total']}")
for c, ctx in res2['alucinacoes']:
    print(f"  CORRETO: {c}")

# Teste 3: TypeScript (linguagem real)
teste3 = "TypeScript e uma superset do JavaScript com tipos estaticos."
res3 = r.revisar(teste3)
print(f"\nTeste 3 - TypeScript (deveria ser REAL):")
print(f"  Alucinacoes: {res3['total']}")
for c, ctx in res3['alucinacoes']:
    print(f"  FALSO POSITIVO: {c}")
