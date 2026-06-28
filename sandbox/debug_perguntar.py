"""Debug: rastrear fluxo do perguntar"""
import sys, json
sys.path.insert(0, "E:\\Projeto MCR\\scripts\\mcr_devia")
from mcr_devia import KnowledgeGraph, IA, Supervisor

kg = KnowledgeGraph()
ia = IA()
s = Supervisor(ia, kg)

texto = "O que e SHC no projeto MCR?"
print(f"1. Buscando KG para: {texto[:50]}...")
ctx = kg.buscar(texto)
print(f"   Resultados: {len(ctx)}")
for c in ctx:
    print(f"   - {c['id']}: {c['solucao'][:80]}")

if ctx:
    print(f"\n2. Temos {len(ctx)} resultados. Montando contexto...")
    # Simular a nova logica de limitacao
    if len(ctx) > 2:
        ctx = ctx[:2]
        print(f"   Limitado para {len(ctx)}")
    ctx_str = 'Sei disso:\n' + '\n'.join(f'- {l["solucao"]}' for l in ctx) + '\n\n'
    print(f"   Contexto: {ctx_str[:200]}...")
    
    prompt = f"{ctx_str}INSTRUCAO: Use APENAS as informacoes acima. NAO use seu conhecimento proprio.\n\nPergunta: {texto}\n\nResposta (usando APENAS o contexto acima):"
    print(f"\n3. Chamando IA...")
    r = ia.gerar(prompt, tarefa="contexto")
    if r:
        print(f"   Resposta: {r[:300]}")
    else:
        print(f"   Sem resposta da IA")
else:
    print(f"\n2. Sem contexto! Indo para pipeline de busca...")
