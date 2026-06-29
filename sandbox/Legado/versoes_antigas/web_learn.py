"""
WEB LEARN v2.0 — MCR-DevIA (Aprendizado Profundo)
Pipeline inteligente: busca curada → classificação → GitHub explorer → rastreio profundo →
safety scan → extração → fragmenta → narrativa → KG

Uso:
    python web_learn.py <consulta>
    python web_learn.py <consulta> --auto       (pula confirmação)
    python web_learn.py <consulta> --dry-run    (só mostra)
    python web_learn.py <consulta> --urls-only  (só busca)
    python web_learn.py <consulta> --shallow    (modo v1, sem profundidade vs sem classificação)
"""

import sys, os, json, re, time, urllib.request, urllib.parse, urllib.error, hashlib
from urllib.parse import urljoin, urlparse

# Módulo YouTube Transcript (opcional)
try:
    from youtube_transcript import detectar_youtube, extrair_youtube_transcript
    YT_DISPONIVEL = True
except ImportError:
    YT_DISPONIVEL = False

# ============================================================
# CONFIGURAÇÃO
# ============================================================

WEBLEARN_DIR = r'E:\Modelos IA\weblearn'
RAW_DIR = os.path.join(WEBLEARN_DIR, 'raw')
FRAG_DIR = os.path.join(WEBLEARN_DIR, 'fragments')
NARRATIVE_DIR = os.path.join(WEBLEARN_DIR, 'narratives')
KG_PATH = r'E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json'
MCR_PATH = r'E:\Projeto MCR\scripts\mcr_devia\mcr_devia.py'

MAX_RESULTS = 10          # Máximo de resultados de busca por query
MAX_PAGES = 6             # Máximo de páginas para baixar (primeiro nível)
MAX_DEEP_PAGES = 4        # Máximo de páginas adicionais de rastreio profundo
MAX_BYTES_PER_PAGE = 2 * 1024 * 1024
MAX_TEXT_PER_PAGE = 120 * 1024
TIMEOUT = 30
FRAGMENT_SIZE = 5000
DEEP_MAX_DEPTH = 2         # Profundidade máxima do rastreio
DEEP_RELEVANCE_THRESHOLD = 40  # Score mínimo para seguir um link interno

# Sinais de classificação de conteúdo
SINAIS_EDUCACIONAIS = re.compile(
    r'\b(tutorial|guia|guide|como|how to|passo a passo|step by|'
    r'exemplo|example|documenta[cç][ãa]o|documentation|'
    r'refer[eê]ncia|reference|manual|apostila|certifica[cç][ãa]o|'
    r'curso|course|aula|lesson|introdu[cç][ãa]o|introduction|'
    r'fundamentos|basics|beginners|iniciantes|conceitos|'
    r'defini[cç][ãa]o|definition|significado|meaning|'
    r'aprender|learn|estudar|study|entender|understand'
    r')\b', re.I
)

SINAIS_CODIGO = re.compile(
    r'(```|def |function |class |import |from |'
    r'#include|int main|public class|fn |func |'
    r'<code>|<pre>|lambda |=>|::|'
    r'const |let |var |if\s*\(|for\s*\()'
)

SINAIS_ECOMMERCE = re.compile(
    r'\b(adicionar ao carrinho|add to cart|comprar|buy now|'
    r'pre[çc]o|price|\$[\d]+|€[\d]+|carrinho|shopping cart|'
    r'checkout|finalizar compra|produto|product|'
    r'estoque|stock|frete|shipping|desconto|discount|'
    r'cupom|coupon|compre|purchase|order now|'
    r'sold out|esgotado|dispon[ií]vel|available|'
    r'tamanho|size|cor|color|quantidade|quantity'
    r')\b', re.I
)

SINAIS_GITHUB = re.compile(
    r'^https?://(www\.)?github\.com/'
    r'[^/]+/[^/]+'
    r'(/)?(blob|tree|raw|docs|wiki)?', re.I
)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0',
]

# === BLACKLISTS (mesmas da v1) ===
DOMAIN_BLACKLIST = [
    'malware', 'trojan', 'hack', 'crack', 'warez', 'piracy', 'torrent',
    'porn', 'xxx', 'adult', 'casino', 'gambling', 'bet',
    'phishing', 'scam', 'spam', 'spyware', 'keylogger',
    'doubleclick', 'googleads', 'googlesyndication',
]
EXT_BLACKLIST = (
    '.exe', '.msi', '.zip', '.rar', '.7z', '.tar.gz', '.dmg', '.pkg',
    '.bat', '.cmd', '.ps1', '.vbs', '.js', '.jar', '.apk', '.app',
    '.scr', '.cpl', '.pif', '.com', '.reg', '.sh', '.bin', '.iso',
    '.docm', '.xlsm', '.pptm',
)

DANGER_PATTERNS_HTML = [
    (re.compile(r'<script[\s>]', re.I), 'script tag'),
    (re.compile(r'<iframe[\s>]', re.I), 'iframe tag'),
    (re.compile(r'<object[\s>]', re.I), 'object tag'),
    (re.compile(r'<embed[\s>]', re.I), 'embed tag'),
    (re.compile(r'<applet[\s>]', re.I), 'applet tag'),
    (re.compile(r'<frame[\s>]', re.I), 'frame tag'),
    (re.compile(r'\bon\w+\s*=', re.I), 'event handler'),
    (re.compile(r'javascript\s*:', re.I), 'javascript: URI'),
    (re.compile(r'data\s*:\s*text/\w+\s*;base64\s*,[a-zA-Z0-9+/]{200,}', re.I), 'large base64 data URI'),
    (re.compile(r'document\.write\s*\(', re.I), 'document.write()'),
    (re.compile(r'window\.open\s*\(', re.I), 'window.open()'),
    (re.compile(r'eval\s*\(', re.I), 'eval()'),
]

DANGER_PATTERNS_TEXT = [
    (re.compile(r'\brm\s+-[rf]\s+[/~]?\s*(?:\*|\/|\.)', re.I), 'destructive rm command'),
    (re.compile(r':\s*\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;'), 'fork bomb'),
    (re.compile(r'\bformat\s+\w:\s*/[fq]', re.I), 'format command'),
    (re.compile(r'\bdd\s+if=', re.I), 'dd with if='),
    (re.compile(r'wget\s+.*\.(exe|msi|bat|ps1|vbs)', re.I), 'wget downloading executable'),
    (re.compile(r'curl\s+.*-o\s+.*\.(exe|msi|bat|ps1|vbs)', re.I), 'curl downloading executable'),
    (re.compile(r'verifique\s+sua\s+conta', re.I), 'phishing - verify account'),
    (re.compile(r'atualize\s+suas\s+informa[çc][õo]es', re.I), 'phishing - update info'),
    (re.compile(r'(https?://)(10\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.)', re.I), 'private IP in URL'),
]

