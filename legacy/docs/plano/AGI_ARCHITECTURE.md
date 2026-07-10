# 🧬 ARQUITETURA AGI — MCR-DevIA como Rede Neural Viva

> AUTOR: Cloud + Kheltz
> DATA: 2026-06-30 (atualizado)
> STATUS: FASE 1 ✅ | FASE 2 ✅ | FASE 3 ⏳ | FASE 4 ⏳
> OBJETIVO: Transformar o pipeline linear em uma AGI ciclica autonoma e autosuficiente

---

## Sumario

1. [Status Atual](#-status-atual)
2. [As 5 Camadas da AGI](#-as-5-camadas-da-agi)
3. [Fluxo Completo](#-fluxo-completo)
4. [Plano de Implementacao](#-plano-de-implementacao-detalhado)
5. [Licoes Aprendidas](#-licoes-aprendidas)
6. [Metricas de Sucesso](#-metricas-de-sucesso)

---

## ✅ Status Atual

### FASE 1 — SENSE (COMPLETA — 7/7 no Teste de Verdade)
| Componente | Status | Detalhes |
|------------|--------|----------|
| Security | ✅ | Filtra input malicioso via `verificar_request()` |
| ContextCrew | ✅ | 5 fontes paralelas (KG, WebLearn, Docs, Codigo, Web) |
| EpisodicMemory | ✅ | Busca experiencias passadas similares |
| ContextInfinity | ✅ | Historico de sessao via fragmentos |
| KG.aprender() | ✅ | Toda resposta vira lesson (ctx=resposta_llm, resposta_tool, etc.) |

### FASE 2 — THINK (COMPLETA — LEVE)
| Componente | Status | Detalhes |
|------------|--------|----------|
| Decider | ✅ | Classifica tipo de pergunta (conceito, codigo, lore...) |
| Mente.think() | ✅ | Reflexao 1.5b SEM KG (leve, ~3s, cache de 5min) |
| Conselho | ⏸️ | So para entropia > 0.95 (atualmente nunca ativado) |
| TreeOfThought | ⏸️ | So para modo maximo/complexo |

### FASE 3 — VALIDATE (PENDENTE)
| Componente | Status | Detalhes |
|------------|--------|----------|
| AutoRevisor | ❌ | Detectar alucinacoes pos-LLM |
| Tradutor | ❌ | Garantir PT-BR (resolver encoding) |
| TruncationFixer Fix | ❌ | Impedir que remova `str(...)[:N]` do codigo |

### FASE 4 — LEARN + BACKGROUND (PENDENTE)
| Componente | Status | Detalhes |
|------------|--------|----------|
| EpisodicMemory (LEARN) | ❌ | Registrar experiencia apos cada resposta |
| LessonsBuffer | ❌ | Bufferizar antes de consolidar no KG |
| Emergir | ❌ | Detectar padroes emergentes a cada 5 respostas |
| SelfStudy | ❌ | Escanear codigo a cada 10min em background |

---

## 🧠 As 5 Camadas da AGI

```
┌────────────────────────────────────────────────────────────────────┐
│                    BACKGROUND PROCESSES                            │
│  SelfStudy (10min)  │  Emergir (5 respostas)  │  Watchdog         │
└──────────────────────────┬─────────────────────────────────────────┘
                           │
┌────────────────────────────────────────────────────────────────────┐
│  CICLO AGI (a cada prompt)                                        │
│                                                                     │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐       │
│  │  SENSE   │──▶│  THINK   │──▶│   ACT    │──▶│ VALIDATE │──┐     │
│  │(camada 1)│   │(camada 2)│   │(camada 3)│   │(camada 4)│  │     │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘  │     │
│       │              │              │              │         │     │
│       ▼              ▼              ▼              ▼         │     │
│  Security        Decider        ToolOrch.       V1-V9       │     │
│  ContextCrew     Mente.think    Reconstructor   AutoRevisor  │     │
│  EpisodicMemory                 ContextEnricher Tradutor     │     │
│  ContextInfinity                IA 14b (LLM)                 │     │
│       │              │              │              │         │     │
│       └──────────────┴──────────────┴──────────────┘         │     │
│                                                              │     │
│  ┌──────────┐                                                │     │
│  │  LEARN   │◀───────────────────────────────────────────────┘     │
│  │(camada 5)│                                                       │
│  └────┬─────┘                                                       │
│       │                                                             │
│       ├─→ KG.aprender() — guarda licao                              │
│       ├─→ EpisodicMemory — guarda experiencia                       │
│       └─→ ContextInfinity — adiciona ao contexto ativo              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Fluxo Completo Atual

```
INPUT (Kheltz)
    ↓
[SENSE] ← FASE 1 ✅
    ├─ Security: verificar_request(texto)
    ├─ ContextCrew: 5 fontes paralelas (KG, WebLearn, Docs, Codigo, Web)
    ├─ EpisodicMemory: buscar experiencias similares
    └─ ContextInfinity: buscar fragmentos do historico
    ↓
[THINK] ← FASE 2 ✅
    ├─ Decider.classificar() → "conceito" / "codigo" / "lore"
    └─ Mente.think(tipo, kg=None) → 1.5b, ~3s, sem KG
    ↓
[ACT] ← FASE 1 + 2 ✅
    ├─ PiEngine.avaliar_entropia() → decide escape vs cascade
    ├─ ESCAPE: Pi → Tool (padroes conhecidos, retorno rapido)
    └─ CASCADE: (perguntas conceituais)
         ├─ Tool (os.walk, sem filtro)
         ├─ KG Weaver (fingerprint + keyword boost no erro)
         ├─ ContextEnricher (lore, dados tecnicos)
         └─ LLM 14b (sintese com TODO contexto limitado a ~7K chars)
    ↓
[VALIDATE] ← PARCIAL
    ├─ V1-V9: ValidationPipeline (nota 0-10)
    ├─ V9 Gate: se cobertura < 30%, loop com mais contexto
    └─ AutoRevisor: ❌ PENDENTE
    ↓
[LEARN] ← FASE 1 ✅
    ├─ KG.aprender() → toda resposta vira lesson
    └─ ContextInfinity → fragmento no historico
    ↓
OUTPUT → Kheltz
```

---

## 📋 Plano de Implementacao Detalhado

### ETAPA 0 — FIX TruncationFixer (PRE-FASE 3)

**Problema**: `truncation_fixer.py` linha 17 tem regex `(?<!sys\.path)\[\s*\:[\s\w\d]+\]` que remove `[:1500]`, `[:2000]` etc. do codigo.

**Solucao**: Adicionar `str\(.*?\)\[:\d+\]` como excecao no `_PADRAO_EXCECOES`.

| # | Arquivo | O que | Linhas |
|---|---------|-------|--------|
| 0a | `modulos/truncation_fixer.py` | Adicionar `str\(.*?\)\[:\d+\]` ao regex de excecoes | ~1 |
| 0b | `modulos/pipeline_executor.py` | Reaplicar `[:1000]`, `[:1500]`, `[:2000]` etc. (serao preservados) | ~7 |

---

### FASE 3 — VALIDATE (Garantia de Qualidade)

**Objetivo**: Garantir que a resposta final seja limpa, sem alucinacoes, em PT-BR correto.

#### Etapa 3.1 — AutoRevisor (pos-LLM)

**O que faz**: Detecta classes inventadas, nomes inconsistentes, expansoes erradas de siglas.
**Quando**: Executa APOS o LLM gerar a resposta, ANTES de retornar ao usuario.
**Como integra**: No `pipeline_executor.py`, nivel `llm` — depois de `self.ia.gerar()`, chamar `AutoRevisor.revisar(resposta)`.

```python
# pseudo-codigo
resposta = self.ia.gerar(prompt, 0.3, 'pesado')
# AutoRevisor
from modulos.auto_revisor import revisar as _revisar
correcoes = _revisar(resposta, texto)  # texto = pergunta original
if correcoes:
    resposta = correcoes  # substitui por versao corrigida
```

| # | Arquivo | O que | Linhas |
|---|---------|-------|--------|
| 3.1 | `pipeline_executor.py` | Chamar AutoRevisor.revisar() pos-LLM | ~10 |
| - | `modulos/auto_revisor.py` | Nao precisa modificar — ja tem `revisar()` | 0 |

#### Etapa 3.2 — Tradutor (PT-BR)

**O que faz**: Garante que a resposta esteja em PT-BR correto. Usa IA para traduzir se necessario.
**Quando**: ULTIMO passo antes de retornar.
**Como integra**: No `pipeline_executor.py`, depois do AutoRevisor.

```python
from modulos.tradutor import traduzir as _traduzir
resposta = _traduzir(resposta)  # Se ja estiver em PT-BR, retorna igual
```

| # | Arquivo | O que | Linhas |
|---|---------|-------|--------|
| 3.2 | `pipeline_executor.py` | Chamar Tradutor.traduzir() como ultimo passo | ~3 |

---

### FASE 4 — LEARN + BACKGROUND (Auto-Evolucao)

**Objetivo**: Sistema aprende continuamente e evolui sozinho.

#### Etapa 4.1 — EpisodicMemory.registrar() (LEARN)

**O que faz**: Registra a experiencia completa (pergunta + resposta + licao) na memoria episodica.
**Como integra**: No `pipeline_executor.py`, no bloco LEARN apos `KG.aprender()`.

| # | Arquivo | O que | Linhas |
|---|---------|-------|--------|
| 4.1 | `pipeline_executor.py` | Chamar EpisodicMemory.registrar() apos cada resposta | ~8 |

#### Etapa 4.2 — LessonsBuffer

**O que faz**: Bufferiza lessons antes de consolidar no KG. Evita escritas frequentes em disco.
**Como integra**: O `KG.aprender()` ja existe. O buffer e intermediario.

| # | Arquivo | O que | Linhas |
|---|---------|-------|--------|
| 4.2 | `modulos/lessons_buffer.py` | Nao precisa modificar — ja existe | 0 |

#### Etapa 4.3 — Emergir (Padroes Emergentes)

**O que faz**: A cada 5 interacoes do usuario, amostra topicos distantes no KG, combina de forma criativa, detecta se o padrao e novo, e aprende no KG.
**Como integra**: No `pipeline_executor.py`, a cada N execuções chamar `emergir._processar_emergencia()`.
**Contexto**: Ja existe em `modulos/emergir.py` e no `MasterAgent`.

```python
# a cada 5 execucoes
if hasattr(self, '_exec_count'):
    self._exec_count += 1
else:
    self._exec_count = 0
if self._exec_count % 5 == 0:
    from modulos.emergir import processar_emergencia
    processar_emergencia(self.kg, self.ia)
```

| # | Arquivo | O que | Linhas |
|---|---------|-------|--------|
| 4.3 | `pipeline_executor.py` | A cada 5 execs, chamar Emergir | ~8 |
| - | `modulos/emergir.py` | Nao precisa modificar | 0 |

#### Etapa 4.4 — SelfStudy (Auto-Conhecimento)

**O que faz**: Escaneia o codigo fonte, detecta metricas (arquivos, linhas, classes, funcoes), gera sugestoes de melhoria, salva no KG.
**Como integra**: Roda em background a cada 10 minutos. Pode ser disparado pelo Kernel ou por thread separada.

```python
# No kernel.py ou pipeline_executor.py startup
import threading
def _background_self_study():
    while True:
        time.sleep(600)  # 10 minutos
        from modulos.self_study import executar as _ss
        _ss()

threading.Thread(target=_background_self_study, daemon=True).start()
```

| # | Arquivo | O que | Linhas |
|---|---------|-------|--------|
| 4.4 | `kernel.py` | Thread background SelfStudy a cada 10min | ~10 |
| - | `modulos/self_study.py` | Nao precisa modificar | 0 |

---

### FASE 5 — TESTE FINAL

| Etapa | O que fazer | Criterio |
|-------|-------------|----------|
| 5.1 | Rodar `test_verdade.py` | 7/7 PASS |
| 5.2 | Rodar com `modo_ia="zero"` | Pi + Tool funcionando sem LLM |
| 5.3 | Verificar tempo medio | < 60s por pergunta |
| 5.4 | Verificar KG nao poluido | Sem lessons `resposta_*` ativas |

---

## 🐛 Licoes Aprendidas (desta sessao)

| Licao | Impacto |
|-------|---------|
| **TruncationFixer remove `[:N]` do codigo** | `str(x)[:1500]` era removido silenciosamente — prompt ficava com 156K chars, modelo perdia contexto |
| **Keyword boost no erro (nao na solucao)** | Todas as lessons seed tinham "MCR" na solucao → boost invalido. Restrito ao `erro` funciona |
| **Contexto do LLM precisa ser limitado** | Cada secao <2000 chars, total <7K chars. Modelo 14b tem 4096 tokens (~16K chars) |
| **Mente.think() sem KG** | Antes passava KG inteiro (376K chars) → 120s por pergunta. Sem KG → ~3s por pergunta |
| **Fingerprint puro nao distingue lessons similares** | Todas as lessons conceituais tem "Tibia/OTServ/MCR" → fingerprint similar. Keyword boost no erro resolve |
| **Enricher gera 156K chars de lixo** | "tecnico_detalhes" gera codigo Lua em massa. Rejeitado pelo validador mas ainda poluia o prompt |
| **Respostas curtas sao aceitaveis** | 43 chars para "Eridanus" e correto — nao ha documentacao alem disso |

---

## 📊 Metricas de Sucesso

```
TESTE DE VERDADE (test_verdade.py):
  7/7 PASS → QUALIDADE REAL = 10/10 ✅ (atingido)
  6/7 PASS → QUALIDADE REAL = 8.6/10
  5/7 PASS → QUALIDADE REAL = 7.1/10

TEMPO DE RESPOSTA (7 perguntas):
  FASE 1 original:      260.8s (37.3s/pergunta)
  FASE 1 + SENSE:       284.3s (40.6s/pergunta)
  FASE 2 + THINK leve:  312.7s (44.7s/pergunta)
  Meta:                 < 420s (60s/pergunta)

QUALIDADE REAL DAS RESPOSTAS:
  Todas corretas. 04_ERIDANUS minimalista (43 chars) mas correta.
  02_SPA incluiu "estados de alma" — terminologia REAL do projeto, nao alucinacao.
```

---

## 🗺️ Proximas Etapas (ordem de execucao)

```
1. Fix TruncationFixer  (~1 linha)  → 5 min
2. AutoRevisor         (~10 linhas) → 15 min
3. Tradutor            (~3 linhas)  → 5 min
4. EpisodicMemory LEARN (~8 linhas) → 10 min
5. Emergir             (~8 linhas)  → 10 min
6. SelfStudy           (~10 linhas) → 10 min
7. Teste final         (test_verdade.py) → 5 min
                         TOTAL: ~60 min
```

---

## 🆕 FASE D — Roteamento Aprendido + Auto-Consciência

### FASE A1 — Roteamento Aprendido (FAST voting + PatternEngine + PiEngine)

**Objetivo**: Substituir cascata fixa de decisões por roteamento dinâmico baseado em fingerprint, entropia e votação do FAST model.

| Componente | Status | Detalhes |
|-----------|--------|----------|
| FAST voting (1.5b, 1 token) | ✅ | Votação Y/N do Conselho Leve para perguntas de entropia < 0.7 |
| FAST voting rotas A/B/C | ✅ | FAST (1.5b) decide rota: A=template, B=Conselho+Orq, C=ReAct |
| PatternEngine fingerprint | ✅ | `_pe.fingerprint()` gera hash semântico do texto para detectar perguntas similares |
| PiEngine entropia | ✅ | `_pi.avaliar_entropia(texto)` — mede quão ambígua é a pergunta |
| KG.buscar_rotas() | ✅ | Busca lessons com mesmo fingerprint no KG, retorna rotas passadas com score |

**Fluxo atual do THINK → ACT**:
```
THINK
  ├─ Mente.think() → reflexão 1.5b (~3s, cache 5min, SEM KG)
  ├─ Decider.classificar_com_fast() → A-G (FAST 1.5b ultra_leve)
  └─ PiEngine.avaliar_entropia() → 0.0-1.0
    ↓
ACT (roteamento dinâmico)
  ├─ SE entropia < 0.7 + Y/N vote → rota A (template 0 IA) ou B (Conselho)
  └─ SENÃO → FAST voting A/B/C + PatternEngine fingerprint + KG.buscar_rotas()
       ├─ A = KG + identidade + template (0 IA, < 5s)
       ├─ B = Conselho + Orquestrador (~15s)
       └─ C = ReAct completo (~30s, ferramentas)
```

### Progresso FASE D

| Etapa | Status | Descrição |
|-------|--------|-----------|
| D-01 | ✅ | Decider.classificar_com_fast() — A-G com ultra_leve, cache semântico 20 entradas |
| D-02 | ✅ | V12 Contexto — busca 0 IA no KG antes do pipeline completo |
| D-03 | ✅ | AutoRepair.reparar_com_validacao() — loop 3x com validação |
| D-04 | ✅ | cmd_criar + cmd_fazer — aliases para o pipeline |
| D-05 | ✅ | AutoConsciência — mesmo erro >2x + IA falhando >2x |
| D-06 | ⏳ | KG.buscar_rotas() integrado ao roteamento dinâmico |

### Ciclo SENSE → THINK → ACT → VALIDATE → LEARN (atualizado)

```
INPUT
  ↓
[SENSE]
  ├─ Security: filtrar input malicioso
  ├─ V12 Contexto: busca 0 IA no KG (keyword seed)
  ├─ ContextCrew: 5 fontes (KG, WebLearn, Docs, Código, Web)
  ├─ EpisodicMemory: experiências passadas similares
  ├─ ContextInfinity: histórico da sessão
  └─ KG Seed: múltiplos termos-chave (siglas + Dominios/SHC/MCR)
  ↓
[THINK]
  ├─ Decider.classificar_com_fast() → A-G (1.5b, 1 token)
  ├─ Mente.think() → reflexão (1.5b, ~3s, cache 5min)
  └─ PiEngine.avaliar_entropia() → decisão Escape ou Cascade
  ↓
[ACT]
  ├─ FAST voting A/B/C + PatternEngine + KG.buscar_rotas()
  ├─ Rota A → template direto (0 IA, <5s)
  ├─ Rota B → Conselho + Orquestrador (~15s)
  └─ Rota C → ReAct loop (LLM decide ferramentas, ~30s)
  ↓
[VALIDATE]
  ├─ V1-V9 ValidationPipeline (fatos, sem notas)
  ├─ V9 Gate: se cobertura < 30%, loop com mais contexto
  ├─ AutoRevisor: heurística anti-alucinação
  └─ Tradutor: garante PT-BR
  ↓
[LEARN] ← FASE 1 ✅ + FASE 4 ⏳
  ├─ KG.aprender() → toda resposta vira lesson
  ├─ EpisodicMemory.registrar() → guarda experiência
  ├─ ContextInfinity → fragmento no histórico
  ├─ Emergir → a cada 5 execuções, detecta padrões
  └─ SelfStudy → thread background a cada 10min
  ↓
OUTPUT
```
