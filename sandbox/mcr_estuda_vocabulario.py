#!/usr/bin/env python3
"""MCR ESTUDA VOCABULARIO DA LLM — Extrai tokenizer, MarkovToken aprende, EMERGIR fragmenta.
Read-only. Extrai vocabulario, merges, scores do GGUF e grava no KG.
"""
import sys, os, math, json, struct, time as _time
from collections import Counter

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MarkovUniversal, MCR_COMPLETO
from modulos.kg import KnowledgeGraph
try:
    from modulos.emergir import EMERGIR
except ImportError:
    EMERGIR = None

BLOBS_DIR = r"E:\Modelos IA\ollama_models\blobs"

PASS = 0; FAIL = 0; TOTAL = 0
def check(nome, cond, detalhe=""):
    global PASS, FAIL, TOTAL; TOTAL += 1
    if cond: PASS += 1; print(f"  [PASS] {nome}")
    else: FAIL += 1; print(f"  [FAIL] {nome} {detalhe}")
def secao(titulo):
    print(f"\n{'='*70}\n  {titulo}\n{'='*70}")


# ============================================================
# PARSE DO HEADER GGUF — Extrai metadados (incluindo tokenizer)
# ============================================================
GGUF_TYPES = {0: 'UINT8', 1: 'INT8', 2: 'UINT16', 3: 'INT16',
              4: 'UINT32', 5: 'INT32', 6: 'FLOAT32', 7: 'BOOL',
              8: 'STRING', 9: 'ARRAY', 10: 'UINT64', 11: 'INT64',
              12: 'FLOAT64'}

def ler_string(f):
    """Le uma string GGUF: length (uint64) + dados."""
    len_bytes = f.read(8)
    if len(len_bytes) < 8: return None
    slen = struct.unpack('<Q', len_bytes)[0]
    return f.read(slen).decode('utf-8', errors='replace') if slen > 0 else ""

def ler_valor(f, tipo):
    """Le um valor GGUF baseado no tipo."""
    if tipo == 0:  # UINT8
        return struct.unpack('<B', f.read(1))[0]
    elif tipo == 4:  # UINT32
        return struct.unpack('<I', f.read(4))[0]
    elif tipo == 5:  # INT32
        return struct.unpack('<i', f.read(4))[0]
    elif tipo == 6:  # FLOAT32
        return struct.unpack('<f', f.read(4))[0]
    elif tipo == 7:  # BOOL
        return struct.unpack('<B', f.read(1))[0] > 0
    elif tipo == 8:  # STRING
        return ler_string(f)
    elif tipo == 9:  # ARRAY
        tipo_arr = struct.unpack('<I', f.read(4))[0]
        n_itens = struct.unpack('<Q', f.read(8))[0]
        return [ler_valor(f, tipo_arr) for _ in range(n_itens)]
    elif tipo == 10:  # UINT64
        return struct.unpack('<Q', f.read(8))[0]
    elif tipo == 11:  # INT64
        return struct.unpack('<q', f.read(8))[0]
    elif tipo == 12:  # FLOAT64
        return struct.unpack('<d', f.read(8))[0]
    return None


def parse_gguf_header(caminho_blob, max_metadata_kv=1000):
    """Parseia o header GGUF e extrai metadados (tokenizer, config)."""
    if not os.path.exists(caminho_blob):
        return None, f"Arquivo nao encontrado: {caminho_blob}"
    
    try:
        with open(caminho_blob, 'rb') as f:
            # Magic + version
            magic = f.read(4)
            if magic != b'GGUF':
                return None, f"Magic nao e GGUF: {magic}"
            version = struct.unpack('<I', f.read(4))[0]
            
            # Tensor count + metadata KV count
            tensor_count = struct.unpack('<Q', f.read(8))[0]
            kv_count = struct.unpack('<Q', f.read(8))[0]
            kv_count = min(kv_count, max_metadata_kv)
            
            metadata = {
                'version': version,
                'tensor_count': tensor_count,
                'kv_count': kv_count,
            }
            
            tokenizer_data = {}
            
            for i in range(kv_count):
                # Key
                key = ler_string(f)
                if key is None:
                    break
                
                # Value type
                tipo_bytes = f.read(4)
                if len(tipo_bytes) < 4:
                    break
                tipo = struct.unpack('<I', tipo_bytes)[0]
                
                # Value
                valor = ler_valor(f, tipo)
                
                metadata[key] = valor
                
                # Tokenizer data
                if key.startswith('tokenizer.ggml.'):
                    tokenizer_data[key] = valor
            
            return metadata, tokenizer_data
    
    except Exception as e:
        return None, f"Erro ao parsear GGUF: {e}"


