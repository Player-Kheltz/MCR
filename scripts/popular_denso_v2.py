"""
RETRY — Densificacao CORRETA:
  1. Reverter para dados originais
  2. Ollama parafraseia 800 dialogos reais (mais variacoes = mais densidade sem vies)
  3. SEM templates sinteticos
  4. N-adaptativo ativado
"""
import sys, os, json, re, time, random, urllib.request
from collections import Counter
from pathlib import Path

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

sys.path.insert(0, _BASE)
from mcr.mcr_sqlite import MCRSQLite

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO = "qwen2.5-coder:1.5b"

def chamar_ollama(prompt, max_tokens=100):
    try:
        payload = json.dumps({
            "model": MODELO, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.7, "max_tokens": max_tokens}
        }).encode()
        req = urllib.request.Request(OLLAMA_URL, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read()).get('response', '').strip()
    except Exception:
        return None

def main():
    t0 = time.time()
    print('=' * 60)
    print('  DENSIFICACAO CORRETA — Apenas Ollama, sem sinteticos')
    print('=' * 60)

    # Carregar originais
    with open(os.path.join(_BASE, 'cache', 'npc_knowledge.json'), 'r', encoding='utf-8') as f:
        dados = json.load(f)

    dialogos = dados.get('dialogos', {})

    # Extrair todas as frases reais
    todas_frases = []
    for keyword, respostas in dialogos.items():
        for resp in respostas:
            if isinstance(resp, list) and len(resp) >= 1:
                texto = resp[0] if isinstance(resp[0], str) else ''
                if 20 < len(texto) < 200:
                    todas_frases.append(texto)

    print(f'  Frases originais: {len(todas_frases)}')

    # Amostrar 800 frases variadas
    random.seed(42)
    random.shuffle(todas_frases)
    amostra = todas_frases[:800]

    # Gerar variacoes via Ollama
    print(f'\n  Gerando variacoes para {len(amostra)} frases...')
    variacoes = []
    for i, original in enumerate(amostra):
        prompt = (
            f"Rephrase this NPC dialogue in a different way. Keep the meaning, "
            f"tone, and similar length. Use the same language style.\n\n"
            f"Original: \"{original}\"\n\n"
            f"Rephrased:"
        )
        resp = chamar_ollama(prompt, max_tokens=120)
        if resp:
            resp = resp.strip().strip('"').strip("'")
            if len(resp) > 15 and resp != original:
                # Verifica que nao e muito diferente
                palavras_orig = set(re.findall(r'[a-zA-Z]{4,}', original.lower()))
                palavras_resp = set(re.findall(r'[a-zA-Z]{4,}', resp.lower()))
                overlap = len(palavras_orig & palavras_resp) / max(len(palavras_orig), 1)
                if overlap > 0.2 or len(resp.split()) >= 4:
                    variacoes.append(resp)

        if (i + 1) % 100 == 0:
            print(f'  Progresso: {i+1}/{len(amostra)} -> {len(variacoes)} variacoes')
            time.sleep(0.2)

    print(f'  Total variacoes: {len(variacoes)}')

    # Converter para sequencias
    def para_sequencias(frases):
        seqs = []
        for f in frases:
            palavras = re.findall(r'[a-zA-Z]{3,}', f.lower())
            if len(palavras) >= 3:
                seqs.append(palavras)
        return seqs

    originais_seq = para_sequencias(todas_frases)
    variacoes_seq = para_sequencias(variacoes)

    print(f'  Sequencias originais: {len(originais_seq)}')
    print(f'  Sequencias variacoes: {len(variacoes_seq)}')

    # Retreinar: originais 2x + variacoes 2x (reforcar padroes comuns)
    todas = originais_seq + originais_seq + variacoes_seq + variacoes_seq
    random.shuffle(todas)

    db_path = os.path.join(_BASE, 'cache', 'mcr_conversa.db')
    if os.path.exists(db_path):
        os.remove(db_path)

    mcr = MCRSQLite(db_path, n_max=5, identidade='conversa')

    print(f'\n  Treinando {len(todas)} sequencias...')
    for i in range(0, len(todas), 2000):
        batch = todas[i:i+2000]
        mcr.aprender_batch(batch)
        mcr.conn.commit()

    estados = mcr.conn.execute('SELECT COUNT(DISTINCT key) FROM trans').fetchone()[0]
    trans = mcr.conn.execute('SELECT COUNT(*) FROM trans').fetchone()[0]
    h = mcr.entropia_media()
    max_count = mcr.conn.execute(
        "SELECT MAX(count) FROM trans"
    ).fetchone()[0] or 0
    multiplos = mcr.conn.execute(
        "SELECT COUNT(*) FROM (SELECT key, COUNT(*) as c FROM trans GROUP BY key HAVING c >= 2)"
    ).fetchone()[0]

    mcr.conn.close()

    print(f'\n  RESULTADO FINAL:')
    print(f'    Estados: {estados}')
    print(f'    Transicoes: {trans}')
    print(f'    Entropia: {h:.4f}')
    print(f'    Max count: {max_count}')
    print(f'    Estados 2+ opcoes: {multiplos}')
    print(f'    Tempo total: {time.time()-t0:.1f}s')

    # Teste rapido de geracao
    print(f'\n  TESTE DE GERACAO:')
    mcr = MCRSQLite(db_path, n_max=5, identidade='conversa')
    for s in ['hello', 'dragon', 'sword', 'buy', 'custa', 'orcs']:
        c = mcr.gerar(s, passos=8)
        print(f'    "{s}" -> {" ".join(c)[:80]}')
    mcr.conn.close()

if __name__ == '__main__':
    main()
