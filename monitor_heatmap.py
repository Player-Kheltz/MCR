#!/usr/bin/env python3
"""monitor_heatmap.py — Consulta o estado do heatmap e exibe métricas.

Uso:
    python monitor_heatmap.py                    # Mostra heatmap atual
    python monitor_heatmap.py --watch             # Atualiza a cada 10s
"""
import sys, os, json, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import urllib.request


def consultar_heatmap(minutes=10):
    """GET /world/entropy_grid e exibe resultado."""
    try:
        url = f'http://127.0.0.1:7778/world/entropy_grid?minutes={minutes}'
        resp = urllib.request.urlopen(url, timeout=5)
        data = json.loads(resp.read())
        
        print(f'Status: {data.get("status", "?")}')
        print(f'Total eventos: {data.get("total_events", 0)}')
        print(f'Coordenadas unicas: {len(data.get("grid", []))}')
        print(f'Entropia: max={data.get("max_entropy", 0):.3f}, min={data.get("min_entropy", 0):.3f}')
        print()
        
        grid = data.get('grid', [])
        # Ordena por entropia decrescente
        grid.sort(key=lambda p: -p['entropy'])
        
        print(f'Top 10 tiles (maior entropia):')
        for p in grid[:10]:
            cor = _entropy_color(p['entropy'], data.get('min_entropy', 0), data.get('max_entropy', 1))
            print(f'  ({p["x"]:>4}, {p["y"]:>4}, {p["z"]})  '
                  f'H={p["entropy"]:.3f}  events={p["event_count"]}  {cor}')
        
        print()
        print(f'Bottom 5 tiles (menor entropia):')
        for p in grid[-5:]:
            cor = _entropy_color(p['entropy'], data.get('min_entropy', 0), data.get('max_entropy', 1))
            print(f'  ({p["x"]:>4}, {p["y"]:>4}, {p["z"]})  '
                  f'H={p["entropy"]:.3f}  events={p["event_count"]}  {cor}')
        
        return data
    except urllib.error.URLError as e:
        print(f'[ERRO] Bridge API offline: {e.reason}')
        return None
    except Exception as e:
        print(f'[ERRO] {e}')
        return None


def consultar_status():
    """GET /world/status e exibe."""
    try:
        resp = urllib.request.urlopen('http://127.0.0.1:7778/world/status', timeout=5)
        data = json.loads(resp.read())
        wo = data.get('world_observer', {})
        ws = data.get('world_state', {})
        print('WorldObserver:', json.dumps(wo, indent=2))
        print('WorldState:', json.dumps(ws, indent=2)[:300])
    except Exception as e:
        print(f'[ERRO] Status: {e}')


def _entropy_color(h, h_min, h_max):
    """Simula a cor do heatmap no terminal."""
    norm = 0.0
    rng = max(h_max - h_min, 0.01)
    norm = (h - h_min) / rng
    norm = max(0, min(1, norm))
    
    if norm < 0.33:
        return '\033[94m[AZUL]\033[0m'      # Baixa
    elif norm < 0.66:
        return '\033[93m[AMARELO]\033[0m'   # Media
    else:
        return '\033[91m[VERMELHO]\033[0m'  # Alta


def main():
    parser = argparse.ArgumentParser(description='Monitor do Heatmap MCR')
    parser.add_argument('--watch', action='store_true', help='Atualizar a cada 10s')
    parser.add_argument('--minutes', type=int, default=10, help='Janela de minutos')
    args = parser.parse_args()
    
    if args.watch:
        ciclo = 0
        while True:
            print(f'\n=== Ciclo {ciclo} - {time.strftime("%H:%M:%S")} ===')
            consultar_heatmap(args.minutes)
            ciclo += 1
            time.sleep(10)
    else:
        consultar_heatmap(args.minutes)
        print()
        consultar_status()


if __name__ == '__main__':
    main()
