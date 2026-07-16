# MCR — Motor Cognitivo Universal

> **1 Equação (Sigmoide 5D). 1 Entropia (Shannon). 1 Markov (1ª ordem). N domínios.**

MCR é um framework cognitivo que usa cadeias de Markov de 1ª ordem com entropia de Shannon e uma equação sigmoide 5D para perceber, decidir, executar, avaliar e aprender. **A mesma equação avalia qualquer saída** — NPC de Tibia, sprite PNG, texto, ou qualquer domínio.

**Sem GPU. Sem nuvem. Sem LLM obrigatório.**

```python
from mcr import MCR
mcr = MCR()
mcr.auto_treinar()
npc = mcr.processar("Crie um ferreiro anão")      # gera Lua válido
sprite = mcr.processar("Gere um sprite de escudo") # gera PNG
```

---

## Arquitetura

```
                EQUAÇÃO 5D + ENTROPIA + MARKOV
                          │
                          ▼
              ┌───────────────────────┐
              │         MCR           │
              │   Cognição Universal  │
              │                       │
              │  perceber → decidir   │
              │  → executar →         │
              │  avaliar → aprender   │
              └───────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
      ┌───────┐     ┌──────────┐     ┌─────────┐
      │ TIBIA │     │  VISUAL  │     │ (áudio, │
      │(prova)│     │  (prova) │     │  outro  │
      └───────┘     └──────────┘     └─────────┘
```

3 domínios funcionais. O motor é o mesmo — só as ferramentas mudam.

---

## O Núcleo

### Equação MCR — Sigmoide 5D (fonte: `mcr/equacao_mcr.py`)

```
NOTA = σ(θ · (soma_ponderada − τ))
     = 1 / (1 + e^(−θ · (s̄ − τ)))
```

**5 dimensões ortogonais** (pesos `{2,2,2,2,2}`):

| Dimensão | Peso | O que mede |
|----------|------|------------|
| **Certeza** | 2 | Confiança da predição Markov (0-1) |
| **Completude** | 2 | Checks estruturais passados / total (0-1) |
| **Informação** | 2 | Entropia Shannon normalizada da saída (0-1) |
| **Estabilidade** | 2 | Gaussiana da entropia (pune loops e caos) |
| **Eficiência** | 2 | 1/log₂(n_tools+1) — recompensa simplicidade |

**Parâmetros:** `θ = 2.0` (inclinação), `τ = 0.35` (limiar de ruído — abaixo disso nota ≈ 0)

**Penalidades dinâmicas:** `compartilhado=0`, `parcial=0.3`, `byte=0.7`, `none=0.9`

**AutoEvolution** pode mutar todos os parâmetros (pesos, θ, τ, penalidades, thresholds).

### Motor Markov — 1ª ordem com contexto composto

| Componente | Arquivo | Função |
|-----------|---------|--------|
| `MCR` (MarkovEngine) | `mcr/engine.py` | Markov 1ª ordem: aprender, predizer, entropia, Jaccard |
| `MCRFingerprint` | `mcr/signature.py` | Fingerprint 8D (categorias de byte) |
| `MCRSignature` | `mcr/signature.py` | Extração de assinatura (entropia, estados, top-5) |
| `compose_state` | `mcr/engine.py` | Contexto composto no nome do estado (mitiga Markov 1ª ordem) |

### Pipeline Unificado

| Estágio | Descrição |
|---------|-----------|
| **Perceber** | Extrai 31 níveis de fingerprint do input (intrínsecos + derivados + estruturais + domínio) |
| **Decidir** | Superposição de 4 distribuições: Markov + coupling palavras + cluster + posições |
| **Executar** | Registry seleciona ferramenta → fallback por taxa de sucesso |
| **Avaliar** | Sigmoide 5D (certeza × completude × informação × estabilidade × eficiência) |
| **Aprender** | Markov reforça transições (3× se nota > 0.7) + coupling + esfera + KG + SQLite |

---

## Estrutura do Projeto (atual)

```
mcr/
├── mcr.py                     ← Cognição unificada (3426 linhas)
├── engine.py                  ← Núcleo Markov (463 linhas)
├── signature.py               ← MCRFingerprint, MCRSignature (258 linhas)
├── equacao_mcr.py             ← Sigmoide 5D (120 linhas)
├── coupling.py                ← Acoplamento palavra→ação
├── registry.py                ← Registry de ferramentas
├── bootstrap.py               ← Bootstrap e descoberta de módulos
├── conselho_multi.py          ← Conselho multi-agente (744 linhas, 11 arquétipos)
├── metacognicao.py            ← Gateway de incerteza (311 linhas)
├── auto_curiosidade.py        ← Auto-estudo em background
├── mcr_auto_evolution.py      ← Mutação de parâmetros da equação
├── evolution.py               ← Algoritmo evolutivo (5 classes)
├── hdc_core.py                ← Hyperdimensional Computing (10k-dim)
├── hdc_kg_memory.py           ← Memória HDC + SDM
├── rag_mcr.py                 ← RAG com ChromaDB
├── sse_server.py              ← Servidor SSE (porta 8765)
├── bridge_api.py              ← Bridge API REST
├── lua_validator.py           ← Validador Lua Canary
├── sanity_validator.py        ← Validador de APIs Canary (6445 APIs)
├── conhecimento/              ← Knowledge system
│   ├── kg.py                  ← Knowledge Graph (500 linhas)
│   ├── episodic_memory.py     ← Memória episódica (356 linhas)
│   ├── memoria_compactada.py  ← Memória fragmentada por data
│   ├── lessons_buffer.py      ← Buffer de lições
│   ├── canary_indexer.py      ← Indexador Canary (540 linhas)
│   └── item_database.py       ← Item Database (505 linhas)
│
nichos/tibia/mcr/              ← Geradores Tibia (NPCs, monstros, sprites)
│
tests/                         ← Testes (105 em tests/real/, 57 passam)
├── real/                      ← Suíte de testes reais
│
docs/                          ← Documentação
```

