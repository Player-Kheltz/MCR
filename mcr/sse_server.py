#!/usr/bin/env python3
"""sse_server.py — SSE Event Bus + REST API + Web Chat para MCR-DevIA.

Unifica a Dashboard de telemetria (SSE) com o Pipeline de worldbuilding.

Endpoints:
    GET  /dashboard.html       — Interface web completa
    GET  /stream               — SSE (eventos em tempo real)
    GET  /api/kg               — Knowledge Graph
    GET  /api/conversa         — Log de conversas
    POST /api/chat             — Envia prompt ao PipelineCompleto
    GET  /api/status           — Status do servidor e metricas
"""
import json, threading, queue, os, sys, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import urllib.parse as _urlparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'devia', 'kernel'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

_canal = queue.Queue()
_clientes = set()
_lock = threading.Lock()
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
KG_DIR = os.path.join(BASE, 'devia', 'knowledge')
_servidor = None


def emit(event_type, data=None):
    """Envia evento SSE para TODOS os browsers conectados."""
    msg = f"event: {event_type}\ndata: {json.dumps(data or {}, ensure_ascii=False, default=str)}\n\n"
    global _clientes
    with _lock:
        mortos = set()
        for q in _clientes:
            try:
                q.put_nowait(msg)
            except queue.Full:
                mortos.add(q)
        _clientes -= mortos