# ============================================================
# HELPERS BÁSICOS
# ============================================================

def log(msg, nivel='INFO'):
    print(f'  [{nivel}] {msg}')

def erro(msg):
    log(msg, 'ERRO')
    return False

def aguardar(segundos=1):
    time.sleep(segundos)

def safe_filename(texto):
    texto = re.sub(r'[^\w\- ]', '', texto)
    texto = re.sub(r'\s+', '_', texto.strip())[:60]
    return texto or 'unknown'

def _request(url, timeout=TIMEOUT):
    headers = {'User-Agent': USER_AGENTS[int(time.time()) % len(USER_AGENTS)]}
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp
    except Exception:
        return None

def extrair_nome_dominio(url):
    m = re.match(r'https?://([^/]+)', url)
    return m.group(1).lower() if m else ''

def dominio_blacklistado(url):
    dominio = extrair_nome_dominio(url)
    for bl in DOMAIN_BLACKLIST:
        if bl in dominio:
            return True, bl
    return False, None

def extensao_perigosa(url):
    url_lower = url.lower()
    for ext in EXT_BLACKLIST:
        if url_lower.endswith(ext) or f'{ext}?' in url_lower or f'{ext}&' in url_lower:
            return True, ext
    return False, None

def _sanitize_for_console(texto):
    texto = texto.replace('\ufffd', '?')
    texto = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', texto)
    return texto

# ============================================================
# MÓDULO 1: SMART QUERY GENERATOR
# ============================================================

def gerar_queries_inteligentes(consulta):
    """
    Gera múltiplas queries otimizadas para busca educacional.
    Quanto mais variações, maior a chance de encontrar conteúdo de qualidade.
    """
    c = consulta.strip()

    # Detecta o contexto da consulta para gerar queries mais específicas
    contexto = _detectar_contexto(c)

    templates = []

    if contexto == 'linguagem_programacao':
        templates = [
            f'{c} tutorial',
            f'{c} documentation',
            f'{c} getting started',
            f'{c} learn programming',
            f'{c} language guide',
            f'site:github.com {c} tutorial',
            f'site:wikipedia.org {c} programming language',
        ]
    elif contexto == 'framework_biblioteca':
        templates = [
            f'{c} documentation',
            f'{c} tutorial',
            f'{c} getting started guide',
            f'{c} examples',
            f'{c} API reference',
            f'site:github.com {c}',
        ]
    elif contexto == 'conceito_teoria':
        templates = [
            f'{c} tutorial',
            f'{c} conceito',
            f'{c} definicao',
            f'{c} guia completo',
            f'{c} passo a passo',
            f'{c} exemplos praticos',
            f'{c} como funciona',
            f'{c} para iniciantes',
            f'{c} PDF',
            f'site:wikipedia.org {c}',
        ]
    elif contexto == 'ferramenta_software':
        templates = [
            f'{c} tutorial',
            f'{c} how to use',
            f'{c} guide',
            f'{c} documentation',
            f'{c} examples',
            f'site:github.com {c}',
        ]
    elif contexto == 'jogo_entretenimento':
        templates = [
            f'{c} guia',
            f'{c}攻略',
            f'{c} tutorial',
            f'{c} dicas',
            f'{c} como jogar',
            f'{c} walkthrough',
        ]
    else:
        # Genérico / costura, culinária, etc.
        templates = [
            f'{c} tutorial',
            f'{c} guia completo',
            f'{c} passo a passo',
            f'{c} para iniciantes',
            f'{c} dicas',
            f'{c} como fazer',
            f'{c} exemplos',
            f'site:wikipedia.org {c}',
        ]

    return templates


def _detectar_contexto(consulta):
    """Detecta o contexto da consulta para gerar queries melhores."""
    c = consulta.lower()

    # Linguagens de programação
    linguagens = [
        'python', 'javascript', 'typescript', 'java', 'c++', 'csharp',
        'rust', 'go', 'golang', 'ruby', 'php', 'swift', 'kotlin',
        'dart', 'lua', 'perl', 'haskell', 'elixir', 'clojure',
        'scala', 'r ', 'matlab', 'assembly', 'wasm', 'webassembly',
    ]
    for lang in linguagens:
        if lang in c:
            return 'linguagem_programacao'

    # Frameworks/bibliotecas
    frameworks = [
        'react', 'angular', 'vue', 'django', 'flask', 'rails',
        'spring', 'express', 'next', 'nuxt', 'svelte', 'jquery',
        'bootstrap', 'tailwind', 'pandas', 'numpy', 'tensorflow',
        'pytorch', 'unity', 'unreal',
    ]
    for fw in frameworks:
        if fw in c:
            return 'framework_biblioteca'

    # Conceitos teóricos
    teoricos = [
        'conceito', 'teoria', 'principio', 'fundamento', 'definicao',
        'significado', 'o que e', 'o que é', 'paradigma', 'arquitetura',
        'design pattern', 'algoritmo', 'estrutura de dados',
    ]
    for t in teoricos:
        if t in c:
            return 'conceito_teoria'

    # Ferramentas
    ferramentas = [
        'docker', 'kubernetes', 'git', 'linux', 'vim', 'vscode',
        'photoshop', 'excel', 'word', 'powerpoint',
    ]
    for f in ferramentas:
        if f in c:
            return 'ferramenta_software'

    # Jogos
    jogos = ['jogo', 'game', 'rpg', 'mmo', 'minecraft', 'tibia']
    for j in jogos:
        if j in c:
            return 'jogo_entretenimento'

    return 'conceito_teoria'


# ============================================================
# MÓDULO 2: RELEVANCE CLASSIFIER
# ============================================================