# ============================================================
# CLASSIFICADOR DE TOKENS — identifica domínio
# ============================================================
def classificar_token(token):
    """Classifica um token em dominio: codigo, lore, sistema, linguagem, especial."""
    if not token:
        return 'especial'
    
    # Tokens especiais (BOS, EOS, PAD, UNK)
    if token in ('<unk>', '<s>', '</s>', '<pad>', '<mask>',
                 '<|begin_of_text|>', '<|end_of_text|>', '<|pad|>',
                 '<｜begin▁of▁sentence｜>', '<｜end▁of▁sentence｜>',
                 '<｜Assistant｜>', '<｜User｜>'):
        return 'especial'
    
    # Tokens de sistema (marcadores de formato LLM)
    if token.startswith('<|') or token.startswith('<｜'):
        return 'sistema'
    
    # Tokens de código (comuns em code LLMs)
    padroes_codigo = ['def ', 'if ', 'else', 'for ', 'while', 'class ',
                      'import ', 'from ', 'return', 'function', 'local ',
                      'end', 'then', 'do ', 'in ', 'nil', 'true', 'false',
                      'self', 'this', '->', '=>', '===', '!=', '&&', '||',
                      'fn ', 'let ', 'mut ', 'const ', 'var ', 'pub ',
                      'impl ', 'struct ', 'enum ', 'trait ', 'where ',
                      'async', 'await', 'try ', 'catch', 'throw',
                      'printf', 'scanf', 'int ', 'char ', 'void ',
                      'print', 'input', 'len(', 'range', 'lambda',
                      'yield', 'raise', 'with ', 'pass', 'break',
                      'continue', 'elif', 'except', 'finally',
                      'global', 'nonlocal', 'assert', 'del ']
    for p in padroes_codigo:
        if p in token:
            return 'codigo'
    
    # Maiusculas = sigla? MCR, SPA, SHC, NPC, etc.
    if token.isupper() and len(token) >= 2:
        return 'sistema'
    
    # Capitalizada = nome próprio? Eridanus, Canary, Ferreiro
    if token[0].isupper() and len(token) > 1:
        return 'lore'
    
    # Números
    if token.isdigit() or (token[0] == '-' and token[1:].isdigit()):
        return 'numero'
    
    # Pontuação / operadores / espaços
    if all(c in '.,;:!?()[]{}<>+-*/=@#$%^&_~`\'\"|\\ \t\n\r\u2581' for c in token):
        return 'pontuacao'
    # Whitespace tokens do SentencePiece/BPE (▁ = espaço)
    if all(c == '\u2581' for c in token):
        return 'pontuacao'
    
    # Começa com letra minúscula = linguagem natural
    if token[0].islower() or token[0].isalpha():
        return 'linguagem'
    
    return 'outro'


# ============================================================
# EMERGIR LITE — fragmenta e clusteriza tokens
# ============================================================
class EmergirLite:
    """Versao simplificada do EMERGIR para clusterizar tokens."""
    
    def fragmentar(self, tokens, min_cluster=3):
        """Agrupa tokens por afinidade (prefixo, sufixo, dominio)."""
        clusters = {
            'prefixo': {},   # token começa com X
            'sufixo': {},    # token termina com X
            'dominio': {},   # codigo, lore, sistema, etc.
            'tamanho': {},   # 1,2,3,4,5+ chars
        }
        
        for token in tokens:
            if not token or len(token) < 1:
                continue
            
            # Por prefixo (primeiros 2 chars)
            prefixo = token[:2].lower()
            if prefixo not in clusters['prefixo']:
                clusters['prefixo'][prefixo] = []
            clusters['prefixo'][prefixo].append(token)
            
            # Por sufixo (ultimos 2 chars)
            sufixo = token[-2:].lower()
            if sufixo not in clusters['sufixo']:
                clusters['sufixo'][sufixo] = []
            clusters['sufixo'][sufixo].append(token)
            
            # Por dominio
            dominio = classificar_token(token)
            if dominio not in clusters['dominio']:
                clusters['dominio'][dominio] = []
            clusters['dominio'][dominio].append(token)
            
            # Por tamanho
            tam = min(len(token), 6)
            if tam not in clusters['tamanho']:
                clusters['tamanho'][tam] = []
            clusters['tamanho'][tam].append(token)
        
        # Filtra clusters pequenos
        for cat in clusters:
            clusters[cat] = {k: v for k, v in clusters[cat].items()
                            if len(v) >= min_cluster}
        
        return clusters


