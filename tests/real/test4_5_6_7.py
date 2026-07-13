"""
TESTE 4 — Codigo: quantos templates geram codigo sintaticamente valido?
+ TESTE 6 — Entropia e densidade
+ TESTE 7 — KG/SDM estado real
Tudo em um arquivo, cada teste imprime seus proprios resultados.
"""
import sys, os, ast, sqlite3, json, math, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

def teste4_codigo():
    print('=' * 60)
    print('TESTE 4 — VALIDADE DE CODIGO GERADO')
    print('=' * 60)

    from mcr.gerador_codigo import GeradorCodigo
    g = GeradorCodigo()

    testes = {
        'Lua NPC': lambda: g.gerar_lua(tipo='npc', semente='local'),
        'Lua Monster': lambda: g.gerar_lua(tipo='monster', semente='local'),
        'Lua Quest': lambda: g.gerar_lua(tipo='quest', semente='local'),
        'Python func': lambda: g.gerar_python(tipo='function', semente='def'),
        'Python class': lambda: g.gerar_python(tipo='class', semente='class'),
        'SQL SELECT': lambda: g.gerar_sql(tipo='select', semente='SELECT'),
        'SQL CREATE': lambda: g.gerar_sql(tipo='create', semente='CREATE'),
    }

    validos = 0
    total = 0
    for nome, fn in testes.items():
        try:
            r = fn()
            total += 1
            if r['valido']:
                validos += 1
                print(f'  [OK]  {nome:15s} valido')
            else:
                err = r.get('erro', '')[:60]
                print(f'  [FAIL] {nome:15s} {err}')
        except Exception as e:
            print(f'  [ERR] {nome:15s} {str(e)[:60]}')

    g.close()
    print(f'\n  Total: {validos}/{total} validos = {validos/total*100:.0f}%')


def teste5_conversa():
    print('\n' + '=' * 60)
    print('TESTE 5 — CONVERSA MULTI-TURNO (saida REAL)')
    print('=' * 60)

    from mcr.npc_criativo import NPCCriativo
    npc = NPCCriativo('Ferronius', 'ferreiro')

    conversa = [
        'Ola!',
        'Quanto custa uma espada?',
        'E uma armadura de dragao?',
        'Obrigado, vou levar a espada!',
        'Ate mais!',
    ]

    for msg in conversa:
        resp = npc.responder(msg)
        palavras = re.findall(r'[a-zA-ZÀ-ÿ]{3,}', resp)
        # Verifica se a resposta tem estrutura minima
        tem_sujeito = any(p in resp.lower() for p in ['eu', 'voc', 'n', 'i', 'you', 'we', 'it'])
        tem_verbo = any(p in palavras[:5] for p in ['est', 'tem', 'pode', 'custa', 'want', 'need',
                                                       'have', 'is', 'are', 'was', 'can', 'will'])
        print(f'  J: "{msg}"')
        print(f'  N: "{resp[:100]}"')
        print(f'    palavras={len(palavras)}, sujeito={tem_sujeito}, verbo={tem_verbo}')

    npc.close()


