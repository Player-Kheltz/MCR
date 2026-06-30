"""Modulo: KnowledgeGraph - Gerenciamento de conhecimento do MCR-DevIA.
Knowledge Graph multi-arquivo: cada contexto em arquivo separado + master index.
- Carregamento lazy: so le ctx files sob demanda
- Salvamento fragmentado: so escreve ctx alterados
- Master index: knowledge.json mantido para compatibilidade (contem metadados)
"""
import os, json, re, hashlib, math, urllib.request, time as _time
from stop_words import STOP_BUSCA

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SANDBOX = os.path.join(BASE, 'sandbox')
KG_DIR = os.path.join(SANDBOX, '.mcr_devia', 'kg')
MASTER_PATH = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')

OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')

_embedding_cache_kg = {}
_EMBED_MODEL = 'nomic-embed-text:latest'

def _cosine_similaridade(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0: return 0.0
    return dot / (na * nb)

def _gerar_embedding_kg(texto):
    if texto in _embedding_cache_kg:
        return _embedding_cache_kg[texto]
    try:
        dados = json.dumps({'model': _EMBED_MODEL, 'prompt': texto}).encode()
        req = urllib.request.Request(
            f'{OLLAMA_URL}/api/embeddings', data=dados,
            headers={'Content-Type': 'application/json'}
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
        emb = resp.get('embedding')
        if emb: _embedding_cache_kg[texto] = emb
        return emb
    except Exception: return None

def init_module(contexto):
    kg = KnowledgeGraph()
    contexto['kg'] = kg
    return 'kg', kg


class KnowledgeGraph:
    """Graph de conhecimento multi-arquivo: cada ctx em arquivo separado."""
    
    def __init__(self):
        self.master_path = MASTER_PATH
        self.kg_dir = KG_DIR
        self._ctx_cache = {}        # {ctx: [lessons]} — ctxs carregados
        self._dirty_ctxs = set()    # ctxs que precisam ser salvos
        self._all_loaded = False    # lazy: so carrega tudo quando necessario
        self.data = self._load()
    
    # ===== CARREGAMENTO =====
    
    def _load(self):
        """Carrega master index. Ctx files sao carregados lazy."""
        # Primeira execucao: criar estrutura
        if not os.path.exists(self.kg_dir):
            return self._migrar_do_legado()
        
        master = self._ler_master()
        os.makedirs(self.kg_dir, exist_ok=True)
        return {
            'versoes': master.get('versoes', 1),
            'licoes': [],  # preenchido lazy
            'index': master.get('index', {}),
            'metricas': master.get('metricas', {'licoes':0,'usos':0,'geracoes':0,'compilacoes':0}),
        }
    
    def _ler_master(self):
        """Le o master index do knowledge.json."""
        path = self.master_path
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass
        return {}
    
    def _carregar_tudo(self):
        """Carrega TODOS os ctxs (lazy full load)."""
        if self._all_loaded:
            return
        self._all_loaded = True
        self.data['licoes'] = []
        if not os.path.exists(self.kg_dir):
            return
        for fname in sorted(os.listdir(self.kg_dir)):
            if fname.endswith('.json') and fname != 'master.json':
                ctx = fname[:-5]
                lessons = self._carregar_ctx(ctx)
                self.data['licoes'].extend(lessons)
                self._ctx_cache[ctx] = lessons
        # Se nao achou nada no kg_dir, tenta master como fallback
        if not self.data['licoes']:
            master = self._ler_master()
            for l in master.get('licoes', []):
                self.data['licoes'].append(l)
                ctx = l.get('ctx', 'geral')
                self._ctx_cache.setdefault(ctx, []).append(l)
    
    def _carregar_ctx(self, ctx):
        """Carrega um ctx especifico do arquivo."""
        if ctx in self._ctx_cache:
            return self._ctx_cache[ctx]
        path = os.path.join(self.kg_dir, f'{ctx}.json')
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    lessons = data.get('licoes', [])
                    self._ctx_cache[ctx] = lessons
                    return lessons
            except (FileNotFoundError, json.JSONDecodeError):
                pass
        self._ctx_cache[ctx] = []
        return []
    
    def _get_licoes(self):
        """Retorna todas as licoes (carrega lazy se necessario)."""
        if not self._all_loaded:
            self._carregar_tudo()
        return self.data['licoes']
    
    # ===== PERSISTENCIA =====
    
    def salvar(self):
        """Salva master index + ctxs alterados.
        So escreve arquivos que mudaram desde o ultimo save."""
        # Garante que tudo esta carregado antes de salvar
        licoes = self._get_licoes()
        
        # Atualiza metricas
        self.data['versoes'] = self.data.get('versoes', 1) + 1
        self.data['metricas']['licoes'] = len(licoes)
        
        # Agrupa licoes por ctx e salva so os alterados
        ctxs_atuais = {}
        for l in licoes:
            ctx = l.get('ctx', 'geral')
            ctxs_atuais.setdefault(ctx, []).append(l)
        
        # Salva ctxs sujos
        for ctx in set(list(self._dirty_ctxs) + list(ctxs_atuais.keys())):
            ctx_path = os.path.join(self.kg_dir, f'{ctx}.json')
            try:
                with open(ctx_path, 'w', encoding='utf-8') as f:
                    json.dump({'ctx': ctx, 'licoes': ctxs_atuais.get(ctx, [])},
                              f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f'[KG] Erro ao salvar ctx {ctx}: {e}')
        
        # Salva master index (knowledge.json para compatibilidade)
        try:
            with open(self.master_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'versoes': self.data['versoes'],
                    'metricas': self.data['metricas'],
                    'index': self.data.get('index', {}),
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f'[KG] Erro ao salvar master: {e}')
        
        self._dirty_ctxs.clear()
    
    def _migrar_do_legado(self):
        """Migracao unica: separa knowledge.json em ctx files."""
        os.makedirs(self.kg_dir, exist_ok=True)
        dados_iniciais = self._licoes_iniciais()
        
        # Tenta ler do legado
        if os.path.exists(self.master_path):
            try:
                with open(self.master_path, 'r', encoding='utf-8') as f:
                    dados_iniciais = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass
        
        # Agrupa por ctx e salva individualmente
        licoes = dados_iniciais.get('licoes', [])
        ctx_groups = {}
        for l in licoes:
            ctx = l.get('ctx', 'geral')
            ctx_groups.setdefault(ctx, []).append(l)
        
        for ctx, lessons in ctx_groups.items():
            ctx_path = os.path.join(self.kg_dir, f'{ctx}.json')
            with open(ctx_path, 'w', encoding='utf-8') as f:
                json.dump({'ctx': ctx, 'licoes': lessons}, f, ensure_ascii=False, indent=2)
        
        # Salva master index compacto
        with open(self.master_path, 'w', encoding='utf-8') as f:
            json.dump({
                'versoes': dados_iniciais.get('versoes', 1),
                'metricas': dados_iniciais.get('metricas', {'licoes': len(licoes)}),
                'index': dados_iniciais.get('index', {}),
            }, f, ensure_ascii=False, indent=2)
        
        print(f'[KG] Migrado: {len(licoes)} lessons em {len(ctx_groups)} contextos')
        return {
            'versoes': dados_iniciais.get('versoes', 1),
            'licoes': licoes,
            'index': dados_iniciais.get('index', {}),
            'metricas': dados_iniciais.get('metricas', {'licoes': len(licoes)}),
        }
    
    def _licoes_iniciais(self):
        return {
            "versoes": 1,
            "licoes": [
                {'id':'L001','erro':'LNK2001 __std_*','causa':'ABI mismatch','solucao':'Usar VS 2026','ctx':'compilar'},
                {'id':'L002','erro':'D9002 /std:c++latest','causa':'stdcpp23','solucao':'stdcpp20','ctx':'compilar'},
                {'id':'L003','erro':'string_view::contains','causa':'C++23','solucao':'find()!=npos','ctx':'compilar'},
            ],
            "index": {},
            "metricas": {"licoes": 3, "usos": 0, "geracoes": 0, "compilacoes": 0},
            "lessons": []
        }
    
    # ===== BUSCA =====
    
    def buscar(self, texto, max_r=5, incluir_inativos=False, incluir_benchmark=False):
        palavras = set(re.findall(r'\w+', texto.lower())) - STOP_BUSCA
        if any(p in texto.lower() for p in ['benchmark','stress','perf_test','performance']):
            incluir_benchmark = True
        
        licoes = self._get_licoes()
        scores = []
        for l in licoes:
            if not incluir_inativos and l.get('inactive', False): continue
            if not incluir_benchmark and l.get('tipo') == 'benchmark': continue
            alvo = l['erro'].lower() + ' ' + l.get('causa','').lower() + ' ' + l['solucao'].lower()
            score = 0
            for p in palavras:
                if len(p) < 3: continue
                if p in alvo:
                    if p in l['erro'].lower(): score += 5
                    elif p in l.get('ctx','').lower(): score += 4
                    elif p in l.get('causa','').lower(): score += 3
                    else: score += 2
            if score > 0: scores.append((score, l))
        scores.sort(key=lambda x: -x[0])
        return [s[1] for s in scores]
    
    def buscar_por_embedding(self, texto, n=3, incluir_benchmark=False):
        if any(p in texto.lower() for p in ['benchmark','stress','perf_test','performance']):
            incluir_benchmark = True
        emb = _gerar_embedding_kg(texto)
        if not emb: return self.buscar(texto, n)
        
        licoes = self._get_licoes()
        scores = []
        for l in licoes:
            if 'embedding' not in l: continue
            if l.get('inactive', False): continue
            if not incluir_benchmark and l.get('tipo') == 'benchmark': continue
            score = _cosine_similaridade(emb, l['embedding'])
            if score > 0: scores.append((score, l))
        scores.sort(key=lambda x: -x[0])
        return [s[1] for s in scores]

    def buscar_expandido(self, texto, max_r=15):
        """Busca expandida: keyword + embedding + fuzzy + ctxs relacionados.
        
        Usado pelo Modo Offline Turbinado para maximizar o contexto interno
        sem depender de internet.
        
        Args:
            texto: str, termos de busca
            max_r: int, maximo de resultados (padrao 15, maior que buscar())
        
        Returns:
            list[dict]: lessons encontradas, ordenadas por relevancia
        """
        from difflib import SequenceMatcher as _SM
        
        licoes = self._get_licoes()
        palavras = set(re.findall(r'\w+', texto.lower())) - STOP_BUSCA
        
        # 1. Keyword scoring (como buscar())
        scores = {}
        for l in licoes:
            if l.get('inactive', False): continue
            if l.get('tipo') == 'benchmark': continue
            
            alvo = (
                l.get('erro','').lower() + ' ' +
                l.get('causa','').lower() + ' ' +
                l.get('solucao','').lower() + ' ' +
                l.get('ctx','').lower()
            )
            score = 0
            for p in palavras:
                if len(p) < 3: continue
                if p in alvo:
                    score += 5 if p in l.get('erro','').lower() else 2
                # Fuzzy match para palavras com 4+ chars
                elif len(p) >= 4:
                    for palavra_alvo in alvo.split():
                        if len(palavra_alvo) >= 4:
                            sim = _SM(None, p, palavra_alvo).ratio()
                            if sim > 0.75:
                                score += 1
                                break
            if score > 0:
                scores[l.get('id', '?')] = (score, l)
        
        # 2. Expansao por ctx: se achou lessons de um ctx, puxa mais do mesmo ctx
        ctxs_encontrados = set()
        for l in scores.values():
            ctx = l[1].get('ctx', '')
            if ctx:
                ctxs_encontrados.add(ctx)
        
        for ctx in ctxs_encontrados:
            for l in licoes:
                if l.get('ctx') == ctx and l.get('id') not in scores:
                    if not l.get('inactive'):
                        scores[l.get('id', '?')] = (1.0, l)  # peso baixo mas inclui
        
        # 3. Ordena e retorna
        ordenados = sorted(scores.values(), key=lambda x: -x[0])
        return [s[1] for s in ordenados]
    
    # ===== APRENDIZADO =====
    
    def aprender(self, erro, causa, solucao, ctx='geral', tipo='dominio', time_sensitive=False):
        """Registra aprendizado — salva APENAS o ctx alterado."""
        licoes = self._get_licoes()
        lid = f'L{len(licoes)+1:04d}'
        lesson = {
            'id': lid, 'erro': erro, 'causa': causa,
            'solucao': solucao, 'ctx': ctx, 'tipo': tipo, 'usos': 0,
            'timestamp': _time.time(), 'time_sensitive': time_sensitive,
        }
        try:
            emb = _gerar_embedding_kg(erro + ' ' + causa)
            if emb: lesson['embedding'] = emb
        except Exception:
            pass
        self.data['licoes'].append(lesson)
        self._ctx_cache.setdefault(ctx, []).append(lesson)
        self._dirty_ctxs.add(ctx)
        # Salva imediatamente (so o ctx alterado)
        self.salvar()
    
    def atualizar_lesson(self, lesson_id, novos_campos):
        licoes = self._get_licoes()
        for l in licoes:
            if l.get('id') == lesson_id:
                ctx_antigo = l.get('ctx', 'geral')
                l.update(novos_campos)
                l['timestamp'] = _time.time()
                if 'solucao' in novos_campos:
                    try:
                        emb = _gerar_embedding_kg(l.get('erro','') + ' ' + novos_campos.get('solucao',''))
                        if emb: l['embedding'] = emb
                    except Exception:
                        pass
                self._dirty_ctxs.add(ctx_antigo)
                if l.get('ctx') and l['ctx'] != ctx_antigo:
                    self._dirty_ctxs.add(l['ctx'])
                self.salvar()
                return True
        return False
    
    def purgar(self, manter_ctxs=None):
        if manter_ctxs is None:
            manter_ctxs = set()
            for l in self._get_licoes():
                ctx = l.get('ctx', '')
                if ctx and not l.get('inactive', False): manter_ctxs.add(ctx)
            if not manter_ctxs: manter_ctxs = {'identidade'}
        count = 0
        for l in self._get_licoes():
            lid = l.get('id', '')
            if lid.startswith('L') and len(lid) <= 5 and int(lid[1:]) <= 100: continue
            ctx = l.get('ctx', 'geral')
            if ctx in manter_ctxs: continue
            if ctx in ('weblearn','learning_scan','weblearn_permanente','pipeline_busca'):
                if not l.get('inactive', False):
                    l['inactive'] = True
                    self._dirty_ctxs.add(ctx)
                    count += 1
        if count:
            self.salvar()
    
    def lessons_stale(self, idade_max_dias=7, time_sensitive_only=True):
        agora = _time.time()
        limite = agora - (idade_max_dias * 86400)
        stale = []
        for l in self._get_licoes():
            ts = l.get('timestamp', 0)
            if ts < limite:
                if time_sensitive_only and not l.get('time_sensitive', False): continue
                stale.append(l)
        return stale
    
    def gerar_licoes(self, dominio, quantidade=5):
        try:
            from modulos.util import gerar as _gerar_k
        except ImportError:
            print(f'[KG] gerar_licoes: router nao disponivel')
            return 0
        temas = {
            'mcr': ['SPA','SHC','Dominios Elementais','Canary','OTClient','Eridanus','Sistema de Progressao','Habilidades Contextuais'],
            'codigo': ['monster','npc','item','spell','quest','creature','event','action','talkaction','movement'],
        }
        temas_dominio = temas.get(dominio, [dominio])
        contagem = 0
        import random
        random.shuffle(temas_dominio)
        for tema in temas_dominio:
            prompt = (
                f"Crie uma licao sobre '{tema}' para o projeto MCR (Tibia/Canary).\n"
                f"Responda no formato:\nPERGUNTA: (pergunta sobre o tema)\nRESPOSTA: (explicacao em 2-3 frases)\nCATEGORIA: {dominio}\n"
            )
            try:
                resp = _gerar_k(prompt, 0.3, "fast") or ""
                if resp and len(resp) > 50:
                    self.aprender(erro=f"O que e {tema}?", causa=f"Lesson gerada para dominio: {dominio}",
                                  solucao=resp.strip(), ctx=f"licao_{dominio}")
                    contagem += 1
                    print(f'  [KG] Licao gerada: {tema}')
            except (FileNotFoundError, json.JSONDecodeError):
                pass
        return contagem
    
    def listar_ctxs(self):
        """Retorna lista de contextos disponiveis sem carregar licoes."""
        ctxs = {}
        if os.path.exists(self.kg_dir):
            for fname in sorted(os.listdir(self.kg_dir)):
                if fname.endswith('.json') and fname != 'master.json':
                    ctx = fname[:-5]
                    try:
                        with open(os.path.join(self.kg_dir, fname), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            ctxs[ctx] = len(data.get('licoes', []))
                    except (FileNotFoundError, json.JSONDecodeError):
                        pass
        if not ctxs:
            # Fallback: master index
            ctxs = master.get('contexts', {})
        return ctxs
