"""SSE Event Bus — distribui eventos do MasterAgent em TEMPO REAL para o dashboard.
Zero dependencias. HTTP puro com EventSource (nativo do browser).

Arquitetura:
    master_agent.py  ──emit()──→  SSE Server (thread)  ──GET /stream──→  Browser

Uso:
    from modulos.sse_server import emit, iniciar_sse
    emit("narrator", "Analisando sua pergunta...")
    emit("token", {"chunk": "local ", "acumulado": "local npc = NP"})
    
O dashboard HTML se conecta em http://localhost:8765/thought_dashboard.html
"""
import json, threading, queue, os, sys, time
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse as _urlparse

_canal = queue.Queue()          # canal global: consumidores leem daqui
_clientes = set()               # filas individuais de cada browser
_lock = threading.Lock()
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SANDBOX = os.path.join(BASE, 'sandbox')
KG_PATH = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')
KG_DIR = os.path.join(SANDBOX, '.mcr_devia', 'kg')
CONVERSA_PATH = os.path.join(SANDBOX, '.mcr_conversa.jsonl')
_servidor = None


def emit(event_type, data=None):
    """Envia evento SSE para TODOS os browsers conectados. Thread-safe.

    Args:
        event_type: 'stage', 'narrator', 'prompt', 'token', 'result', 'error'
        data: dict com os dados do evento (sera convertido a JSON)
    """
    msg = f"event: {event_type}\ndata: {json.dumps(data or {}, ensure_ascii=False, default=str)}\n\n"
    global _clientes
    with _lock:
        mortos = set()
        for q in _clientes:
            try:
                q.put_nowait(msg)
            except (queue.Full):
                mortos.add(q)
        _clientes -= mortos