def classificar_pagina(titulo, snippet, url, texto_extraido=''):
    """
    Classifica a página e retorna (tipo, score, motivo).

    tipos: 'tutorial' | 'documentacao' | 'github_repo' | 'wiki' | 'forum' |
           'blog' | 'ecommerce' | 'garbage' | 'video' | 'social'

    score: 0-100 (0 = lixo, 100 = exatamente o que precisamos)
    """
    score = 0
    tipo = 'desconhecido'
    amostra = (titulo + ' ' + snippet + ' ' + texto_extraido[:1000]).lower()

    # ===== SINAIS POSITIVOS =====

    # Sinal educacional forte
    matches_edu = len(SINAIS_EDUCACIONAIS.findall(amostra))
    score += matches_edu * 8

    # Sinal de código
    if SINAIS_CODIGO.search(amostra):
        score += 15
    if '```' in texto_extraido:
        score += 10
    if texto_extraido.count('\n\n') > 10:
        score += 10  # Conteúdo substancial

    # Sinal de documentação oficial
    if any(w in url.lower() for w in ['docs.', '.docs.', '/docs/', '/documentation', '/manual', '/wiki/']):
        score += 15

    # Sinal Wikipedia
    if 'wikipedia.org' in url.lower():
        score += 20
        tipo = 'wiki'

    # Sinal GitHub
    if SINAIS_GITHUB.match(url):
        score += 10
        if '/blob/' in url or '/tree/' in url or 'README' in url:
            score += 10
        tipo = 'github_repo'

    # Sinal de site educacional conhecido
    sites_educacionais = [
        'w3schools', 'geeksforgeeks', 'programiz', 'realpython',
        'tutorialspoint', 'javatpoint', 'digitalocean', 'freecodecamp',
        'dev.to', 'medium.com', 'stackoverflow', 'stackexchange',
        'gitbooks.io', 'readthedocs', 'mdn.', 'developer.mozilla',
        'learn.microsoft', 'docs.python', 'doc.rust',
    ]
    for site in sites_educacionais:
        if site in url.lower():
            score += 10
            break

    # Tamanho do conteúdo
    if len(texto_extraido) > 5000:
        score += 5
    if len(texto_extraido) > 20000:
        score += 5

    # ===== SINAIS NEGATIVOS =====

    # E-commerce
    matches_eco = len(SINAIS_ECOMMERCE.findall(amostra))
    if matches_eco >= 3:
        score -= 30
        tipo = 'ecommerce'
    elif matches_eco >= 1:
        score -= 10

    # Página muito pequena (provavelmente placeholder ou redirecionamento)
    if len(texto_extraido) < 200 and texto_extraido != '':
        score -= 20

    # Domínios de e-commerce conhecidos
    dominios_ecommerce = [
        'shop', 'store', 'loja', 'produto', 'carrinho', 'mercadolivre',
        'amazon', 'ebay', 'aliexpress', 'shopee', 'magazineluiza',
    ]
    for d in dominios_ecommerce:
        if d in url.lower():
            score -= 15
            break

    # Redes sociais (pouco valor educacional)
    redes = ['facebook.com', 'twitter.com', 'instagram.com', 'tiktok.com']
    for r in redes:
        if r in url.lower():
            score -= 20
            tipo = 'social'
            break

    # Vídeo (YouTube - só metadata, não o conteúdo)
    if 'youtube.com' in url.lower() or 'youtu.be' in url.lower():
        score -= 15
        tipo = 'video'

    # Páginas de login/registro
    if any(w in url.lower() for w in ['/login', '/register', '/signup', '/auth']):
        score -= 25

    # ===== CLASSIFICAÇÃO FINAL =====

    # Determina o tipo baseado nos sinais mais fortes
    if tipo == 'desconhecido':
        if score >= 50:
            tipo = 'tutorial'
        elif score >= 30:
            tipo = 'blog'
        elif score >= 10:
            tipo = 'referencia'
        else:
            tipo = 'garbage'

    return tipo, max(0, min(100, score))


# ============================================================
# MÓDULO 3: GITHUB CRAWLER
# ============================================================

def explorar_github(url_repo, consulta, nome_base, idx_inicial, dry_run=False):
    """
    Navega por um repositório GitHub e baixa conteúdo relevante.
    1. Detecta se é página de repositório (github.com/user/repo)
    2. Baixa README.md (raw)
    3. Lista docs/, examples/, src/ se existirem
    4. Baixa arquivos .md, .lua, .cpp, .py, .rs, .go, .js etc.

    Retorna lista de páginas processadas.
    """
    paginas = []
    idx = idx_inicial

    # Normaliza URL do GitHub
    m = re.match(r'^https?://(www\.)?github\.com/([^/]+)/([^/]+)', url_repo)
    if not m:
        return paginas

    user, repo = m.group(2), m.group(3).rstrip('/').split('/')[0]
    base_api = f'https://api.github.com/repos/{user}/{repo}'
    base_raw = f'https://raw.githubusercontent.com/{user}/{repo}/master'
    base_github = f'https://github.com/{user}/{repo}'

    # 1. Tenta baixar README.md (raw)
    readme_urls = [
        f'{base_raw}/README.md',
        f'{base_raw}/README.markdown',
        f'{base_raw}/README.rst',
        f'{base_raw}/readme.md',
        f'{base_raw}/docs/README.md',
    ]

    log(f'GitHub: explorando {user}/{repo}', 'GITHUB')

    for readme_url in readme_urls:
        if dry_run:
            log(f'[DRY-RUN] GitHub: leria README de {readme_url}', 'GITHUB')
            continue

        resp = _request(readme_url)
        if resp and resp.status == 200:
            try:
                texto_raw = resp.read().decode('utf-8', errors='replace')
                if len(texto_raw) > 200 and len(texto_raw) < 500000:
                    log(f'GitHub: README encontrado ({len(texto_raw)//1024}KB)', 'GITHUB')

                    # Salva como página processada
                    pagina = {
                        'titulo': f'GitHub: {user}/{repo} - README',
                        'url': f'{base_github}#readme',
                        'tamanho_kb': len(texto_raw) // 1024,
                        'raw_path': '',
                        'texto': texto_raw[:MAX_TEXT_PER_PAGE],
                        'texto_preview': texto_raw[:400],
                        'fragmentos': 0,
                        'tipo': 'github_repo',
                        'relevancia': 85,
                        'alertas': 0,
                        'alertas_lista': [],
                        'aprovado': True,
                        'profundidade': 0,
                        'origem': url_repo,
                    }

                    frag_path, num_frag = fragmentar(texto_raw, f'{safe_filename(nome_base)}_github_{repo}', idx)
                    pagina['frag_dir'] = str(frag_path)
                    pagina['fragmentos'] = num_frag
                    paginas.append(pagina)
                    idx += 1
                    break
            except Exception:
                continue

    # 2. Tenta explorar docs/ e exemplos (via GitHub API)
    if not dry_run:
        aguardar(1)
        dirs_para_explorar = ['docs', 'examples', 'example', 'sample', 'src/' + consulta.lower().split()[0] if consulta.split() else 'src']

        for subdir in dirs_para_explorar:
            api_url = f'{base_api}/contents/{subdir}'
            try:
                req = urllib.request.Request(api_url, headers={'User-Agent': USER_AGENTS[0], 'Accept': 'application/vnd.github.v3+json'})
                resp = urllib.request.urlopen(req, timeout=15)
                data = json.loads(resp.read().decode('utf-8'))

                if isinstance(data, list):
                    # Encontra arquivos .md, .txt, e de código
                    ext_interessantes = ('.md', '.txt', '.lua', '.cpp', '.hpp', '.h', '.c',
                                         '.py', '.rs', '.go', '.js', '.ts', '.java', '.rb',
                                         '.php', '.swift', '.kt', '.dart', '.sh', '.yaml', '.yml',
                                         '.toml', '.json', '.xml', '.lua', '.cfg')

                    arquivos = [item for item in data if isinstance(item, dict)
                                and item.get('type') == 'file'
                                and item.get('name', '').endswith(ext_interessantes)]

                    if arquivos:
                        log(f'GitHub: {len(arquivos)} arquivos em {subdir}', 'GITHUB')

                    for item in arquivos[:8]:  # Máximo 8 arquivos
                        nome_arq = item['name']
                        download_url = item.get('download_url', '')
                        if not download_url:
                            continue

                        aguardar(0.5)
                        try:
                            resp2 = _request(download_url)
                            if resp2:
                                conteudo = resp2.read().decode('utf-8', errors='replace')
                                if len(conteudo) > 100 and len(conteudo) < 500000:
                                    pagina = {
                                        'titulo': f'GitHub: {user}/{repo}/{subdir}/{nome_arq}',
                                        'url': item.get('html_url', download_url),
                                        'tamanho_kb': len(conteudo) // 1024,
                                        'raw_path': '',
                                        'texto': conteudo[:MAX_TEXT_PER_PAGE],
                                        'texto_preview': conteudo[:300],
                                        'fragmentos': 0,
                                        'tipo': 'github_repo',
                                        'relevancia': 80,
                                        'alertas': 0,
                                        'alertas_lista': [],
                                        'aprovado': True,
                                        'profundidade': 1,
                                        'origem': url_repo,
                                    }
                                    frag_path, num_frag = fragmentar(conteudo, f'{safe_filename(nome_base)}_{repo}_{subdir}', idx)
                                    pagina['frag_dir'] = str(frag_path)
                                    pagina['fragmentos'] = num_frag
                                    paginas.append(pagina)
                                    idx += 1
                                    log(f'GitHub: OK {nome_arq} ({len(conteudo)//1024}KB)', 'GITHUB')
                        except Exception:
                            continue

            except urllib.error.HTTPError as e:
                if e.code == 404:
                    continue  # Diretório não existe
                elif e.code == 403:
                    log(f'GitHub API rate limit', 'WARN')
                    break
            except Exception:
                continue

    return paginas


