"""Testa conexao_bridge com dados reais do KG."""
import sys, os, json, random, time, urllib.request

sys.path.insert(0, r'E:\MCR')

from conexao_bridge import CerebroKG

# Simula um KG simplificado — carrega direto dos JSONs do KG
class KGSimples:
    def __init__(self):
        self.data = {'licoes': []}
        kg_dir = r'E:\Projeto MCR\historia\sandbox\.mcr_devia\kg'
        if os.path.isdir(kg_dir):
            for f in os.listdir(kg_dir)[:30]:  # 30 arquivos bastam
                if not f.endswith('.json'): continue
                try:
                    with open(os.path.join(kg_dir, f), encoding='utf-8') as fh:
                        data = json.load(fh)
                    licoes = data.get('licoes', []) if isinstance(data, dict) else []
                    if isinstance(licoes, list):
                        for l in licoes:
                            if isinstance(l, dict) and l.get('erro'):
                                l['ctx'] = l.get('ctx', data.get('ctx', 'geral'))
                                self.data['licoes'].append(l)
                except:
                    pass
    
    def buscar(self, texto, max_r=5):
        return []

kg = KGSimples()
print(f'KG: {len(kg.data["licoes"])} lessons carregadas')

# Cria cerebro e alimenta com KG
t0 = time.time()
cerebro = CerebroKG(kg)
t = time.time() - t0
print(f'Cerebro criado em {t*1000:.0f}ms')
print(f'Topicos: {len(cerebro.topicos)}')
print(f'Palavras: {cerebro.mk_palavra.total}')

# Descobre conexoes
t0 = time.time()
descobertas = cerebro.descobrir_conexoes(top_k=5)
t = time.time() - t0
print(f'\nDescobertas (MCRConexao, {t*1000:.2f}ms, 0 LLM):')
for d in descobertas:
    print(f'  [{d["topico_a"][:20]} + {d["topico_b"][:20]}]')
    print(f'    ponte="{d["ponte"]}" score={d["score"]}')
    pergunta = cerebro.gerar_pergunta_e_se(d)
    print(f'    E se...: {pergunta[:120]}')

# Tenta gerar com LLM a melhor descoberta
if descobertas:
    try:
        urllib.request.urlopen('http://localhost:11434', timeout=2)
        print(f'\n=== LLM gera "E se..." (1 call) ===')
        t0 = time.time()
        pergunta_llm = cerebro.gerar_pergunta_e_se(descobertas[0], 
            lambda p: json.loads(urllib.request.urlopen(
                urllib.request.Request('http://localhost:11434/api/generate',
                    data=json.dumps({"model":"qwen2.5-coder:7b","prompt":p,"stream":False,
                                    "options":{"num_predict":128,"temperature":0.7}}).encode(),
                    headers={"Content-Type":"application/json"}),
                timeout=60).read()).get('response',''))
        t = time.time() - t0
        print(f'  {pergunta_llm.strip()}')
        print(f'  Tempo LLM: {t:.1f}s')
        print(f'\nComparacao: Emergir original ~25s (5 chamadas LLM)')
        print(f'           Bridge+MCRConexao ~{t:.1f}s (1 chamada LLM)')
        print(f'           Proximo ciclo: 0ms (MCRConexao ja sabe a ponte)')
    except Exception as e:
        print(f'  LLM offline: {e}')