---

## Domínios Comprovados

### Prova 1: Tibia (Geração de Conteúdo)

| Ferramenta | Descrição | Tier |
|-----------|-----------|------|
| `gerar_npc_lua` | NPC Canary via template (zero LLM, 0ms) | 1 |
| `gerar_monstro_lua` | Monstro Canary via template | 1 |
| `mcr_world_builder` | Geração LLM com validação Sanity+Shadow | 2-3 |
| `dialogue_trainer` | Treino Markov com 448 NPCs, 4529 diálogos | — |
| `lua_validator` | Validação sintática + SQL injection + boas práticas | — |
| `sanity_validator` | 6445 APIs Canary conhecidas (zero hardcode) | — |

### Prova 2: Visual (Geração de Sprites)

| Ferramenta | Descrição |
|-----------|-----------|
| `sprite_corpus` | Corpus de sprites categorizados + extração B/L/F |
| `MCRDiscriminador` | Avalia qualidade via P(token | contexto) |
| `mcr_sprite_motor` | Motor 4-níveis Markov (byte, palavra, token, cor) |
| `template_entropico` | Template Shannon: baixa H = fixo, alta H = criativo |
| `regioes_anatomicas` | Segmentação projeção 1D + clusterização CIELAB |

---

## Conselho Multi-Agente (V10)

11 arquétipos executados em paralelo com router de modelos:

| Arquétipo | Modelo Ollama | Função |
|-----------|---------------|--------|
| Analista | `mistral:7b` | Dados e fatos concretos |
| Crítico | `mistral:7b` | Riscos e problemas |
| Estrategista | `mistral:7b` | Visão geral e planejamento |
| Arquiteto | `qwen2.5-coder:14b` | Design de sistemas |
| Contador de Histórias | `mistral:7b` | Lore e narrativa |
| Revisor de Código | `qwen2.5-coder:14b` | Segurança e boas práticas |
| Psicólogo | `phi4-mini` | Análise do processo |
| Técnico | `qwen2.5-coder:14b` | Implementação |
| Especialista | `qwen2.5-coder:14b` | Conhecimento profundo |
| Filósofo | `mistral:7b` | Reflexão |
| Criativo | `phi4-mini` (temp alta) | Ideias novas |

Inclui: **TreeOfThought** (3 perspectivas), **Debate Protocol**, **Validação anti-alucinação**, **Prompt Cache**.

---

## Setup

```powershell
# Núcleo (zero dependências):
python -c "from mcr import MCR; print('MCR pronto')"

# Com auto-treinamento:
python -c "from mcr import MCR; m = MCR(); m.auto_treinar()"

# Conselho multi-agente (requer Ollama):
# 1. ollama pull qwen2.5-coder:14b
# 2. ollama pull mistral:7b
# 3. ollama pull phi4-mini:latest
# 4. python -c "from mcr.conselho_multi import Conselho; c=Conselho(); r=c.deliberar('sua pergunta')"

# Servidor SSE:
# python mcr/sse_server.py
# http://localhost:8765
```

---

## Estado Atual

| Métrica | Valor |
|---------|-------|
| Linhas de código (`mcr/`) | ~6500 |
| Módulos Python | 65+ |
| Ferramentas registradas | ~130+ |
| Equação | Sigmoide 5D (θ=2.0, τ=0.35) |
| Arquétipos do Conselho | 11 |
| Testes automáticos | 105 (57 passam, 48 falham por módulos legados) |
| NPCs treinados (diálogo) | 448 |
| Diálogos aprendidos | 4529 |
| APIs Canary conhecidas | 6445 |
| Código Lua gerado | ✅ Estruturalmente válido |

---

## Limitações Honestas

1. **Markov de 1ª ordem.** O motor só vê o estado atual. `compose_state()` mitiga compondo contexto no nome do estado, mas o limite é fundamental.

2. **Classificação depende de seeds.** O MCR classifica entradas comparando com estados pré-treinados. Sem seeds suficientes, a confiança é baixa.

3. **Semântica complexa requer LLM.** O pipeline Tier 2-3 usa Ollama para descrições ricas. O MCR decide quando usar LLM via superposição entrópica.

4. **Equação 5D com parâmetros mutáveis.** `mcr_auto_evolution` pode reajustá-los, mas o processo é lento.

5. **Módulos legados não migrados.** `devia.*`, `golden_templates`, `cielab` existem sob `nichos/tibia/mcr/` mas não estão no path correto.

6. **Testes com falhas.** 48/105 testes falham por `ModuleNotFoundError` — módulos movidos para `nichos/tibia/mcr/`.

---

## Licença

**AGPL v3** ou licença comercial. Consulte o autor.

---

## Autor

**Kheltz** — Pesquisador independente.
