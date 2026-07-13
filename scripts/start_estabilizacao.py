#!/usr/bin/env python3
"""start_estabilizacao.py — Inicia o ecossistema MCR em modo de estabilização.

Sobe:
1. WorldObserver (em thread, tail do arquivo de eventos)
2. Bridge API (porta 7778)
3. Simulador de eventos (se servidor Canary offline)

Uso:
    python start_estabilizacao.py              # Modo normal (espera eventos reais)
    python start_estabilizacao.py --simular     # Injeta eventos sintéticos a cada 30s
    python start_estabilizacao.py --simular --intervalo 10  # A cada 10s
"""
import sys, os, json, time, threading, argparse, socket

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
from mcr.world_observer import WorldObserver, EVENTS_FILE
from mcr.bridge_api import BridgeAPI, configurar_observer


# ============================================================
# SIMULADOR DE EVENTOS (usado quando servidor Canary offline)
# ============================================================

EVENTOS_SINTETICOS = [
    # farming area (entropy baixa)
    {"type": "death", "target": "Dragon Lord", "killer": "Hero", "pos": {"x": 100, "y": 200, "z": 7}},
    {"type": "death", "target": "Dragon Lord", "killer": "Hero", "pos": {"x": 100, "y": 200, "z": 7}},
    {"type": "death", "target": "Dragon Lord", "killer": "Hero", "pos": {"x": 100, "y": 200, "z": 7}},
    # spawn area (entropy media)
    {"type": "spawn", "target": "NPC_Ferreiro", "killer": "environment", "pos": {"x": 50, "y": 150, "z": 7}},
    {"type": "spawn", "target": "NPC_Mago", "killer": "environment", "pos": {"x": 50, "y": 150, "z": 7}},
    {"type": "spawn", "target": "NPC_Guard", "killer": "environment", "pos": {"x": 50, "y": 150, "z": 7}},
    # area diversa (entropy alta)
    {"type": "death", "target": "NPC_Trader", "killer": "Player1", "pos": {"x": 200, "y": 300, "z": 7}},
    {"type": "spawn", "target": "NPC_Trader", "killer": "environment", "pos": {"x": 200, "y": 300, "z": 7}},
    {"type": "kill", "target": "Wolf", "killer": "Player1", "pos": {"x": 200, "y": 300, "z": 7}},
    {"type": "login", "target": "Player2", "killer": "player", "pos": {"x": 200, "y": 300, "z": 7}},
    # novos eventos (entropy variavel)
    {"type": "death", "target": "Demon", "killer": "Hero", "pos": {"x": 400, "y": 500, "z": 7}},
    {"type": "kill", "target": "Demon", "killer": "Hero", "pos": {"x": 400, "y": 500, "z": 7}},
    {"type": "death", "target": "Rat", "killer": "Player2", "pos": {"x": 150, "y": 250, "z": 7}},
    {"type": "login", "target": "Player3", "killer": "player", "pos": {"x": 320, "y": 400, "z": 7}},
    {"type": "login", "target": "Player4", "killer": "player", "pos": {"x": 320, "y": 400, "z": 7}},
    {"type": "spawn", "target": "NPC_Bartender", "killer": "environment", "pos": {"x": 300, "y": 350, "z": 7}},
]


def _simular_eventos(observer: WorldObserver, intervalo: int, ativo: threading.Event):
    """Injeta eventos sinteticos em intervalo regular."""
    idx = 0
    print(f'[Simulador] Iniciado (intervalo={intervalo}s)')
    while ativo.is_set():
        evento = EVENTOS_SINTETICOS[idx % len(EVENTOS_SINTETICOS)]
        evento['ts'] = time.strftime('%Y-%m-%dT%H:%M:%S')
        evento['_processed_at'] = time.time()
        observer.injetar_evento(evento)
        idx += 1
        if idx % len(EVENTOS_SINTETICOS) == 0:
            # Mostra metrica a cada ciclo completo
            grid = observer.get_entropy_grid(minutes=60)
            print(f'[Simulador] Ciclo completo. Grid: {len(grid["grid"])} tiles, '
                  f'H_max={grid["max_entropy"]:.2f}, H_min={grid["min_entropy"]:.2f}, '
                  f'total_events={grid["total_events"]}')
        ativo.wait(intervalo)