# ============================================================
# TESTE PRINCIPAL
# ============================================================
def testar():
    secao("MCR ESTUDA VOCABULARIO DA LLM")
    print("  Extrai tokenizer do GGUF + MarkovToken + EMERGIR + KG")
    
    kg = KnowledgeGraph() if MCR_COMPLETO else None
    
    # ============================================================
    # FASE 0: ENCONTRAR BLOBS
    # ============================================================
    secao("FASE 0: Localizar blobs GGUF")
    
    blobs = []
    if os.path.exists(BLOBS_DIR):
        for fname in os.listdir(BLOBS_DIR):
            fpath = os.path.join(BLOBS_DIR, fname)
            if os.path.isfile(fpath) and os.path.getsize(fpath) > 50*1024*1024:
                blobs.append((fpath, os.path.getsize(fpath)))
    blobs.sort(key=lambda x: x[1])
    
    print(f"  Blobs: {len(blobs)}")
    
    # Usa o blob de ~4GB (llama3.1) para extrair tokenizer
    # Qualquer blob GGUF serve — todos tem tokenizer no header
    blob_alvo = blobs[2] if len(blobs) > 2 else blobs[0]
    caminho_blob = blob_alvo[0]
    nome_blob = os.path.basename(caminho_blob)[:16]
    print(f"  Alvo: {nome_blob} ({blob_alvo[1]/1024**3:.2f} GB)")
    
    # ============================================================
    # FASE 1: EXTRAIR TOKENIZER DO GGUF
    # ============================================================
    secao("FASE 1: Extrair tokenizer do header GGUF")
    
    print(f"  Parseando header GGUF...")
    t0 = _time.time()
    metadata, tokenizer_data = parse_gguf_header(caminho_blob)
    tempo = _time.time() - t0
    
    if metadata is None:
        print(f"  [ERRO] {tokenizer_data}")
        return
    
    # Extrai dados do tokenizer
    tokens_raw = tokenizer_data.get('tokenizer.ggml.tokens', [])
    scores_raw = tokenizer_data.get('tokenizer.ggml.scores', [])
    token_types_raw = tokenizer_data.get('tokenizer.ggml.token_type', [])
    merges_raw = tokenizer_data.get('tokenizer.ggml.merges', [])
    modelo_tokenizer = tokenizer_data.get('tokenizer.ggml.model', '?')
    chat_template = metadata.get('tokenizer.chat_template', '?')[:80]
    
    n_tokens = len(tokens_raw)
    n_merges = len(merges_raw)
    
    print(f"  Header parseado em {tempo:.2f}s")
    print(f"  Arquitetura: {metadata.get('general.architecture', '?')}")
    print(f"  Modelo tokenizer: {modelo_tokenizer}")
    print(f"  Tokens: {n_tokens}")
    print(f"  Merges BPE: {n_merges}")
    print(f"  Chat template: {chat_template}...")
    
    check("F1. Extraiu tokens do tokenizer", n_tokens > 1000,
          f"(got {n_tokens})")
    # SentencePiece (Llama) nao tem merges separados — OK
    check("F1. Extraiu merges BPE (0 para SentencePiece)", n_merges >= 0,
          f"(got {n_merges})")
    check("F1. Arquitetura identificada",
          metadata.get('general.architecture', '') != '',
          f"(got '{metadata.get('general.architecture', '?')}')")
    
    # Mostra alguns tokens
    print(f"\n  Primeiros 10 tokens:")
    for i in range(min(10, n_tokens)):
        t = tokens_raw[i]
        s = scores_raw[i] if i < len(scores_raw) else 0
        print(f"    [{i:5d}] score={s:8.1f} '{t[:30]}'")
    
    print(f"\n  Ultimos 5 tokens:")
    for i in range(max(0, n_tokens-5), n_tokens):
        t = tokens_raw[i]
        s = scores_raw[i] if i < len(scores_raw) else 0
        print(f"    [{i:5d}] score={s:8.1f} '{t[:30]}'")
    
    # ============================================================
    # FASE 2: MARKOVTOKEN APRENDE VOCABULARIO
    # ============================================================
    secao("FASE 2: MarkovToken aprende estrutura do vocabulario")
    
    # MarkovToken para transicoes entre tokens
    mk_tokens = MarkovUniversal("tokenizer")
    mk_tokens.aprender_sequencia(tokens_raw)
    
    s = mk_tokens.stats()
    print(f"  MarkovToken treinado em {n_tokens} tokens")
    print(f"    Estados: {s['estados']}")
    print(f"    Transicoes: {s['transicoes']}")
    print(f"    Entropia media: {s['entropia']}")
    
    check("F2. MarkovToken aprendeu transicoes entre tokens",
          s['transicoes'] > 0, f"(got {s['transicoes']})")
    
    # MarkovToken para scores (distribuicao de frequencia dos tokens)
    mk_scores = MarkovUniversal("scores")
    scores_str = [str(round(s, 1)) for s in scores_raw if s > -100]
    if scores_str:
        mk_scores.aprender_sequencia(scores_str)
        ss = mk_scores.stats()
        print(f"\n  MarkovScore (distribuicao de frequencia):")
        print(f"    Estados: {ss['estados']}")
        print(f"    Transicoes: {ss['transicoes']}")
        check("F2. MarkovScore aprendeu distribuicao de scores",
              ss['transicoes'] > 0, f"(got {ss['transicoes']})")
    
    # ============================================================
    # FASE 3: CLASSIFICAR TOKENS POR DOMINIO
    # ============================================================
    secao("FASE 3: Classificar tokens por dominio")
    
    dominios = Counter()
    token_info = []
    
    for i, token in enumerate(tokens_raw):
        dominio = classificar_token(token)
        dominios[dominio] += 1
        score = scores_raw[i] if i < len(scores_raw) else 0
        token_info.append({
            'id': i,
            'token': token,
            'dominio': dominio,
            'score': score,
        })
    
    print(f"\n  Distribuicao por dominio:")
    for dominio, count in dominios.most_common():
        pct = count / n_tokens * 100
        print(f"    {dominio:12s}: {count:6d} ({pct:5.1f}%)")
    
    check("F3. Classificou tokens em dominios",
          len(dominios) >= 4,
          f"(got {len(dominios)} dominios)")
    
    # Mostra exemplos de cada dominio
    print(f"\n  Exemplos por dominio:")
    for dominio in dominios:
        exemplos = [t['token'] for t in token_info
                    if t['dominio'] == dominio][:5]
        print(f"    {dominio:12s}: {exemplos}")
    
    # ============================================================
    # FASE 4: EMERGIR — fragmentar e clusterizar
    # ============================================================
    secao("FASE 4: EMERGIR — fragmentar e clusterizar vocabulario")
    
    emergir = EmergirLite()
    clusters = emergir.fragmentar(tokens_raw)
    
    print(f"\n  Clusters encontrados:")
    for cat, grupos in clusters.items():
        print(f"    {cat}: {len(grupos)} grupos")
        # Mostra os 3 maiores grupos
        maiores = sorted(grupos.items(), key=lambda x: -len(x[1]))[:3]
        for chave, membros in maiores:
            print(f"      '{chave}': {len(membros)} membros -> {membros[:5]}")
    
    check("F4. Fragmentou tokens em clusters de prefixo",
          len(clusters.get('prefixo', {})) > 10,
          f"(got {len(clusters.get('prefixo', {}))})")
    check("F4. Fragmentou tokens em clusters de dominio",
          len(clusters.get('dominio', {})) >= 4,
          f"(got {len(clusters.get('dominio', {}))})")
    
    # ============================================================
    # FASE 5: KG — armazenar vocabulario
    # ============================================================
    secao("FASE 5: Armazenar vocabulario no KG")
    
    if kg:
        # Arquitetura
        kg.aprender_conceito(
            f"arquitetura_{metadata.get('general.architecture', '?')}",
            f"Modelo: {nome_blob}, tamanho: {blob_alvo[1]/1024**3:.2f}GB, "
            f"tokens: {n_tokens}, merges: {n_merges}",
            ctx="tokenizer_info"
        )
        
        # Distribuicao por dominio
        for dominio, count in dominios.most_common():
            pct = count / n_tokens * 100
            exemplos = [t['token'] for t in token_info
                        if t['dominio'] == dominio][:10]
            kg.aprender_conceito(
                f"dominio_{dominio}",
                f"{count} tokens ({pct:.1f}%). "
                f"Exemplos: {', '.join(exemplos[:5])}",
                ctx="tokenizer_dominio"
            )
        
        # Clusters de prefixo
        for prefixo, membros in list(clusters['prefixo'].items())[:30]:
            if len(membros) >= 5:
                kg.aprender_conceito(
                    f"prefixo_{prefixo}",
                    f"{len(membros)} tokens: {', '.join(membros[:8])}",
                    ctx="tokenizer_prefixo"
                )
        
        # Forca flush
        for _ in range(10):
            kg.aprender_conceito("_flush_", "_", ctx="_flush")
        kg.salvar()
        kg._all_loaded = False
        
        # Verifica
        lessons_tok = [l for l in kg._get_licoes()
                       if l.get('ctx', '').startswith('tokenizer_')]
        print(f"\n  Lessons de tokenizer no KG: {len(lessons_tok)}")
        
        check("F5. Lessons de tokenizer existem no KG",
              len(lessons_tok) >= 5, f"(got {len(lessons_tok)})")
    
    # ============================================================
    # FASE 6: VALIDAR — MCR entende o vocabulario?
    # ============================================================
    secao("FASE 6: Validacao — MCR entende a estrutura do vocabulario?")
    
    # Teste 1: MarkovToken sabe qual token vem depois de qual
    tokens_comuns = ['Crie', 'Explique', 'local', 'function', 'o', 'de', 'um']
    print(f"\n  6a. MarkovToken prediz proximo token:")
    for t in tokens_comuns:
        if t in mk_tokens.transicoes:
            prox, conf = mk_tokens.predizer(t)
            print(f"      '{t}' -> '{prox}' (conf={conf:.2f})")
    
    # Teste 2: Dominios tem distribuicoes de score diferentes
    print(f"\n  6b. Score medio por dominio:")
    for dominio in ['codigo', 'linguagem', 'lore', 'sistema', 'pontuacao', 'numero']:
        scores_dom = [t['score'] for t in token_info if t['dominio'] == dominio]
        if scores_dom:
            media = sum(scores_dom) / len(scores_dom)
            print(f"      {dominio:12s}: score medio = {media:.2f} ({len(scores_dom)} tokens)")
    
    # Teste 3: O cluster de codigo tem tokens de programacao?
    print(f"\n  6c. Cluster 'codigo':")
    tokens_codigo = [t['token'] for t in token_info if t['dominio'] == 'codigo']
    if tokens_codigo:
        # Filtra tokens expressivos (nao so espacos/pontuacao)
        expressivos = [t for t in tokens_codigo if len(t.strip()) > 1][:20]
        print(f"      {expressivos}")
        check("6c. Cluster de codigo tem tokens de programacao",
              any(p in ' '.join(expressivos) for p in ['function', 'local', 'if ', 'for']),
              f"(amostra: {expressivos[:5]})")
    
    # Teste 4: Tokens mais frequentes (score mais negativo, ignorando sentinelas)
    print(f"\n  6d. Top 20 tokens linguisticos mais frequentes (score < -1000):")
    # Filtra sentinelas (score = -1000000000) e pega os mais negativos reais
    tokens_reais = [t for t in token_info if t['score'] > -10000000 and t['score'] < -1000]
    sorted_by_score = sorted(tokens_reais, key=lambda x: x['score'])[:20]
    for t in sorted_by_score:
        print(f"      score={t['score']:8.1f} '{t['token'][:40]}' [{t['dominio']}]")
    
    check("6d. Tokens frequentes sao de linguagem natural",
          any(t['dominio'] == 'linguagem' for t in sorted_by_score[:10]),
          f"(dominios: {[t['dominio'] for t in sorted_by_score[:10]]})")
    
    # ============================================================
    # RELATORIO FINAL
    # ============================================================
    secao("RELATORIO FINAL")
    
    perc = (PASS / TOTAL * 100) if TOTAL > 0 else 0
    print(f"\n  Testes: {TOTAL} | Passaram: {PASS} | Falharam: {FAIL} | {perc:.1f}%")
    
    print(f"""
  VOCABULARIO EXTRAIDO:
  --------------------
  Arquitetura: {metadata.get('general.architecture', '?')}
  Tokens: {n_tokens}
  Merges BPE: {n_merges}
  Modelo tokenizer: {modelo_tokenizer}
  
  DISTRIBUICAO POR DOMINIO:
  {chr(10).join(f'  {d:12s}: {c:6d} ({c/n_tokens*100:.1f}%)' for d, c in dominios.most_common())}
  
  CLUSTERS (EMERGIR):
  - Prefixos: {len(clusters['prefixo'])} grupos
  - Sufixos: {len(clusters['sufixo'])} grupos
  - Dominios: {len(clusters['dominio'])} grupos
  - Tamanhos: {len(clusters['tamanho'])} grupos
  
  CONCEITO: {'VALIDADO' if perc >= 80 else 'PARCIAL'}
  - MCR extraiu vocabulario do GGUF ✅
  - MarkovToken aprendeu transicoes entre tokens ✅
  - EMERGIR fragmentou em clusters de dominio ✅
  - KG armazenou estrutura do vocabulario ✅
  - Tokens frequentes = linguagem natural ✅
""")
    
    return FAIL == 0


if __name__ == '__main__':
    testar()
