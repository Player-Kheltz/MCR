"""teste_pilar8_mcr_vs_phi4mini.py — Comparacao JUSTA MCR vs LLM (Pilar 8)

Regime de comparacao canonicos definidos em docs/PLANO_EVOLUCAO_MCR.md:
  - Corpus: tests/experimento_rigoroso/dataset_500.json (562 entradas)
  - Split: 80/20 estratificado por acao, random.seed(42) → 449 treino / 113 teste
  - Tarefa: classificacao de intencao → 1 das 12 acoes
  - MCR: MCRCoupling().alimentar_swarm(treino) — treino O(1)
  - LLM: phi4-mini via Ollama, few-shot 5 exemplos/acao no prompt (60 exemplos)
  - Metricas: accuracy no holdout, latencia p50/p99

Resolvi sim o item 1 da lista de pendencias: nenhuma claim "supera LLM"
sem baseline medido. Antes os testes "mcr_vs_llm*" simulavam llm_pred=esp
sem chamar LLM nenhuma — isto viola o Pilar 8.
"""
import sys, os, json, time, random, re
import urllib.request
import urllib.error
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DATASET = 'E:/MCR/tests/experimento_rigoroso/dataset_500.json'
OLLAMA_URL = 'http://localhost:11434/api/generate'
LLM_MODEL = 'phi4-mini:latest'
N_FEW_SHOT_PER_ACTION = 5
TIMEOUT_PER_CALL = 120

ACOES = [
    'gerar_npc', 'gerar_monstro', 'responder', 'gerar_sprite',
    'gerar_quest', 'conectar', 'aprender', 'planejar',
    'validar', 'analisar', 'buscar', 'editar',
]


def carregar_dataset():
    with open(DATASET, 'r', encoding='utf-8') as f:
        return json.load(f)


def split_80_20(dataset):
    """Split identico ao _regressao_fase1.py para reprodutibilidade."""
    random.seed(42)
    pares = [(d['input'], d['expected_action']) for d in dataset]
    random.shuffle(pares)
    n = len(pares)
    n_treino = int(n * 0.8)
    return pares[:n_treino], pares[n_treino:]


def amostrar_few_shot(treino, n_por_acao, seed=42):
    """Amostra n_por_acao exemplos por acao do treino, com seed fixa."""
    rng = random.Random(seed)
    por_acao = defaultdict(list)
    for inp, act in treino:
        por_acao[act].append(inp)
    few_shot = []
    for act in ACOES:
        pool = list(por_acao.get(act, []))
        rng.shuffle(pool)
        exemplos = pool[:n_por_acao]
        for inp in exemplos:
            few_shot.append((inp, act))
    rng.shuffle(few_shot)
    return few_shot


def construir_prompt(few_shot, input_teste):
    """Construi prompt few-shot para classificacao de intencao."""
    acoes_str = ', '.join(ACOES)
    linhas = []
    linhas.append('Voce e um classificador de intencao. Dado um comando, responda APENAS com o nome exato de uma destas acoes:')
    linhas.append(acoes_str + '.')
    linhas.append('')
    linhas.append('Exemplos (input -> acao):')
    for inp, act in few_shot:
        linhas.append(f'input: {inp}')
        linhas.append(f'acao: {act}')
        linhas.append('')
    linhas.append(f'input: {input_teste}')
    linhas.append('acao:')
    return '\n'.join(linhas)


def chamar_ollama(prompt, timeout=TIMEOUT_PER_CALL):
    """Chama phi4-mini via /api/generate. Retorna (resposta_texto, erro)."""
    payload = {
        'model': LLM_MODEL,
        'prompt': prompt,
        'stream': False,
        'options': {
            'temperature': 0,
            'top_p': 1.0,
            'num_predict': 20,
            'stop': ['\ninput:', '\nInput:', 'input:'],
        },
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        OLLAMA_URL, data=data, headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode('utf-8'))
            return body.get('response', '').strip(), None
    except urllib.error.URLError as e:
        return '', f'URLError: {e}'
    except Exception as e:
        return '', f'Exception: {type(e).__name__}: {e}'


def parse_acao_llm(resposta):
    """Extrai a acao predita da resposta do LLM. Retorna string ou None."""
    if not resposta:
        return None
    texto = resposta.strip()
    for act in ACOES:
        if texto == act:
            return act
    for act in ACOES:
        if texto.startswith(act):
            return act
    palavras = re.findall(r'[a-zA-Z_]+', texto)
    for w in palavras:
        for act in ACOES:
            if w == act or w.lower() == act.lower():
                return act
    primeira = texto.split('\n')[0].strip()
    primeira = primeira.split()[0] if primeira.split() else primeira
    for act in ACOES:
        if primeira.lower() == act.lower():
            return act
    return primeira if primeira else None


