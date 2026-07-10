# MCR

> 1 equação. N níveis. 0 hardcode. 0 nuvem.

MCR é um motor de **reconhecimento de padrões e geração por assinatura** que opera em múltiplos níveis de abstração simultaneamente. Python stdlib, zero dependências externas para o núcleo — nada de GPU, nada de nuvem.

```python
MCR(nivel).aprender(a, b)  # aprende que "a" leva a "b"
MCR(nivel).predizer(a)      # "b" mais provável dado "a"
```

---

## O Núcleo Universal

### Equação MCR

```
PONTE_OTIMA = (divergencia × 5 + especificidade × 3 + profundidade × 2) / 10
PENALIDADE  = dispersao_entropica / niveis_validos
NOTA_FINAL  = PONTE_OTIMA × (1 − PENALIDADE)
```

Todos os thresholds, pesos e decisões emergem dos dados. Nenhum valor fixo. A equação se aplica a qualquer domínio: texto, código, binário, áudio, sequências numéricas.

### Kernel Markov Multi-Nível

| Capacidade | Descrição |
|-----------|-----------|
| **8 níveis** | Byte → palavra → token → intenção → decisão → assinatura → filosofia → qualidade |
| **Acoplamento N-Dimensional** | Correlação cross-level via matriz de acoplamento |
| **Superposição** | Duas cadeias colidem → token que nenhuma preveria sozinha |
| **Auto-Validação** | Validação recursiva por entropia, sem ground truth |
| **Criticalidade** | Auto-modificação na borda do caos (entropia 0.2–0.7) |
| **Fingerprinting** | Projeção 8–128D com auto-descoberta de dimensão |
| **HDC** | Bundle, bind, permute, analogia vetorial |
| **Auto-Evolução** | Mutação de thresholds com medição de impacto na entropia |

### Kernel Refatorado

O núcleo monolito (`MCR.py`, ~7K linhas, 48 classes) está sendo modularizado em `devia/kernel/mcr_kernel/` (10 módulos):

| Módulo | Função |
|--------|--------|
| `engine.py` | Motor principal — `compose_state()`, `compor_contexto()`, `gerar()` |
| `decisor.py` | Decisões adaptativas — Ponte Ótima para pular parser |
| `signature.py` | Assinatura multidimensional — `raw_token_set()`, fingerprint |
| `memory.py` | Memória hierárquica — persistência entre sessões |
| `meta.py` | Metacognição — auto-avaliação sobre o próprio kernel |
| `evolution.py` | Auto-evolução — mutação e seleção de parâmetros |
| `state.py` | Gerenciamento de estado do kernel |
| `system.py` | Coordenação entre módulos |
| `feedback.py` | Loop de feedback para aprendizado |
| `persistence.py` | Serialização e salvamento |

---

## Aplicação Atual: GMA Station (Tibia OTServ)

Tibia é o **berço** do MCR — o primeiro domínio de aplicação onde o sistema está sendo validado em produção. A Game Master Artificial Station conecta o kernel Markov a LLMs locais (Ollama) para gerar, curar e gerenciar conteúdo de servidores OTServ.

```
HTTP SSE :8765 ─── Web Console (Alpine.js)
     │
  Pipeline de Mundo
     │
  ┌──┴───────────────────────┐
  │  mcr_kernel              │
  │  MCR.py (Markov)         │
  │  Ensemble 7B             │
  │  Chain-of-Verification   │
  └──┬───────────────────────┘
     │
  ┌──┴──────────┐    ┌──────────────┐
  │ WPF Grimório│    │ Bridge API   │
  │ (C# .NET 8) │    │ (:7778 REST) │
  └─────────────┘    └──────┬───────┘
                            │
                     ┌──────┴──────┐
                     │ Ollama      │
                     │ (:11434)    │
                     └─────────────┘
```

### Pipeline de Mundo (58 módulos em `mcr/`)

