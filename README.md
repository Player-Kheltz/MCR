# MCR — Game Master Artificial (GMA) Station

Sistema de geração, curadoria e gestão de conteúdo para servidores **Tibia OTServ** (Canary).
Opera localmente com Ollama para criatividade e kernel Markov para decisões. Zero dependências de nuvem.

```
HTTP SSE :8765 ─── Web Console (Alpine.js)
     │
  Pipeline GMA
     │
  ┌──┴───────────────────────┐
  │  mcr_kernel (Markov)     │
  │  MCR.py (48 classes)     │
  │  WorldAnomalyDetector    │
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

---

## Componentes

### Pipeline de Geração (58 módulos em `mcr/`)

| Módulo | Função |
|--------|--------|
| `pipeline_completo.py` | Orquestrador: VERIFICAR → INJETAR_CONTEXTO → LLM → ANOMALY_CHECK → CANONIZAR |
| `sse_server.py` | Servidor HTTP SSE + REST (porta 8765) + chat streaming |
| `prompts_criativos.py` | Model router (Mistral→narrativa, Qwen→código, DeepSeek→fallback) + templates |
| `world_anomaly_detector.py` | Detecção adaptativa de anacronismos por entropia |
| `world_observer.py` | Observação de eventos do servidor → perturbações de entropia |
| `world_state.py` | Estado do mundo persistente em `devia/world_state.json` |
| `world_chronicle.py` | Crônica narrativa em `devia/world_chronicle.md` |
| `seed_world.py` | Canonização de conteúdo existente no banco de mundo |
| `bridge_api.py` | HTTP REST :7778 — interface Python ↔ C# Grimório |
| `ensemble_7b.py` | Ensemble paralelo 3 modelos com juiz Jaccard |
| `chain_of_verification.py` | Pós-geração: verificação contra KG |
| `cache_hierarquico.py` | Cache L1→L2→L3 (dict→Markov→fingerprint→LLM) |
| `prompt_compressor.py` | Compressão de contexto para janela 32K |
| `signature_cluster.py` | Descoberta automática de tipos por cluster de APIs |
| `anti_pattern.py` | Classificação de erros + registro no KG |
| `pattern_miner.py` | Tree-sitter AST → padrões no KG |
| `raw_miner.py` | Tokenização raw sem tree-sitter (85% coverage) |
| `seed_markov.py` | Seed de cadeias Markov para bootstrap |
| `shadow_canary.py` | Ambiente mock LuaJIT + auto-aprendizado |
| `sanity_validator.py` | Validação de APIs contra KG (0 hardcoded) |
| `mcr_auto_evolution.py` | Mutação de thresholds com medição de entropia |
| `npc_server.py` | Servidor TCP :7777 para diálogo NPC |
| `entity_factory.py` | 3 tiers (template/codificado/quest) |
| `entity_validator.py` | Validação individual de entidades |
| `idea_to_spec.py` | Ideia → especificação JSON via LLM + golden examples |
| `world_foundation.py` | WorldSeed + coerência temática |
| `metacognicao.py` | Gateway de Incerteza — threshold adaptativo |
| +31 outros | — |

### Núcleo Markov (`devia/kernel/`)

| Capacidade | Como |
|-----------|------|
| Multi-level Markov | Byte, palavra, token, decisão, threshold, assinatura |
| N-Dimensional Coupling | Matriz de acoplamento cross-level + esfera |
| Superposition | Duas cadeias colidem → token que nenhuma preveria sozinha |
| Auto-Validation | Validação recursiva por entropia |
| Criticality | Auto-modificação na borda do caos (entropia 0.2–0.7) |
| Fingerprinting | Projeção 8–128D com auto-descoberta de dimensão |
| HDC | Bundle, bind, permute, analogia |
| Self-Evolution | MCRAutoEvolution — muta thresholds, mede impacto |
| Kernel Refatorado | `mcr_kernel/` (10 módulos: engine, decisor, signature, memory, etc.) |

### Painel WPF (`tools/grimorio/`)

- Interface administrativa C# .NET 8
- Abas: Dashboard, NPCs, Quests, Scripts, Items, Database, Map, Config
- Integração com Bridge API (:7778) + SSE Server (:8765)
- Heatmap de entropia com overlay no mapa

### Web Console (`mcr/sse_server.py` + `mcr/templates/dashboard.html`)

- Interface web Alpine.js com 6 abas
- Streaming de chat (tokens aparecem caractere por caractere)
- Telemetria de entropia em tempo real
- Sidebar colapsável, tema escuro
- Zero pop-ups ou modais

---

## Serviços de Rede

| Serviço | Porta | Tecnologia | Função |
|---------|-------|-----------|--------|
| SSE Server | 8765 | Python ThreadingHTTPServer | API REST + SSE + chat streaming |
| Bridge API | 7778 | Python HTTP | Interface Python ↔ C# |
| NPC Server | 7777 | Socket TCP | Diálogo NPC em tempo real |
| Ollama | 11434 | Local | LLMs (qwen2.5-coder:7b-32k, mistral:7b-32k, deepseek-r1:7b-32k) |

---

## Modelos

| Modelo | Contexto | Função |
|--------|----------|--------|
| `qwen2.5-coder:7b-32k` | 32K | Geração de código, estrutura |
| `mistral:7b-32k` | 32K | Narrativa, NPCs, quests, lore |
| `deepseek-r1:7b-32k` | 32K | Ensemble fallback, raciocínio |

Benchmark: Mistral 7B → melhor para criatividade; Qwen 7B → melhor para código.

---

## Estrutura de Diretórios

```
E:/MCR/
├── mcr/                       # 58 módulos — pipeline GMA
│   ├── sse_server.py          # Servidor web + streaming
│   ├── pipeline_completo.py   # Orquestrador de geração
│   ├── templates/             # Web Console (dashboard.html)
│   └── ...
├── devia/
│   ├── kernel/
│   │   ├── MCR.py             # Núcleo Markov (48 classes)
│   │   └── mcr_kernel/        # Kernel refatorado (10 módulos)
│   ├── world_state.json       # Estado do mundo (40+ NPCs, lore)
│   └── world_chronicle.md     # Crônica narrativa
├── tools/
│   └── grimorio/              # Painel admin C# WPF
├── docs/                      # Documentação atual
│   ├── HISTORIA_MCR.md        # História completa do projeto
│   ├── MCR_WHITEPAPER*.md     # Whitepapers
│   └── ...
├── legacy/                    # Arquivo morto (histórico)
│   ├── scripts/               # Scripts antigos
│   └── docs/                  # Documentação arquivada
├── server/                    # Canary OTServ (sub-repo)
├── client/                    # OTClient (sub-repo)
└── golden_examples/           # Exemplos canônicos
```

---

## Setup Rápido

```powershell
# 1. Instalar Python 3.10+ (stdlib apenas)

# 2. Instalar Ollama
winget install Ollama.Ollama

# 3. Baixar modelos 32K
ollama pull qwen2.5-coder:7b-32k
ollama pull mistral:7b-32k
ollama pull deepseek-r1:7b-32k

# 4. Iniciar servidor SSE
python mcr/sse_server.py

# 5. Abrir navegador
# http://localhost:8765

# Pipeline completa (gerar NPC, quest ou lore):
python mcr/pipeline_completo.py --tipo npc --ideia "um mago ancião em Thais"

# Worldbuilding inicial:
python mcr/seed_world.py
```

---

## Licença

Dupla licença: **AGPL v3** (código aberto) ou licença comercial.
Veja [LICENSE](LICENSE) e [LICENCA_COMERCIAL.md](LICENCA_COMERCIAL.md).

---

## Autor

**Kheltz** — Pesquisador independente.