# ============================================================
# MÓDULO 4: DEEP CRAWLER (com ContextGuard)
# ============================================================

def extrair_links_internos(html, url_base):
    """
    Extrai links internos do mesmo domínio de uma página HTML.
    Retorna lista de URLs absolutas.
    """
    dominio_base = extrair_nome_dominio(url_base)
    links = set()

    for m in re.finditer(r'<a[^>]*href="([^"]+)"', html, re.I):
        href = m.group(1).strip()
        # Ignora âncoras, javascript, mailto
        if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
            continue
        # Resolve URL relativa
        url_abs = urljoin(url_base, href)
        # Só mantém do mesmo domínio
        if extrair_nome_dominio(url_abs) == dominio_base:
            # Ignora arquivos estáticos comuns
            if not any(url_abs.endswith(ext) for ext in ['.css', '.js', '.png', '.jpg', '.gif', '.svg', '.ico', '.woff', '.ttf', '.pdf']):
                links.add(url_abs.split('#')[0].split('?')[0])  # Remove âncoras e query string

    return list(links)


def pontuar_relevancia_link(url, consulta):
    """
    Avalia quão relevante um link interno é para a consulta original.
    Score 0-100. Só segue se >= DEEP_RELEVANCE_THRESHOLD.
    """
    score = 0
    url_lower = url.lower()
    palavras_consulta = set(re.findall(r'\w+', consulta.lower()))

    # Palavras-chave da consulta na URL
    for palavra in palavras_consulta:
        if len(palavra) >= 3 and palavra in url_lower:
            score += 15

    # URLs com palavras educacionais
    palavras_boas = ['tutorial', 'guide', 'doc', 'manual', 'example', 'how-to',
                     'learn', 'intro', 'basics', 'reference', 'api', 'conceito',
                     'guia', 'aula', 'exemplo', 'passo', 'dica']
    for p in palavras_boas:
        if p in url_lower:
            score += 10

    # URLs de e-commerce ou navegação genérica
    palavras_ruins = ['cart', 'checkout', 'login', 'register', 'signup',
                      'tag/', 'category/', 'author/', 'page/', 'feed']
    for p in palavras_ruins:
        if p in url_lower:
            score -= 20

    return max(0, min(100, score))