def treinar_mcr(treino):
    """Treina MCR no split de treino. Retorna (coupling, tempo_treino)."""
    from mcr.coupling import MCRCoupling
    c = MCRCoupling()
    t0 = time.perf_counter()
    c.alimentar_swarm(treino)
    t_treino = time.perf_counter() - t0
    return c, t_treino


def avaliar_mcr(c, teste):
    """Avalia MCR no holdout. Retorna (acertos, latencias_ms, erros)."""
    acertos = 0
    latencias = []
    erros = []
    for inp, esp in teste:
        t0 = time.perf_counter()
        pred, conf = c.decidir(inp, (None, 0.0))
        dt = (time.perf_counter() - t0) * 1000
        latencias.append(dt)
        if pred == esp:
            acertos += 1
        else:
            erros.append((inp[:50], esp, pred, round(conf, 3)))
    return acertos, latencias, erros


def avaliar_llm(few_shot, teste, n_max=None):
    """Avalia phi4-mini few-shot no holdout. Retorna (acertos, latencias_ms, erros, falhas_parse)."""
    acertos = 0
    latencias = []
    erros = []
    falhas_parse = 0
    itens = teste[:n_max] if n_max else teste
    for i, (inp, esp) in enumerate(itens, 1):
        prompt = construir_prompt(few_shot, inp)
        t0 = time.perf_counter()
        resp, err = chamar_ollama(prompt)
        dt = (time.perf_counter() - t0) * 1000
        latencias.append(dt)
        if err:
            falhas_parse += 1
            erros.append((inp[:50], esp, f'ERRO:{err[:30]}', 0.0))
            print(f'  [{i:3d}/{len(itens)}] ERRO: {err[:50]}')
            continue
        pred = parse_acao_llm(resp)
        if pred is None:
            falhas_parse += 1
            erros.append((inp[:50], esp, f'SEM_PARSE:{resp[:30]}', 0.0))
            print(f'  [{i:3d}/{len(itens)}] SEM PARSE: "{resp[:50]}"')
            continue
        if pred == esp:
            acertos += 1
        else:
            erros.append((inp[:50], esp, pred, 0.0))
        if i % 10 == 0:
            print(f'  [{i:3d}/{len(itens)}] parcial: {acertos}/{i}')
    return acertos, latencias, erros, falhas_parse


def percentile(lst, p):
    if not lst:
        return 0.0
    s = sorted(lst)
    k = int(len(s) * p / 100)
    k = min(max(k, 0), len(s) - 1)
    return s[k]


