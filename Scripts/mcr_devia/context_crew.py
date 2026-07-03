"""
CONTEXT CREW V3 — Leitor universal (LGPD OK: so le, nunca edita, sem dados pessoais)
Busca contexto em: KG, WebLearn, Docs, Codigo Fonte, Web.
Tudo que encontra vira contexto. Nunca modifica nada.
"""
import os, json, re, time, hashlib, urllib.request, threading, concurrent.futures

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SANDBOX = os.path.join(BASE, 'sandbox')
KG_PATH = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')  # master index
KG_DIR = os.path.join(SANDBOX, '.mcr_devia', 'kg')  # ctx files
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
    except ImportError:
        pass

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
        except FileNotFoundError:
            pass
    
    def _carregar_cache(self):
        if not os.path.exists(CACHE_PATH): return
        try:
            with open(CACHE_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        item = json.loads(line)
                        if item.get('v', 0) == self._versao_kg:
                            self._cache[item['h']] = item
                    except KeyError:
                        pass
                    except:
                        pass
        except Exception:
            pass
    
    def _salvar_cache(self, h, pergunta, resultado, fonte, n_docs):
        try:
            with open(CACHE_PATH, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    'h': h, 'ts': time.time(), 'p': pergunta,
                    'r': resultado, 'n': n_docs, 'v': self._versao_kg, 'f': fonte
                }, ensure_ascii=False) + '\n')
        except Exception as e:
            pass
    
    def _extrair_termos(self, texto, max_t=8):
        palavras = re.findall(r'\b[a-zA-Z]{3,}\b', texto.lower())
        return list(dict.fromkeys(p for p in palavras if p not in _STOP))
    
    def _hash(self, q):
        return hashlib.md5(q.lower().encode()).hexdigest()
    
    # === FONTES DE CONHECIMENTO ===
    
    def _buscar_kg(self, termos, max_r=5):
        """Busca no KG multi-arquivo: le de kg/ diretorio."""
        if not os.path.exists(KG_DIR): return []
        try:
            resultados = []
            for fname in sorted(os.listdir(KG_DIR)):
                if not fname.endswith('.json') or fname == 'master.json':
                    continue
                try:
                    with open(os.path.join(KG_DIR, fname), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except:
                    continue
                for l in data.get('licoes', []):
                    if l.get('inactive'): continue
                    alvo = (l.get('erro','') + ' ' + l.get('solucao','') + ' ' + l.get('ctx','')).lower()
                    score = sum(1 for t in termos if t in alvo)
                    if score > 0:
                        ctx = l.get('ctx', 'geral')
                        peso = {'identidade':1.0,'conceito_codigo':0.9,'bugfix':0.8,'feature':0.75,
                                'weblearn':0.5,'v12_genero':0.4}.get(ctx, 0.3)
                        resultados.append((score * peso, l.get('solucao',''), f'KG:{ctx}:{peso:.1f}'))
                        resultados.sort(key=lambda x: -x[0])
                        return [(r[1], r[2]) for r in resultados]
        except Exception:
            pass
    
    def _buscar_weblearn(self, termos, max_r=5):
        wl_dir = os.path.join(SANDBOX, '.mcr_devia', 'weblearn')
        if not os.path.exists(wl_dir): return []
        resultados = []
        try:
            for f in sorted(os.listdir(wl_dir)):
                if not f.endswith('.json'): continue
                with open(os.path.join(wl_dir, f), 'r', encoding='utf-8') as fh:
                    item = json.load(fh)
                txt = (str(item.get('titulo','')) + ' ' + str(item.get('texto',''))).lower()
                score = sum(1 for t in termos if t in txt)
                if score > 0:
                    resultados.append((score, item.get('texto',''), 'WebLearn:0.5'))
        except TypeError:
            pass
        resultados.sort(key=lambda x: -x[0])
        return [(r[1], r[2]) for r in resultados]
    
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
                                resultados.append((score, p, f'Docs:{rel}'))
                    except FileNotFoundError:
                        pass
        except Exception:
            pass
        resultados.sort(key=lambda x: -x[0])
        return [(r[1], r[2]) for r in resultados]
    
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
                for t in termos:
                    for palavra, arquivos in indice.items():
                        if t.lower() in palavra.lower():
                            for arq in arquivos:
                                if arq not in arquivos_para_ler:
                                    arquivos_para_ler.add(arq)
                # Le apenas os arquivos encontrados
                for fpath in arquivos_para_ler:
                    try:
                        if os.path.getsize(fpath) > 256000: continue
                        with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                            lines = fh.readlines()
                        for i, line in enumerate(lines):
                            line_lower = line.lower()
                            score = sum(1 for t in termos if t in line_lower)
                            if score > 0 and len(line.strip()) > 20:
                                ctx_antes = ''.join(lines[max(0,i-1):i])
                                ctx_depois = ''.join(lines[i:min(len(lines),i+2)])
                                trecho = ctx_antes + line + ctx_depois
                                rel = os.path.relpath(fpath, BASE)
                                resultados.append((score, trecho, f'Code:{rel}:L{i+1}'))
                                break
                    except Exception:
                        pass
                if resultados:
                    resultados.sort(key=lambda x: -x[0])
                    return [(r[1], r[2]) for r in resultados]
            except Exception:
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
                            for i, line in enumerate(lines):
                                line_lower = line.lower()
                                score = sum(1 for t in termos if t in line_lower)
                                if score > 0 and len(line.strip()) > 20:
                                    ctx_antes = ''.join(lines[max(0,i-1):i])
                                    ctx_depois = ''.join(lines[i:min(len(lines),i+2)])
                                    trecho = ctx_antes + line + ctx_depois
                                    rel = os.path.relpath(fpath, BASE)
                                    resultados.append((score, trecho, f'Code:{rel}:L{i+1}'))
                                    break
                        except Exception as e:
                            pass
        
            except Exception:
                pass
        
        resultados.sort(key=lambda x: -x[0])
        return [(r[1], r[2]) for r in resultados]
    
    def _buscar_weblearn_cache(self, termos, max_r=5):
        """Le conteudos baixados da Web pelo weblearn para estudo.
        Os arquivos estao em sandbox/.mcr_devia/weblearn/"""
        wl_dir = os.path.join(SANDBOX, '.mcr_devia', 'weblearn')
        if not os.path.exists(wl_dir): return []
        resultados = []
        try:
            for f in sorted(os.listdir(wl_dir)):
                if not f.endswith('.json'): continue
                with open(os.path.join(wl_dir, f), 'r', encoding='utf-8') as fh:
                    item = json.load(fh)
                txt = (str(item.get('titulo','')) + ' ' + str(item.get('texto',''))).lower()
                score = sum(1 for t in termos if t in txt)
                if score > 0:
                    resultados.append((score, item.get('texto',''), 'WebLearn:' + f))
        except ValueError:
            pass
        resultados.sort(key=lambda x: -x[0])
        return [(r[1], r[2]) for r in resultados]
    
    def _buscar_web(self, termos, max_r=3):
        """Busca na web usando DuckDuckGo via IA.buscar_web()."""
        from modulos.ia import IA
        resultados = []
        consulta = ' '.join(termos)
        try:
            ia = IA()
            resultado = ia.buscar_web(consulta, max_resultados=max_r)
            if resultado and len(resultado) > 20:
                resultados.append((3, resultado, 'Web:IA'))
        except Exception:
            pass
        # Fallback: Wikipedia API se DuckDuckGo falhar
        if not resultados:
            try:
                consulta_wiki = '+'.join(termos)
                url = f'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={consulta_wiki}&format=json&srlimit={max_r}'
                req = urllib.request.Request(url, headers={'User-Agent': 'MCR-DevIA/1.0'})
                resp = urllib.request.urlopen(req, timeout=10)
                data = json.loads(resp.read().decode('utf-8'))
                for item in data.get('query', {}).get('search', []):
                    titulo = item.get('title', '')
                    snippet = re.sub(r'<[^>]+>', '', item.get('snippet', ''))
                    resultados.append((2, f'{titulo}: {snippet}', f'Web:{titulo}'))
            except KeyError:
                pass
        return [(r[1], r[2]) for r in resultados]
    
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
            consulta = ' '.join(termos)
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
                        except Exception as e:
                            pass
            except Exception as e:
                print(f'  [ContextCrew] WebLearn ERRO: {e}')
        
        if not todas_fontes:
            return ""
        
        # Monta contexto com marcadores de fonte e prioridade
        contexto = '\n'.join(f'[{fonte}] {texto}' for fonte, texto in todas_fontes)
        
        self._cache[h] = {'r': contexto, 'n': len(todas_fontes)}
        self._salvar_cache(h, pergunta, contexto, 'multi', len(todas_fontes))
        
        return contexto
    
    def _heuristicas_quebra(self, texto):
        """Tenta quebrar texto por pontuacao logica. Retorna lista de partes."""
        # 1. Tenta quebrar por ? primeiro (perguntas multiplas)
        partes = re.split(r'\?\s*', texto)
        partes = [p.strip() + '?' for p in partes if len(p.strip()) > 15]
        if len(partes) > 1:
            return partes
        
        # 2. Tenta quebrar por ": o que", ": como", ": qual" (sub-perguntas apos dois-pontos)
        # "Explique X: o que e A, como funciona B, o que C mede, e como D" 
        # -> ["Explique X", "o que e A", "como funciona B", "o que C mede", "e como D"]
        if ': ' in texto:
            antes, depois = texto.split(': ', 1)
            # Depois dos dois-pontos, tenta quebrar por virgula onde cada parte
            # comeca com palavra interrogativa
            sub_partes = re.split(r'(?=,\s*(?:o que|como|qual|quais|onde|quando|por que))', depois)
            sub_partes = [p.strip().lstrip(',').strip() for p in sub_partes if len(p.strip()) > 10]
            resultado = [antes.strip()]
            if antes.strip():
                resultado = [antes.strip()]
            else:
                resultado = []
            resultado.extend(sub_partes)
            resultado = [p for p in resultado if len(p) > 15]
            if len(resultado) > 2:
                return resultado
            # Fallback: se nao quebrou por virgula, retorna 2 partes (antes + depois)
            if antes.strip() and depois.strip():
                resultado2 = [antes.strip(), depois.strip()]
                resultado2 = [p for p in resultado2 if len(p) > 20]
                if len(resultado2) > 1:
                    return resultado2
        
        # 3. Tenta quebrar por conectores "e", "mas", "ou", "tambem"
        partes = re.split(r'(?:,\s*(?:e|mas|ou)\s*|\s+e\s+tamb[ée]m\s+)', texto)
        partes = [p.strip() for p in partes if len(p.strip()) > 20]
        if len(partes) > 1:
            return partes
        
        # 4. Tenta quebrar por "." seguido de maiuscula
        partes = re.split(r'\.\s+(?=[A-Z])', texto)
        partes = [p.strip() for p in partes if len(p.strip()) > 20]
        if len(partes) > 1:
            return partes
        
        # 5. Tenta quebrar por virgulas em texto longo
        if len(texto) > 300:
            partes = re.split(r',\s*', texto)
            partes = [p.strip() for p in partes if len(p.strip()) > 30]
            if len(partes) > 2:
                return partes
        
        return [texto]
    
    def fragmentar_recursivo(self, texto, profundidade=0, max_depth=6):
        """Fragmenta recursivamente até encontrar padroes brutos (baixa entropia).
        
        Um padrao bruto e definido por:
        - Entropia < 0.4 (PatternEngine)
        - Tokens < 100
        - Tamanho < 500 chars
        
        Args:
            texto: str, texto a fragmentar
            profundidade: int, nivel atual de profundidade
            max_depth: int, maximo de niveis
        
        Returns:
            dict: {texto, entropia, tokens_count, bruto, filhos, profundidade}
                  filhos = None se for bruto, senao lista de sub-arvores
        """
        from modulos.pattern_engine import PatternEngine
        _pe = PatternEngine()
        
        # Mede entropia
        tokens = _pe.tokenizar(texto, 'texto')
        padroes = _pe.extrair_padroes(tokens)
        entropia = padroes.get('entropia', 0.5)
        tokens_count = len(tokens)
        tamanho = len(texto)
        
        # Verifica se e padrao bruto
        e_bruto = (entropia < 0.3 and tokens_count < 50) or profundidade >= max_depth
        if e_bruto and tamanho < 50:
            return {
                'texto': texto,
                'entropia': round(entropia, 3),
                'tokens_count': tokens_count,
                'bruto': True,
                'profundidade': profundidade,
                'filhos': None,
            }
        
        # Tenta quebrar ANTES de decidir se e bruto
        # (textos curtos podem conter multiplas perguntas)
        partes = self._heuristicas_quebra(texto)
        
        if len(partes) <= 1:
            # Nao conseguiu quebrar — trata como bruto
            return {
                'texto': texto,
                'entropia': round(entropia, 3),
                'tokens_count': tokens_count,
                'bruto': True,
                'profundidade': profundidade,
                'filhos': None,
            }
        
        print(f'  [Fragmentar] Depth {profundidade}: {len(partes)} partes (entropia {entropia:.3f})')
        
        filhos = []
        for i, parte in enumerate(partes):
            sub = self.fragmentar_recursivo(parte, profundidade + 1, max_depth)
            sub['indice'] = i
            filhos.append(sub)
        
        return {
            'texto': texto,
            'entropia': round(entropia, 3),
            'tokens_count': tokens_count,
            'bruto': False,
            'profundidade': profundidade,
            'filhos': filhos,
        }
    
    def fragmentar(self, texto, max_depth=6):
        """Interface publica: retorna arvore de fragmentacao recursiva.
        
        Returns:
            dict: arvore completa com todos os niveis
        """
        return self.fragmentar_recursivo(texto, 0, max_depth)
    
    def extrair_folhas(self, arvore):
        """Extrai todas as folhas (padroes brutos) de uma arvore de fragmentacao.
        
        Returns:
            list[dict]: [{texto, entropia, profundidade, caminho}]
        """
        folhas = []
        def _visitar(no, caminho=""):
            if no.get('bruto') or not no.get('filhos'):
                folhas.append({
                    'texto': no['texto'],
                    'entropia': no.get('entropia', 0.5),
                    'profundidade': no.get('profundidade', 0),
                    'caminho': caminho + str(no.get('indice', 0)),
                })
            else:
                for f in (no.get('filhos') or []):
                    _visitar(f, caminho + str(no.get('indice', 0)) + '.')
        _visitar(arvore, '')
        return folhas
