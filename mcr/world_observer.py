#!/usr/bin/env python3
"""mcr.world_observer — Observador de eventos do servidor Canary.
Faz tail do arquivo mcr_events.jsonl (escrito pelos hooks Lua),
parseia eventos, calcula impacto na entropia e notifica o MCRWorldSystem."""
import json
import os
import time
import threading
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Optional, Callable

from mcr.paths import SERVER_DIR

EVENTS_FILE = SERVER_DIR / "data" / "mcr_events.jsonl"
POLL_INTERVAL = 1.0  # segundos entre verificacoes
COOLDOWN_REACAO = 30.0  # segundos entre reacoes


class WorldObserver:
    """Observa eventos do servidor e notifica o MCRWorldSystem.
    
    Modo de uso:
        observer = WorldObserver(world_system)
        observer.iniciar()  # thread background
        # ... sistema continua rodando ...
        observer.parar()
    """

    def __init__(self, world_system=None, callback_notificar: Callable = None):
        self.world_system = world_system
        self.callback_notificar = callback_notificar
        self._thread: Optional[threading.Thread] = None
        self._ativo = False
        self._posicao_arquivo = 0
        self._fila_eventos: List[Dict] = []
        self._ultima_reacao = 0.0
        self._total_eventos = 0
        self._eventos_por_tipo: Dict[str, int] = defaultdict(int)
        self._ultimos_eventos: List[Dict] = []
        self._poll_interval = POLL_INTERVAL  # adaptativo

    # ─── API publica ───────────────────────────────────────

    def iniciar(self):
        """Inicia thread de observacao em background."""
        if self._ativo:
            return
        self._ativo = True
        self._posicao_arquivo = self._obter_tamanho_atual()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print('[WorldObserver] Observador iniciado (poll=%ds, cooldown=%ds)' % (
            POLL_INTERVAL, COOLDOWN_REACAO))

    def parar(self):
        """Para a thread de observacao."""
        self._ativo = False
        if self._thread:
            self._thread.join(timeout=3)
        print('[WorldObserver] Observador parado.')

    def get_ultimos_eventos(self, n: int = 10) -> List[Dict]:
        """Retorna os ultimos N eventos processados."""
        return self._ultimos_eventos[-n:]

    def get_entropy_grid(self, minutes: int = 5) -> Dict:
        """Calcula entropia de Shannon por coordenada do mapa.

        Para cada coordenada com eventos na janela de tempo, calcula
        H sobre a distribuição de tipos de evento (death, spawn, etc.).
        Normaliza H dividindo por log2(n_tipos) → [0, 1].

        Args:
            minutes: janela de tempo em minutos para considerar eventos

        Returns:
            dict com grid, max_entropy, min_entropy, total_events
        """
        import math
        from collections import defaultdict

        # Filtra eventos dentro da janela de tempo
        agora = time.time()
        janela = minutes * 60
        eventos_recentes = [
            e for e in self._ultimos_eventos
            if e.get('_processed_at', 0) > agora - janela
        ]

        if not eventos_recentes:
            return {'grid': [], 'max_entropy': 0, 'min_entropy': 0, 'total_events': 0}

        # Agrupa eventos por coordenada (x, y, z)
        tiles: Dict[tuple, Counter] = defaultdict(Counter)
        for e in eventos_recentes:
            pos = e.get('pos', {})
            if not pos or not all(k in pos for k in ('x', 'y', 'z')):
                continue
            chave = (pos['x'], pos['y'], pos['z'])
            tiles[chave][e.get('type', 'unknown')] += 1

        if not tiles:
            return {'grid': [], 'max_entropy': 0, 'min_entropy': 0, 'total_events': len(eventos_recentes)}

        # Calcula entropia por tile
        grid = []
        entropias = []
        for (x, y, z), dist in tiles.items():
            total = sum(dist.values())
            h = 0.0
            for count in dist.values():
                p = count / total
                if p > 0:
                    h -= p * math.log2(p)
            # Normaliza: H / H_max onde H_max = log2(n_tipos_distintos)
            n_tipos = len(dist)
            h_max = math.log2(max(n_tipos, 2))
            entropia_norm = h / h_max if h_max > 0 else 0.0
            grid.append({
                'x': x, 'y': y, 'z': z,
                'entropy': round(entropia_norm, 4),
                'event_count': total,
            })
            entropias.append(entropia_norm)

        return {
            'grid': grid,
            'max_entropy': max(entropias) if entropias else 0,
            'min_entropy': min(entropias) if entropias else 0,
            'total_events': len(eventos_recentes),
        }

    def get_estatisticas(self) -> Dict:
        """Retorna estatisticas do observador."""
        return {
            'total_eventos': self._total_eventos,
            'eventos_por_tipo': dict(self._eventos_por_tipo),
            'fila_atual': len(self._fila_eventos),
            'ultima_reacao': self._ultima_reacao,
            'cooldown_restante': max(0, COOLDOWN_REACAO - (time.time() - self._ultima_reacao)),
        }

    def injetar_evento(self, evento: dict):
        """Injeta um evento manualmente (para testes ou Bridge API)."""
        if isinstance(evento, dict):
            evento['_processed_at'] = time.time()
            self._fila_eventos.append(evento)
            self._total_eventos += 1
            self._eventos_por_tipo[evento.get('type', 'unknown')] += 1
            self._ultimos_eventos.append(evento)
            if len(self._ultimos_eventos) > 100:
                self._ultimos_eventos.pop(0)
            print('[WorldObserver] Evento injetado manualmente: %s' % evento.get('type', '?'))

    # ─── Loop interno ──────────────────────────────────────

    def _obter_tamanho_atual(self) -> int:
        """Retorna tamanho atual do arquivo de eventos."""
        try:
            return EVENTS_FILE.stat().st_size
        except Exception:
            return 0

    def _ler_novas_linhas(self) -> List[str]:
        """Le linhas novas desde a ultima leitura.
        
        Adaptativo: se arquivo nao existe ou esta vazio,
        aumenta intervalo ate 30s para reduzir I/O.
        """
        if not EVENTS_FILE.exists():
            self._poll_interval = min(30.0, self._poll_interval * 2)
            return []

        try:
            with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
                f.seek(self._posicao_arquivo)
                linhas = f.readlines()
                self._posicao_arquivo = f.tell()
            if linhas:
                self._poll_interval = POLL_INTERVAL  # reset ao achar dados
            else:
                self._poll_interval = min(30.0, self._poll_interval * 1.5)
            return [l.strip() for l in linhas if l.strip()]
        except Exception:
            return []

    def _processar_evento(self, linha: str):
        """Parseia uma linha JSON de evento."""
        try:
            evento = json.loads(linha)
        except json.JSONDecodeError:
            return

        evento['_processed_at'] = time.time()
        self._fila_eventos.append(evento)
        self._total_eventos += 1
        self._eventos_por_tipo[evento.get('type', 'unknown')] += 1
        self._ultimos_eventos.append(evento)
        # Limita historico
        if len(self._ultimos_eventos) > 100:
            self._ultimos_eventos.pop(0)

    def _calcular_impacto_entropia(self, eventos: List[Dict]) -> float:
        """Calcula o impacto dos eventos na entropia do mundo.
        
        Retorna delta_h: 
            negativo = perda de diversidade (NPC unico morreu)
            positivo = ganho de diversidade (novo tipo apareceu)
            ~0 = impacto irrelevante
        """
        if not eventos:
            return 0.0

        # Agrupa por tipo de target
        targets = Counter()
        for e in eventos:
            targets[e.get('target', 'unknown')] += 1

        # Se o mesmo target morreu muitas vezes, impacto zero (farming)
        target_mais_comum = targets.most_common(1)
        if target_mais_comum and target_mais_comum[0][1] > 3:
            return 0.0

        # Tipos de evento com impacto negativo
        delta = 0.0
        for e in eventos:
            tipo = e.get('type', '')
            target = e.get('target', '')

            if tipo == 'death':
                # Morte de NPC nomeado = perda de entropia
                if target and not target.startswith('NPC_'):
                    delta -= 0.1  # NPC unico
                else:
                    delta -= 0.02  # NPC generico
            elif tipo == 'spawn':
                delta += 0.05  # novidade = ganho
            elif tipo == 'login':
                delta += 0.01  # presenca = ganho

        return max(-1.0, min(1.0, delta))

    def _notificar_world_system(self, eventos: List[Dict], delta_h: float):
        """Notifica o MCRWorldSystem sobre a perturbacao."""
        if self.world_system and hasattr(self.world_system, 'perceber_perturbacao'):
            # Agrupa em um unico evento de perturbacao
            ultimo = eventos[-1] if eventos else {}
            perturbacao = {
                'type': 'world_perturbation',
                'delta_h': delta_h,
                'trigger_event': ultimo,
                'batch_size': len(eventos),
                'timestamp': time.time(),
            }
            self.world_system.perceber_perturbacao(perturbacao)
            print('[WorldObserver] Notificado MCRWorldSystem: delta_h=%.2f, batch=%d' % (
                delta_h, len(eventos)))
        elif self.callback_notificar:
            self.callback_notificar(eventos, delta_h)

    def _processar_fila(self):
        """Processa a fila de eventos acumulados."""
        if not self._fila_eventos:
            return

        agora = time.time()
        if agora - self._ultima_reacao < COOLDOWN_REACAO:
            return  # Ainda em cooldown

        # Pega todos os eventos acumulados
        batch = list(self._fila_eventos)
        self._fila_eventos.clear()

        # Calcula impacto
        delta_h = self._calcular_impacto_entropia(batch)

        # So notifica se impacto significativo
        if abs(delta_h) > 0.05:
            self._notificar_world_system(batch, delta_h)
            self._ultima_reacao = agora
        else:
            print('[WorldObserver] Eventos com impacto irrelevante (%.2f), ignorando.' % delta_h)

    def _loop(self):
        """Loop principal da thread com sleep adaptativo."""
        print('[WorldObserver] Loop iniciado. Arquivo: %s' % EVENTS_FILE)
        while self._ativo:
            try:
                linhas = self._ler_novas_linhas()
                for linha in linhas:
                    self._processar_evento(linha)
                self._processar_fila()
            except Exception as e:
                print('[WorldObserver] Erro no loop: %s' % e)
            time.sleep(self._poll_interval)
