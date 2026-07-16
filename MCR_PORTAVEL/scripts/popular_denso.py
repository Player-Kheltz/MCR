"""
POPULAR — Pipeline de Densificação de Dados para MCR

Etapas:
  1. Extrair top keywords dos 13.751 diálogos
  2. Gerar dados densos via Ollama (parafraseando)
  3. Gerar dados sintéticos via templates
  4. Corrigir KG path + carregar dados orfãos
  5. Popular SDM com cerebro.json
  6. Corrigir MCRSQLite.gerar() para N-adaptativo
  7. Retreinar com dados densos
"""
import sys, os, json, re, time, random, urllib.request, sqlite3
from collections import Counter
from pathlib import Path

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

sys.path.insert(0, _BASE)
from mcr.mcr_sqlite import MCRSQLite

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO_RAPIDO = "qwen2.5-coder:1.5b"
MODELO_BOM = "mistral:7b"

# ═══════════════════════════════════════════════════════════
# ETAPA 1: Extrair Top Keywords
# ═══════════════════════════════════════════════════════════

def extrair_top_keywords(arquivo_json, top_n=100):
    print(f'\n[ETAPA 1] Extraindo top {top_n} keywords...')
    with open(arquivo_json, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    dialogos = dados.get('dialogos', {})
    contador = Counter()

    for keyword, respostas in dialogos.items():
        for resp in respostas:
            if isinstance(resp, list) and len(resp) >= 1:
                texto = resp[0] if isinstance(resp[0], str) else ''
                palavras = re.findall(r'\b[a-zA-Z]{3,}\b', texto.lower())
                contador.update(palavras)

    top = contador.most_common(top_n)
    print(f'  Top 10: {[(w, c) for w, c in top[:10]]}')
    return [w for w, _ in top]


# ═══════════════════════════════════════════════════════════
# ETAPA 2: Ollama — Gerar Dados Densos
# ═══════════════════════════════════════════════════════════

def chamar_ollama(prompt, modelo=MODELO_RAPIDO, max_tokens=100):
    try:
        payload = json.dumps({
            "model": modelo, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.8, "max_tokens": max_tokens}
        }).encode()
        req = urllib.request.Request(OLLAMA_URL, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read())
        return resp.get('response', '').strip()
    except Exception as e:
        return None

def gerar_variacoes_ollama(dialogos_originais, n_variacoes=2, max_dialogos=500):
    print(f'\n[ETAPA 2] Gerando variacoes via Ollama ({MODELO_RAPIDO})...')
    print(f'  Amostra: {min(max_dialogos, len(dialogos_originais))} dialogos x {n_variacoes} variacoes')

    # Pega amostra representativa
    amostras = []
    for keyword, respostas in dialogos_originais.items():
        for resp in respostas:
            if isinstance(resp, list) and len(resp) >= 1:
                texto = resp[0] if isinstance(resp[0], str) else ''
                if len(texto) > 20:
                    amostras.append(texto)
            if len(amostras) >= max_dialogos:
                break
        if len(amostras) >= max_dialogos:
            break

    random.shuffle(amostras)
    amostras = amostras[:max_dialogos]

    variacoes = []
    for i, original in enumerate(amostras):
        prompt = (
            f"Rewrite this NPC dialogue in 2 different ways. "
            f"Keep the same meaning and tone. Use similar length.\n\n"
            f"Original: \"{original}\"\n\n"
            f"Variation 1:"
        )
        resposta = chamar_ollama(prompt, modelo=MODELO_RAPIDO, max_tokens=150)
        if resposta:
            # Extrai frases da resposta
            frases = re.split(r'(?:Variation \d:|[\n\r]+)', resposta)
            for frase in frases:
                frase = frase.strip().strip('"').strip("'")
                if len(frase) > 15 and frase != original:
                    variacoes.append(frase)

        if (i + 1) % 50 == 0:
            print(f'  Progresso: {i+1}/{len(amostras)} -> {len(variacoes)} variacoes geradas')
            time.sleep(0.1)

    print(f'  Total variacoes geradas: {len(variacoes)}')
    return variacoes


# ═══════════════════════════════════════════════════════════
# ETAPA 3: Gerar Dados Sintéticos via Templates
# ═══════════════════════════════════════════════════════════