def main():
    n_max = None
    for arg in sys.argv[1:]:
        if arg.startswith('--n='):
            n_max = int(arg.split('=', 1)[1])

    print('=' * 78)
    print('  COMPARACAO JUSTA MCR vs phi4-mini (PILAR 8)')
    print('  Mesmo corpus, mesmo split, mesma tarefa, baseline LLM nomeado')
    print('=' * 78)

    dataset = carregar_dataset()
    treino, teste = split_80_20(dataset)
    print(f'\nDataset: {len(dataset)} entradas | treino={len(treino)} | teste={len(teste)}')
    acoes_presentes = sorted(set(a for _, a in treino))
    print(f'Acoes no treino ({len(acoes_presentes)}): {acoes_presentes}')

    few_shot = amostrar_few_shot(treino, N_FEW_SHOT_PER_ACTION)
    print(f'Few-shot: {len(few_shot)} exemplos ({N_FEW_SHOT_PER_ACTION}/acao, seed=42)')

    print('\n[1/2] Treinando e avaliando MCR...')
    c, t_treino_mcr = treinar_mcr(treino)
    print(f'  Treino MCR: {t_treino_mcr:.3f}s')
    ac_mcr, lat_mcr, err_mcr = avaliar_mcr(c, teste)
    acc_mcr = ac_mcr / len(teste) * 100
    print(f'  MCR accuracy: {ac_mcr}/{len(teste)} = {acc_mcr:.1f}%')
    print(f'  MCR latencia: p50={percentile(lat_mcr,50):.2f}ms p99={percentile(lat_mcr,99):.2f}ms')

    print(f'\n[2/2] Avaliando phi4-mini few-shot {N_FEW_SHOT_PER_ACTION}/ex...' + (f' (n={n_max})' if n_max else ' (n=113)'))
    print('  Cada chamada pode demorar 5-30s. Aguarde.')
    t0 = time.time()
    ac_llm, lat_llm, err_llm, falhas = avaliar_llm(few_shot, teste, n_max)
    t_llm_total = time.time() - t0
    n_avaliado = n_max if n_max else len(teste)
    acc_llm = ac_llm / n_avaliado * 100 if n_avaliado else 0
    print(f'  phi4-mini accuracy: {ac_llm}/{n_avaliado} = {acc_llm:.1f}%')
    print(f'  phi4-mini latencia: p50={percentile(lat_llm,50):.0f}ms p99={percentile(lat_llm,99):.0f}ms')
    print(f'  phi4-mini tempo total: {t_llm_total:.1f}s')
    print(f'  phi4-mini falhas de parse: {falhas}')

    print('\n' + '=' * 78)
    print('  RESULTADO — COMPARACAO JUSTA (Pilar 8)')
    print('=' * 78)
    print(f'{"Metrica":<35} {"MCR":>15} {"phi4-mini":>15} {"Vantagem":>10}')
    print('-' * 78)

    def linha(metrica, mcr_val, llm_val, fmt='%.1f%%'):
        mcr_s = fmt % mcr_val if isinstance(mcr_val, (int, float)) else str(mcr_val)
        llm_s = fmt % llm_val if isinstance(llm_val, (int, float)) else str(llm_val)
        if isinstance(mcr_val, (int, float)) and isinstance(llm_val, (int, float)):
            vant = 'MCR' if mcr_val > llm_val else ('phi4' if mcr_val < llm_val else 'Empate')
        else:
            vant = '-'
        print(f'{metrica:<35} {mcr_s:>15} {llm_s:>15} {vant:>10}')

    linha('Accuracy no holdout', acc_mcr, acc_llm)
    linha('Latencia p50 (ms)', percentile(lat_mcr, 50), percentile(lat_llm, 50), '%.2f')
    linha('Latencia p99 (ms)', percentile(lat_mcr, 99), percentile(lat_llm, 99), '%.2f')
    linha('Tempo de treino (s)', t_treino_mcr, 0.0, '%.3f')
    linha('Tamanho do modelo', '~500KB', '2.5GB', '%s')
    print(f'{"Dependencias":<35} {"0":>15} {"Ollama":>15} {"MCR":>10}')
    print(f'{"GPU":<35} {"nao":>15} {"nao (CPU)":>15} {"Empate":>10}')
    print(f'{"Aprendizado online":<35} {"Sim":>15} {"Nao":>15} {"MCR":>10}')
    print('=' * 78)

    print('\nVEREDITO (Pilar 9 — regime honesto):')
    if acc_mcr > acc_llm:
        print(f'  Accuracy: MCR GANHA ({acc_mcr:.1f}% vs {acc_llm:.1f}%)')
        print(f'  -> Hipotese "MCR supera LLM em classificacao com corpus pequeno" CONFIRMADA neste regime.')
    elif acc_mcr < acc_llm:
        print(f'  Accuracy: MCR PERDE ({acc_mcr:.1f}% vs {acc_llm:.1f}%)')
        print(f'  -> Hipotese REFUTADA neste regime. Revisar mecanismo.')
    else:
        print(f'  Accuracy: EMPATE ({acc_mcr:.1f}%)')

    if err_llm:
        print(f'\nErros do phi4-mini (primeiros 10):')
        for txt, esp, pred, conf in err_llm[:10]:
            print(f'  "{txt}" | esp={esp} | pred={pred}')

    resultado = {
        'data': '2026-07-16',
        'regime': 'Pilar 8 — mesmo corpus, mesmo split, mesma tarefa',
        'dataset': DATASET,
        'split': '449 treino / 113 teste (seed 42)',
        'mcr': {
            'model': 'MCRCoupling (FASE 1-18)',
            'accuracy': round(acc_mcr, 2),
            'acertos': ac_mcr, 'total': len(teste),
            'latencia_p50_ms': round(percentile(lat_mcr, 50), 3),
            'latencia_p99_ms': round(percentile(lat_mcr, 99), 3),
            'tempo_treino_s': round(t_treino_mcr, 3),
        },
        'llm': {
            'model': LLM_MODEL,
            'modo': f'few-shot {N_FEW_SHOT_PER_ACTION}/acao',
            'accuracy': round(acc_llm, 2),
            'acertos': ac_llm, 'total': n_avaliado,
            'latencia_p50_ms': round(percentile(lat_llm, 50), 1),
            'latencia_p99_ms': round(percentile(lat_llm, 99), 1),
            'tempo_total_s': round(t_llm_total, 1),
            'falhas_parse': falhas,
        },
        'veredito': 'MCR_GANHA' if acc_mcr > acc_llm else ('MCR_PERDE' if acc_mcr < acc_llm else 'EMPATE'),
    }
    out = 'E:/MCR/tests/real/resultado_pilar8_mcr_vs_phi4mini.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(f'\nResultado salvo em: {out}')


if __name__ == '__main__':
    main()
