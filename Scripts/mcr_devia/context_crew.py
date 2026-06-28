"""
CONTEXT CREW V3 — Leitor universal (LGPD OK: so le, nunca edita, sem dados pessoais)
Busca contexto em: KG, WebLearn, Docs, Codigo Fonte, Web.
Tudo que encontra vira contexto. Nunca modifica nada.
"""
import os, json, re, time, hashlib, urllib.request, threading, concurrent.futures

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SANDBOX = os.path.join(BASE, 'sandbox')
KG_PATH = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')
CACHE_PATH = os.path.join(SANDBOX, '.mcr_devia', 'context_crew_cache.jsonl')
DOCS_DIR = os.path.join(BASE, 'docs')
SRC_DIR = os.path.join(BASE, 'Canary', 'src')
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/generate')
from stop_words import STOP_V12 as _STOP

def _fast(prompt, temp=0.1):
    """Usa router padronizado do MCR-DevIA em vez de hardcoded."""
    try:
        from modulos.util import fast as _util_fast
        return _util_fast(prompt, temp, "fast") or None
    except: return None

class ContextCrew:
    """Leitor universal de contexto. So le, nao edita. Respeita LGPD (sem dados pessoais)."""
    
    def __init__(self):
        self._cache = {}
        self._versao_kg = self._get_versao_kg()
        self._carregar_cache()
    
    def _get_versao_kg(self):
        try:
            with open(KG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f).get('versoes', 0)
        except: return 0
    
    def _carregar_cache(self):
        if not os.path.exists(CACHE_PATH): return
        try:
            with open(CACHE_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        item = json.loads(line)
                        if item.get('v', 0) == self._versao_kg:
                            self._cache[item['h']] = item
                    except: pass
        except: pass
    
    def _salvar_cache(self, h, pergunta, resultado, fonte, n_docs):
        try:
            with open(CACHE_PATH, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    'h': h, 'ts': time.time(), 'p': pergunta[:100],
                    'r': resultado[:300], 'n': n_docs, 'v': self._versao_kg, 'f': fonte
                }, ensure_ascii=False) + '\n')
        except: pass
    
    def _extrair_termos(self, texto, max_t=8):
        palavras = re.findall(r'\b[a-zA-Z]{3,}\b', texto.lower())
        return list(dict.fromkeys(p for p in palavras if p not in _STOP))[:max_t]
    
    def _hash(self, q):
        return hashlib.md5(q.lower().encode()).hexdigest()[:12]
    
    # === FONTES DE CONHECIMENTO ===
    
    def _buscar_kg(self, termos, max_r=5):
        if not os.path.exists(KG_PATH): return []
        try:
            with open(KG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            resultados = []
            for l in data.get('licoes', []):
                if l.get('inactive'): continue
                alvo = (l.get('erro','') + ' ' + l.get('solucao','') + ' ' + l.get('ctx','')).lower()
                score = sum(1 for t in termos if t in alvo)
                if score > 0:
                    ctx = l.get('ctx', 'geral')
                    peso = {'identidade':1.0,'conceito_codigo':0.9,'bugfix':0.8,'feature':0.75,
                            'weblearn':0.5,'v12_genero':0.4}.get(ctx, 0.3)
                    resultados.append((score * peso, l.get('solucao','')[:300], f'KG:{ctx}:{peso:.1f}'))
            resultados.sort(key=lambda x: -x[0])
            return [(r[1], r[2]) for r in resultados[:max_r]]
        except: return []
    
    def _buscar_weblearn(self, termos, max_r=5):
        wl_dir = os.path.join(SANDBOX, '.mcr_devia', 'weblearn')
        if not os.path.exists(wl_dir): return []
        resultados = []
        try:
            for f in sorted(os.listdir(wl_dir))[:30]:
                if not f.endswith('.json'): continue
                with open(os.path.join(wl_dir, f), 'r', encoding='utf-8') as fh:
                    item = json.load(fh)
                txt = (str(item.get('titulo','')) + ' ' + str(item.get('texto',''))).lower()
                score = sum(1 for t in termos if t in txt)
                if score > 0:
                    resultados.append((score, item.get('texto','')[:300], 'WebLearn:0.5'))
        except: pass
        resultados.sort(key=lambda x: -x[0])
        return [(r[1], r[2]) for r in resultados[:max_r]]
    
    def _buscar_docs(self, termos, max_r=5):
        """Le arquivos .md de docs/ e extrai paragrafos relevantes."""
        if not os.path.exists(DOCS_DIR): return []
        resultados = []
        try:
            for root, dirs, files in os.walk(DOCS_DIR):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for f in files:
                    if not f.endswith('.md'): continue
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                            content = fh.read()
                        # Divide em paragrafos e busca
                        paragrafos = re.split(r'\n\s*\n', content)
                        for p in paragrafos:
                            p_lower = p.lower()
                            score = sum(1 for t in termos if t in p_lower)
                            if score > 0:
                                rel = os.path.relpath(fpath, BASE)
                                resultados.append((score, p[:300], f'Docs:{rel}'))
                    except: pass
        except: pass
        resultados.sort(key=lambda x: -x[0])
        return [(r[1], r[2]) for r in resultados[:max_r]]
    
    def _buscar_codigo(self, termos, max_r=8):
        """Grep usando INDICE do Watchdog (cache em arquivo). Fallback: varredura."""
        resultados = []
        
        # Tenta ler indice do watchdog (cache em arquivo)
        indice_path = os.path.join(SANDBOX, '.mcr_devia', 'indice_watchdog.json')
        if os.path.exists(indice_path):
            try:
                with open(indice_path, 'r', encoding='utf-8') as _f:
                    indice = json.load(_f)
                # Procura termos no indice
                arquivos_para_ler = set()
                for t in termos[:3]:
                    for palavra, arquivos in indice.items():
                        if t.lower() in palavra.lower():
                            for arq in arquivos[:3]:
                                if arq not in arquivos_para_ler:
                                    arquivos_para_ler.add(arq)
                # Le apenas os arquivos encontrados
                for fpath in arquivos_para_ler:
                    try:
                        if os.path.getsize(fpath) > 256000: continue
                        with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                            lines = fh.readlines()
                        for i, line in enumerate(lines[:100]):
                            line_lower = line.lower()
                            score = sum(1 for t in termos if t in line_lower)
                            if score > 0 and len(line.strip()) > 20:
                                ctx_antes = ''.join(lines[max(0,i-1):i])
                                ctx_depois = ''.join(lines[i:min(len(lines),i+2)])
                                trecho = ctx_antes + line + ctx_depois
                                rel = os.path.relpath(fpath, BASE)
                                resultados.append((score, trecho[:200], f'Code:{rel}:L{i+1}'))
                                break
                    except: pass
                if resultados:
                    resultados.sort(key=lambda x: -x[0])
                    return [(r[1], r[2]) for r in resultados[:max_r]]
            except:
                pass
        
        # Fallback: varredura direta
        
        # Diretorios para INCLUIR na busca (apenas codigo FONTE relevante)
        INCLUIR = [
            os.path.join(BASE, 'scripts'),
            os.path.join(BASE, 'docs'),
            os.path.join(BASE, 'sandbox'),
            os.path.join(BASE, 'Canary', 'src'),
            os.path.join(BASE, 'OTClient', 'src'),
        ]
        
        # Extensoes de interesse
        EXTENSOES = {'.py', '.h', '.hpp', '.cpp', '.lua', '.md', '.txt', '.json', '.xml'}
        
        for start_dir in INCLUIR:
            if not os.path.exists(start_dir):
                continue
            try:
                for root, dirs, files in os.walk(start_dir):
                    # Exclui diretorios problematicos
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in 
                              ('__pycache__', 'node_modules', 'vcpkg', '.opencode')]
                    
                    for f in files:
                        ext = os.path.splitext(f)[1].lower()
                        if ext not in EXTENSOES: continue
                        
                        fpath = os.path.join(root, f)
                        try:
                            if os.path.getsize(fpath) > 256000: continue  # Max 250KB
                            with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                                lines = fh.readlines()
                            for i, line in enumerate(lines[:100]):
                                line_lower = line.lower()
                                score = sum(1 for t in termos if t in line_lower)
                                if score > 0 and len(line.strip()) > 20:
                                    ctx_antes = ''.join(lines[max(0,i-1):i])
                                    ctx_depois = ''.join(lines[i:min(len(lines),i+2)])
                                    trecho = ctx_antes + line + ctx_depois
                                    rel = os.path.relpath(fpath, BASE)
                                    resultados.append((score, trecho[:200], f'Code:{rel}:L{i+1}'))
                                    break
                        except: pass
            except: pass
        
        resultados.sort(key=lambda x: -x[0])
        return [(r[1], r[2]) for r in resultados[:max_r]]
    
    def _buscar_weblearn_cache(self, termos, max_r=5):
        """Le conteudos baixados da Web pelo weblearn para estudo.
        Os arquivos estao em sandbox/.mcr_devia/weblearn/"""
        wl_dir = os.path.join(SANDBOX, '.mcr_devia', 'weblearn')
        if not os.path.exists(wl_dir): return []
        resultados = []
        try:
            for f in sorted(os.listdir(wl_dir))[:20]:
                if not f.endswith('.json'): continue
                with open(os.path.join(wl_dir, f), 'r', encoding='utf-8') as fh:
                    item = json.load(fh)
                txt = (str(item.get('titulo','')) + ' ' + str(item.get('texto',''))).lower()
                score = sum(1 for t in termos if t in txt)
                if score > 0:
                    resultados.append((score, item.get('texto','')[:300], 'WebLearn:' + f[:30]))
        except: pass
        resultados.sort(key=lambda x: -x[0])
        return [(r[1], r[2]) for r in resultados[:max_r]]
    
    def _buscar_web(self, termos, max_r=3):
        """WebFetch para buscar informacoes atualizadas (LGPD: sem dados pessoais)."""
        resultados = []
        consulta = '+'.join(termos[:3])
        urls = [
            f'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={consulta}&format=json&srlimit={max_r}',
        ]
        for url in urls:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'MCR-DevIA/1.0'})
                resp = urllib.request.urlopen(req, timeout=10)
                data = json.loads(resp.read().decode('utf-8'))
                for item in data.get('query', {}).get('search', [])[:max_r]:
                    titulo = item.get('title', '')
                    snippet = re.sub(r'<[^>]+>', '', item.get('snippet', ''))
                    resultados.append((2, f'{titulo}: {snippet[:200]}', f'Web:{titulo[:30]}'))
            except: pass
        return [(r[1], r[2]) for r in resultados[:max_r]]
    
    # === EXECUTAR ===
    
    def executar(self, pergunta):
        """Busca contexto em TODAS as fontes em PARALELO. Retorna o mais relevante."""
        termos = self._extrair_termos(pergunta)
        if not termos: return ""
        
        h = self._hash(pergunta)
        if h in self._cache:
            return self._cache[h].get('r', '')
        
        # Busca em todas as fontes EM PARALELO usando ThreadPoolExecutor
        todas_fontes = []
        fontes = [
            ('KG', self._buscar_kg, 5),
            ('WebLearn', self._buscar_weblearn, 5),
            ('Docs', self._buscar_docs, 3),
            ('Codigo', self._buscar_codigo, 3),
            ('WebLearnCache', self._buscar_weblearn_cache, 3),
            ('Web', self._buscar_web, 2),
        ]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futuros = {
                executor.submit(fn, termos, max_r): nome
                for nome, fn, max_r in fontes
            }
            for futuro in concurrent.futures.as_completed(futuros, timeout=15):
                nome = futuros[futuro]
                try:
                    resultados = futuro.result()
                    for texto, fonte in resultados:
                        todas_fontes.append((fonte, texto))
                except Exception as e:
                    pass  # Uma fonte falhar nao impede as outras
        
        # AUTO-WEBLEARN: se 0 resultados, dispara aprendizado
        if not todas_fontes:
            consulta = ' '.join(termos[:5])
            print(f'  [ContextCrew] Sem resultados — disparando WebLearn para: {consulta}')
            try:
                import subprocess as _sp
                kernel = os.path.join(os.path.dirname(__file__), 'MCR_DevIA-Kernel.py')
                _sp.run([sys.executable, kernel, 'weblearn', consulta, '--shallow'],
                       capture_output=True, text=True, timeout=120)
                # Tenta novamente apos weblearn
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    futuros2 = {
                        executor.submit(fn, termos, max_r): nome
                        for nome, fn, max_r in [('WebLearn', self._buscar_weblearn, 5),
                                                  ('WebLearnCache', self._buscar_weblearn_cache, 3)]
                    }
                    for futuro2 in concurrent.futures.as_completed(futuros2, timeout=15):
                        nome = futuros2[futuro2]
                        try:
                            resultados = futuro2.result()
                            for texto, fonte in resultados:
                                todas_fontes.append((fonte, texto))
                        except: pass
            except Exception as e:
                print(f'  [ContextCrew] WebLearn ERRO: {e}')
        
        if not todas_fontes:
            return ""
        
        # Monta contexto com marcadores de fonte e prioridade
        contexto = '\n'.join(f'[{fonte}] {texto}' for fonte, texto in todas_fontes)
        
        self._cache[h] = {'r': contexto, 'n': len(todas_fontes)}
        self._salvar_cache(h, pergunta, contexto, 'multi', len(todas_fontes))
        
        return contexto