def rastrear_profundidade(html, url_origem, consulta, nome_base, idx_inicial,
                          max_paginas=MAX_DEEP_PAGES, max_profundidade=DEEP_MAX_DEPTH,
                          visitados=None, dry_run=False):
    """
    Rastreia links internos do mesmo domínio com profundidade limitada.
    Usa ContextGuard: só segue links com score >= threshold.
    Evita loops com conjunto de URLs visitadas.

    Retorna lista de páginas processadas adicionais.
    """
    if visitados is None:
        visitados = set()

    paginas_adicionais = []
    idx = idx_inicial
    dominio = extrair_nome_dominio(url_origem)

    links = extrair_links_internos(html, url_origem)
    log(f'DeepCrawl: {len(links)} links internos encontrados', 'DEEP')

    # Filtra e ordena links por relevância
    links_avaliados = []
    for link in links:
        if link in visitados:
            continue
        score = pontuar_relevancia_link(link, consulta)
        if score >= DEEP_RELEVANCE_THRESHOLD:
            links_avaliados.append((score, link))

    # Ordena pelos mais relevantes
    links_avaliados.sort(key=lambda x: -x[0])

    if links_avaliados:
        log(f'DeepCrawl: {len(links_avaliados)} links relevantes (threshold>{DEEP_RELEVANCE_THRESHOLD})', 'DEEP')

    for score, link in links_avaliados[:max_paginas]:
        if link in visitados or len(paginas_adicionais) >= max_paginas:
            continue

        visitados.add(link)

        if dry_run:
            log(f'[DRY-RUN] DeepCrawl: seguiria {link} (score:{score})', 'DEEP')
            continue

        aguardar(1.5)

        # Baixa a página
        resp = _request(link)
        if not resp:
            continue

        try:
            html_pag = resp.read().decode('utf-8', errors='replace')
        except:
            continue

        # Extrai texto
        texto = extrair_texto_limpo(html_pag)

        # ContextGuard: verifica se o texto ainda é relevante para a consulta
        palavras_consulta = set(re.findall(r'\w+', consulta.lower()))
        palavras_texto = set(re.findall(r'\w+', texto.lower()))
        overlap = len(palavras_consulta & palavras_texto)

        if overlap < max(1, len(palavras_consulta) // 3):
            log(f'DeepCrawl: ignorado (context drift) {link[:60]}', 'DEEP')
            continue

        # Safety scans
        alertas_html = safety_scan_html(html_pag, link)
        aprovado_texto, alertas_texto = safety_scan_text(texto, link)

        total_alertas = len(alertas_html) + len(alertas_texto)
        aprovado = aprovado_texto or total_alertas < 3

        if not aprovado:
            log(f'DeepCrawl: rejeitado por segurança: {link[:60]}', 'DEEP')
            continue

        if len(texto) < 200:
            continue  # Página muito pequena

        # Limita tamanho
        if len(texto) > MAX_TEXT_PER_PAGE:
            texto = texto[:MAX_TEXT_PER_PAGE]

        # Tenta extrair título
        titulo_m = re.search(r'<title[^>]*>(.*?)</title>', html_pag, re.DOTALL | re.IGNORECASE)
        titulo = re.sub(r'<[^>]+>', '', titulo_m.group(1)).strip() if titulo_m else f'Deep: {link[:50]}'

        pagina = {
            'titulo': titulo[:80],
            'url': link,
            'tamanho_kb': len(html_pag) // 1024,
            'raw_path': '',
            'texto': texto[:50000],
            'texto_preview': texto[:300],
            'fragmentos': 0,
            'tipo': 'deep_crawl',
            'relevancia': score,
            'alertas': total_alertas,
            'alertas_lista': alertas_html + alertas_texto,
            'aprovado': True,
            'profundidade': 1,
            'origem': url_origem,
        }

        frag_path, num_frag = fragmentar(texto, nome_base, idx)
        pagina['frag_dir'] = str(frag_path)
        pagina['fragmentos'] = num_frag

        paginas_adicionais.append(pagina)
        idx += 1
        log(f'DeepCrawl: OK ({len(texto)//1024}KB, score:{score}) - {titulo[:50]}', 'DEEP')

    return paginas_adicionais


# ============================================================
# MÓDULO 5: WEB SEARCH (ddgs)
# ============================================================

_HAS_DDGS = False
for mod_name in ['ddgs', 'duckduckgo_search']:
    try:
        mod = __import__(mod_name, fromlist=['DDGS'])
        DDGS = mod.DDGS
        _HAS_DDGS = True
        break
    except ImportError:
        continue


def search_duckduckgo(query, max_results=MAX_RESULTS):
    if not _HAS_DDGS:
        log('ddgs nao instalado. pip install ddgs', 'WARN')
        return None
    try:
        with DDGS() as ddgs:
            raw = list(ddgs.text(query, max_results=max_results))
            resultados = []
            for r in raw:
                resultados.append({
                    'titulo': r.get('title', ''),
                    'snippet': r.get('body', ''),
                    'url': r.get('href', ''),
                    'fonte': 'DuckDuckGo',
                })
            return resultados if resultados else None
    except Exception as e:
        log(f'DuckDuckGo error: {e}', 'WARN')
        return None


def web_search_multi(consulta):
    """
    Busca com MÚLTIPLAS queries inteligentes.
    Retorna lista de resultados DEDUPLICADOS e CLASSIFICADOS.
    """
    queries = gerar_queries_inteligentes(consulta)
    log(f'SmartQuery: {len(queries)} variacoes geradas', 'QUERY')

    todos_resultados = []
    urls_vistas = set()

    for i, query in enumerate(queries[:5], 1):  # Máximo 5 queries
        log(f'Query [{i}/{min(5,len(queries))}]: {query}', 'QUERY')
        aguardar(1.5)

        resultados = search_duckduckgo(query, max_results=MAX_RESULTS)
        if not resultados:
            continue

        for r in resultados:
            url = r['url']
            if url in urls_vistas:
                continue
            urls_vistas.add(url)

            # Classifica antes de adicionar
            tipo, score = classificar_pagina(r['titulo'], r.get('snippet', ''), url)

            # Filtra garbage
            if tipo != 'garbage' or score > 20:
                r['tipo'] = tipo
                r['relevancia'] = score
                todos_resultados.append(r)

        aguardar(0.5)

    if not todos_resultados:
        log('Nenhum resultado encontrado nas buscas.', 'ERRO')
        return []

    # Ordena por relevância (melhores primeiro)
    todos_resultados.sort(key=lambda x: -x.get('relevancia', 0))

    # Log das classificações
    for r in todos_resultados[:MAX_RESULTS]:
        log(f'{r["tipo"]}({r["relevancia"]}): {r["titulo"][:60]}', 'CLASS')

    return todos_resultados


# ============================================================
# MÓDULO 6: URL FILTER (v2 com classificação)
# ============================================================

def filtrar_urls_v2(resultados, max_pages=MAX_PAGES):
    """
    Filtra URLs perigosas E de baixa relevância.
    Só mantém as melhores páginas.
    """
    filtrados = []
    for r in resultados:
        url = r['url']

        # Filtros de segurança (v1)
        bl_dominio, motivo = dominio_blacklistado(url)
        if bl_dominio:
            log(f'Dominio bloqueado: {motivo}', 'BLOQ')
            continue

        bl_ext, ext = extensao_perigosa(url)
        if bl_ext:
            log(f'Extensao bloqueada: {ext}', 'BLOQ')
            continue

        if not url.startswith(('http://', 'https://')):
            continue

        # Filtro por tipo (só mantém tipos com valor educacional)
        tipo = r.get('tipo', 'desconhecido')
        if tipo in ('ecommerce', 'garbage', 'social'):
            log(f'Ignorado ({tipo}): {url[:60]}', 'CLASS')
            continue

        # Detecta YouTube e marca para transcricao
        if YT_DISPONIVEL and detectar_youtube(url):
            r['tipo'] = 'youtube'
            log(f'YouTube detectado: {url[:60]}', 'CLASS')

        filtrados.append(r)

    # Limita aos melhores
    filtrados = filtrados[:max_pages]

    removidos = len(resultados) - len(filtrados)
    if removidos:
        log(f'{removidos} resultados descartados (baixa relevancia)', 'CLASS')

    return filtrados


# ============================================================
# MÓDULO 7: SAFETY, TEXT EXTRACTION, FRAGMENT (v1 mantido)
# ============================================================

def safety_scan_html(html, url=''):
    alertas = []
    for pattern, nome in DANGER_PATTERNS_HTML:
        if pattern.search(html):
            alertas.append(f'{nome} detectado')
    if alertas:
        log(f'Safety Scan V1: {len(alertas)} alertas', 'SCAN')
    return alertas


def extrair_texto_limpo(html):
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<iframe[^>]*>.*?</iframe>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<object[^>]*>.*?</object>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<embed[^>]*>.*?</embed>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<applet[^>]*>.*?</applet>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<frame[^>]*>.*?</frame>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<noscript[^>]*>.*?</noscript>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    html = re.sub(r'\s+on\w+\s*=\s*(?:"[^"]*"|\'[^\']*\')', '', html, flags=re.IGNORECASE)
    html = re.sub(r'\s+on\w+\s*=\s*\w+', '', html, flags=re.IGNORECASE)
    html = re.sub(r'href\s*=\s*(?:"javascript:[^"]*"|\'javascript:[^\']*\')', 'href="#"', html, flags=re.IGNORECASE)
    html = re.sub(r'src\s*=\s*(?:"javascript:[^"]*"|\'javascript:[^\']*\')', 'src=""', html, flags=re.IGNORECASE)
    html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<header[^>]*>.*?</header>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<aside[^>]*>.*?</aside>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'</?(?:p|div|h[1-6]|li|tr|td|th|blockquote|pre|code|article|section|main|br|hr)[^>]*>', '\n', html, flags=re.IGNORECASE)
    texto = re.sub(r'<[^>]+>', ' ', html)
    texto = re.sub(r'&nbsp;', ' ', texto)
    texto = re.sub(r'&amp;', '&', texto)
    texto = re.sub(r'&lt;', '<', texto)
    texto = re.sub(r'&gt;', '>', texto)
    texto = re.sub(r'&quot;', '"', texto)
    texto = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))) if int(m.group(1)) < 128 else '?', texto)
    texto = re.sub(r'\n\s*\n', '\n\n', texto)
    texto = re.sub(r'[ \t]+', ' ', texto)
    return texto.strip()


