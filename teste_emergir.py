"""Testa MCRConexao com topicos reais do KG do DevIA."""
import sys, os, json, random, time, urllib.request

# Importa MCR.py do E:\MCR\ via caminho absoluto
mcr_path = r'E:\MCR\MCR.py'
import importlib.util
spec = importlib.util.spec_from_file_location("MCR_engine", mcr_path)
mcr_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcr_mod)

MCR = mcr_mod.MCR
MCRConexao = mcr_mod.MCRConexao

# Agora adiciona DevIA
sys.path.insert(0, r'E:\Projeto MCR\historia\scripts\mcr_devia')
sys.path.insert(0, r'E:\Projeto MCR\historia\scripts\mcr_devia\modulos')
from kg import KnowledgeGraph

kg = KnowledgeGraph()
licoes = kg.data.get('licoes', [])
ativas = [l for l in licoes if not l.get('inactive', False)]

from collections import defaultdict
por_ctx = defaultdict(list)
for l in ativas[:500]:
    ctx = l.get('ctx', 'geral')
    palavras = l.get('erro', '') + ' ' + l.get('solucao', '')
    por_ctx[ctx].append(palavras)

ctxs_com_conteudo = [(c, ls) for c, ls in por_ctx.items() if len(ls) >= 3]
print(f'KG: {len(ativas)} ativas, {len(ctxs_com_conteudo)} contextos')

if len(ctxs_com_conteudo) >= 2:
    (ctx_a, palavras_a), (ctx_b, palavras_b) = random.sample(ctxs_com_conteudo, 2)
    
    texto_a = ' '.join(palavras_a[:10])
    texto_b = ' '.join(palavras_b[:10])
    
    print(f'\nTopico A ({ctx_a}): {texto_a[:100]}...')
    print(f'Topico B ({ctx_b}): {texto_b[:100]}...')
    
    # Cria cerebro simplificado pro MCRConexao
    cerebro = type('Cerebro', (), {})()
    cerebro.mk_palavra = MCR('palavra')
    cerebro.topicos = {}
    
    cerebro.mk_palavra.aprender_sequencia(texto_a.split())
    cerebro.mk_palavra.aprender_sequencia(texto_b.split())
    
    cerebro.topicos[ctx_a] = {'conteudo': list(set(texto_a.lower().split()))}
    cerebro.topicos[ctx_b] = {'conteudo': list(set(texto_b.lower().split()))}
    
    # MCRConexao (0 LLM)
    conexao = MCRConexao(cerebro)
    t0 = time.time()
    resultado = conexao.analisar(ctx_a, ctx_b)
    t = time.time() - t0
    
    print(f'\n=== MCRConexao (0 LLM, {t*1000:.2f}ms) ===')
    if resultado.get('melhor'):
        melhor = resultado['melhor']
        print(f"Melhor ponte: '{melhor['palavra']}' (score={melhor['score']})")
        print(f"  Divergencia: {melhor.get('divergencia',0):.3f}")
        print(f"  Especificidade: {melhor.get('especificidade',0):.3f}")
        print(f"  Profundidade: {melhor.get('profundidade',0):.3f}")
    
    if resultado.get('pontes'):
        print(f"\nTop 5 pontes:")
        for p in resultado['pontes'][:5]:
            print(f"  '{p['palavra']}' score={p['score']:.2f}")
    
    # Gera "E se..." via LLM (1 chamada so)
    print(f"\n=== LLM gera 'E se...?' (1 call) ===")
    prompt = (
        f"Crie UMA pergunta criativa 'E se...?' combinando estes dois conceitos:\n"
        f"1. {ctx_a}: {texto_a[:150]}\n"
        f"2. {ctx_b}: {texto_b[:150]}\n\n"
        f"A pergunta deve revelar algo NOVO que nao esta em nenhum dos topicos.\n"
        f"Responda APENAS com a pergunta. Em PT-BR."
    )
    
    try:
        r = urllib.request.urlopen('http://localhost:11434', timeout=2)
        payload = json.dumps({
            "model": "qwen2.5-coder:7b",
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 256, "temperature": 0.7}
        }).encode()
        req = urllib.request.Request('http://localhost:11434/api/generate', data=payload,
                                     headers={"Content-Type": "application/json"})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            resposta = result.get('response', '')
        t = time.time() - t0
        print(f'  Tempo LLM: {t:.1f}s')
        print(f'  "E se...?": {resposta.strip()[:300]}')
        
        print(f'\n=== COMPARACAO ===')
        print(f'Emergir original: 5 chamadas LLM por ciclo, ~25-40s')
        print(f'Emergir + MCRConexao: 0ms descoberta + {t:.1f}s LLM = ~{t:.1f}s')
        print(f'Ganho: ~{25/t:.0f}x mais rapido')
    except Exception as e:
        print(f'  LLM offline: {e}')
        print(f'\nSem LLM, mas as pontes foram encontradas em {t*1000:.2f}ms')