class _Handler(BaseHTTPRequestHandler):
    """Handler HTTP minimalista: SSE streaming + servir HTML."""

    def _responder_json(self, dados, status=200):
        """Helper: envia resposta JSON com Content-Length."""
        corpo = json.dumps(dados, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(corpo)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(corpo)

    def _carregar_kg(self):
        """Carrega dados do Knowledge Graph (multi-arquivo)."""
        if not os.path.exists(KG_DIR):
            try:
                with open(KG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {'licoes': []}
        try:
            licoes = []
            for fname in sorted(os.listdir(KG_DIR)):
                if not fname.endswith('.json') or fname == 'master.json':
                    continue
                try:
                    with open(os.path.join(KG_DIR, fname), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        licoes.extend(data.get('licoes', []))
                except Exception:
                    pass
            return {'licoes': licoes}
        except Exception:
            return {'licoes': []}

    def _carregar_conversa(self, limite=50):
        """Carrega ultimas linhas do log de conversa."""
        if not os.path.exists(CONVERSA_PATH):
            return []
        linhas = []
        try:
            with open(CONVERSA_PATH, 'r', encoding='utf-8') as f:
                for linha in f:
                    linha = linha.strip()
                    if linha:
                        try:
                            linhas.append(json.loads(linha))
                        except Exception:
                            pass
        except Exception:
            pass
        return linhas[-limite:]

    def do_GET(self):
        parsed = _urlparse.urlparse(self.path)
        path = parsed.path.rstrip('/')
        query = _urlparse.parse_qs(parsed.query)

        # SSE endpoint
        if path == '/stream':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            q = queue.Queue(maxsize=200)
            with _lock:
                _clientes.add(q)
            try:
                while True:
                    msg = q.get(timeout=30)
                    self.wfile.write(msg.encode('utf-8'))
                    self.wfile.flush()
            except (queue.Empty, BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass
            finally:
                with _lock:
                    _clientes.discard(q)
            return

        # ===== API ENDPOINTS =====
        try:
            # GET /api/emergir — lista de lessons ctx='emergente'
            if path == '/api/emergir':
                kg = self._carregar_kg()
                emergentes = [l for l in kg.get('licoes', []) if l.get('ctx') == 'emergente']
                lista = []
                for l in emergentes:
                    lista.append({
                        'id': l.get('id'), 'erro': l.get('erro',''),
                        'causa': (l.get('causa','') or ''),
                        'chars': len(l.get('solucao','')), 'timestamp': l.get('timestamp'),
                        'status': l.get('status', 'hipotese'),
                        'viabilidade': l.get('viabilidade', 0),
                    })
                self._responder_json({'total': len(lista), 'items': lista})
                return

            # GET /api/emergir/<id> — lesson completa
            if path.startswith('/api/emergir/'):
                lid = path.split('/')[-1]
                kg = self._carregar_kg()
                for l in kg.get('licoes', []):
                    if l.get('id') == lid and l.get('ctx') == 'emergente':
                        self._responder_json(l)
                        return
                self._responder_json({'erro': 'lesson nao encontrada'}, 404)
                return

            # GET /api/kg — resumo do KG ou filtrado por ctx
            if path == '/api/kg':
                kg = self._carregar_kg()
                ctx_filter = (query.get('ctx') or [None])[0]
                lessons = kg.get('licoes', [])
                if ctx_filter:
                    lessons = [l for l in lessons if l.get('ctx') == ctx_filter]
                ctxs = {}
                for l in kg.get('licoes', []):
                    c = l.get('ctx', 'geral')
                    ctxs[c] = ctxs.get(c, 0) + 1
                contextos = [{'ctx': k, 'count': v} for k, v in sorted(ctxs.items(), key=lambda x: -x[1])]
                self._responder_json({
                    'total_lessons': len(kg.get('licoes',[])),
                    'filtradas': len(lessons),
                    'contextos': contextos,
                    'items': [{'id': l.get('id'), 'erro': l.get('erro',''),
                               'ctx': l.get('ctx',''), 'chars': len(l.get('solucao','')),
                               'timestamp': l.get('timestamp')} for l in lessons[-50:]],
                })
                return

            # GET /api/kg/<id> — lesson completa do KG
            if path.startswith('/api/kg/'):
                lid = path.split('/')[-1]
                kg = self._carregar_kg()
                for l in kg.get('licoes', []):
                    if l.get('id') == lid:
                        self._responder_json(l)
                        return
                self._responder_json({'erro': 'lesson nao encontrada'}, 404)
                return

            # GET /api/conversa — log de conversa
            if path == '/api/conversa':
                limite = int((query.get('limite') or [50])[0])
                conversa = self._carregar_conversa(limite=limite)
                self._responder_json({'total': len(conversa), 'items': conversa})
                return

            # GET /api/contexto — contexto atual do sistema
            if path == '/api/contexto':
                kg = self._carregar_kg()
                emergentes = [l for l in kg.get('licoes', []) if l.get('ctx') == 'emergente']
                ultimo_emergente = emergentes[-1] if emergentes else None
                self._responder_json({
                    'total_lessons_kg': len(kg.get('licoes', [])),
                    'total_emergentes': len(emergentes),
                    'ultimo_emergente': {
                        'id': ultimo_emergente.get('id',''),
                        'titulo': ultimo_emergente.get('erro',''),
                        'chars': len(ultimo_emergente.get('solucao','') or ''),
                        'timestamp': ultimo_emergente.get('timestamp'),
                    } if ultimo_emergente else None,
                    'agora': time.time(),
                })
                return

            # GET /api/self — auto-conhecimento (lessons self_knowledge + sugestao_melhoria)
            if path == '/api/self':
                kg = self._carregar_kg()
                auto_licoes = [l for l in kg.get('licoes', []) if l.get('ctx') == 'self_knowledge']
                sugestoes = [l for l in kg.get('licoes', []) if l.get('ctx') == 'sugestao_melhoria']
                self._responder_json({
                    'total_self_knowledge': len(auto_licoes),
                    'total_sugestoes': len(sugestoes),
                    'ultimo_scan': auto_licoes[-1].get('solucao','') if auto_licoes else None,
                    'ultimo_scan_timestamp': auto_licoes[-1].get('timestamp') if auto_licoes else None,
                    'sugestoes': [{'id': l.get('id'), 'erro': l.get('erro',''),
                                   'solucao': l.get('solucao',''),
                                   'timestamp': l.get('timestamp')} for l in sugestoes[-5:]],
                })
                return
        except Exception as api_err:
            self._responder_json({'erro': str(api_err)}, 500)
            return

        # ===== ARQUIVOS ESTATICOS =====
        caminho = path or '/thought_dashboard.html'
        caminho = caminho.lstrip('/')
        caminho_seguro = os.path.join(SANDBOX, caminho)

        if os.path.exists(caminho_seguro) and os.path.isfile(caminho_seguro):
            try:
                if caminho.endswith('.html'):
                    with open(caminho_seguro, 'rb') as f:
                        conteudo = f.read()
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Content-Length', str(len(conteudo)))
                    self.end_headers()
                    self.wfile.write(conteudo)
                elif caminho.endswith('.css'):
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/css')
                    self.end_headers()
                    with open(caminho_seguro, 'r', encoding='utf-8') as f:
                        self.wfile.write(f.read().encode('utf-8'))
                else:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/octet-stream')
                    self.end_headers()
                    with open(caminho_seguro, 'rb') as f:
                        self.wfile.write(f.read())
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass  # navegador fechou — normal
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

    def log_message(self, *args):
        pass  # silencia logs HTTP


def _heartbeater(intervalo=10):
    """Thread: emite heartbeat a cada N segundos para o dashboard saber que o servidor esta vivo."""
    while True:
        time.sleep(intervalo)
        try:
            emit('heartbeat', {'ts': time.time()})
        except Exception:
            pass


def iniciar_sse(porta=8765):
    """Inicia servidor SSE em thread separada. Chame UMA vez no startup."""
    global _servidor, _heartbeat_thread
    if _servidor is not None:
        return _servidor
    _servidor = HTTPServer(('0.0.0.0', porta), _Handler)
    t = threading.Thread(target=_servidor.serve_forever, daemon=True, name='SSE-Server')
    t.start()
    _heartbeat_thread = threading.Thread(target=_heartbeater, args=(10,), daemon=True, name='SSE-Heartbeat')
    _heartbeat_thread.start()
    print(f'\n[SSE] Dashboard: http://localhost:{porta}/thought_dashboard.html\n')
    return _servidor


if __name__ == '__main__':
    iniciar_sse(8765)
    print('[SSE] Servidor rodando. Pressione Ctrl+C para parar.')
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print('[SSE] Parando...')