def teste6_entropia():
    print('\n' + '=' * 60)
    print('TESTE 6 — ENTROPIA E DENSIDADE')
    print('=' * 60)

    conn = sqlite3.connect(os.path.join(_BASE, 'cache', 'mcr_conversa.db'))

    # Entropia por palavra
    palavras = ['you', 'want', 'custa', 'moedas', 'voc', 'est', 'pode',
                'para', 'com', 'que', 'hello', 'dragon']
    print('\n  ENTROPIA POR PALAVRA:')
    for p in palavras:
        rows = conn.execute(
            "SELECT count FROM trans WHERE key=?",
            (f'conversa|{p}',)).fetchall()
        if rows:
            total = sum(r[0] for r in rows)
            h = 0.0
            for r in rows:
                prob = r[0] / total
                if prob > 0:
                    h -= prob * math.log2(prob)
            h_max = math.log2(max(len(rows), 2))
            h_norm = h / h_max if h_max > 0 else 0
            # Quanto MENOR entropia = MAIS previsivel
            qualidade = 'ALTA' if h_norm < 0.3 else 'MEDIA' if h_norm < 0.6 else 'BAIXA'
            print(f'    {p:12s} H={h:.3f} H_norm={h_norm:.3f} ({qualidade})   {len(rows)} alternativas, {total} total')

    # Entropia media global
    rows = conn.execute("""
        SELECT key, COUNT(*) as cnt
        FROM trans GROUP BY key
    """).fetchall()
    entropias = []
    for key, cnt in rows:
        if cnt > 1:
            rows2 = conn.execute("SELECT count FROM trans WHERE key=?", (key,)).fetchall()
            total = sum(r[0] for r in rows2)
            h = -sum((r[0]/total) * math.log2(r[0]/total) for r in rows2 if r[0] > 0)
            entropias.append(h)

    h_media = sum(entropias) / len(entropias) if entropias else 0
    print(f'\n  Entropia media (estados com 2+ opcoes): {h_media:.4f}')
    print(f'  Estados analisados: {len(entropias)}')

    conn.close()


def teste7_kg_sdm():
    print('\n' + '=' * 60)
    print('TESTE 7 — ESTADO REAL DO KG E SDM')
    print('=' * 60)

    # KG
    print('\n  KNOWLEDGE GRAPH:')
    kg_dir = os.path.join(_BASE, 'devia', 'knowledge')
    patterns = list(__import__('pathlib').Path(kg_dir).glob('patterns_*.json'))
    print(f'    Arquivos patterns: {len(patterns)}')
    if patterns:
        with open(patterns[0], 'r', encoding='utf-8') as f:
            data = json.load(f)
        padroes = data.get('padroes', [])
        anti = data.get('anti_patterns', [])
        print(f'    Padroes: {len(padroes)}')
        print(f'    Anti-padroes: {len(anti)}')

    # KG orfao
    kg_orfao = r'E:\Coisas\sandbox\.mcr_devia\kg'
    kg_path = __import__('pathlib').Path(kg_orfao)
    if kg_path.exists():
        arquivos = list(kg_path.glob('*.json'))
        print(f'    KG orfao em E:\\Coisas: {len(arquivos)} arquivos')
        tamanho = sum(f.stat().st_size for f in arquivos) / 1024
        print(f'    Tamanho total: {tamanho:.0f} KB')
        # Testa formato
        with open(arquivos[0], 'r', encoding='utf-8') as f:
            sample = json.load(f)
        print(f'    Formato: {"lista" if isinstance(sample, list) else "dict"}')
        if isinstance(sample, list) and len(sample) > 0:
            print(f'    Campos: {list(sample[0].keys())[:6]}')
    else:
        print(f'    KG orfao: NAO ENCONTRADO em {kg_orfao}')

    # SDM
    print('\n  SDM (Sparse Distributed Memory):')
    sdm_files = list(__import__('pathlib').Path(os.path.join(_BASE, 'cache')).glob('*.sdm'))
    print(f'    Arquivos SDM em cache: {len(sdm_files)}')
    sdm_files2 = list(__import__('pathlib').Path(_BASE).glob('**/*.sdm'))
    print(f'    Arquivos SDM no projeto: {len(sdm_files2)}')

    # Cerebro
    cerebro = os.path.join(_BASE, 'cache', 'cerebro.json')
    if __import__('pathlib').Path(cerebro).exists():
        with open(cerebro, 'r', encoding='utf-8') as f:
            c = json.load(f)
        topicos = c.get('topicos', {})
        print(f'\n  CEREBRO.JSON:')
        print(f'    Topicos: {len(topicos)}')
        print(f'    Palavras (palavra_trans): {len(c.get("palavra_trans", {}))}')
    else:
        print('\n  CEREBRO.JSON: NAO ENCONTRADO')


if __name__ == '__main__':
    teste4_codigo()
    teste5_conversa()
    teste6_entropia()
    teste7_kg_sdm()
