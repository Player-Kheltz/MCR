"""mcr.npc_server — Servidor de NPCs para o Canary.
Recebe requisicoes de NPCs do jogo e responde via MCR + Dialogos reais treinados."""
import json
import socket
import threading
import time
import re
import sys
import os
from pathlib import Path
from typing import Optional

# Path setup para imports do DevIA e prototype
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from mcr.npc_sanity_filter import filtrar_resposta, enriquecer_com_historia
from mcr.dialogue_trainer import DialogueTrainer

# Memoria episodica (cache L3) — importada diretamente
_MEMORIA = None
try:
    from episodic_memory import EpisodicMemory
    _MEMORIA = EpisodicMemory()
except Exception:
    pass

# MCR (Sistema 1) — tenta carregar
_MCR_SYSTEM = None
try:
    from mcr.mcr import MCR as _MCR_CLASS
    _MCR_SYSTEM = _MCR_CLASS()
    print('[NPC-Server] MCRSystem carregado (via mcr.mcr)')
except Exception as e:
    print('[NPC-Server] MCRSystem nao disponivel: %s' % e)
    _MCR_SYSTEM = None

# Inicializa DialogueTrainer com dialogos treinados
_DIALOGUE_TRAINER = DialogueTrainer(mcr_system=_MCR_SYSTEM)
try:
    _dialogos = _DIALOGUE_TRAINER.carregar_dialogos_json()
    if _dialogos:
        _DIALOGUE_TRAINER.treinar_com_dialogos(_dialogos)
        print('[NPC-Server] DialogueTrainer: %d NPCs treinados' % _DIALOGUE_TRAINER.total_npcs)
    else:
        print('[NPC-Server] DialogueTrainer: nenhum dialogo carregado (execute dialogue_miner primeiro)')
except Exception as e:
    print('[NPC-Server] DialogueTrainer erro: %s' % e)


def _gerar_resposta_markov(npc_id: str, player_id: str, mensagem: str) -> str:
    """Gera resposta via Markov (Sistema 1) — 0.006s."""
    if not _MCR_SYSTEM:
        return ""

    palavras = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', (mensagem + ' ' + npc_id).lower())
    if not palavras:
        return ""

    # Gera cadeia de ate 25 palavras
    mk = getattr(_MCR_SYSTEM, 'mk', None) or getattr(_MCR_SYSTEM, 'mk_palavra', None)
    if not mk:
        return ""
    cadeia = []
    conf_min = 1.0
    for p in palavras[:3]:
        pred, conf = mk.predizer(p)
        if pred and conf > 0.05:
            atual = p
            for _ in range(25):
                prox, c = mk.predizer(atual)
                if not prox or c < 0.02:
                    break
                cadeia.append(prox)
                atual = prox
                conf_min = min(conf_min, c)
            break

    if cadeia:
        return ' '.join(cadeia)
    return ""


def _buscar_memoria(player_id: str, npc_id: str) -> list:
    """Busca historico de interacoes na EpisodicMemory."""
    if not _MEMORIA:
        return []
    try:
        resultados = _MEMORIA.buscar('%s %s' % (player_id, npc_id), n=3)
        return resultados or []
    except Exception:
        return []


def processar_dialogo(dados: dict) -> dict:
    """Processa um dialogo de NPC e retorna resposta.
    
    Args:
        dados: dict com npc_id, player_id, message
    
    Returns:
        dict com response (string)
    """
    t0 = time.time()

    npc_id = dados.get('npc_id', 'NPC')
    player_id = dados.get('player_id', 'Player')
    mensagem = dados.get('message', '')

    if not mensagem:
        return {'response': 'Ola.', 'tempo': 0}

    # 1. Resposta via dialogo treinado (NPC-specific)
    resposta = ''
    if _DIALOGUE_TRAINER:
        resposta = _DIALOGUE_TRAINER.gerar_resposta(npc_id, mensagem)

    # 2. Se dialogo nao encontrou, tenta Markov (Sistema 1)
    if not resposta:
        resposta = _gerar_resposta_markov(npc_id, player_id, mensagem)

    # 3. Fallback KG (Metacognicao — confianca + justificativa)
    if not resposta:
        try:
            from mcr.metacognicao import Metacognicao
            meta = Metacognicao()
            score, just = meta.calcular_confianca(mensagem)
            if score > 0.3:
                resposta = just
        except Exception:
            pass

    # 4. Enriquece com historico
    historico = _buscar_memoria(player_id, npc_id)
    resposta = enriquecer_com_historia(resposta, historico)

    # 5. Filtro de sanidade
    resposta = filtrar_resposta(resposta, npc_id)

    # 6. Registra na EpisodicMemory para contexto futuro
    if _MEMORIA and resposta:
        try:
            _MEMORIA.registrar(
                '%s disse a %s: %s' % (player_id, npc_id, mensagem),
                'Resposta: %s' % resposta,
                'npc_dialogo'
            )
        except Exception:
            pass

    tempo = round((time.time() - t0) * 1000, 1)
    return {'response': resposta, 'tempo_ms': tempo}


# ─── Servidor Socket ──────────────────────────────────────────

class NPCServer:
    """Servidor TCP que escuta requisicoes de NPCs do Canary."""

    def __init__(self, host='127.0.0.1', port=7777):
        self.host = host
        self.port = port
        self._running = False

    def iniciar(self):
        """Inicia o servidor em background."""
        self._running = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()
        print('[NPC-Server] Ouvindo em %s:%s' % (self.host, self.port))

    def _loop(self):
        """Loop principal do servidor."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(5)
        sock.settimeout(1.0)

        while self._running:
            try:
                conn, addr = sock.accept()
                threading.Thread(target=self._atender, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    print('[NPC-Server] Erro: %s' % e)

    def _atender(self, conn):
        """Atende uma conexao."""
        try:
            conn.settimeout(5.0)
            data = conn.recv(4096)
            if not data:
                return

            # Parse do JSON
            try:
                dados = json.loads(data.decode('utf-8'))
            except json.JSONDecodeError:
                conn.send(json.dumps({'response': 'Erro: JSON invalido'}).encode('utf-8'))
                return

            # Processa
            resultado = processar_dialogo(dados)

            # Envia resposta
            resposta = json.dumps(resultado)
            conn.send(resposta.encode('utf-8'))

        except socket.timeout:
            try:
                conn.send(json.dumps({'response': '...', 'timeout': True}).encode('utf-8'))
            except Exception:
                pass
        except Exception as e:
            print('[NPC-Server] Erro no atendimento: %s' % e)
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def parar(self):
        self._running = False


# ─── Ponto de entrada ──────────────────────────────────────────

if __name__ == '__main__':
    print('=' * 50)
    print('  NPC-SERVER — Caminho Druida v1.0')
    print('  Teste de Turing para NPCs do Canary')
    print('=' * 50)

    server = NPCServer()
    server.iniciar()

    # Loop principal
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\n[NPC-Server] Encerrando...')
        server.parar()