# ============================================================
# MONITOR
# ============================================================

def _monitorar(observer: WorldObserver, ativo: threading.Event):
    """Monitora estatisticas do observer a cada 15s."""
    while ativo.is_set():
        stats = observer.get_estatisticas()
        grid = observer.get_entropy_grid(minutes=60)
        print(f'[Monitor] Eventos: {stats["total_eventos"]} | '
              f'Tipos: {dict(stats["eventos_por_tipo"])} | '
              f'Fila: {stats["fila_atual"]} | '
              f'Grid: {len(grid["grid"])} tiles | '
              f'H_max: {grid["max_entropy"]:.2f}')
        ativo.wait(15)


# ============================================================
# BLOQUEIO DE DUPLICATA (evita 2 instâncias consumindo I/O)
# ============================================================

def _adquirir_lock() -> bool:
    """Cria socket lock para impedir execução duplicada."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 7779))
        s.listen()
        return True
    except OSError:
        print('[ERRO] start_estabilizacao.py já está rodando (porta 7779 ocupada)')
        return False


# ============================================================
# MAIN
# ============================================================

def main():
    if not _adquirir_lock():
        sys.exit(1)

    parser = argparse.ArgumentParser(description='Estabilizacao MCR-DevIA')
    parser.add_argument('--simular', action='store_true',
                       help='Injetar eventos sinteticos (Canary offline)')
    parser.add_argument('--intervalo', type=int, default=30,
                       help='Intervalo entre eventos sinteticos (s) (default: 30)')
    args = parser.parse_args()

    print('=' * 60)
    print('  MCR-DevIA — Modo Estabilizacao')
    print('=' * 60)
    print()

    # 1. WorldObserver
    observer = WorldObserver()
    observer.iniciar()
    print('[OK] WorldObserver iniciado')
    print(f'     Arquivo de eventos: {EVENTS_FILE}')

    # 2. Configura Bridge
    configurar_observer(observer=observer, world_system=None)

    # 3. Bridge API
    api = BridgeAPI()
    api.iniciar()

    # 4. Verifica se arquivo de eventos ja existe (Canary rodando?)
    eventos_reais = EVENTS_FILE.exists() and EVENTS_FILE.stat().st_size > 0
    if eventos_reais:
        print(f'[OK] Arquivo de eventos real encontrado: {EVENTS_FILE.stat().st_size} bytes')
    else:
        print('[Info] Nenhum arquivo de eventos real encontrado.')

    # 5. Simulador (opcional)
    ativo = threading.Event()
    ativo.set()
    threads = []

    if args.simular or not eventos_reais:
        t_sim = threading.Thread(
            target=_simular_eventos,
            args=(observer, args.intervalo, ativo),
            daemon=True
        )
        t_sim.start()
        threads.append(t_sim)
        print(f'[OK] Simulador de eventos ativo (intervalo={args.intervalo}s)')
    else:
        print('[OK] Aguardando eventos reais do Canary...')

    # 6. Monitor
    t_mon = threading.Thread(
        target=_monitorar,
        args=(observer, ativo),
        daemon=True
    )
    t_mon.start()
    threads.append(t_mon)
    print('[OK] Monitor ativo')

    print()
    print('=' * 60)
    print('  Sistema em estabilizacao.')
    print('  Bridge API: http://127.0.0.1:7778')
    print('  Endpoints:')
    print('    GET  /status')
    print('    GET  /world/events')
    print('    GET  /world/entropy_grid?minutes=10')
    print('    GET  /world/status')
    print('    POST /world/perturb')
    print('    POST /mcr/gerar_npc')
    print('=' * 60)
    print('  Pressione Ctrl+C para parar.')
    print()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\n[Estabilizacao] Parando...')
        ativo.clear()
        api.parar()
        observer.parar()
        print('[Estabilizacao] Sistema parado.')


if __name__ == '__main__':
    main()
