"""LessonsBuffer - Buffer de conhecimento antes de ir pro KG.
Evita duplicatas, contradicoes, e informacao falsa.
Contradicoes sao resolvidas automaticamente pelo ContextCrew."""
import os, json, time, hashlib, urllib.request
from modulos.util import fast as _util_fast

SANDBOX = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'sandbox'))
BUFFER_PATH = os.path.join(SANDBOX, '.mcr_devia', 'lessons_buffer.json')
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
EMBED_MODEL = 'nomic-embed-text:latest'
_embedding_cache_buf = {}

def _fast(prompt, temp=0.1):
    try:
        return _util_fast(prompt, temp, "fast") or None
    except: return None

def _gerar_embedding_buffer(texto):
    """Gera embedding para o buffer (cache proprio)."""
    if texto in _embedding_cache_buf:
        return _embedding_cache_buf[texto]
    if len(texto) < 10:
        return None
    try:
        dados = json.dumps({'model': EMBED_MODEL, 'prompt': texto[:500]}).encode()
        req = urllib.request.Request(
            f'{OLLAMA_URL}/api/embeddings', data=dados,
            headers={'Content-Type': 'application/json'}
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
        emb = resp.get('embedding')
        if emb:
            _embedding_cache_buf[texto] = emb
        return emb
    except Exception:
        return None

class LessonsBuffer:
    """Buffer de lessons. Contradicoes resolvidas automaticamente por IA."""
    
    def __init__(self, kg=None):
        self.kg = kg
        self._buffer = self._carregar()
    
    def _carregar(self):
        if os.path.exists(BUFFER_PATH):
            try:
                with open(BUFFER_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return {"lessons": [], "versao": 1}
    
    def _salvar(self):
        os.makedirs(os.path.dirname(BUFFER_PATH), exist_ok=True)
        with open(BUFFER_PATH, 'w', encoding='utf-8') as f:
            json.dump(self._buffer, f, ensure_ascii=False, indent=2)
    
    def adicionar(self, erro, causa, solucao, ctx='conhecimento', fonte=''):
        for l in self._buffer['lessons']:
            if l['erro'] == erro[:80] and l['ctx'] == ctx and l['solucao'] == solucao[:500]:
                return  # Exatamente igual, ignorar
        
        self._buffer['lessons'].append({
            'id': f'B{len(self._buffer["lessons"])+1:04d}',
            'erro': erro[:80], 'causa': causa[:200],
            'solucao': solucao[:500], 'ctx': ctx, 'fonte': fonte[:100],
            'ts': time.time(), 'status': 'pendente',
        })
        self._buffer['versao'] += 1
        self._salvar()
    
    def verificar_contradicoes(self):
        contradicoes = []
        lessons = self._buffer['lessons']
        for i, l1 in enumerate(lessons):
            for l2 in lessons[i+1:]:
                if l1['erro'] == l2['erro'] and l1['ctx'] == l2['ctx']:
                    if l1['solucao'] != l2['solucao']:
                        contradicoes.append((l1, l2))
                        l1['status'] = 'contradicao'
                        l2['status'] = 'contradicao'
        if contradicoes:
            self._salvar()
        return contradicoes
    
    def resolver_contradicoes(self):
        """Resolve contradicoes automaticamente usando IA.
        A IA consulta as duas versoes e decide qual e mais consistente."""
        lessons = self._buffer['lessons']
        resolvidas = 0
        
        # Remove rejeitados antigos
        self._buffer['lessons'] = [l for l in lessons if l['status'] != 'rejeitado']
        lessons = self._buffer['lessons']
        
        for i, l1 in enumerate(lessons):
            if l1['status'] != 'contradicao': continue
            for j, l2 in enumerate(lessons):
                if j <= i or l2['status'] != 'contradicao': continue
                if l1['erro'] == l2['erro'] and l1['ctx'] == l2['ctx']:
                    # IA decide qual é a verdade
                    decisao = _fast(
                        f'Duas fontes discordam sobre "{l1["erro"]}":\n'
                        f'Fonte A: {l1["solucao"][:200]}\n'
                        f'Fonte B: {l2["solucao"][:200]}\n\n'
                        f'Qual esta CORRETA? Responda apenas A ou B:',
                        0.1
                    ) or ''
                    
                    if 'A' in decisao.upper() and 'B' not in decisao.upper():
                        l1['status'] = 'verificado'
                        l2['status'] = 'rejeitado'
                        resolvidas += 1
                    elif 'B' in decisao.upper() and 'A' not in decisao.upper():
                        l1['status'] = 'rejeitado'
                        l2['status'] = 'verificado'
                        resolvidas += 1
                    # Se nao conseguiu decidir, ambos ficam como contradicao
        
        if resolvidas:
            self._salvar()
        return resolvidas
    
    def comitar(self):
        """Resolve contradicoes e comita no KG com batch embedding.
        
        Batch: em vez de N embeddings individuais, gera 1 embedding
        para o texto concatenado do lote inteiro. Reduz tempo de
        50 chamadas (106s) para 1 chamada (~2s).
        """
        if not self.kg: return 0
        
        # Resolve contradicoes primeiro
        self.resolver_contradicoes()
        
        count = 0
        restantes = []
        lessons_para_comitar = []
        
        for l in self._buffer['lessons']:
            if l['status'] == 'verificado' or l['status'] == 'pendente':
                lessons_para_comitar.append(l)
                count += 1
            elif l['status'] == 'contradicao':
                restantes.append(l)
            # 'rejeitado': descarta
        
        # Gera 1 embedding BATCH para todas as lessons do lote
        if lessons_para_comitar:
            texto_lote = ' '.join(f"{l['erro']} {l['causa']}" for l in lessons_para_comitar)
            embedding_lote = _gerar_embedding_buffer(texto_lote)
            
            for l in lessons_para_comitar:
                lid = f'L{len(self.kg.data["licoes"])+1:04d}'
                lesson = {
                    'id': lid, 'erro': l['erro'], 'causa': l['causa'],
                    'solucao': l['solucao'], 'ctx': l['ctx'], 'usos': 0
                }
                if embedding_lote:
                    lesson['embedding'] = embedding_lote  # mesmo embedding para o lote
                self.kg.data['licoes'].append(lesson)
            self.kg.salvar()
        
        self._buffer['lessons'] = restantes
        self._salvar()
        return count
    
    def estatisticas(self):
        total = len(self._buffer['lessons'])
        pendentes = sum(1 for l in self._buffer['lessons'] if l['status'] == 'pendente')
        contradicoes = sum(1 for l in self._buffer['lessons'] if l['status'] == 'contradicao')
        verificados = sum(1 for l in self._buffer['lessons'] if l['status'] == 'verificado')
        return {'total': total, 'pendentes': pendentes, 
                'contradicoes': contradicoes, 'verificados': verificados}
