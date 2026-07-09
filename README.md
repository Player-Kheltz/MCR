# MCR

> 1 equação. N níveis. 0 hardcode.

```python
MCR(nivel).aprender(a, b)  # learns that "a" leads to "b"
MCR(nivel).predizer(a)      # most probable "b" given "a"
```

MCR é um experimento de pesquisa. Não é uma AGI, não é um produto, não é um negócio.
Apenas stdlib. Zero GPU necessário para decisões.

## O Que Realmente Faz

### Núcleo (devia/kernel/MCR.py — 7072 linhas, 48 classes)

| Capacidade | Como |
|-----------|------|
|-----------|-----|
| **Multi-level Markov** | Byte, palavra, token, decisão, threshold, assinatura, filosofia, qualidade |
| **N-Dimensional Coupling** | Cross-level correlation via coupling matrix + esfera |
| **Superposition** | Two Markov chains collide → novel token neither predicted alone |
| **Auto-Validation** | Recursive self-validation by entropy |
| **Criticality** | Self-modification at the edge of chaos (entropy 0.2–0.7) |
| **Fingerprinting** | 8–128D projection with auto-dimensionality discovery |
| **HDC** | Bundle, bind, permute, analogy: `rei − homem + mulher → rainha` |
| **Semantic Parsing** | Extracts (subject, relation, object) triples from Portuguese text |
| **Relational State Space** | subject→relation→object chains + transitive BFS |
| **Self-Evolution** | `MCRAutoEvolution` — mutates thresholds, measures entropy impact, accepts/rejects |

### Pipeline de Mundo (44 módulos em mcr/)

| Módulo | Função |
|--------|--------|
| `mcr_world_builder.py` | Geração de código Lua Canary com validação dupla (sintaxe + semântica) |
| `mcr_radar.py` | Busca semântica em 4 ondas (70/50/30/10% threshold) |
| `emergir.py` | Motor de criatividade "E se..." conectando conceitos do KG |
| `sanity_validator.py` | **0 APIs hardcoded** — minera APIs do C++ e Lua em runtime via tree-sitter |
| `shadow_canary.py` | Ambiente mock LuaJIT + auto-aprendizado por erro |
| `mcr_world_system.py` | Orquestrador Markoviano com 5 estados (EXPANDIR/CONECTAR/EQUILIBRAR/EVOLUIR/COMPENSAR) |
| `mcr_world_state.py` | Estado do mundo persistente em `devia/world_state.json` |
| `mcr_world_chronicle.py` | Crônica narrativa em `devia/world_chronicle.md` |
| `mcr_world_foundation.py` | WorldSeed + validação de coerência temática + `world_event()` |
| `mcr_signature_cluster.py` | Descoberta automática de tipos por cluster de APIs (27 clusters de 2.691 entidades) |
| `mcr_cold_start.py` | Cold Start tabula rasa — aprende regras de qualquer servidor em ~2s |
| `golden_templates.py` | Templates zero-LLM, 100% canônicos Canary |
| `bridge_api.py` | HTTP REST :7778 — interface para Grimório C# |
| `world_observer.py` | Observação de eventos do servidor → perturbações de entropia |
| `metacognicao.py` | Gateway de Incerteza — threshold adaptativo 70% |
| `anti_pattern.py` | Classificação de erros Lua + registro no KG |
| `pattern_miner.py` | Tree-sitter AST → 2.690+ padrões no KG |
| `mcr_entity_factory.py` | 3 tiers (template/codificado/quest) |
| `mcr_entity_validator.py` | Validação individual de entidades |
| `mcr_idea_to_spec.py` | Ideia → especificação JSON via LLM + golden examples |
| `mcr_world_seed.py` | Semente minimalista (world_name + concepts) via Mistral |
| `equacao_mcr.py` | Fonte da verdade: `_EQUACAO_ATUAL` com 15 parâmetros, 8 fórmulas |
| `mcr_meta.py` | Auto-avaliação via `PONTE_OTIMA = (5*div + 3*esp + 2*prof) / 10` |
| `mcr_auto_evolution.py` | Mutação de thresholds com medição de entropia |
| `npc_server.py` | Servidor TCP :7777 para diálogo NPC |
| +19 outros | — |