def safety_scan_text(texto, url=''):
    alertas = []
    for pattern, nome in DANGER_PATTERNS_TEXT:
        for m in pattern.finditer(texto):
            alertas.append(f'{nome}')
    if alertas:
        log(f'Safety Scan V2: {len(alertas)} alertas', 'SCAN')
    return len(alertas) == 0, alertas


def fragmentar(texto, nome_base, idx_pagina):
    frag_path = os.path.join(FRAG_DIR, safe_filename(f'{nome_base}_{idx_pagina:04d}'))
    os.makedirs(frag_path, exist_ok=True)
    existentes = [f for f in os.listdir(frag_path) if f.endswith('.txt')]
    offset = len(existentes)
    partes = [texto[i:i+FRAGMENT_SIZE] for i in range(0, len(texto), FRAGMENT_SIZE)]
    for i, parte in enumerate(partes):
        if not parte.strip():
            continue
        with open(os.path.join(frag_path, f'{offset + i:04d}.txt'), 'w', encoding='utf-8') as f:
            f.write(parte)
    return frag_path, len(partes)


def baixar_pagina(url, nome_base, idx):
    try:
        log(f'Baixando [{idx}]: {url[:80]}')
        resp = _request(url)
        if not resp:
            return None, f'Falha ao acessar: {url[:60]}', 0

        ct = resp.headers.get('Content-Type', '')
        if 'text' not in ct and 'html' not in ct and 'json' not in ct and 'xml' not in ct:
            return None, f'Content-Type ignorado: {ct}', 0

        dados = resp.read(MAX_BYTES_PER_PAGE + 1)
        if len(dados) > MAX_BYTES_PER_PAGE:
            dados = dados[:MAX_BYTES_PER_PAGE]

        try:
            texto = dados.decode('utf-8', errors='replace')
        except:
            texto = dados.decode('latin-1', errors='replace')

        raw_path = os.path.join(RAW_DIR, nome_base, f'{idx:04d}.html')
        os.makedirs(os.path.dirname(raw_path), exist_ok=True)
        with open(raw_path, 'w', encoding='utf-8') as f:
            f.write(texto)

        log(f'OK [{idx}]: {len(texto)//1024}KB')
        return texto, raw_path, len(texto)

    except Exception as e:
        return None, str(e), 0


# ============================================================
# MÓDULO 8: NARRATIVA + KG
# ============================================================

def gerar_narrativa_v2(consulta, resultados_originais, paginas_processadas):
    """Gera narrativa .md enriquecida com classificações e deep info."""
    nome_arq = safe_filename(consulta)
    narr_path = os.path.join(NARRATIVE_DIR, f'{nome_arq}.md')
    os.makedirs(NARRATIVE_DIR, exist_ok=True)

    # Conta estatísticas
    total_fragmentos = sum(p.get('fragmentos', 0) for p in paginas_processadas)
    por_tipo = {}
    for p in paginas_processadas:
        t = p.get('tipo', 'desconhecido')
        por_tipo[t] = por_tipo.get(t, 0) + 1

    with open(narr_path, 'w', encoding='utf-8') as f:
        f.write(f'# WebLearn v2: {consulta}\n\n')
        f.write(f'**Data:** {time.strftime("%Y-%m-%d %H:%M")}\n\n')

        f.write(f'## Resumo\n\n')
        f.write(f'- {len(paginas_processadas)} páginas processadas\n')
        f.write(f'- {total_fragmentos} fragmentos gerados\n')
        f.write(f'- Tipos: {", ".join(f"{t}: {n}" for t, n in por_tipo.items())}\n\n')

        f.write(f'## Resultados da Busca\n\n')
        f.write(f'| # | Tipo | Relevância | Título |\n')
        f.write(f'|---|------|-----------|--------|\n')
        for i, r in enumerate(resultados_originais[:15], 1):
            tipo = r.get('tipo', '?')
            rel = r.get('relevancia', 0)
            f.write(f'| {i} | {tipo} | {rel} | [{r["titulo"][:50]}]({r["url"]}) |\n')

        f.write(f'\n\n## Páginas Processadas\n\n')
        for p in paginas_processadas:
            depth_str = f' (profundidade {p.get("profundidade",0)})' if p.get('profundidade', 0) > 0 else ''
            f.write(f'### {p["titulo"][:60]}{depth_str}\n')
            f.write(f'- **URL:** {p["url"]}\n')
            f.write(f'- **Tipo:** {p.get("tipo", "?")} | **Relevância:** {p.get("relevancia", "?")}\n')
            f.write(f'- **Tamanho:** {p["tamanho_kb"]}KB | **Fragmentos:** {p["fragmentos"]}\n')
            f.write(f'- **Alertas Safety:** {p["alertas"]}\n')
            if p.get('origem'):
                f.write(f'- **Origem:** {p["origem"][:60]}\n')
            f.write('\n')

        f.write(f'\n## Safety Scan\n\n')
        for p in paginas_processadas:
            if p.get('alertas_lista'):
                f.write(f'### {p["titulo"][:40]}\n')
                for a in p['alertas_lista']:
                    f.write(f'- ⚠️ {a}\n')
                f.write('\n')

        f.write(f'\n## Amostra de Conteúdo\n\n')
        for p in paginas_processadas[:3]:
            if p.get('texto_preview'):
                f.write(f'### {p["titulo"][:40]}\n\n')
                f.write(f'```\n{p["texto_preview"]}\n```\n\n')

    return narr_path


