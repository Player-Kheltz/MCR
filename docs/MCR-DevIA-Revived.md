# MCR-DevIA Revived — Plano de Arquitetura

> Data: 06/07/2026
> Baseado em: PERSONALIDADE.md, MCR-Revive.md, MCR.py (311KB, 50 classes),
> mcr_devia_v2.py (659 linhas), 52 comandos do DevIA original,
> 18 módulos de raciocínio (pattern_engine, diagnostic_engine, conselho, etc.)

---

## O que ele é

Assistente de engenharia de software **local** que:
- Conhece o projeto MCR profundamente (SPA, SHC, Multi-Piso, Grimório, Canary, encoding, pilares)
- Decide via Markov (0.000004s), gera via LLM (só quando necessário)
- Aprende a cada interação (KG + Markov + EpisodicMemory)
- Melhora o próprio código (MCRAutoEvolution + MCRCodex)
- Substitui 80% do assistente Cloud em tarefas diárias

## O que ele NÃO vai ser (limites reais)

- Não vai ter raciocínio multi-step profundo como um modelo grande — compensa com Markov + árvore de busca
- Não vai acertar 100% na primeira vez — compensa aprendendo com erros (KG)
- Não vai substituir decisões arquiteturais complexas sem supervisão — escala pra humano quando confiança baixa

---

## Pipeline completa (5 camadas)

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENTRADA                                       │
│  Chat, CLI, FileObserver (mudanças no projeto), Watchdog        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [1] SENSE — perceber o que foi pedido                          │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ MarkovDecider.classificar(pergunta)                     │     │
│  │ → 12 classes (do PERSONALIDADE.md) + subclasses         │     │
│  │ → confiança: 0.0-1.0                                    │     │
│  │ → tempo: 0.000004s                                      │     │
│  │                                                          │     │
│  │ intention_engine.detectar(pergunta)  [pattern matching]  │     │
│  │ → intenção: "criar", "diagnosticar", "explicar", "ler"  │     │
│  │ → tempo: 0.0001s (Markov, não LLM)                      │     │
│  │                                                          │     │
│  │ ContextCrew.carregar_contexto(classe, intencao)          │     │
│  │ → 5 fontes paralelas: KG + Docs + Código + Web + Cache  │     │
│  │ → docs relevantes do PERSONALIDADE.md mapeados           │     │
│  │ → tempo: ~0.5s                                           │     │
│  └────────────────────────────────────────────────────────┘     │
│                           │                                      │
│  [2] THINK — decidir o que fazer                                │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ MarkovRouter.decidir(estado_atual)                      │     │
│  │ → estado: "classe:criar_habilidade_intencao:criar"      │     │
│  │ → ação: pipeline de comandos                            │     │
│  │ → tempo: 0.000004s                                      │     │
│  │                                                          │     │
│  │ Radar (detector de loop)                                │     │
│  │ → mesma ação 4x consecutivas? força alternativa         │     │
│  │                                                          │     │
│  │ Se confiança < limiar:                                   │     │
│  │   ├── diagnostic_engine.diagnosticar()  [se for bug]    │     │
│  │   ├── pattern_engine.encontrar_padroes() [se for criar] │     │
│  │   └── conselho.avaliar()  [se for decisão]              │     │
│  └────────────────────────────────────────────────────────┘     │
│                           │                                      │
│  [3] ACT — executar                                             │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Pipeline de comandos (52 disponíveis):                  │     │
│  │                                                          │     │
│  │ Para "diagnosticar bug":                                 │     │
│  │   cmd_grep → cmd_read → pattern_engine → LLM(relatório) │     │
│  │                                                          │     │
│  │ Para "criar código":                                     │     │
│  │   cmd_grep(template) → cmd_read(template) →              │     │
│  │   TemplateExtractor → DeterministicFiller →              │     │
│  │   LLM(blanks criativos) → cmd_write                      │     │
│  │                                                          │     │
│  │ Para "ler/explicar":                                     │     │
│  │   cmd_read → LLM(explicar)  ou  cache → resposta direta  │     │
│  │                                                          │     │
│  │ CommandCapture: stdout de cada comando → input do próximo│     │
│  │ tempo: ~0.5-2s (tools) + ~12s (se LLM necessário)       │     │
│  └────────────────────────────────────────────────────────┘     │
│                           │                                      │
│  [4] VALIDATE — verificar                                       │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ EntropyValidator.validar(pergunta, resposta, contexto)  │     │
│  │ → entropia alta = possível alucinação                   │     │
│  │ → tempo: 0.0005s                                        │     │
│  │                                                          │     │
│  │ AutorevisaoTracker.verificar(criterios=PERSONALIDADE.md) │     │
│  │ → 15 critérios + 14 regras + 7 pilares                  │     │
│  │ → gera seção "Autorevisão" automaticamente              │     │
│  └────────────────────────────────────────────────────────┘     │
│                           │                                      │
│  [5] LEARN — melhorar (background, usuário não espera)          │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ KG.aprender(pergunta, resposta, classe, confianca)      │     │
│  │ EpisodicMemory.registrar(episódio completo)             │     │
│  │ MarkovDecider.aprender(pergunta, classe)                │     │
│  │ FeedbackFilter: se resposta inválida → não contamina KG │     │
│  │                                                          │     │
│  │ A cada 5 ciclos: Emergir (reativar conexões)            │     │
│  │ A cada 10 minutos: SelfStudy (estudar gaps)             │     │
│  │ A cada 50 interações: MCRAutoEvolution.ciclo()          │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Capacidades reais