def gerar_sinteticos(keywords, n=1000):
    print(f'\n[ETAPA 3] Gerando {n} dialogos sinteticos...')

    # Templates comuns de NPC
    templates_compra = [
        "How much does the {item} cost?",
        "I want to buy a {item}.",
        "Can I see your {item}?",
        "Do you sell {item}s here?",
        "What's the price of this {item}?",
        "I need a {item} for my journey.",
    ]
    templates_venda = [
        "I have a {item} to sell.",
        "Would you buy this {item}?",
        "How much will you pay for my {item}?",
        "I found this {item} in the dungeon.",
        "Can I trade this {item} for something?",
    ]
    templates_quest = [
        "Do you have any quests for me?",
        "I completed the {item} mission.",
        "What is the reward for the {item} quest?",
        "Can you tell me about the {item} quest?",
        "I'm looking for a mission involving {item}s.",
    ]
    templates_saudacao = [
        "Hello there, {item}!",
        "Greetings, {item}.",
        "Well met, {item}!",
        "Hi {item}, how are you today?",
        "Good day to you, {item}.",
    ]
    templates_info = [
        "Tell me about {item}s.",
        "What do you know about {item}s?",
        "I've heard stories about {item}s.",
        "Where can I find {item}s?",
        "Are {item}s dangerous?",
    ]

    all_templates = (templates_compra + templates_venda + templates_quest +
                     templates_saudacao + templates_info)

    itens = ['sword', 'shield', 'armor', 'potion', 'ring', 'helmet', 'boots',
             'dragon', 'orc', 'troll', 'spell', 'rune', 'gold', 'crystal',
             'axe', 'bow', 'arrow', 'staff', 'wand', 'amulet']

    sinteticos = []
    for _ in range(n):
        template = random.choice(all_templates)
        item = random.choice(itens)
        frase = template.replace('{item}', item)
        sinteticos.append(frase)

    print(f'  Gerados: {len(sinteticos)}')
    return sinteticos


# ═══════════════════════════════════════════════════════════
# ETAPA 4: Corrigir KG e Carregar Dados Órfãos
# ═══════════════════════════════════════════════════════════