def aprender_no_kg_v2(consulta, resultados_originais, paginas_processadas, narr_path, auto=False):
    """Registra aprendizado no KG com metadados da classificação."""
    total_paginas = len(paginas_processadas)
    total_fragmentos = sum(p.get('fragmentos', 0) for p in paginas_processadas)

    # Estatísticas de tipos
    por_tipo = {}
    for p in paginas_processadas:
        t = p.get('tipo', '?')
        por_tipo[t] = por_tipo.get(t, 0) + 1
    tipos_str = ', '.join(f'{t}:{n}' for t, n in por_tipo.items())

    # Deep info
    deep_count = sum(1 for p in paginas_processadas if p.get('profundidade', 0) > 0)
    github_count = sum(1 for p in paginas_processadas if p.get('tipo') == 'github_repo')

    urls = '\n'.join(f'- [{p["tipo"]}][{p.get("relevancia",0)}] {p["titulo"][:40]}: {p["url"]}' for p in paginas_processadas[:8])

    # Concatena textos relevantes
    textos = [p['texto'] for p in paginas_processadas if p.get('texto') and p['aprovado'] and len(p.get('texto','')) > 500]
    conhecimento = '\n\n---\n\n'.join(textos)
    if len(conhecimento) > 10000:
        conhecimento = conhecimento[:10000] + '\n[...]'

    c = _sanitize_for_console(consulta)
    solucao = (
        f'WebLearn v2: {c}\n'
        f'Paginas: {total_paginas} | Fragmentos: {total_fragmentos} | Tipos: {tipos_str}\n'
        f'Rastreio profundo: {deep_count} paginas | GitHub: {github_count} arquivos\n'
        f'Narrativa: {narr_path}\n'
        f'---\n{_sanitize_for_console(conhecimento[:600])}...'
    )

    if not auto:
        print(f'\n{"="*55}')
        print(f'  MCR-DevIA quer aprender sobre:')
        print(f'  "{consulta}"')
        print(f'  {total_paginas} paginas ({tipos_str})')
        print(f'  {total_fragmentos} fragmentos | Deep: {deep_count} | GitHub: {github_count}')
        print(f'  Narrativa: {narr_path}')
        print(f'{"="*55}')
        try:
            if sys.stdin and sys.stdin.isatty():
                resp = input('  Registar no KG? (S/n): ').strip().lower()
                if resp not in ('', 's', 'sim', 'y', 'yes'):
                    log('Aprendizado cancelado.')
                    return False
        except:
            pass

    try:
        import subprocess
        cmd = [sys.executable, MCR_PATH, 'ensinar',
               f'WebLearn v2: {c}',
               f'Conhecimento via web sobre: {c} (tipos: {tipos_str})',
               solucao, 'web_learn']
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        r = subprocess.run(cmd, capture_output=True, timeout=30, env=env)
        saida = r.stdout.decode('utf-8', errors='replace')
        log(f'KG: {_sanitize_for_console(saida[:100])}')
        log(f'Aprendizado registrado: {c}')
        return True
    except Exception as e:
        erro(f'Falha ao registar no KG: {_sanitize_for_console(str(e))}')
        return False


# ============================================================
# PIPELINE V2 COMPLETA
# ============================================================