### Nível 1 — Tarefas determinísticas (100% Markov, 0% LLM)

| Tarefa | Pipeline | Tempo |
|--------|----------|-------|
| "Leia progresso.md" | cmd_read → output | 0.1s |
| "Onde está o arquivo X?" | cmd_grep → output | 0.3s |
| "Qual o estado da compilação?" | cmd_read(config) → parse → output | 0.2s |
| "Quantas habilidades tem o domínio 100?" | cmd_grep + contagem | 0.5s |
| "Mostre os últimos 10 commits" | cmd_system("git log") | 0.3s |

### Nível 2 — Tarefas com template (90% Markov, 10% LLM)

| Tarefa | Pipeline | Tempo |
|--------|----------|-------|
| "Crie uma habilidade de gelo pro domínio 132" | TemplateExtractor + DeterministicFiller + LLM(nome+desc) | ~3s |
| "Gere um NPC comerciante" | TemplateExtractor(NPC shop) + LLM(falas) | ~2s |
| "Crie uma quest de kill 10 orcs" | TemplateExtractor(quest) + LLM(diálogos) | ~3s |
| "Compile o Grimório" | cmd_build + output check | ~5s |
| "Traduza essas strings pra PT-BR" | LLM(tradução) — única chamada | ~8s |

### Nível 3 — Tarefas de análise (60% Markov, 40% LLM)

| Tarefa | Pipeline | Tempo |
|--------|----------|-------|
| "Encontre bugs de encoding no projeto" | cmd_grep + pattern_engine + LLM(relatório) | ~15s |
| "Analise a performance do pathfinding" | cmd_read + diagnostic_engine + LLM(análise) | ~12s |
| "Revise este código seguindo os 15 critérios" | cmd_read + verificador(15 critérios) + LLM(relatório) | ~15s |
| "Compare o items.xml PT vs EN" | script diff_items.py + LLM(resumo) | ~10s |

### Nível 4 — Tarefas de design (30% Markov, 70% LLM + supervisão)

| Tarefa | Pipeline | Tempo |
|--------|----------|-------|
| "Projete um sistema de crafting" | diagnostic_engine + pattern_engine + tree_of_thought + conselho + LLM(design) | ~40s |
| "Como integrar o LoginServer com o Canary?" | ContextCrew(KG+docs) + LLM(arquitetura) | ~25s |
| "Refatore o monster_ai.cpp" | diagnostic_engine + pattern_engine + LLM(plano) | ~30s |