def carregar_kg_orfao():
    print('\n[ETAPA 4] Carregando KG orfao...')
    kg_orfao = Path(r'E:\Coisas\sandbox\.mcr_devia\kg')

    if not kg_orfao.exists():
        print(f'  KG orfao nao encontrado em {kg_orfao}')
        return [], 0

    arquivos = list(kg_orfao.glob('*.json'))
    print(f'  {len(arquivos)} arquivos encontrados')

    todas_licoes = []
    for arq in arquivos:
        try:
            with open(arq, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                todas_licoes.extend(data)
            elif isinstance(data, dict):
                licoes = data.get('licoes', data.get('data', []))
                if isinstance(licoes, list):
                    todas_licoes.extend(licoes)
        except Exception as e:
            pass

    print(f'  Total licoes carregadas: {len(todas_licoes)}')
    return todas_licoes, len(todas_licoes)


# ═══════════════════════════════════════════════════════════
# ETAPA 5: Popular SDM
# ═══════════════════════════════════════════════════════════

def popular_sdm(cerebro_path, kg_licoes):
    print('\n[ETAPA 5] Populando SDM...')

    class MiniSDMPersistente:
        def __init__(self, path, dim=200, n_enderecos=2000):
            self.path = path
            self.dim = dim
            self.n_enderecos = n_enderecos
            self.enderecos = []
            self.conteudo = []
            self._hash_cache = {}
            self._init_enderecos()

        def _init_enderecos(self):
            rng = random.Random(42)
            for _ in range(self.n_enderecos):
                self.enderecos.append([1 if rng.random() < 0.5 else -1 for _ in range(self.dim)])
                self.conteudo.append([0] * self.dim)

        def _hash_vec(self, texto):
            if texto in self._hash_cache:
                return self._hash_cache[texto]
            rng = random.Random(hash(texto) & 0xFFFFFFFF)
            vec = [1 if rng.random() < 0.5 else -1 for _ in range(self.dim)]
            self._hash_cache[texto] = vec
            return vec

        def store(self, texto):
            v = self._hash_vec(texto)
            for i, end in enumerate(self.enderecos):
                dot = sum(v[j] * end[j] for j in range(self.dim))
                if dot > self.dim * 0.25:
                    for j in range(self.dim):
                        self.conteudo[i][j] += v[j]

        def retrieve(self, texto):
            if not self.enderecos:
                return None, 0.0, 0
            v = self._hash_vec(texto)
            soma = [0] * self.dim
            ativos = 0
            for i, end in enumerate(self.enderecos):
                dot = sum(v[j] * end[j] for j in range(self.dim))
                if dot > self.dim * 0.25:
                    for j in range(self.dim):
                        soma[j] += self.conteudo[i][j]
                    ativos += 1
            if ativos == 0:
                return None, 0.0, 0
            recon = [1 if s > 0 else -1 for s in soma]
            concordancia = sum(1 for j in range(self.dim) if abs(soma[j]) > 0)
            fidelidade = concordancia / self.dim
            return recon, fidelidade, ativos

        def salvar(self):
            data = {
                'dim': self.dim, 'n_enderecos': self.n_enderecos,
                'enderecos': self.enderecos, 'conteudo': self.conteudo,
            }
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(data, f)

    sdm_path = os.path.join(_BASE, 'cache', 'mcr_sdm.json')
    sdm = MiniSDMPersistente(sdm_path, dim=200, n_enderecos=2000)

    # Fonte 1: cerebro.json
    if Path(cerebro_path).exists():
        with open(cerebro_path, 'r', encoding='utf-8') as f:
            cerebro = json.load(f)
        topicos = cerebro.get('topicos', {})
        for nome, dados in topicos.items():
            texto = str(nome)
            if isinstance(dados, dict):
                texto += ' ' + str(dados.get('texto', ''))
                palavras = dados.get('palavras', [])
                texto += ' ' + ' '.join(palavras[:20] if isinstance(palavras, list) else [])
            sdm.store(texto[:200])
            for palavra in re.findall(r'[a-zA-Z]{4,}', texto.lower())[:10]:
                sdm.store(palavra)
        print(f'  SDM: {len(topicos)} topicos do cerebro.json indexados')

    # Fonte 2: KG licoes
    for licao in kg_licoes[:2000]:
        texto = str(licao.get('erro', '')) + ' ' + str(licao.get('solucao', ''))
        sdm.store(texto[:200])
    print(f'  SDM: {min(len(kg_licoes), 2000)} licoes do KG indexadas')

    sdm.salvar()
    print(f'  SDM salvo em {sdm_path}')

    return sdm


# ═══════════════════════════════════════════════════════════
# ETAPA 6: Retreinar MCRSQLite com Dados Densos
# ═══════════════════════════════════════════════════════════

def retreinar_mcr(dados_originais, variacoes_ollama, sinteticos, db_path):
    print(f'\n[ETAPA 6] Retreinando MCRSQLite com dados densos...')

    if os.path.exists(db_path):
        os.remove(db_path)

    mcr = MCRSQLite(db_path, n_max=5, identidade='conversa')

    def para_sequencias(textos):
        seqs = []
        for t in textos:
            palavras = re.findall(r'[a-zA-Z]{3,}', t.lower())
            if len(palavras) >= 3:
                seqs.append(palavras)
        return seqs

    # Originais
    originais_seq = []
    dialogos = dados_originais.get('dialogos', {})
    for keyword, respostas in dialogos.items():
        for resp in respostas:
            if isinstance(resp, list) and len(resp) >= 1:
                texto = resp[0] if isinstance(resp[0], str) else ''
                palavras = re.findall(r'[a-zA-Z]{3,}', texto.lower())
                if len(palavras) >= 3:
                    originais_seq.append(palavras)

    print(f'  Sequencias originais: {len(originais_seq)}')

    # Variacoes Ollama
    ollama_seq = para_sequencias(variacoes_ollama)
    print(f'  Variacoes Ollama: {len(ollama_seq)}')

    # Sinteticos
    sinteticos_seq = para_sequencias(sinteticos)
    print(f'  Sinteticos: {len(sinteticos_seq)}')

    # Treinar em batches — ORIGINAIS PRIMEIRO (peso maior)
    todas = originais_seq * 2 + ollama_seq * 2 + sinteticos_seq * 3
    random.shuffle(todas)

    for i in range(0, len(todas), 2000):
        batch = todas[i:i+2000]
        mcr.aprender_batch(batch)
        mcr.conn.commit()

    estados = mcr.conn.execute('SELECT COUNT(DISTINCT key) FROM trans').fetchone()[0]
    trans = mcr.conn.execute('SELECT COUNT(*) FROM trans').fetchone()[0]
    h = mcr.entropia_media()

    print(f'  Estados: {estados}, Transicoes: {trans}, Entropia: {h:.4f}')

    # Medir densidade
    rows = mcr.conn.execute(
        "SELECT COUNT(*) FROM (SELECT key, COUNT(*) as c FROM trans GROUP BY key HAVING c >= 2)"
    ).fetchone()[0]
    max_count = mcr.conn.execute(
        "SELECT MAX(count) FROM (SELECT key,next,count FROM trans ORDER BY count DESC LIMIT 1)"
    ).fetchone()[0] or 0

    print(f'  Estados com 2+ opcoes: {rows}')
    print(f'  Contagem maxima: {max_count}')

    mcr.conn.close()
    return {'estados': estados, 'transicoes': trans, 'entropia': h,
            'estados_multiplos': rows, 'max_count': max_count}


# ═══════════════════════════════════════════════════════════
# ETAPA 7: Corrigir MCRSQLite.gerar() para N-adaptativo
# ═══════════════════════════════════════════════════════════

def corrigir_gerar():
    print('\n[ETAPA 7] Corrigindo MCRSQLite.gerar() para N-adaptativo...')

    mcr_sqlite_path = os.path.join(_BASE, 'mcr', 'mcr_sqlite.py')
    with open(mcr_sqlite_path, 'r', encoding='utf-8') as f:
        codigo = f.read()

    # Verifica se ja foi corrigido
    if 'self.gerar_n_adaptativo' in codigo:
        print('  gerar() ja corrigido.')
        return

    old_gerar = '''    def gerar(self, semente: str, passos: int = 10) -> List[str]:
        """Gera sequencia (compativel com MCR.engine)."""
        seq = [semente]
        atual = semente
        for _ in range(passos):
            prox, conf = self.predizer(atual)
            if prox is None or conf < 0.01:
                break
            seq.append(prox)
            atual = prox
        return seq'''

    new_gerar = '''    def gerar(self, semente: str, passos: int = 10) -> List[str]:
        """Gera sequencia usando N-adaptativo.
        
        Acumula contexto a cada passo: em vez de predizer(token_atual),
        predizer(token_atual) com fallback para contextos maiores.
        """
        seq = [semente]
        atual = semente
        
        for _ in range(passos):
            # Tenta predizer com contexto acumulado (N>1)
            prox, conf = None, 0.0
            for depth in range(min(self.n_max, len(seq)), 0, -1):
                ctx = '|'.join(seq[-depth:])
                p, c = self.predizer(ctx)
                if p is not None and c > conf:
                    prox, conf = p, c
                if conf > 0.05:
                    break
            
            if prox is None or conf < 0.01:
                # Fallback: predizer so o ultimo token
                prox, conf = self.predizer(atual)
            
            if prox is None or conf < 0.01:
                break
            seq.append(prox)
            atual = prox
        return seq'''

    if old_gerar in codigo:
        codigo = codigo.replace(old_gerar, new_gerar)
        with open(mcr_sqlite_path, 'w', encoding='utf-8') as f:
            f.write(codigo)
        print('  gerar() CORRIGIDO para N-adaptativo.')
    else:
        print('  AVISO: nao encontrei gerar() para corrigir. Verifique manualmente.')


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    t0 = time.time()

    # ETAPA 1: Keywords
    keywords = extrair_top_keywords(os.path.join(_BASE, 'cache', 'npc_knowledge.json'), top_n=100)

    # ETAPA 2: Variacoes Ollama
    with open(os.path.join(_BASE, 'cache', 'npc_knowledge.json'), 'r', encoding='utf-8') as f:
        dados_originais = json.load(f)
    variacoes = gerar_variacoes_ollama(dados_originais.get('dialogos', {}),
                                        n_variacoes=2, max_dialogos=300)

    # ETAPA 3: Sinteticos
    sinteticos = gerar_sinteticos(keywords, n=2000)

    # ETAPA 4: KG orfao
    kg_licoes, n_licoes = carregar_kg_orfao()

    # ETAPA 5: SDM
    sdm = popular_sdm(os.path.join(_BASE, 'cache', 'cerebro.json'), kg_licoes)

    # ETAPA 6: Retreinar
    stats = retreinar_mcr(dados_originais, variacoes, sinteticos,
                          os.path.join(_BASE, 'cache', 'mcr_conversa.db'))

    # ETAPA 7: Corrigir gerar()
    corrigir_gerar()

    print(f'\n{"=" * 60}')
    print(f'  DENSIFICACAO CONCLUIDA em {time.time()-t0:.1f}s')
    print(f'  Variacoes Ollama: {len(variacoes)}')
    print(f'  Sinteticos: {len(sinteticos)}')
    print(f'  KG licoes: {n_licoes}')
    print(f'  MCR Estados: {stats["estados"]}')
    print(f'  MCR Max count: {stats["max_count"]}')
    print(f'  MCR Estados multiplos: {stats["estados_multiplos"]}')
    print(f'{"=" * 60}')


if __name__ == '__main__':
    main()