| Módulo | Função |
|--------|--------|
| `pipeline_completo.py` | Orquestrador: VERIFICAR → INJETAR → LLM → ANOMALY → CANONIZAR |
| `sse_server.py` | Servidor HTTP SSE + REST (:8765) + chat streaming |
| `prompts_criativos.py` | Roteador de modelos + templates de prompt |
| `world_anomaly_detector.py` | Detecção adaptativa de anacronismos por entropia |
| `world_observer.py` | Observação de eventos → perturbações de entropia |
| `seed_world.py` | Canonização de conteúdo no banco de mundo |
| `ensemble_7b.py` | Ensemble paralelo 3 modelos (Mistral/Qwen/DeepSeek) |
| `chain_of_verification.py` | Pós-geração: verificação contra grafo de conhecimento |
| `cache_hierarquico.py` | Cache L1→L2→L3 (dict→Markov→fingerprint→LLM) |
| `bridge_api.py` | HTTP REST (:7778) — interface Python ↔ C# |
| `raw_miner.py` | Tokenização raw sem tree-sitter (85% coverage) |
| +47 outros | — |

### Painel WPF (`tools/grimorio/`)

Interface administrativa C# .NET 8 com abas de Dashboard, NPCs, Quests, Scripts, Items, Database, Map, Config. Integração com Bridge API e SSE Server. Heatmap de entropia com overlay no mapa.

### Web Console (`mcr/sse_server.py` + `mcr/templates/dashboard.html`)

Interface web com Alpine.js, 6 abas, streaming de chat em tempo real (tokens caractere por caractere), telemetria de entropia, tema escuro, zero pop-ups.

---

## Modelos (Ollama)

| Modelo | Contexto | Função |
|--------|----------|--------|
| `qwen2.5-coder:7b-32k` | 32K | Geração de código, estrutura |
| `mistral:7b-32k` | 32K | Narrativa, NPCs, quests, lore |
| `deepseek-r1:7b-32k` | 32K | Ensemble fallback, raciocínio |

Benchmark: Mistral 7B → melhor criatividade; Qwen 7B → melhor código.

---

## Estrutura

```
E:/MCR/
├── mcr/                       # 58 módulos — pipeline de mundo
│   ├── sse_server.py          # Servidor web + streaming
│   ├── pipeline_completo.py   # Orquestrador de geração
│   ├── templates/             # Web Console (dashboard.html)
│   └── ...
├── devia/
│   ├── kernel/
│   │   ├── MCR.py             # Núcleo Markov (48 classes, ~7K linhas)
│   │   └── mcr_kernel/        # Kernel refatorado (10 módulos)
│   ├── world_state.json       # Estado do mundo
│   └── world_chronicle.md     # Crônica narrativa
├── tools/
│   └── grimorio/              # Painel admin C# WPF
├── docs/                      # Documentação atual
│   ├── HISTORIA_MCR.md        # História completa (438 commits, 13 fases)
│   ├── MCR_WHITEPAPER_*.md    # Whitepapers acadêmicos
│   └── ...
├── legacy/                    # Arquivo morto (histórico preservado)
├── server/                    # Canary OTServ (sub-repo)
├── client/                    # OTClient (sub-repo)
└── golden_examples/           # Exemplos canônicos
```

---

## Setup

```powershell
# Núcleo (stdlib Python, sem instalação):
python -c "from devia.kernel.MCR import MCRMotor; print('MCR pronto')"

# Aplicação Tibia:
# 1. Instalar Ollama
# 2. ollama pull qwen2.5-coder:7b-32k
# 3. ollama pull mistral:7b-32k
# 4. python mcr/sse_server.py
# 5. http://localhost:8765
```

---

## Licença

**AGPL v3** ou licença comercial. Veja [LICENSE](LICENSE) e [LICENCA_COMERCIAL.md](LICENCA_COMERCIAL.md).

---

## Autor

**Kheltz** — Pesquisador independente.
