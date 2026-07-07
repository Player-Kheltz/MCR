import sys, os, time, json
sys.path.insert(0, r'E:\MCR')
from mcr_devia import processar

print('=' * 50)
print('TESTE: MCR + RAG integrados')
print('=' * 50)

testes = [
    'explique o que e SPA no Projeto MCR',
    'traduza hello world para PT-BR',
]

for pergunta in testes:
    print(f'\n> {pergunta}')
    t0 = time.time()
    r = processar(pergunta)
    t = time.time() - t0
    
    print(f'  classe: {r["classe"]} conf={r["confianca"]:.2f}')
    print(f'  validacao: {"OK" if r["validacao"]["valida"] else "X"}')
    print(f'  tempo: {t:.2f}s')
    print(f'  resposta: {r["resposta"][:200]}')