### Validação (3 camadas)

| Camada | O que faz | Como |
|--------|-----------|------|
| **LuaValidator** | Verifica sintaxe Lua | Sandbox LuaJIT + regex fallback |
| **SanityValidator** | Verifica APIs contra KG | 0 APIs hardcoded — minera do C++ em runtime |
| **Shadow Canary** | Execução mock Lua | Detecta crashes antes da produção + auto-aprendizado |

### Cold Start (Agnóstico de Domínio)

O MCR pode ser plugado em qualquer servidor OTServ (ou qualquer projeto de código) e aprender suas regras do zero:

```
cold_start()
├── Apaga Knowledge Graph
├── Minera APIs do C++ e Lua (tree-sitter)
├── Forma clusters de assinatura (27 clusters de 2.691 entidades)
├── Constrói meta-clusters (Monster group: 1.657, NPC group: 1.034)
├── Gera código válido (SanityValidator + LuaValidator + Shadow Canary)
└── Aprende com erros de execução (penalidades Markov)
```

~2 segundos. Zero intervenção humana.

### Serviços de Rede

| Serviço | Porta | Função |
|---------|-------|--------|
| NPC Server | 7777 | Socket TCP — diálogo NPC em tempo real |
| Bridge API | 7778 | HTTP REST — interface Python↔C# |
| Ollama | 11434 | LLM local (qwen2.5-coder:7b, mistral:7b) |

---

## Arquitetura

```
                      ┌──────────────────────┐
                      │     Bridge API       │
                      │     (:7778 REST)     │
                      └──────┬───────┬───────┘
                             │       │
              ┌──────────────┘       └──────────────┐
              ▼                                      ▼
   ┌──────────────────┐                  ┌─────────────────────┐
   │  Grimório C# WPF │                  │  WorldObserver      │
   │  (Painel Admin)  │                  │  (Eventos Servidor) │
   └──────────────────┘                  └─────────────────────┘
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │ MCRWorldSystem   │
                                          │ (Loop Markov)    │
                                          └─────────────────┘
                                                   │
                                      ┌────────────┼────────────┐
                                      ▼            ▼            ▼
                               ┌──────────┐ ┌──────────┐ ┌──────────┐
                               │ Emergir  │ │ RadarMCR │ │ expandir │
                               │ (Ideias) │ │ (Busca)  │ │ (Injecao)│
                               └──────────┘ └──────────┘ └──────────┘
```

---

## Arquivos

```
E:/MCR/
├── devia/kernel/MCR.py       # 7072 lines, 48 classes — núcleo Markov
├── mcr/                       # 44 módulos Python
├── server/                    # Canary (Tibia OT)
├── client/                    # OTClient (jogadores)
├── tools/
│   ├── grimorio/              # Painel admin C# WPF
│   └── login-server/          # Login server HTTP
├── devia/
│   ├── knowledge/             # Knowledge Graph
│   ├── world_state.json       # Estado do mundo
│   └── world_chronicle.md     # Crônica narrativa
└── docs/                      # Documentação
```

---

## Filosofia

> **Entropia é uma coordenada, não uma métrica.**
> Ela mede onde o sistema está no espaço N-dimensional — não quão "bom" ou "ruim" ele é.

> **Criticalidade, não otimização.**
> O sistema busca a borda do caos (entropia 0.2–0.7), não entropia zero. Sistemas mortos têm entropia zero. Aprendizado acontece na fronteira.

> **Observação, não controle.**
> O MCR é um observador em um sistema aberto. Ele não pode prevenir flutuações de entropia. Ele aprende com o que não pode controlar.

> **Emergência, não programação.**
> Novas dimensões se autodescobrem. Cadeias colidem em novidade. A topologia emerge dos dados. Nenhum humano decide o que o sistema deve encontrar.

---

## Licença

Dupla licença: AGPL v3 (código aberto) ou licença comercial. Veja [LICENSE](LICENSE) e [LICENCA_COMERCIAL.md](LICENCA_COMERCIAL.md).

---

## Autor

**Kheltz** — Pesquisador independente.