### Nível 5 — O que ele NÃO faz (escala pra humano/Cloud)

| Tarefa | Por que |
|--------|---------|
| Sistema novo do zero sem referência (ex: Multi-Piso) | Precisa de design conceitual novo |
| Debug cross-language profundo (C++ crash → Lua → protocolo) | Precisa de raciocínio multi-camada |
| Decisão arquitetural com trade-offs complexos | Precisa de julgamento de engenharia |

**Nível 5 diminui com o tempo — cada sistema novo criado vira template no KG.**

---

## Evolução temporal

```
SEMANA 1 (MVP):
  52 comandos funcionando (encoding corrigido)
  MarkovDecider com seeds do PERSONALIDADE.md
  MarkovRouter básico
  Faz Nível 1 + Nível 2 (tarefas simples)
  ~70% das perguntas respondidas sem LLM

MÊS 1:
  KG com 500+ lessons (aprendeu com uso)
  MarkovDecider com 80%+ acurácia
  TemplateExtractor cobre 20+ tipos de arquivo
  Faz Nível 1-3 consistentemente
  ~85% das perguntas respondidas sem LLM

MÊS 3:
  KG com 3000+ lessons
  diagnostic_engine treinado nos bugs do projeto
  tree_of_thought explora soluções multi-passo
  Faz Nível 4 com supervisão reduzida
  MCRAutoEvolution já ajustou thresholds sozinho

MÊS 6:
  Já viu sistemas como Multi-Piso, MountSummon, SQH
  Cria variações desses sistemas sem ajuda
  Só escala pra humano em conceitos verdadeiramente novos
  Substitui 95% do assistente Cloud
```

---

## Inventário de arquivos

### Arquivos que PERMANECEM (herdados do DevIA original)

```
historia/scripts/mcr_devia/
├── kernel.py              — EventBus + CommandLoader (ok)
├── comandos/cmd_*.py      — 52 comandos (corrigir encoding)
├── modulos/
│   ├── kg.py              — KnowledgeGraph (ok)
│   ├── episodic_memory.py — EpisodicMemory (ok)
│   ├── pattern_engine.py  — trocar LLM→Markov nos nós (~15 linhas)
│   ├── diagnostic_engine.py — trocar LLM→Markov (~10 linhas)
│   ├── tree_of_thought.py — trocar LLM→Markov nos nós (~20 linhas)
│   ├── conselho.py        — trocar 4xLLM→4xMarkovDecider (~30 linhas)
│   ├── intention_engine.py — trocar LLM→Markov (~10 linhas)
│   ├── decider.py         — substituído por MarkovDecider do v2 (~5 linhas)
│   └── ia.py              — LLM interface (adaptar)
├── context_crew.py        — (ok)
└── MCR_DevIA-Kernel.py    — entry point (ok)
```

### Arquivos MODIFICADOS

| Arquivo | Linha | Mudança |
|---------|-------|---------|
| `mcr_devia_v2.py` | 27-30 | Corrigir import: MCR_AGI.py → MCR.py |
| `mcr_devia_v2.py` | — | Adicionar MarkovRouter + Radar |
| `cmd_read.py` | 35,47 | Corrigir encoding: ascii→utf8; detectar .lua→latin1 |
| `cmd_write.py` | 31,35 | Corrigir encoding + espaços |
| `cmd_edit.py` | 24,91 | Corrigir encoding hardcoded |
| `cmd_grep.py` | 26 | Aceitar BASE como parâmetro |
| `pattern_engine.py` | — | Substituir `ia.gerar()` por `MarkovDecider` (~15 linhas) |
| `diagnostic_engine.py` | — | Substituir `ia.gerar()` por `MarkovDecider` (~10 linhas) |
| `tree_of_thought.py` | — | Substituir LLM nos nós por `MarkovDecider` (~20 linhas) |
| `conselho.py` | — | 4 cadeias Markov substituem 4 chamadas LLM (~30 linhas) |

