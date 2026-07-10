# Heatmap de Entropia — Radar Cognitivo do Mundo

## Visão Geral

O Heatmap de Entropia transforma a Aba Mapa do Grimório em um radar
cognitivo, colorindo as coordenadas do mapa de acordo com a diversidade
de eventos observados em cada tile. A cor reflete a entropia de Shannon
da distribuição de tipos de evento naquela coordenada.

## Fluxo de Dados

```
Servidor Canary (Lua)
  │ os.date() + pos.x/y/z
  ▼
mcr_events.jsonl
  │ tail (1s)
  ▼
WorldObserver.get_entropy_grid(minutes=10)
  │ Agrupa eventos por (x, y, z)
  │ Calcula H = -Σpᵢ·log₂(pᵢ) para cada tile
  │ Normaliza H / log₂(n_tipos) → [0, 1]
  ▼
Bridge API: GET /world/entropy_grid?minutes=10
  │ Retorna {grid, max_entropy, min_entropy, total_events}
  ▼
Grimório WPF (MapView)
  │ Polling a cada 10s (só quando heatmap ativo)
  │ Interpola cor: 0=Azul → 0.5=Amarelo → 1.0=Vermelho
  ▼
Overlay semi-transparente sobre o mapa
```

## Endpoint

```
GET http://127.0.0.1:7778/world/entropy_grid?minutes=10
```

### Resposta

```json
{
  "status": "ok",
  "grid": [
    {"x": 100, "y": 200, "z": 7, "entropy": 0.9183, "event_count": 3},
    {"x": 400, "y": 500, "z": 7, "entropy": 1.0, "event_count": 2}
  ],
  "max_entropy": 1.0,
  "min_entropy": 0.0,
  "total_events": 20
}
```

| Campo | Descrição |
|-------|-----------|
| `grid` | Lista de pontos com entropia |
| `grid[].x` | Coordenada X do tile (Tibia) |
| `grid[].y` | Coordenada Y do tile |
| `grid[].z` | Piso |
| `grid[].entropy` | Entropia normalizada [0, 1] |
| `grid[].event_count` | Total de eventos naquele tile |
| `max_entropy` | Maior entropia no grid (para escala de cor) |
| `min_entropy` | Menor entropia no grid |
| `total_events` | Total de eventos na janela de tempo |

## Interpretação da Entropia

| Valor | Significado | Cor |
|-------|-------------|-----|
| 0.0 | Mesmo tipo de evento repetido (farming, spawn único) | Azul |
| ~0.5 | Tipos misturados (ex.: death + spawn) | Amarelo |
| 1.0 | Máxima diversidade (death, spawn, kill, login) | Vermelho |

A escala usa `min_entropy` e `max_entropy` da resposta para se adaptar
dinamicamente à amplitude dos dados, sem thresholds fixos.

## WPF: Como Usar

1. Abra o Grimório, navegue para a Aba **Mapa**
2. Carregue um arquivo `.otbm` (ou use o auto-detect)
3. Clique no botão **"🔥 Heatmap"** na toolbar
4. O mapa exibirá quadrados coloridos sobrepondo as áreas com eventos
5. A atualização ocorre a cada 10 segundos (enquanto o toggle estiver ativo)
6. Para desligar, clique novamente em "🔥 Heatmap"

### Resiliência
- Se a Bridge API estiver offline, exibe "Heatmap: Bridge API indisponivel"
- Grid vazio é tratado como informação válida (não desenha nada)
- A atualização só ocorre quando o toggle está ativo

## Arquivos Modificados

| Arquivo | Mudança |
|---------|---------|
| `mcr/world_observer.py` | Novo método `get_entropy_grid(minutes)` |
| `mcr/bridge_api.py` | Nova rota `GET /world/entropy_grid` |
| `mcr/test_events.jsonl` | 20 eventos simulados para teste |
| `tools/grimorio/Models/EntropyPoint.cs` | Modelos `EntropyPoint` + `EntropyGridResponse` |
| `tools/grimorio/Core/MinimapRenderer.cs` | Novo método `DrawEntropyGrid()` |
| `tools/grimorio/Modules/Map/MapView.xaml` | Botão "🔥 Heatmap" na toolbar |
| `tools/grimorio/Modules/Map/MapView.xaml.cs` | `RefreshHeatmapLoop()`, `ToggleHeatmap_Click()` |
| `tools/grimorio/Modules/Map/MapViewModel.cs` | Propriedades `HeatmapVisible`, `EntropyGrid` |

## Exemplo de Teste

```bash
# 1. Iniciar Bridge com observer
python -c "
import sys; sys.path.insert(0, 'E:/MCR')
from mcr.world_observer import WorldObserver
from mcr.bridge_api import BridgeAPI, configurar_observer

observer = WorldObserver()
# Injetar eventos de teste
with open('mcr/test_events.jsonl') as f:
    for line in f:
        if line.strip():
            observer._processar_evento(line.strip())
configurar_observer(observer=observer)
api = BridgeAPI(); api.iniciar()
import time; time.sleep(1)

# 2. Verificar grid (usando HTTP)
import urllib.request, json
resp = urllib.request.urlopen('http://127.0.0.1:7778/world/entropy_grid?minutes=60')
print(json.dumps(json.loads(resp.read()), indent=2))
api.parar()
"
```

## Próximos Passos

- Opção 3: Estados Compostos (`compose_state()`) para superar limite da Markov 1ª ordem
- Opção 4: Fase E — terceiro domínio (Java/Python do próprio MCR)