def pipeline_v2(consulta, auto=False, dry_run=False, urls_only=False, shallow=False):
    """
    Pipeline v2 com busca inteligente, classificação, GitHub explorer e deep crawl.
    """
    inicio = time.time()
    nome_base = safe_filename(consulta)
    log(f'{"="*55}')
    log(f'WEB LEARN v2: "{consulta}"')
    log(f'Modo: {"SHALLOW" if shallow else "DEEP"} | {"AUTO" if auto else "SEMI"} | {"DRY-RUN" if dry_run else "REAL"}')
    log(f'{"="*55}')
    print()

    # ================================================================
    # PASSO 1: Web Search (multi-query inteligente)
    # ================================================================
    log('--- PASSO 1/8: Smart Web Search ---')
    resultados = web_search_multi(consulta)
    if not resultados:
        erro('Nenhum resultado encontrado.')
        return False

    # Mostra melhores resultados
    log(f'TOP {min(10, len(resultados))} resultados (classificados):')
    for i, r in enumerate(resultados[:10], 1):
        tipo = r.get('tipo', '?')
        rel = r.get('relevancia', 0)
        print(f'  [{i}] [{tipo}/{rel}] {r["titulo"][:60]}')
        print(f'       {r["url"][:70]}')

    if urls_only:
        return True

    # ================================================================
    # PASSO 2: Filtra URLs (com classificação)
    # ================================================================
    log('--- PASSO 2/8: URL Filter (curadoria) ---')
    selecionados = filtrar_urls_v2(resultados)
    if not selecionados:
        erro('Nenhuma URL passou pelo filtro de relevância.')
        return False

    # ================================================================
    # PASSO 3-8: Processa cada página
    # ================================================================
    paginas_processadas = []
    visitados_global = set()

    for idx, r in enumerate(selecionados, 1):
        url = r['url']
        visitados_global.add(url)
        aguardar(1.5)

        if dry_run:
            paginas_processadas.append({
                'titulo': r['titulo'],
                'url': url, 'tipo': r.get('tipo', '?'),
                'relevancia': r.get('relevancia', 0),
                'aprovado': True, 'tamanho_kb': 0, 'alertas': 0,
                'fragmentos': 0, 'texto': '(dry-run)',
                'texto_preview': '(dry-run)', 'profundidade': 0,
            })
            log(f'[DRY-RUN] Processaria: {r["tipo"]}/{r.get("relevancia",0)} - {url[:60]}')
            continue

        # Se for GitHub, explora o repositório
        if r.get('tipo') == 'github_repo':
            log(f'GitHub detectado: explorando {url[:70]}', 'GITHUB')
            paginas_github = explorar_github(url, consulta, nome_base, len(paginas_processadas) + 1, dry_run)
            paginas_processadas.extend(paginas_github)
            log(f'GitHub: {len(paginas_github)} paginas extraidas', 'GITHUB')
            continue

        # Se for YouTube, extrai transcricao em vez de baixar HTML
        if r.get('tipo') == 'youtube' and YT_DISPONIVEL:
            log(f'--- PASSO 3/8: YouTube Transcript [{idx}] ---')
            texto_yt = extrair_youtube_transcript(url)
            if texto_yt is None:
                erro(f'YouTube: falha ao extrair transcricao')
                continue
            log(f'OK [{idx}]: {len(texto_yt)} chars (transcricao YouTube)')
            if len(texto_yt) > MAX_TEXT_PER_PAGE:
                texto_yt = texto_yt[:MAX_TEXT_PER_PAGE]
            texto_limpo = texto_yt
            tipo_real, score_real = 'youtube', 80
            tamanho = len(texto_yt)
            alertas_html, alertas_texto = [], []
            total_alertas = 0
            aprovado_final = True
            pagina = {
                'titulo': r['titulo'][:80], 'url': url,
                'tamanho_kb': tamanho // 1024, 'raw_path': '',
                'texto': texto_limpo[:50000],
                'texto_preview': texto_limpo[:300],
                'fragmentos': 0, 'tipo': tipo_real,
                'relevancia': score_real, 'alertas': 0,
                'alertas_lista': [], 'aprovado': True,
                'profundidade': 0, 'origem': '',
            }
            if texto_limpo.strip():
                frag_path, num_frag = fragmentar(texto_limpo, nome_base, idx)
                pagina['frag_dir'] = str(frag_path)
                pagina['fragmentos'] = num_frag
                log(f'Fragmentos: {num_frag} | Tipo: youtube | Score: {score_real}')
            paginas_processadas.append(pagina)
            continue

        # PASSO 3: Baixa página
        log(f'--- PASSO 3/8: Download [{idx}] ---')
        html, erro_msg, tamanho = baixar_pagina(url, nome_base, idx)
        if html is None:
            erro(erro_msg)
            continue

        # PASSO 4: Safety Scan V1
        log(f'--- PASSO 4/8: Safety Scan V1 [{idx}] ---')
        alertas_html = safety_scan_html(html, url)

        # PASSO 5: Extração de texto
        log(f'--- PASSO 5/8: Text Extraction [{idx}] ---')
        texto_limpo = extrair_texto_limpo(html)

        # Classificação com texto completo
        tipo_real, score_real = classificar_pagina(r['titulo'], r.get('snippet', ''), url, texto_limpo[:3000])

        if len(texto_limpo) > MAX_TEXT_PER_PAGE:
            texto_limpo = texto_limpo[:MAX_TEXT_PER_PAGE]

        # Se for muito baixa qualidade, pula
        if score_real < 20 and len(texto_limpo) < 500:
            log(f'Pagina de baixa qualidade ({score_real}), ignorando', 'CLASS')
            continue

        # PASSO 6: Safety Scan V2
        log(f'--- PASSO 6/8: Safety Scan V2 [{idx}] ---')
        aprovado, alertas_texto = safety_scan_text(texto_limpo, url)

        total_alertas = len(alertas_html) + len(alertas_texto)
        aprovado_final = aprovado or total_alertas < 3

        pagina = {
            'titulo': r['titulo'][:80],
            'url': url,
            'tamanho_kb': tamanho // 1024,
            'raw_path': '',
            'texto': texto_limpo[:50000] if aprovado_final else '',
            'texto_preview': texto_limpo[:300] if aprovado_final else '(rejeitado)',
            'fragmentos': 0,
            'tipo': tipo_real,
            'relevancia': score_real,
            'alertas': total_alertas,
            'alertas_lista': alertas_html + alertas_texto,
            'aprovado': aprovado_final,
            'profundidade': 0,
            'origem': '',
        }

        if aprovado_final and texto_limpo.strip():
            frag_path, num_frag = fragmentar(texto_limpo, nome_base, idx)
            pagina['frag_dir'] = str(frag_path)
            pagina['fragmentos'] = num_frag
            log(f'Fragmentos: {num_frag} | Tipo: {tipo_real} | Score: {score_real}')

        paginas_processadas.append(pagina)

        # ================================================================
        # PASSO 7: Deep Crawl (se não for shallow e página aprovada)
        # ================================================================
        if not shallow and aprovado_final and texto_limpo.strip() and len(texto_limpo) > 2000:
            log(f'--- PASSO 7/8: Deep Crawl [{idx}] ---')
            paginas_deep = rastrear_profundidade(
                html, url, consulta, nome_base, len(paginas_processadas) + 1,
                max_paginas=MAX_DEEP_PAGES, max_profundidade=DEEP_MAX_DEPTH,
                visitados=visitados_global, dry_run=dry_run
            )
            if paginas_deep:
                log(f'DeepCrawl: {len(paginas_deep)} paginas adicionais', 'DEEP')
                paginas_processadas.extend(paginas_deep)

        print()

    if not paginas_processadas:
        erro('Nenhuma pagina foi processada com sucesso.')
        return False

    # ================================================================
    # PASSO 8: Narrativa + KG
    # ================================================================
    log('--- PASSO 8/8: Gerando Narrativa ---')
    narr_path = gerar_narrativa_v2(consulta, resultados[:15], paginas_processadas)

    if dry_run:
        log(f'[DRY-RUN] Narrativa: {narr_path}')
        log(f'[DRY-RUN] {sum(p["fragmentos"] for p in paginas_processadas)} fragmentos')
        log(f'[DRY-RUN] KG NAO alterado')
        return True

    log('--- Registrando no KG ---')
    return aprender_no_kg_v2(consulta, resultados[:15], paginas_processadas, narr_path, auto)


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    auto = '--auto' in args and args.remove('--auto') or False
    dry_run = '--dry-run' in args and args.remove('--dry-run') or False
    urls_only = '--urls-only' in args and args.remove('--urls-only') or False
    shallow = '--shallow' in args and args.remove('--shallow') or False

    consulta = ' '.join(args).strip()
    if not consulta:
        print('ERRO: Informe uma consulta.')
        print(__doc__)
        sys.exit(1)

    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(FRAG_DIR, exist_ok=True)
    os.makedirs(NARRATIVE_DIR, exist_ok=True)

    sucesso = pipeline_v2(consulta, auto=auto, dry_run=dry_run, urls_only=urls_only, shallow=shallow)
    sys.exit(0 if sucesso else 1)