### Arquivos NOVOS

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `TemplateExtractor.py` | ~50 | Extrai esqueleto de arquivo similar, remove valores variáveis |
| `DeterministicFiller.py` | ~40 | Preenche campos por mapeamento (domínio→cor, tipo→categoria) |
| `MarkovRouter.py` | ~50 | Estado → pipeline de ações (usa módulos existentes) |
| `AutorevisaoTracker.py` | ~50 | Tracking docs consultados + pilares + geração linha 502 |
| `CommandCapture.py` | ~60 | Captura stdout dos comandos como string estruturada |
| `EncodingDetector.py` | ~30 | Detecta encoding: .lua→latin1, .cpp→utf8, .md→utf8 |
| `FeedbackFilter.py` | ~40 | Evita contaminação do KG com respostas inválidas |
| `SeedLoader.py` | ~60 | PERSONALIDADE.md → seeds para MarkovDecider |

### Total

| Categoria | Linhas |
|-----------|--------|
| Correções em arquivos existentes | ~30 |
| Substituições LLM→Markov nos módulos | ~90 |
| Arquivos novos | ~380 |
| **Total** | **~500** |

---

## O LLM no sistema final

| Tarefa | Quem faz | % do código |
|--------|----------|------------|
| Estrutura do arquivo | TemplateExtractor (Markov) | 40% |
| Campos determinísticos | DeterministicFiller (mapeamento) | 30% |
| Valores por similaridade | Markov fingerprints | 20% |
| **Nomes, descrições, lore** | **LLM (snippets 1-3 linhas)** | **10%** |

O LLM é uma ferramenta de preenchimento de blanks criativos — não um gerador de código.
O nome BlankFiller foi herdado do protótipo e reflete exatamente esta função.

---

## Mapeamento PERSONALIDADE.md → implementação

| O que PERSONALIDADE.md exige | Como o MCR-DevIA implementa |
|------------------------------|---------------------------|
| **12 análises** (bugs, perf, arq...) | MarkovDecider classifica → MarkovRouter encadeia comandos |
| **15 critérios** (domínio, pai-filho, encoding...) | SeedLoader converte em sub-rotas + verificações |
| **14 regras** ("não invente problemas", "hipótese"...) | AutorevisaoTracker valida cada regra |
| **Report** (ANALYSIS_REPORT.md) | Template no Router: cmd_write + LLM(relatório) |
| **Autorevisão** (linha 502) | AutorevisaoTracker.gerar() no final de toda resposta |
| **26 docs** (SPA, SHC, NPC...) | SeedLoader.carregar_contexto() → ContextCrew |
| **Encoding** (UTF-8, toLatin1) | EncodingDetector + validação no cmd_write |
| **Pilares (7)** | AutorevisaoTracker.verificar_pilar() em toda modificação |
| **Aprendizado contínuo** | MCRConversa + MCRAutoEvolution + background threads |

---

## Ordem de implementação

1. **Consertar encoding** (30min) — cmd_read, cmd_write, cmd_edit, cmd_grep
2. **SeedLoader** (1h) — PERSONALIDADE.md → seeds → MarkovDecider funcional
3. **TemplateExtractor + DeterministicFiller** (1.5h) — ativa geração de código Nível 2
4. **MarkovRouter + Radar** (1h) — ativa pipeline autônomo
5. **Módulos de raciocínio → Markov** (1.5h) — pattern_engine, diagnostic_engine, tree_of_thought, conselho
6. **CommandCapture + AutorevisaoTracker** (1h) — pipeline funcional + validação
7. **FeedbackFilter + EncodingDetector** (0.5h) — qualidade dos dados
8. **Bridge fix_mcr_devia_v2.py** (1h) — entry point final
9. **Testes** (1h) — 243 testes + smoke test do pipeline completo

**Total estimado: ~9h**
