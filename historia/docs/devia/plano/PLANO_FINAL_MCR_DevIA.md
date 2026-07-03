# PLANO FINAL — MCR-DevIA: ARRUMAR E OTIMIZAR

> **Aprovado em:** 2026-06-28
> **Sessão de revisão:** Cloud (assistente) revisou sistema completo, usuário aprovou tudo
> **Total:** 28 tarefas em 7 fases
> **Estimativa:** ~7 horas de trabalho
> **Prioridade:** Limpeza estrutural → Otimizacao → Qualidade → Future-proof

---

## SUMARIO

- [Fase 1 — Limpeza Estrutural](#-fase-1--limpeza-estrutural)
- [Fase 2 — Otimizacao de Modulos](#-fase-2--otimizacao-de-modulos)
- [Fase 3 — Sistema de Arquivos](#-fase-3--sistema-de-arquivos)
- [Fase 4 — Testes e Qualidade](#-fase-4--testes-e-qualidade)
- [Fase 5 — V12 e Cache Inteligente](#-fase-5--v12-e-cache-inteligente)
- [Fase 6 — Knowledge Graph Real](#-fase-6--knowledge-graph-real)
- [Fase 7 — Correcoes Pontuais](#-fase-7--correcoes-pontuais)
- [Dependencias Entre Fases](#-dependencias-entre-fases)
- [Registro de Decisoes](#-registro-de-decisoes)

---

## 🔴 FASE 1 — LIMPEZA ESTRUTURAL

> **Prioridade: PRIMEIRO.** Base para tudo. Remove sujeira, duplicacao e arquivos mortos.
> **Esforco total:** ~1 hora

---

### 1.1 — Config de modelos: DEDUP

| Campo | Detalhe |
|-------|---------|
| **O que** | `util.py` tem `_get_modelo()` com dict proprio de modelos — duplicado de `ia.py` |
| **Onde** | `modulos/util.py:45-80`, `modulos/ia.py:32-57` |
| **Como** | `util.py` importa `MODELOS` de `ia.py` em vez de ter o seu proprio |
| **Codigo** | `from modulos.ia import MODELOS as _IA_MODELOS` e usa `_IA_MODELOS.get(tarefa, ...)` |
| **Risco** | Baixo — refatoracao de import |
| **Tempo** | 15 min |
| **Aprovado** | ✅ Sim |

### 1.2 — KG: TAGGEAR stress_test

| Campo | Detalhe |
|-------|---------|
| **O que** | 100 lessons com `ctx=stress_test` poluem a busca semântica |
| **Onde** | `sandbox/.mcr_devia/knowledge.json` |
| **Como** | Adicionar campo `"tipo": "benchmark"` nas 100 lessons de stress. Modificar `kg.buscar()` para filtrar `tipo=benchmark` em consultas normais |
| **Codigo** | `if l.get('tipo') == 'benchmark' and not query_benchmark: continue` |
| **Risco** | Baixo — lessons intactas, so ganham tag |
| **Tempo** | 20 min |
| **Nota** | Lessons de benchmark continuam uteis para metricas de performance, mas nao poluem conhecimento de dominio |
| **Aprovado** | ✅ Sim |

### 1.3 — engine/ → LEGADO

| Campo | Detalhe |
|-------|---------|
| **O que** | `engine/` (5 arquivos, 1.457 linhas, 11 classes) — marcado EXPERIMENTAL, 0 imports no codigo ativo |
| **Onde** | `scripts/mcr_devia/engine/` |
| **Como** | Mover para `/Legado/engine/` |
| **Conteudo** | `executor.py` (220 linhas, 2 classes), `gap_detector.py` (453 linhas, 4 classes), `meta_creator.py` (354 linhas, 2 classes), `task_analyzer.py` (425 linhas, 3 classes) |
| **Risco** | Baixo — nada importa desses arquivos |
| **Tempo** | 5 min |
| **Aprovado** | ✅ Sim |

### 1.4 — strategies/ → LEGADO + EXTRAIR items_xml

| Campo | Detalhe |
|-------|---------|
| **O que** | `strategies/` (7 arquivos, 824 linhas, 7 classes) — marcado EXPERIMENTAL, 0 imports |
| **Onde** | `scripts/mcr_devia/strategies/` |
| **Extrair antes** | `items_xml.py` (162 linhas) — logica de busca fuzzy em items.xml. **Extrair** como ferramenta `buscar_item_canary()` no ToolOrchestrator |
| **Mover** | Restante do `strategies/` → `/Legado/strategies/` |
| **Risco** | Baixo — extracao limpa, funcionalidade nova opcional |
| **Tempo** | 30 min (15 extrair + 5 mover + 10 testar) |
| **Aprovado** | ✅ Sim |

### 1.5 — templates/ (VAZIO) → APAGAR

| Campo | Detalhe |
|-------|---------|
| **O que** | Diretorio `templates/` existe mas esta **VAZIO** (0 arquivos) |
| **Onde** | `scripts/mcr_devia/templates/` |
| **Como** | Deletar o diretorio |
| **Risco** | Baixo |
| **Tempo** | 2 min |
| **Aprovado** | ✅ Sim |

### 1.6 — personalidades/ → LEGADO

| Campo | Detalhe |
|-------|---------|
| **O que** | Conselho gera arquetipos dinamicamente agora — diretorio nao usado |
| **Onde** | `scripts/mcr_devia/personalidades/` |
| **Como** | Mover para `/Legado/personalidades/` |
| **Risco** | Baixo |
| **Tempo** | 2 min |
| **Aprovado** | ✅ Sim |

### 1.7 — _archive/ → LEGADO

| Campo | Detalhe |
|-------|---------|
| **O que** | 10 scripts legados (corrida_final_absoluta, crew_deepseek, input_pipeline, etc) |
| **Onde** | `scripts/mcr_devia/_archive/` |
| **Como** | Mover para `/Legado/_archive/` |
| **Risco** | Baixo |
| **Tempo** | 3 min |
| **Aprovado** | ✅ Sim |

### 1.8 — MCR_DevIA-Legado.py → REMOVER

| Campo | Detalhe |
|-------|---------|
| **O que** | Alias de compatibilidade de 7 linhas |
| **Onde** | `scripts/mcr_devia/MCR_DevIA-Legado.py` |
| **Como** | Deletar o arquivo |
| **Risco** | Baixo — nada importa esse alias |
| **Tempo** | 1 min |
| **Aprovado** | ✅ Sim |

---

## 🟡 FASE 2 — OTIMIZACAO DE MODULOS

> **Prioridade: SEGUNDO.** Melhorar arquitetura interna sem mudar comportamento externo.
> **Esforco total:** ~55 minutos

---

### 2.1 — Conselho: KEYWORD → DECIDER

| Campo | Detalhe |
|-------|---------|
| **O que** | `_classificar()` em `conselho.py:228-254` usa `if any(k in t for k in lista_de_keywords)` — hardcode que o Decider deveria substituir |
| **Onde** | `modulos/conselho.py` |
| **Como** | Substituir `_classificar()` por `Decider.classificar()` com exemplos |
| **Exemplos** | `"crie um ferreiro em lua" → "codigo"`, `"o que e SPA?" → "factual"`, `"crie lore de Eridanus" → "ambientacao"` |
| **Risco** | Medio — precisa testar classificacao depois (bateria) |
| **Tempo** | 20 min |
| **Aprovado** | ✅ Sim (com testes depois) |

### 2.2 — Mente: 1.5b no router em vez de hardcode

| Campo | Detalhe |
|-------|---------|
| **Decisao final** | Mente mantem 1.5b para **classificacao rapida** (System 1). Mas em vez de hardcode `_MODELO_MENTE = "qwen2.5-coder:1.5b"`, usa o router padrao com tarefa `"leve"` |
| **Onde** | `modulos/mente.py:18` |
| **Como** | Substituir chamada direta ao Ollama por `ia.fast(prompt, 0.1, 'leve')` |
| **Motivo** | Fonte unica de config. Se um dia o modelo `"leve"` mudar no router, a Mente acompanha |
| **Risco** | Baixo — 1.5b continua sendo o modelo da categoria `"leve"` no router |
| **Tempo** | 10 min |
| **Aprovado** | ✅ Sim |

### 2.3 — Watchdog: SIMPLIFICAR

| Campo | Detalhe |
|-------|---------|
| **O que** | Watchdog tem 3 responsabilidades, mas 2 nunca sao usadas |
| **Onde** | `modulos/watchdog.py` |
| **Manter** | ✅ Monitoramento de `sandbox/.mcr_conversa.jsonl` para ContextInfinity |
| **Manter** | ✅ Indice invertido para ContextCrew |
| **Remover** | ❌ Hot-reload de comandos (kernel ja carrega sob demanda) |
| **Remover** | ❌ Auto-revisao de sandbox (nunca disparou) |
| **Risco** | Baixo |
| **Tempo** | 15 min |
| **Aprovado** | ✅ Sim |

### 2.4 — stop_words: UNIFICAR

| Campo | Detalhe |
|-------|---------|
| **O que** | `kg.py` e `episodic_memory.py` tem listas de stop words proprias — duplicadas |
| **Onde** | `modulos/kg.py:43-53`, `modulos/episodic_memory.py:28-34`, `stop_words.py` |
| **Como** | Usar `stop_words.py` como fonte unica. `kg.py` e `episodic_memory.py` importam de la |
| **Risco** | Baixo |
| **Tempo** | 10 min |
| **Aprovado** | ✅ Sim |

---

## 🟡 FASE 3 — SISTEMA DE ARQUIVOS (regras anti-lixo)

> **Prioridade: TERCEIRO.** Onde criar o que. Organizacao que se auto-mantem.
> **Esforco total:** ~20 minutos

---

### 3.1 — Estrutura de diretorios final

```
sandbox/
├── .mcr_devia/              ← Estado interno (auto-gerenciado pelo sistema)
│   ├── knowledge.json           Lessons do KG
│   ├── lessons_buffer.json      Buffer de lessons (batch embedding)
│   ├── context_cache.jsonl      Cache de contexto unificado (fragmentos)
│   ├── session_cache.json       SessionCache persistente (conversa)
│   ├── conselho_memoria/        Memoria individual dos membros do Conselho
│   ├── weblearn/               Pesquisas web anteriores
│   └── crews/                  Crews do ContextCrew
│
├── output/                   ← Resultados gerados (organizado por tipo)
│   ├── npcs/                     Scripts Lua de NPCs gerados
│   ├── projetos/                 Projetos completos gerados
│   ├── analises/                 Analises de codigo
│   └── relatorios/               Relatorios de teste/bateria
│
├── testes/                   ← Testes e baterias (prefixo _test_ obrigatorio)
│   ├── _test_bateria.py
│   ├── _test_auto_repair.py
│   ├── _test_decider.py
│   ├── _test_master.py
│   ├── _test_tool_orchestrator.py
│   ├── _test_validador.py
│   └── ... (outros mantidos)
│
└── temp/                     ← Experimentos temporarios (AUTO-LIMPO no startup!)
    └── (dura so 1 sessao — deletado se > 24h)
```

### 3.2 — Regras de uso

| Diretorio | Para | Regra |
|-----------|------|-------|
| `output/npcs/` | Scripts Lua de NPCs validados | Sub-dir por cidade/tipo |
| `output/projetos/` | Projetos completos (Python, JS, etc) | Um diretorio por projeto |
| `output/analises/` | Resultados de analise de codigo | Nome descritivo |
| `output/relatorios/` | Relatorios de teste/bateria | `relatorio_{data}.json` |
| `testes/` | Scripts de teste | Prefixo `_test_` obrigatorio |
| `temp/` | Qualquer experimento novo | **Auto-deletado no startup** se > 24h |

### 3.3 — Auto-cleanup no startup

Adicionar no `kernel.py` (ou `MCR_DevIA-Kernel.py`):

```python
def _auto_cleanup():
    """Limpa diretorios temporarios e caches antigos no startup."""
    import shutil, time
    
    # temp/ — deleta tudo com mais de 24h
    temp_dir = os.path.join(SANDBOX, 'temp')
    if os.path.exists(temp_dir):
        agora = time.time()
        for item in os.listdir(temp_dir):
            path = os.path.join(temp_dir, item)
            try:
                idade = agora - os.path.getmtime(path)
                if idade > 86400:  # 24h
                    if os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                    else:
                        os.remove(path)
            except:
                pass
```

| Risco | Baixo |
|-------|-------|
| **Tempo** | 20 min |
| **Aprovado** | ✅ Sim |

---

## 🔴 FASE 4 — TESTES E QUALIDADE

> **Prioridade: PARALELO A FASE 1.** Fazer os testes refletirem a realidade do sistema.
> **Esforco total:** ~1h05

---

### 4.1 — Refazer bateria de testes

| Campo | Detalhe |
|-------|---------|
| **O que** | Rodar `_test_bateria.py` novamente com as correcoes ja aplicadas |
| **Ultimo resultado** | 1/3 aprovados (33%) — JS falhou por sintaxe, FastAPI por dependencia ausente |
| **Expectativa atual** | ~100% (AutoRepair corrige JS, Geracao Consciente detecta dependencias) |
| **Se falhar** | Investigar e ajustar imediatamente |
| **Tempo** | 30 min |
| **Aprovado** | ✅ Sim |

### 4.2 — Revisar cmd_autoteste

| Campo | Detalhe |
|-------|---------|
| **O que** | Atualizar `cmd_autoteste.py` para refletir o pipeline atual (MasterAgent, Conselho, SessionCache) |
| **Onde** | `comandos/cmd_autoteste.py` |
| **Tempo** | 15 min |
| **Aprovado** | ✅ Sim |

### 4.3 — Consolidar testes

| Campo | Detalhe |
|-------|---------|
| **O que** | Dos 32 testes em `sandbox/testes/`, manter os relevantes e arquivar one-offs |
| **Manter (6)** | `_test_bateria.py`, `_test_auto_repair.py`, `_test_decider.py`, `_test_master.py`, `_test_tool_orchestrator.py`, `_test_validador.py` |
| **Arquivar (26)** | Mover para `/Legado/testes/` — testes one-off ja validados de features antigas |
| **Tempo** | 20 min |
| **Aprovado** | ✅ Sim |

---

## 🟡 FASE 5 — V12 E CACHE INTELIGENTE

> **Prioridade: QUARTO.** Respostas V12 confiaveis + cache fragmentado que nunca expira.
> **Esforco total:** ~2h35

---

### 5.1 — V12 com confidence threshold

| Campo | Detalhe |
|-------|---------|
| **O que** | V12 so deve responder se tiver **confianca ≥ 70%** na lesson encontrada |
| **Calculo** | Similaridade cosseno entre embedding da pergunta e embedding da lesson |
| **Fluxo** | Pergunta → busca KG → similarity ≥ 70%? → Sim: V12 expande. Nao: chama LLM completo |
| **Onde** | `modulos/kg.py` + onde o dispatch V12 acontece |
| **Risco** | Baixo — fallback para LLM se confianca baixa |
| **Tempo** | 20 min |
| **Aprovado** | ✅ Sim |

### 5.2 — V12 + ContextInfinity: staleness check

| Campo | Detalhe |
|-------|---------|
| **O que** | Verificar se lesson do V12 esta desatualizada antes de usar |
| **Ciclo** | Lesson tem `time_sensitive: false`? → usa direto (0 custo). `true` e +7 dias? → websearch rapido. Achou novo? → FAST revisa. Nao? → lesson valida |
| **Onde** | `modulos/kg.py`, `context_infinity.py` (adicionar metodo de staleness) |
| **Campo novo na lesson** | `"time_sensitive": false` para conceitos (SPA, SHC, etc), `true` para versoes, datas |
| **Risco** | Baixo — websearch so acontece quando necessario |
| **Tempo** | 30 min |
| **Aprovado** | ✅ Sim |

### 5.3 — Cache fragmentado (SessionCache universal)

| Campo | Detalhe |
|-------|---------|
| **O que** | Em vez de `caches/arquivo.json` para cada cache separado, usar SessionCache como unico repositorio |
| **Como** | `ctx.absorver(dados, tipo="cache", tags=["validacao", "js"], time_sensitive=True)` |
| **Beneficio** | Cache nunca expira — vira fragmento no SessionCache. Pesca sob demanda |
| **Migrar** | `caches/` parciais viram fragmentos. `canary_index.json` mantem (4MB, muito grande) |
| **Risco** | Medio — mudanca de paradigma de cache |
| **Tempo** | 30 min |
| **Aprovado** | ✅ Sim |

### 5.4 — Coleta de lixo inteligente (HOT/WARM/COLD)

| Campo | Detalhe |
|-------|---------|
| **O que** | 3 niveis de fragmento no SessionCache persistente |
| **Niveis** | HOT (RAM, ultimos 30min) → WARM (disco, ultimas 24h) → COLD (disco comprimido, resumo + hash) |
| **Thread coletora** | Roda a cada 5 min. Promove/rebaixa conforme acesso |
| **Principio** | **Nada e deletado** — so comprimido. Se o tema voltar, o resumo ja da contexto |
| **Onde** | `context_infinity.py` — classes `Fragmento`, `Coletor`, `GerenciadorNiveis` |
| **Compressao COLD** | FAST gera resumo de 1 linha, armazena hash do original. Original comprimido (gzip) |
| **Risco** | Medio — mecanica de niveis precisa ser testada |
| **Tempo** | 45 min |
| **Aprovado** | ✅ Sim (future-proof) |

### 5.5 — SessionCache Persistente

| Campo | Detalhe |
|-------|---------|
| **O que** | SessionCache atual e volatil (RAM). Salvar em disco, carregar no startup |
| **Onde** | `sandbox/.mcr_devia/session_cache.json` (formato JSONL, append-only) |
| **Como** | `salvar()` → append no JSONL ao final de cada resposta. `carregar()` → le todas as linhas no startup |
| **Arquivo** | `context_infinity.py` — metodos `salvar()` e `carregar()` na classe `SessionCache` |
| **Risco** | Medio — primeira vez que SessionCache vira persistente |
| **Tempo** | 30 min |
| **Aprovado** | ✅ Sim |

---

## 💡 FASE 6 — KNOWLEDGE GRAPH REAL

> **Prioridade: ULTIMO.** Aprender sobre o que realmente importa.
> **Esforco total:** ~1 hora

---

### 6.1 — Ferramenta `buscar_item_canary()`

| Campo | Detalhe |
|-------|---------|
| **O que** | Extrair logica de `strategies/items_xml.py` como ferramenta no ToolOrchestrator |
| **Como** | `tools.registrar('buscar_item_canary', ...)` que busca item por nome fuzzy no `items.xml` |
| **Retorna** | `{"id": 3274, "nome": "Axe", "tipo": "weapon", "attack": 7, "weight": 45}` |
| **Util** | NPCGenerator e AgentLoop podem usar para gerar shop lists com itens reais |
| **Nota** | `knowledge/item_database.py` ja tem classe `ItemDatabase` pronta! So conectar como ferramenta |
| **Risco** | Baixo — funcionalidade ja existe, so expor |
| **Tempo** | 20 min |
| **Aprovado** | ✅ Sim |

### 6.2 — KG sobre Canary/OTClient/RME

| Campo | Detalhe |
|-------|---------|
| **O que** | Alimentar KG com conhecimento real do ecossistema MCR |
| **Topicos** | Estrutura do Canary (src/), API do Canary (Game, Player, NpcHandler, register), OTClient modules, RME (tiles, spawns) |
| **Como** | Usar `cmd_aprender_conceito.py` para cada topico. Ou script que varre codigo fonte e gera lessons |
| **Resultado** | KG passa de 53 lessons uteis → 100+ lessons sobre o dominio real |
| **Risco** | Baixo — so adiciona conhecimento |
| **Tempo** | 40 min (10 por topico) |
| **Aprovado** | ✅ Sim |

---

## 🟢 FASE 7 — CORRECOES PONTUAIS

> **Prioridade: QUALQUER HORA.** Ajeitar arestas.
> **Esforco total:** ~15 minutos

---

### 7.1 — cmd_master sem truncamento

| Campo | Detalhe |
|-------|---------|
| **O que** | `cmd_master.py:59` — `print(resposta_final[:max_print])` trunca resposta em 2000 chars |
| **Regra violada** | AGENTS.md diz "Respostas sao COMPLETAS (sem [:2000])" |
| **Como** | Mostrar resumo de 500 chars + "... [Resposta completa salva em .mcr_resposta.txt]" |
| **Onde** | `comandos/cmd_master.py:59` |
| **Risco** | Baixo |
| **Tempo** | 5 min |
| **Aprovado** | ✅ Sim |

### 7.2 — ProgressTracker: otimizar escrita

| Campo | Detalhe |
|-------|---------|
| **O que** | So escrever `.mcr_progress.json` se o progresso realmente mudou (deteccao de delta) |
| **Onde** | `modulos/progress_tracker.py` |
| **Como** | Comparar estado anterior com novo antes de escrever. Se igual, skip |
| **Risco** | Baixo |
| **Tempo** | 10 min |
| **Aprovado** | ✅ Sim |

---

## 🔗 DEPENDENCIAS ENTRE FASES

```
Fase 1 (Limpeza Estrutural)
    │
    ├──→ Fase 4 (Testes) 
    │     └── Precisa do sistema limpo para testes serem verdadeiros
    │
    ├──→ Fase 2 (Modulos)
    │     └── Independente, pode ser paralelo a Fase 1
    │
    ├──→ Fase 3 (Arquivos)
    │     └── Independente, pode ser paralelo a Fase 1
    │
    └──→ Fase 5 (V12/Cache)
          └── Precisa da Fase 1 (KG limpo) + Fase 2 (Conselho otimizado)
                │
                └──→ Fase 7 (Pontuais)
                      └── Independente, qualquer hora
                            │
                            └──→ Fase 6 (KG Real)
                                  └── Ultimo, quando tudo esta estavel
```

**Ordem recomendada de execucao:**

```
Iteracao 1: Fase 1 (Limpeza) + Fase 4 (Testes) ▸ paralelo
Iteracao 2: Fase 2 (Modulos) + Fase 3 (Arquivos) ▸ paralelo
Iteracao 3: Fase 5 (V12/Cache Inteligente)
Iteracao 4: Fase 7 (Pontuais) + Fase 6 (KG Real) ▸ paralelo
```

---

## 📋 CHECKLIST DE EXECUCAO

### 🔴 Fase 1 — Limpeza Estrutural
- [ ] 1.1 Dedup config modelos (util.py importa de ia.py)
- [ ] 1.2 KG taggear stress_test (tipo=benchmark)
- [ ] 1.3 engine/ → Legado
- [ ] 1.4 strategies/ → Legado (extrair items_xml antes)
- [ ] 1.5 templates/ apagar
- [ ] 1.6 personalidades/ → Legado
- [ ] 1.7 _archive/ → Legado
- [ ] 1.8 MCR_DevIA-Legado.py remover

### 🔴 Fase 4 — Testes e Qualidade
- [ ] 4.1 Refazer bateria de testes
- [ ] 4.2 Revisar cmd_autoteste
- [ ] 4.3 Consolidar testes (manter 6, arquivar 26)

### 🟡 Fase 2 — Otimizacao de Modulos
- [ ] 2.1 Conselho: keyword → Decider
- [ ] 2.2 Mente: router em vez de hardcode
- [ ] 2.3 Watchdog: simplificar
- [ ] 2.4 stop_words: unificar

### 🟡 Fase 3 — Sistema de Arquivos
- [ ] 3.1 Criar estrutura (output/, temp/)
- [ ] 3.2 Auto-cleanup no startup
- [ ] 3.3 Mover diretorios existentes para novo layout

### 🟡 Fase 5 — V12 e Cache Inteligente
- [ ] 5.1 V12 confidence threshold (≥70%)
- [ ] 5.2 V12 + ContextInfinity staleness check
- [ ] 5.3 Cache fragmentado no SessionCache
- [ ] 5.4 Coleta de lixo inteligente (HOT/WARM/COLD)
- [ ] 5.5 SessionCache persistente

### 💡 Fase 6 — KG Real
- [ ] 6.1 Ferramenta buscar_item_canary()
- [ ] 6.2 KG sobre Canary/OTClient/RME

### 🟢 Fase 7 — Correcoes Pontuais
- [ ] 7.1 cmd_master sem truncamento
- [ ] 7.2 ProgressTracker: escrita otimizada

---

## 📊 SUMARIO DE ESFORCO

| Fase | Tarefas | Esforco | Risco | Prioridade |
|------|---------|---------|-------|------------|
| **1** — Limpeza Estrutural | 8 | ~1h | 🟢 Baixo | 🔴 **1** |
| **2** — Otimizacao Modulos | 4 | ~55min | 🟡 Medio | 🟡 3 |
| **3** — Sistema de Arquivos | 3 | ~20min | 🟢 Baixo | 🟡 3 |
| **4** — Testes e Qualidade | 3 | ~1h05 | 🟡 Medio | 🔴 **1** |
| **5** — V12 e Cache Inteligente | 5 | ~2h35 | 🟡 Medio | 🟡 4 |
| **6** — KG Real | 2 | ~1h | 🟢 Baixo | 💡 5 |
| **7** — Correcoes Pontuais | 2 | ~15min | 🟢 Baixo | 🟢 Qualquer |
| **TOTAL** | **27** | **~7h10** | — | — |

---

## 📝 REGISTRO DE DECISOES

| Data | Decisao | Motivo |
|------|---------|--------|
| 2026-06-28 | `util.py` importa MODELOS de `ia.py` | Fonte unica de config de modelos, evita divergencia |
| 2026-06-28 | Lessons stress_test viram `tipo=benchmark` | Preserva para metricas, nao polui busca de dominio |
| 2026-06-28 | engine/ + strategies/ → Legado | 2281 linhas orfas, 0 imports no codigo ativo |
| 2026-06-28 | Extrair items_xml.py como ferramenta | Logica de busca fuzzy e util para NPCGenerator |
| 2026-06-28 | Mente mantem 1.5b (router `leve`) | Classificacao rapida (System 1), Conselho 7b profundidade (System 2) |
| 2026-06-28 | Watchdog simplificado | So ContextInfinity + ContextCrew index. Resto nunca usado |
| 2026-06-28 | Cache fragmentado no SessionCache | Nunca expira, pesca sob demanda. Coleta lixo inteligente so comprime |
| 2026-06-28 | V12 com confidence threshold ≥70% | Evita respostas genericas/incorretas. Fallback para LLM |
| 2026-06-28 | V12 + ContextInfinity staleness check | Websearch so quando necessario (time_sensitive + antigo) |
| 2026-06-28 | SessionCache persistente em JSONL | Append-only, rapido. Carrega no startup |
| 2026-06-28 | Estrutura sandbox: output/, testes/, temp/ | Regra anti-lixo. temp/ auto-limpo no startup |
| 2026-06-28 | 32 testes → manter 6, arquivar 26 | One-offs validados vao para Legado para referencia |

---

## 🔄 ESTADO ATUAL (antes de comecar)

| Componente | Valor |
|-----------|-------|
| Modulos ativos | 27 (313 KB) |
| Comandos | 50 |
| KG lessons | 153 (53 dominio + 100 benchmark) |
| Memoria episodica | ~2 MB |
| Sandbox total | 874 files, 48.2 MB |
| Testes | 32 arquivos (6 manter, 26 arquivar) |
| Ultima bateria | 1/3 (33%) — precisa refazer |
| Performance baseline | 57.1s |
| Stress test | 369.7s |
| Cobertura V12 | ~62% (com confidence threshold vai cair, mas qualidade sobe) |

---

> **Proximo passo:** Executar Fase 1 — Limpeza Estrutural + Fase 4 — Testes em paralelo.
> Script de inicio: `python scripts/mcr_devia/MCR_DevIA-Kernel.py status`
