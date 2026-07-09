#!/usr/bin/env python3
"""mcr.bridge_api — Ponte HTTP REST entre Grimorio C# e MCR-DevIA Python.
Porta 7778 (separada do socket 7777 de NPC).
Endpoints: POST /tool/npc, POST /tool/monster, POST /tool/npc/custom, GET /status"""
import json
import sys
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

# Path para importar os modulos do toolset
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcr_server_toolset import criar_npc, criar_monstro
from mcr.golden_templates import salvar_npc_parametrizado, salvar_monstro_parametrizado

HOST = '127.0.0.1'
PORT = 7778

# Referencias para WorldObserver e MCRWorldSystem (setados externamente)
_world_observer = None
_world_system = None


def configurar_observer(observer=None, world_system=None):
    """Configura referencias para o WorldObserver e MCRWorldSystem."""
    global _world_observer, _world_system
    _world_observer = observer
    _world_system = world_system


class BridgeHandler(BaseHTTPRequestHandler):
    """Handler HTTP para as requisicoes do Grimorio."""

    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        global _world_observer, _world_system
        if self.path == '/status':
            self._send_json({
                'status': 'online',
                'porta': PORT,
                'models': ['qwen2.5-coder:7b'],
                'endpoints': ['/tool/npc', '/tool/monster', '/tool/npc/custom',
                              '/status', '/world/status', '/world/events',
                              '/mcr/gerar_npc'],
            })
        elif self.path == '/world/status':
            dados = {
                'world_observer': _world_observer.get_estatisticas() if _world_observer else {'ativo': False},
            }
            # Tenta ler o world_state
            try:
                from mcr.mcr_world_state import _carregar
                ws = _carregar()
                npcs = ws.get('npcs', {})
                nomes_npcs = list(npcs.keys())
                dados['world_state'] = {
                    'total_npcs': len(nomes_npcs),
                    'npcs': nomes_npcs[:20],
                    'tem_foundation': 'current_foundation' in ws,
                }
            except Exception as e:
                dados['world_state'] = {'erro': str(e)}
            self._send_json(dados)
        elif self.path == '/world/events':
            if _world_observer:
                eventos = _world_observer.get_ultimos_eventos(20)
                self._send_json({'eventos': eventos, 'total': len(eventos)})
            else:
                self._send_json({'eventos': [], 'total': 0})
        else:
            self._send_json({'erro': 'Endpoint nao encontrado'}, 404)

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length).decode('utf-8'))
        except Exception as e:
            self._send_json({'status': 'erro', 'mensagem': 'JSON invalido: %s' % e}, 400)
            return

        prompt = body.get('prompt', '')
        params = body.get('params', None)

        if self.path == '/tool/npc':
            if not prompt:
                self._send_json({'status': 'erro', 'mensagem': 'Campo "prompt" obrigatorio'}, 400)
                return
            resultado = criar_npc(prompt)
            self._send_json({
                'status': 'ok',
                'tipo': 'npc',
                'mensagem': resultado,
            })

        elif self.path == '/tool/npc/custom':
            if params:
                # Modo rapido: golden template (Sistema 1, 0ms, zero LLM)
                resultado = salvar_npc_parametrizado(params)
                self._send_json({
                    'status': 'ok',
                    'tipo': 'npc_custom',
                    'modo': 'template',
                    'mensagem': resultado,
                })
            elif prompt:
                # Modo criativo: LLM
                resultado = criar_npc(prompt)
                self._send_json({
                    'status': 'ok',
                    'tipo': 'npc_custom',
                    'modo': 'llm',
                    'mensagem': resultado,
                })
            else:
                self._send_json({'status': 'erro', 'mensagem': 'Envie "params" (template) ou "prompt" (LLM)'}, 400)

        elif self.path == '/tool/monster':
            if not prompt:
                self._send_json({'status': 'erro', 'mensagem': 'Campo "prompt" obrigatorio'}, 400)
                return
            resultado = criar_monstro(prompt)
            self._send_json({
                'status': 'ok',
                'tipo': 'monster',
                'mensagem': resultado,
            })

        elif self.path == '/world/perturb':
            global _world_observer, _world_system
            evento = body.get('evento', body)
            if _world_observer:
                _world_observer.injetar_evento(evento)
                self._send_json({'status': 'ok', 'mensagem': 'Evento injetado no observer'})
            elif _world_system:
                if hasattr(_world_system, 'perceber_perturbacao'):
                    resultado = _world_system.perceber_perturbacao({
                        'delta_h': body.get('delta_h', -0.3),
                        'trigger_event': evento,
                        'batch_size': 1,
                    })
                    self._send_json({
                        'status': 'ok',
                        'mensagem': 'Perturbacao processada',
                        'resultado': resultado,
                    })
                else:
                    self._send_json({'status': 'erro', 'mensagem': 'WorldSystem sem perceber_perturbacao'}, 500)
            else:
                self._send_json({'status': 'erro', 'mensagem': 'Observer e WorldSystem nao configurados'}, 500)
        elif self.path == '/mcr/gerar_npc':
            tema = body.get('tema', '')
            if not tema:
                self._send_json({'status': 'erro', 'mensagem': 'Campo "tema" obrigatorio'}, 400)
                return
            try:
                from devia.kernel.mcr_kernel.engine import MCR
                from devia.kernel.mcr_kernel.memory import MCRConector, MCRCadeia, _get_kg

                conector = MCRConector()

                # 1. Alimenta dados do Knowledge Graph se disponivel
                kg = _get_kg()
                if kg and hasattr(kg, 'buscar'):
                    try:
                        lessons = kg.buscar(tema, max_r=5) if hasattr(kg, 'buscar') else []
                        if not lessons and hasattr(kg, '_get_licoes'):
                            licoes = kg._get_licoes()
                            for l in licoes[:20]:
                                sol = l.get('solucao', '')
                                if sol and len(sol) > 30:
                                    conector.alimentar(sol[:1000], f"lesson_{l.get('ctx','?')}")
                    except:
                        pass

                # 2. Alimenta o tema do usuario
                conector.alimentar(
                    f'{tema}. NPC com configuracao, dialogo e comportamento.',
                    'tema_usuario'
                )

                # 3. Tenta usar MCRWorldSystem se configurado
                if _world_system and hasattr(_world_system, 'ciclo'):
                    try:
                        from mcr.mcr_world_state import _carregar
                        estado = _carregar()
                        estado_percebido = _world_system._perceber_estado(estado)
                        res_sys = _world_system.ciclo(tema, estado, max_entidades=1)
                        if res_sys.get('sucesso', False):
                            self._send_json({
                                'status': 'ok',
                                'tipo': 'npc',
                                'nome': res_sys.get('nome', tema.replace(' ', '_')),
                                'modo': 'mcr_world_system',
                                'mensagem': str(res_sys.get('entidade', {}))[:500],
                                'nota': res_sys.get('nota', 5),
                            })
                            return
                    except:
                        pass

                # 4. Fallback: geracao via MCRCadeia pura
                if not conector.topicos:
                    self._send_json({
                        'status': 'erro_entropia',
                        'mensagem': 'Conhecimento insuficiente — execute Cold Start para gerar entidades',
                        'modo': 'entropia_insuficiente',
                        'estado': 'EXPANDIR',
                        'acao': 'execute Cold Start para minerar mais APIs',
                        'nota': 0,
                        'tamanho_gerado': 0,
                    }, 200)
                    return

                cadeia = MCRCadeia(conector)
                palavras_tema = tema.split()
                semente = palavras_tema[0] if palavras_tema else 'NPC'
                if semente not in conector.mcr_palavra.freq:
                    # Encontra a primeira palavra conhecida
                    for t, dados in conector.topicos.items():
                        for p in dados.get('palavras', []):
                            if p in conector.mcr_palavra.freq and len(p) > 2:
                                semente = p
                                break
                        if semente in conector.mcr_palavra.freq:
                            break

                res = cadeia.gerar(semente, n_tokens=100, top_k=3)
                texto_gerado = res.get('texto', '')
                nota = res.get('nota', 0)

                if len(texto_gerado) < 20 or nota < 3:
                    self._send_json({
                        'status': 'erro_entropia',
                        'mensagem': 'Conhecimento insuficiente para gerar entidade com qualidade minima',
                        'modo': 'entropia_insuficiente',
                        'estado': 'EXPANDIR',
                        'acao': 'execute Cold Start para minerar mais APIs',
                        'nota': nota,
                        'tamanho_gerado': len(texto_gerado),
                    }, 200)
                    return

                self._send_json({
                    'status': 'ok',
                    'tipo': 'npc',
                    'nome': tema.replace(' ', '_'),
                    'modo': 'mcr_generativo',
                    'mensagem': texto_gerado[:500],
                    'nota': nota,
                    'n_tokens': res.get('n_tokens', 0),
                })
            except Exception as e:
                import traceback
                traceback.print_exc()
                self._send_json({'status': 'erro', 'mensagem': str(e)[:200]}, 500)

        else:
            self._send_json({'status': 'erro', 'mensagem': 'Endpoint nao encontrado'}, 404)

    def log_message(self, format, *args):
        """Silencia logs padrao do HTTP server."""
        pass


class BridgeAPI:
    """Servidor HTTP para integracao com Grimorio C#."""

    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self._server = None
        self._thread = None

    def iniciar(self):
        """Inicia o servidor em background."""
        self._server = HTTPServer((self.host, self.port), BridgeHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        print('[BridgeAPI] Servidor HTTP em http://%s:%s' % (self.host, self.port))
        print('[BridgeAPI] Endpoints: POST /tool/npc, POST /tool/monster, '
              'POST /world/perturb, GET /status, GET /world/status, GET /world/events')

    def parar(self):
        if self._server:
            self._server.shutdown()
            print('[BridgeAPI] Servidor parado.')


if __name__ == '__main__':
    api = BridgeAPI()
    api.iniciar()
    print('[BridgeAPI] Pressione Ctrl+C para parar.')
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        api.parar()
