# MANIFESTO MCR

**Status atual do ecossistema:** 8 FASES + Generalização (Fase D)
**Hardware:** Ryzen 7 5800X3D | 32GB RAM | RTX 3080
**Núcleo:** MCR.py (7.072 linhas, 48 classes, stdlib puro)

---

## 1. Arquitetura Atual

### Núcleo Cognitivo (devia/kernel/)

| Componente | Linhas | Função |
|-----------|--------|--------|
| `MCR.py` | 7.072 | 48 classes — cadeias Markov multi-nível acopladas por entropia |
| `LuaSyntaxValidator.py` | 138 | Validação de sintaxe Lua (sandbox LuaJIT + regex) |

### Pipeline de Mundo (mcr/ — 44 módulos)

| Módulo | Função |
|--------|--------|
| `mcr_world_builder.py` | Orquestrador de geração de código Canary (2 modos: padrão/fundação/iterativo) |
| `mcr_world_system.py` | Motor Markoviano com 5 estados (EXPANDIR, CONECTAR, EQUILIBRAR, EVOLUIR, COMPENSAR) |
| `mcr_world_state.py` | Estado persistente em `devia/world_state.json` |
| `mcr_world_chronicle.py` | Crônica narrativa em `devia/world_chronicle.md` |
| `mcr_world_foundation.py` | WorldSeed + validação de coerência + `world_event()` |
| `mcr_world_seed.py` | Semente minimalista via Mistral |
| `mcr_signature_cluster.py` | Descoberta automática de tipos por cluster de APIs |
| `mcr_cold_start.py` | Cold Start tabula rasa (~2s) |

### Inteligência e Validação

| Módulo | Função |
|--------|--------|
| `sanity_validator.py` | **0 APIs hardcoded** — minera do C++/Lua em runtime via tree-sitter |
| `shadow_canary.py` | Ambiente mock LuaJIT + auto-aprendizado por erro |
| `anti_pattern.py` | Classificação de erros + registro no KG |
| `metacognicao.py` | Gateway de Incerteza adaptativo (threshold 70%) |
| `LuaSyntaxValidator.py` | Sandbox Lua + loadstring + correção por LLM |

### Criatividade e Geração

| Módulo | Função |
|--------|--------|
| `emergir.py` | Motor "E se..." conectando conceitos do KG |
| `mcr_radar.py` | Busca semântica em 4 ondas (70/50/30/10%) |
| `golden_templates.py` | Zero LLM, templates Canary canônicos |
| `mcr_idea_to_spec.py` | Ideia → especificação JSON + golden examples |
| `mcr_entity_factory.py` | 3 tiers (template/codificado/quest) |
| `mcr_entity_validator.py` | Validação individual (nome único + coerência) |

### Comunicação

| Módulo | Função |
|--------|--------|
| `bridge_api.py` | HTTP REST :7778 (Grimório C# ↔ Python) |
| `world_observer.py` | Observação de eventos do servidor → entropia |
| `npc_server.py` | Socket TCP :7777 para diálogo NPC |

### Auto-Evolução

| Módulo | Função |
|--------|--------|
| `equacao_mcr.py` | `_EQUACAO_ATUAL` — 15 parâmetros, 8 fórmulas, 4 penalidades |
| `mcr_meta.py` | `PONTE_OTIMA = (5*div + 3*esp + 2*prof) / 10` |
| `mcr_auto_evolution.py` | Mutação de thresholds com medição de entropia |

### Fases Completas (8 + Generalização)

| Fase | Módulos | Descrição |
|------|---------|-----------|
| FASE 1 | `pattern_miner.py` | Tree-sitter → 2.690+ padrões no KG |
| FASE 2 | `metacognicao.py` | Gateway de Incerteza adaptativo |
| FASE 3 | `meta_gap.py`, `auto_curiosidade.py` | Detector de lacunas + thread background |
| FASE 4 | `anti_pattern.py`, `logwatcher_bridge.py`, `anti_pattern_injector.py` | Loop de aprendizado com erros reais |
| FASE 5 | `shadow_canary.py` | Mock LuaJIT com auto-aprendizado |
| FASE 6 | `emergir.py`, `sanity_validator.py` | Motor de criatividade |
| FASE 7 | `npc_server.py`, `dialogue_miner.py`, `dialogue_trainer.py` | NPC Server :7777 |
| FASE 8 | `mcr_self.py`, `mcr_autobiography.py`, `mcr_inner_voice.py`, `mcr_conversa.py` | Consciência |
| FASE D | `mcr_signature_cluster.py`, `mcr_cold_start.py` | Generalização — zero hardcode, aprendizado do zero |

## 2. Validação (Zero Hardcode)

O SanityValidator não possui **nenhuma API hardcoded**. Ele descobre as APIs do servidor em tempo de execução:

1. **C++ source** — minera `server/src/` por `bindClassMemberFunction<...>("nome", ...)`
2. **Scripts Lua** — minera `data-otservbr-global/npc/*.lua` por chamadas de função
3. **Knowledge Graph** — carrega `devia/knowledge/patterns_*.json` (quando existente)

Total: ~561 APIs descobertas dinamicamente.

## 3. Cold Start (Prova de Generalização)

O MCR pode aprender as regras de qualquer servidor do zero em ~2 segundos:

```
cold_start()
├── Apaga Knowledge Graph
├── Minera APIs do C++ (29) + scripts Lua (309)
├── Forma 21+ clusters de assinatura
├── Gera código Canary válido
└── Valida em 3 camadas (sintaxe + semântica + sandbox)
```

## 4. Como Iniciar

```bash
# Terminal único: sobe tudo
python start_mcr_organism.py

# Bridge API (Grimório C#)
python -c "from mcr.bridge_api import BridgeAPI; BridgeAPI().iniciar(); import time; time.sleep(99999)"

# Cold Start (aprender servidor do zero)
python -c "from mcr.mcr_cold_start import cold_start; cold_start()"
```

## 5. Métricas de Performance

| Operação | Tempo | GPU |
|----------|-------|-----|
| Pergunta conceitual (KG) | 0.007s | 0% |
| Geração NPC Tier 1 (template) | <0.001s | 0% |
| Geração NPC Tier 2 (codificar) | ~5-10s | 100% |
| Pipeline iterativo (10 entidades) | ~2.8s | 0% (template) |
| Validação Lua | <0.1s | 0% |
| Cold Start completo | ~1.7s | 0% |
| Mineração AST 2.690+ arquivos | ~2s | 0% |
| NPC Server: 100 req | 100ms | 0% |

**MCR não é AGI. MCR é um experimento de pesquisa honesto.** Os resultados são mensuráveis, mas modestos em termos absolutos.
