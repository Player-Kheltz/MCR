import sys, time
sys.path.insert(0, r'E:\MCR')
from mcr_devia import processar, _decider, MODELO_POR_CLASSE

for pergunta in ['traduza hello world para PT-BR', 'explique o que e SPA']:
    classe, conf = _decider.classificar(pergunta)
    modelo = MODELO_POR_CLASSE.get(classe, "qwen2.5-coder:7b (DEFAULT)")
    print(f'> {pergunta}')
    print(f'  classe: {classe} conf={conf:.2f}')
    print(f'  modelo: {modelo}')
    t0 = time.time()
    r = processar(pergunta)
    t = time.time() - t0
    print(f'  tempo: {t:.1f}s')
    
    # Testa o modelo diretamente no LLM
    from mcr_devia import _llm
    if classe == 'traduzir_texto':
        t0 = time.time()
        resp = _llm.gerar('traduza hello world para PT-BR', modelo='qwen2.5-coder:1.5b', temp=0.3)
        t = time.time() - t0
        print(f'  1.5b manual: {t:.1f}s -> {resp[:60]}')