class _Handler(BaseHTTPRequestHandler):
    """Handler HTTP: SSE streaming + API REST + arquivos estaticos."""

    def _responder_json(self, dados, status=200):
        corpo = json.dumps(dados, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(corpo)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(corpo)

    def _carregar_kg(self):
        """Carrega lessons do KG (multi-arquivo)."""
        if not os.path.exists(KG_DIR):
            return {'licoes': []}
        licoes = []
        for fname in sorted(os.listdir(KG_DIR)):
            if not fname.endswith('.json'):
                continue
            try:
                with open(os.path.join(KG_DIR, fname), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        licoes.extend(data.get('licoes', []))
                    elif isinstance(data, list):
                        licoes.extend(data)
            except Exception:
                pass
        return {'licoes': licoes}

    def _stream_sse_header(self):
        """Envia headers para resposta SSE."""
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def _sse_send(self, event, data):
        """Envia um evento SSE para o cliente."""
        msg = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"
        try:
            self.wfile.write(msg.encode('utf-8'))
            self.wfile.flush()
        except:
            pass

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length).decode('utf-8'))
        except Exception as e:
            self._responder_json({'erro': f'JSON invalido: {e}'}, 400)
            return

        prompt = body.get('prompt', '')
        if not prompt:
            self._responder_json({'erro': 'Campo "prompt" obrigatorio'}, 400)
            return

        # ─── Chat síncrono (resposta completa) ─────────
        if self.path == '/api/chat':
            emit('chat_start', {'prompt': prompt[:100]})
            try:
                from mcr.pipeline_completo import PipelineCompleto
                pipe = PipelineCompleto()
                t0 = time.time()
                resultado = []
                def _exec():
                    try:
                        resultado.append(pipe.processar(prompt))
                    except Exception as ex:
                        resultado.append({'erro': str(ex)})
                t = threading.Thread(target=_exec, daemon=True)
                t.start()
                t.join(timeout=120)
                if not resultado:
                    self._responder_json({'erro': 'Tempo limite excedido'})
                    return
                res = resultado[0]
                if 'erro' in res:
                    self._responder_json({'erro': res['erro']}, 500)
                    return
                tempo = round(time.time() - t0, 2)
                resposta = res.get('resposta', '')
                rota = res.get('rota', '?')
                emit('chat_response', {'prompt': prompt[:100], 'resposta': resposta[:500], 'rota': rota, 'tempo': tempo})
                self._responder_json({'resposta': resposta, 'rota': rota, 'tempo': tempo})
            except Exception as e:
                self._responder_json({'erro': str(e)}, 500)
            return

        # ─── Chat streaming (tokens em tempo real) ─────
        if self.path == '/api/chat-stream':
            self._stream_sse_header()
            self._sse_send('chat_start', {'prompt': prompt[:100]})
            try:
                from mcr.prompts_criativos import obter_prompt, obter_modelo
                from mcr_devia_v2 import MarkovDecider
                md = MarkovDecider()
                classe, conf = md.classificar(prompt)
                modelo = obter_modelo(classe) or 'mistral:7b-32k'
                prompt_llm = obter_prompt(classe, prompt, tipo=classe, npc='NPC', resumo=prompt)

                import urllib.request
                payload = json.dumps({
                    "model": modelo, "prompt": prompt_llm, "stream": True,
                    "options": {"num_predict": 1024, "temperature": 0.7, "num_ctx": 32768}
                }).encode()
                req = urllib.request.Request(
                    "http://localhost:11434/api/generate", data=payload,
                    headers={"Content-Type": "application/json"}
                )
                t0 = time.time()

                with urllib.request.urlopen(req, timeout=120) as resp:
                    acumulado = ""
                    buffer = b""
                    while True:
                        chunk = resp.read(4096)
                        if not chunk:
                            break
                        buffer += chunk
                        while b'\n' in buffer:
                            line, buffer = buffer.split(b'\n', 1)
                            linha = line.decode('utf-8', errors='replace').strip()
                            if not linha:
                                continue
                            try:
                                data = json.loads(linha)
                                if data.get('done'):
                                    break
                                token = data.get('response', '')
                                if token:
                                    acumulado += token
                                    self._sse_send('chat_token', {'token': token, 'acumulado': acumulado})
                            except:
                                continue

                tempo = round(time.time() - t0, 2)

                # Canoniza no mundo
                try:
                    from mcr.pipeline_completo import _canonizar
                    _canonizar(prompt, acumulado, classe, modelo)
                except:
                    pass

                self._sse_send('chat_done', {'rota': 'llm_stream', 'classe': classe, 'tempo': tempo})
            except Exception as e:
                self._sse_send('chat_error', {'erro': str(e)})
            return

        self._responder_json({'erro': 'POST nao suportado'}, 404)

    def do_GET(self):
        parsed = _urlparse.urlparse(self.path)
        path = parsed.path.rstrip('/')
        query = _urlparse.parse_qs(parsed.query)

        # SSE
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
            except (queue.Empty, BrokenPipeError, ConnectionResetError):
                pass
            finally:
                with _lock:
                    _clientes.discard(q)
            return

        # API: KG
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
            self._responder_json({
                'total_lessons': len(kg.get('licoes', [])),
                'filtradas': len(lessons),
                'contextos': [{'ctx': k, 'count': v} for k, v in sorted(ctxs.items(), key=lambda x: -x[1])],
                'items': [{'id': l.get('id'), 'erro': l.get('erro',''),
                           'ctx': l.get('ctx',''), 'chars': len(l.get('solucao','')),
                           'timestamp': l.get('timestamp')} for l in lessons[-50:]],
            })
            return

        # API: World Status
        if path == '/api/world/status':
            try:
                from mcr.mcr_world_state import _carregar
                from mcr.mcr_world_chronicle import get_chronicle
                mundo = _carregar()
                npcs = mundo.get('npcs', {})
                lores = mundo.get('lores', {})
                total_quests = sum(len(n.get('quests', [])) for n in npcs.values())
                entropia = 0.5
                try:
                    from devia.kernel.mcr_kernel.engine import MCR
                    mk = MCR('sys_entropy')
                    entropia = round(mk.entropia_media(), 3) if mk.transicoes else 0.5
                except Exception:
                    pass
                cronicas = []
                try:
                    cronicas = get_chronicle(ultimas=5) if callable(get_chronicle) else []
                except Exception:
                    pass
                self._responder_json({
                    'total_npcs': len(npcs),
                    'total_lores': len(lores),
                    'total_quests': total_quests,
                    'entropia': entropia,
                    'estado': 'EXPANDIR' if entropia > 0.7 else 'EQUILIBRAR' if entropia > 0.3 else 'CONECTAR',
                    'ultimos_eventos': cronicas[:5] if isinstance(cronicas, list) else [],
                })
            except Exception as e:
                self._responder_json({'erro': str(e)}, 500)
            return

        if path == '/api/world/npcs':
            try:
                from mcr.mcr_world_state import _carregar
                mundo = _carregar()
                npcs = mundo.get('npcs', {})
                lista = []
                for nome, dados in npcs.items():
                    lista.append({
                        'nome': nome,
                        'role': dados.get('role', ''),
                        'raca': dados.get('raca', ''),
                        'local': dados.get('local', ''),
                        'traco_secreto': dados.get('traco_secreto', ''),
                        'tier': dados.get('tier', ''),
                        'quests': dados.get('quests', []),
                        'expansoes': len(dados.get('expansoes', [])),
                    })
                self._responder_json({'total': len(lista), 'items': lista})
            except Exception as e:
                self._responder_json({'erro': str(e)}, 500)
            return

        if path == '/api/world/quests':
            try:
                from mcr.mcr_world_state import _carregar
                mundo = _carregar()
                quests = []
                for nome, dados in mundo.get('npcs', {}).items():
                    for q in dados.get('quests', []):
                        quests.append({
                            'titulo': q,
                            'npc': nome,
                            'status': 'disponivel',
                        })
                for nome, dados in mundo.get('lores', {}).items():
                    quests.append({
                        'titulo': nome,
                        'npc': '(lore)',
                        'status': 'registrada',
                        'resumo': dados.get('resumo', '')[:100],
                    })
                self._responder_json({'total': len(quests), 'items': quests})
            except Exception as e:
                self._responder_json({'erro': str(e)}, 500)
            return

        if path == '/api/world/scripts':
            try:
                from pathlib import Path
                scripts_dir = Path(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'server', 'data', 'scripts'))
                arquivos = []
                if scripts_dir.exists():
                    for f in sorted(scripts_dir.rglob('*.lua'))[:200]:
                        arquivos.append({
                            'nome': f.name,
                            'caminho': str(f.relative_to(SERVER_DIR)),
                            'tamanho': f.stat().st_size,
                        })
                self._responder_json({'total': len(arquivos), 'items': arquivos})
            except Exception:
                self._responder_json({'total': 0, 'items': []})
            return

        if path == '/api/world/entropy_grid':
            try:
                import urllib.request
                resp = urllib.request.urlopen('http://127.0.0.1:7778/world/entropy_grid?minutes=10', timeout=3)
                data = json.loads(resp.read())
                self._responder_json(data)
            except Exception:
                self._responder_json({'grid': [], 'max_entropy': 0, 'min_entropy': 0, 'total_events': 0})
            return

        if path == '/api/world/logs':
            try:
                from mcr.mcr_world_chronicle import get_chronicle
                chronicle = get_chronicle(ultimas=50) if callable(get_chronicle) else []
                logs = []
                for entry in chronicle:
                    if isinstance(entry, dict):
                        logs.append({
                            'hora': entry.get('timestamp', '')[:19],
                            'tipo': 'info',
                            'msg': f"{entry.get('evento', '')} | {entry.get('resumo', '')[:120]}"
                        })
                    elif isinstance(entry, str):
                        logs.append({'hora': '', 'tipo': 'info', 'msg': entry[:200]})
                arquivos_log = []
                log_dir = os.path.join(BASE, 'logs')
                if os.path.exists(log_dir):
                    for f in sorted(os.listdir(log_dir))[-5:]:
                        fpath = os.path.join(log_dir, f)
                        if f.endswith('.log') and os.path.isfile(fpath):
                            try:
                                with open(fpath, 'r', encoding='utf-8') as lf:
                                    for linha in lf.readlines()[-20:]:
                                        linha = linha.strip()
                                        if linha:
                                            tipo = 'erro' if 'error' in linha.lower() or 'erro' in linha.lower() else 'aviso' if 'warn' in linha.lower() or 'aviso' in linha.lower() else 'info'
                                            arquivos_log.append({'hora': f[:19], 'tipo': tipo, 'msg': linha[:200]})
                            except: pass
                todas = (arquivos_log + logs)[:100]
                self._responder_json({'total': len(todas), 'items': todas})
            except Exception as e:
                self._responder_json({'total': 0, 'items': [], 'erro': str(e)})
            return

        # API: Status
        if path == '/api/status':
            try:
                from mcr.cache_hierarquico import CacheHierarquico
                cache_stats = CacheHierarquico().estatisticas()
            except Exception:
                cache_stats = {}
            try:
                from mcr.mcr_world_state import _carregar
                mundo = _carregar()
                total_npcs = len(mundo.get('npcs', {}))
                total_lores = len(mundo.get('lores', {}))
            except Exception:
                total_npcs = total_lores = 0
            self._responder_json({
                'status': 'online',
                'cache': cache_stats,
                'mundo': {'npcs': total_npcs, 'lores': total_lores},
                'timestamp': time.time(),
            })
            return

        # Dashboard HTML
        if path == '' or path == '/dashboard' or path == '/dashboard.html':
            html_path = os.path.join(TEMPLATES, 'dashboard.html')
            if os.path.exists(html_path):
                try:
                    with open(html_path, 'rb') as f:
                        conteudo = f.read()
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Content-Length', str(len(conteudo)))
                    self.end_headers()
                    self.wfile.write(conteudo)
                except (BrokenPipeError, ConnectionResetError):
                    pass
                return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b'Not Found')

    def log_message(self, *args):
        pass


def iniciar_sse(porta=8765):
    """Inicia servidor SSE em thread separada."""
    global _servidor
    if _servidor is not None:
        return _servidor
    _servidor = ThreadingHTTPServer(('0.0.0.0', porta), _Handler)
    t = threading.Thread(target=_servidor.serve_forever, daemon=True, name='SSE-Server')
    t.start()
    print(f'\n[SSE] MCR-DevIA Web Console: http://localhost:{porta}/dashboard.html\n')
    return _servidor


if __name__ == '__main__':
    iniciar_sse(8765)
    print('[SSE] Servidor rodando. Pressione Ctrl+C para parar.')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('[SSE] Parando...')
