# 🗺️ IMPLEMENTAÇÃO MANIFEST — Guia Vivo de Implementação

> **LEIA SEMPRE** antes de planejar ou executar qualquer implementação.
> **ATUALIZE** ao concluir cada etapa — status, data e observações.
> **PONTE** entre o `MANIFEST.md` (o que existe) e a AGI real (o que está rodando).
> Versão: 1.0 | Data: 2026-06-30

---

## Sumário

1. [Etapas Concluídas](#-etapas-concluidas)
2. [Próximas Etapas](#-proximas-etapas)
3. [Barreiras / Bloqueios](#-barreiras--bloqueios)
4. [Testes de Validação](#-testes-de-validacao)
5. [Decisões de Implementação](#-decisoes-de-implementacao)
6. [Checklist Pré-Implementação](#-checklist-pre-implementacao)

---

## ✅ Etapas Concluídas

| # | Etapa | Onde | Data | Teste | Ref. MANIFEST |
|---|-------|------|------|-------|---------------|
| 0 | **KGCleaner automático** — marca lessons poluentes como inactive no startup | `kg_cleaner.py`, `kernel.py` | 30/06 | 7/7 | § Módulos |
| 1 | **Modelo DeepSeek-r1:7b como padrão** — melhor em seguir instruções | `ia.py`, `pipeline_executor.py` | 30/06 | 7/7 | § Módulos |
| 2 | **Prompt universal** — sem hardcode de MCR/SPA/SHC no prompt | `pipeline_executor.py` | 30/06 | 7/7 | § Módulos |
| 3 | **Dashboard SSE** — emit() no ReAct (ciclos, ferramentas, resultado) | `pipeline_executor.py` | 30/06 | - | § Módulos |
| 4 | **WebLearn automático** — dispara weblearn se seed não achar dados | `pipeline_executor.py` | 30/06 | - | § Módulos |
| 5 | **AutoRevisor + Tradutor** — detecta alucinações, garante PT-BR | `pipeline_executor.py` | 30/06 | 7/7 | § Módulos |
| 6 | **TruncationFixer: exceção str(...)[:N]** — `str(x)[:1500]` não removido | `truncation_fixer.py` | 30/06 | 7/7 | § Módulos |
| 7 | **Busca Estratégica** — `buscar_estrategico()` descobre diretórios + arquivos + funções | `tool_orchestrator.py` | 30/06 | 8.0/10 | § Ferramentas |
| 8 | **MANIFEST.md v2** — 400 linhas, 12 seções, tudo mapeado | `docs/MANIFEST.md` | 30/06 | - | § Este arquivo |

---

## 🔥 Próximas Etapas

### FASE A1 — ROTEAMENTO APRENDIDO (Sistema aprende a se rotEAR)

> **Objetivo**: Substituir roteamento fixo (if/else de entropia, thresholds) por um sistema que APRENDE rotas baseado em fingerprint + KG + histórico. Zero hardcode de decisão.
> 
> **Filosofia**: LLM é água — flui pelos canais que o sistema aprendeu. PatternEngine mapeia o fingerprint, PiEngine mede entropia (como DADO, não REGRA), KG mostra o que funcionou antes, FAST vota a rota com 1 token. LEARN registra o resultado para a próxima vez.

| # | Etapa | Onde | Linhas | Depende de | Ref. MANIFEST | Status |
|---|-------|------|--------|-----------|--------------|--------|
| 1 | **KG.buscar_rotas(fingerprint)** — novo método que busca lessons de rota por similaridade de fingerprint. Retorna: "fingerprint similar usou [modulos] com score 0.92" | `kg.py` | ~15 | - | §34 kg.py | ✅ Feito |
| 2 | **SENSE: coletar dados de roteamento** — PatternEngine (fingerprint) + PiEngine (entropia) + KG (rotas passadas) + EpisodicMemory (experiências) → contexto para o THINK | `pipeline_executor.py` | ~20 | Etapa 1 | §52 pattern_engine + §62 pi_engine + §34 kg | ✅ Feito |
| 3 | **THINK: FAST vota rota** — FAST (1.5b) recebe fingerprint + entropia + rotas passadas + scores. Vota com 1 token: A (KG direto), B (Conselho+Orquestrador) ou C (ReAct). Zero thresholds fixos. | `pipeline_executor.py` | ~15 | Etapa 2 | §37 decider | ✅ Feito |
| 4 | **ACT: executar rota votada** — Rota A: template direto. Rota B: Conselho+Orquestrador. Rota C: ReAct. Cada rota é apenas uma sequência de módulos existentes. | `pipeline_executor.py` | ~15 | Etapa 3 | §55 conselho + §56 orquestrador | ✅ Feito |
| 5 | **LEARN: registrar rota + resultado** — KG.aprender(fingerprint, rota, score). EpisodicMemory.registrar(input, rota, resultado). Próximo SENSE terá mais dados. | `pipeline_executor.py` | ~10 | Etapa 4 | §34 kg + §36 episodic_memory | ✅ Feito |
| 6 | **Keyword classifier (0 IA)** — complemento opcional para o THINK. Tenta classificar por keywords primeiro. | `pipeline_executor.py` | ~20 | - | §61 supervisor | ✅ Feito |
| 7 | **Remover if/else de entropia e thresholds fixos** — limpar qualquer decisão hardcoded que sobrou do pipeline antigo | `pipeline_executor.py` | ~10 | Etapa 3 | §62 pi_engine | ✅ Feito |

### FASE A2 — Qualidade + Ferramentas Universais

> **Objetivo**: Adicionar ferramentas universais que estão faltando no ReAct e melhorar qualidade.

| # | Etapa | Onde | Linhas | Depende de | Ref. MANIFEST | Status |
|---|-------|------|--------|-----------|--------------|--------|
| 8 | **validar_codigo + extrair_codigo no ReAct** — valida código em QUALQUER linguagem | `pipeline_executor.py` | ~5 | - | §111/114 Ferramentas | ✅ Feito |
| 9 | **auto_repair no fluxo de criação** — se validar_codigo falhar, tenta corrigir automaticamente | `pipeline_executor.py` | ~5 | Etapa 8 | §72 auto_repair | ✅ Feito |
| 10 | **Router Híbrido (local + cloud)** — fallback para web search (DuckDuckGo) quando modelo local falha | `ia.py` | ~30 | - | §35 ia.py | ✅ Feito |

### FASE B — Limpeza e Legado

> **Objetivo**: Remover código morto e revisar scripts legados com conceitos úteis.

| # | Etapa | Onde | Linhas | Depende de | Ref. MANIFEST | Status |
|---|-------|------|--------|-----------|--------------|--------|
| 11 | **Remover fallbacks mortos do supervisor** — ~50 linhas de código nunca executado | `supervisor.py` | ~20 | - | §61 supervisor | ✅ Feito |
| 12 | **Remover fallbacks mortos do cmd_perguntar** — ia.orquestrar + ia.gerar (nunca alcançados) | `cmd_perguntar.py` | ~10 | - | §137 cmd_perguntar | ✅ Feito |
| 13 | **Revisar scripts legados úteis** — crew_deepseek (validador), super_fragmentador (fragmentação), mcr_knowledge (KG), mcr_auto_improve (auto-melhoria) | `scripts/` | ~30 | - | §285-292 Legados | ✅ Feito |
| 34 | **Remover comandos-alias** — cmd_intencao, cmd_orquestrar, cmd_processar (stubs de 7 linhas que só delegam) | `comandos/` | ~5 | - | §187-189 MANIFEST | ✅ Feito |
| 35 | **Remover conceptual_planner.py** — 174 linhas, NUNCA usado (só referenciado em cmd_super_test) | `modulos/` | ~5 | - | §63 MANIFEST | ✅ Feito |
| 36 | **Verificar imports quebrados** — kernel.py, cmd_memoria.py, master_agent.py podem ter ImportError em runtime | `kernel.py` | ~10 | - | FeedBack externo §1.1 | ✅ Feito |

### FASE C — Background + Otimizações

> **Objetivo**: Ativar processos background e otimizar aprendizado contínuo.

| # | Etapa | Onde | Linhas | Depende de | Ref. MANIFEST | Status |
|---|-------|------|--------|-----------|--------------|--------|
| 14 | **Iniciar Watchdog no kernel** — índice invertido para ContextCrew | `kernel.py` | ~3 | - | §75 watchdog | ✅ Feito |
| 15 | **Adicionar ferramentas faltantes ao ReAct** — +7 ferramentas (buscar_inteligente, aprender_kg, buscar_web, etc.) | `pipeline_executor.py` | ~5 | - | §120-129 Ferramentas | ✅ Feito |
| 16 | **Integrar memoria_compactada no LEARN** — compressão automática de memória episódica antiga (>7 dias) | `pipeline_executor.py` | ~8 | - | §80 memoria_compactada | ✅ Feito |
| 17 | **PLANO_FINAL: Config de modelos: DEDUP (util.py vs ia.py)** — remover dict duplicado de modelos em util.py | `util.py` | ~15 | - | PLANO_FINAL 1.1 | ✅ Feito |
| 18 | **PLANO_FINAL: KG TAGGEAR stress_test** — marcar lessons de benchmark p/ não poluir busca | `kg.py` | ~10 | - | PLANO_FINAL 1.2 | ✅ Feito |
| 19 | **PLANO_FINAL: ContextInfinity modo silencioso** — reduzir logs | `context_infinity.py` | ~5 | - | PLANO_FINAL 1.5 | ✅ Feito |
| 37 | **Self-Study: 10min → 60min** — reduz consumo de VRAM/CPU em background. Só rodar sob demanda ou a cada 60 min | `kernel.py` | ~2 | - | FeedBack externo §3.3 | ✅ Feito |
| 38 | **Session cache: adicionar expiração (5min)** — evitar respostas desatualizadas | `session_cache.py` | ~5 | - | FeedBack externo §3.4 | ✅ Feito |

| 20 | **PLANO_FINAL: Merge tools/ com modulos/** — consolidar duplicatas | `vários` | ~20 | - | PLANO_FINAL 3.1 | ✅ Feito |
| 21 | **PLANO_FINAL: Merge analysis/ com modulos/** — consolidar duplicatas | `vários` | ~20 | - | PLANO_FINAL 3.2 | ✅ Feito |
| 22 | **PLANO_FINAL: Merge core/ com modulos/** — consolidar duplicatas | `vários` | ~10 | - | PLANO_FINAL 3.3 | ✅ Feito |
| 23 | **PLANO_FINAL: Merge agents/ com modulos/** — consolidar duplicatas | `vários` | ~20 | - | PLANO_FINAL 3.4 | ✅ Feito |
| 24 | **PLANO_FINAL: V12 Decider + Cache semântico** — substituir regex do supervisor por Decider | `decider.py` | ~15 | - | PLANO_FINAL 5.1 | ✅ Feito |
| 25 | **PLANO_FINAL: KG Seed com aprender_conceito** — popular KG com dados reais | `kg.py` | ~15 | - | PLANO_FINAL 6.1 | ✅ Feito |
| 26 | **PLANO_FINAL: KG aprender() async com buffer** — não travar pipeline em escrita de KG | `lessons_buffer.py` | ~10 | - | PLANO_FINAL 6.3 | ✅ Feito |
| 27 | **PLANO_FINAL: Orquestrador modo silencioso** — reduzir logs | `orquestrador.py` | ~5 | - | PLANO_FINAL 7.3 | ✅ Feito |

### FASE D — Conceitos Novo/Reavivados (do MASTER_AGENT + Planos)

> **Objetivo**: Integrar conceitos dos planos existentes que nunca foram implementados.

| # | Etapa | Onde | Linhas | Depende de | Ref. MANIFEST | Status |
|---|-------|------|--------|-----------|--------------|--------|
| 28 | **Decider/FAST Universal** — substituir TODO regex (classificar, extrair, decidir) por FAST model | `vários` | ~30 | - | PLANO_MASTER_AGENT Fase D | ✅ Feito |
| 29 | **V12 Contexto (keyword KG)** — revive busca 0 IA no KG antes do pipeline completo | `pipeline_executor.py` | ~15 | - | §61 supervisor (V12) | ✅ Feito |
| 30 | **Integrar reparar_com_validacao() no auto_repair** — PatternEngine Gatekeeper nunca usado | `pipeline_executor.py` | ~8 | Etapa 9 | PATTERN_GATEKEEPER.md | ✅ Feito |
| 31 | **cmd_criar + cmd_fazer** — comandos do ToolRegistry que existem no catálogo mas não no código | `comandos/` | ~30 | - | ToolRegistry criar_universal | ✅ Feito |
| 32 | **Atualizar AGI_ARCHITECTURE.md** — refletir arquitetura híbrida pós-FASE A1 | `docs/plano/` | ~30 | FASE A1 | PLANO_MASTER_AGENT | ✅ Feito |
| 33 | **Detalhar AutoConsciencia** — especificar padrões: mesmo erro >2x, IA falhando >2x, pipeline falhando | `kernel.py` | ~15 | - | §210 autoconsciencia | ✅ Feito |

---

### 📋 Detalhamento da FASE A1

#### Estrutura do pipeline (sem hardcode)

```
SENSE:
  1. PatternEngine → fingerprint(P) + entropia(P)
  2. KG.buscar_rotas(fingerprint) → rotas usadas em inputs similares
  3. EpisodicMemory.buscar(fingerprint) → experiências passadas
  4. ContextCrew → 5 fontes de contexto
  5. ContextInfinity → histórico da sessão

THINK:
  FAST (1.5b) recebe: fingerprint + entropia + rotas passadas (com scores)
  Vota com 1 token: A (KG + template direto), B (Conselho + Orquestrador), C (ReAct)
  
ACT:
  Executa a rota votada. Cada rota é APENAS uma sequência de módulos existentes.
  Rota A: KG.seed + Template → resposta (0 chamada LLM para código)
  Rota B: Conselho + Orquestrador → resposta (LLM preenche blanks)
  Rota C: Seed KG + ReAct Loop → resposta (LLM gera livremente)

VALIDATE:
  AutoRevisor + Tradutor + V1-V9 (já existem)

LEARN:
  KG.aprender: fingerprint → rota → score (AutoRevisor)
  EpisodicMemory.registrar: input → rota → resultado
  ContextInfinity.adicionar: fragmento da sessão
```

#### Etapa 1 — `KG.buscar_rotas(fingerprint)`

```python
# NO kg.py:
def buscar_rotas(self, fingerprint, max_r=5):
    """Busca rotas aprendidas por similaridade de fingerprint."""
    licoes = self._get_licoes()
    candidatos = []
    for l in licoes:
        if l.get('inactive') or l.get('ctx') != 'rota':
            continue
        fp_lesson = l.get('fingerprint', [])
        if fp_lesson and len(fp_lesson) == len(fingerprint):
            sim = sum(a*b for a,b in zip(fp_lesson, fingerprint))
            if sim > 0.7:
                candidatos.append((sim, l))
    candidatos.sort(key=lambda x: -x[0])
    return [c[1] for c in candidatos[:max_r]]
```

#### Etapa 2 — SENSE + THINK (roteamento aprendido)

```python
# NO pipeline_executor.py, substituindo toda a lógica de THINK atual:
from modulos.pattern_engine import PatternEngine
from modulos.pi_engine import PiEngine

_pe_local = PatternEngine()
_pi_local = PiEngine(pe=_pe_local, kg=_kg_v)
_tokens = _pe_local.tokenizar(texto, 'texto')
_fingerprint = _pe_local.fingerprint(_tokens)
_entropia = _pi_local.avaliar_entropia(texto)

# Busca rotas aprendidas no KG
_rotas = []
if hasattr(_kg_v, 'buscar_rotas'):
    _rotas = _kg_v.buscar_rotas(_fingerprint) or []

# FAST vota com base nos dados
_prompt_voto = f"""fingerprint: {_fingerprint[:5]}...
entropia: {_entropia:.2f}
rotas passadas: {_rotas[:3]}

Escolha a rota:
A = KG + template direto (rapido, 0 IA)
B = Conselho + Orquestrador (medio, ~15s)
C = ReAct completo (lento, ~30s)

Resposta (apenas A, B ou C):"""

_rota = self.ia.fast(_prompt_voto, 0.1, 'ultra_leve') or 'B'
_rota = _rota.strip().upper()[0] if _rota.strip() else 'B'
```

#### Etapa 3 — ACT (executar rota)

```python
if _rota == 'A':
    # KG + template direto
    ...  # template match
elif _rota == 'B':
    # Conselho + Orquestrador
    ...  # conselho + orquestrador
else:
    # ReAct completo (atual)
    ...  # react loop
```

#### Etapa 5 — LEARN

```python
# NO pipeline_executor.py, apos cada resposta:
try:
    _kg_v.aprender(
        erro=f"rota_{_rota}: {texto[:100]}",
        causa=f"fingerprint={_fingerprint[:10]}, entropia={_entropia:.2f}",
        solucao=f"rota={_rota}, score={nota}",
        ctx='rota'
    )
except: pass
```

---

## 🚧 Barreiras / Bloqueios

| # | Barreira | Afeta | Solução |
|---|----------|-------|---------|
| 1 | **Conselho V10** usa `_MCR_IDENTITY` hardcoded (conselho.py:27-35) | Etapa 2 | Substituir por loading de `docs/MCR_IDENTITY.md` |
| 2 | **Orquestrador** tem templates hardcoded em `_TEMPLATES` (orquestrador.py:59-640) | Etapa 3 | Não é barreira — templates são padrões, não dados. Aceitável. |
| 3 | **Fragmenter** não tem interface padronizada — é uma classe solta em `analysis/fragmenter.py` | Etapa 5 | Criar wrapper: `fragmenter.py` → método `fragmentar(texto, tamanho_alvo)` |
| 4 | **Watchdog** nunca foi testado rodando no kernel — pode ter bugs de inicialização | Etapa 14 | Testar em isolamento antes de ativar no kernel |
| 5 | **supervisor.py fallbacks** são grandes (~50 linhas) — remoção pode quebrar cmd_perguntar | Etapa 11 | Remover com cuidado, testar com test_verdade |
| 6 | **Router Híbrido** requer web search com DuckDuckGo — pode falhar sem internet | Etapa 10 | Fallback silencioso para local se web falhar |

---

## 🧪 Testes de Validação

Cada etapa DEVE passar no teste correspondente antes de marcar como concluída:

| Etapa(s) | Teste | Critério | Comando |
|----------|-------|----------|---------|
| 1-7 | `test_verdade.py` | **7/7 PASS** | `python tests/test_verdade.py` |
| 1-7 | `test_complexo.py` | **≥ 8.0/10** | `python tests/test_complexo.py` |
| 1-7 | `test_criacao.py` | **≥ 8.0/10** | `python tests/test_criacao.py` |
| 8-9 | `test_react.py` | **≥ 7.0/10** | `python tests/test_react.py` |
| 10 | Teste manual internet ON/OFF | Funciona nos 2 modos | `python -c "from ia import IA; ia=IA(); print(ia.gerar('teste',0.3,'fast'))"` |
| 11-12 | `test_verdade.py` | **7/7 PASS** (nada quebrou) | `python tests/test_verdade.py` |
| 14 | Verificar logs | Índice sendo gerado | `Get-Content sandbox/.mcr_devia/indice_watchdog.json` |
| 15-16 | `test_verdade.py` | **7/7 PASS** | `python tests/test_verdade.py` |
| Todas | `test_complexo.py` | **≥ 8.0/10** | `python tests/test_complexo.py` |
| Todas | `test_criacao.py` | **≥ 8.0/10** | `python tests/test_criacao.py` |

### Ordem de Teste Obrigatória

```
1. test_verdade.py → 7/7 (qualidade factual)
2. test_complexo.py → ≥ 8.0 (qualidade complexa)
3. test_criacao.py → ≥ 8.0 (criação de código)
```

Se QUALQUER um falhar, **NÃO PROSSIGA** — reverta a etapa.

---

## 📐 Decisões de Implementação

### Ordem de Execução

```
FASE A1: 1 → 2 → 2.5 → 3 → 4 → 5 → 6 → 7
  └─ Etapa 2.5 integra PiEngine + Conselho (gate de entropia)
  └─ Testar após CADA etapa
  └─ Se test_verdade falhar, REVERTER

FASE A2: 8 → 9 → 10
  └─ Testar após CADA etapa

FASE B: 11 → 12 → 13
  └─ Testar após cada uma (verdade + complexo)

FASE C: 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21 → 22 → 23 → 24 → 25 → 26 → 27
  └─ Testar a cada 2 etapas (verdade + complexo)

FASE D: 28 → 29 → 30 → 31 → 32 → 33
  └─ Testar ao final da FASE D
```

### Regras

1. **Testar APÓS cada etapa** — nunca pular 2 etapas sem testar no meio
2. **Se etapa > 20 linhas, quebrar em sub-etapas** e testar cada sub-etapa
3. **Se test_verdade falhar, REVERTER a etapa** imediatamente
4. **MANIFEST.md deve ser atualizado** junto com as mudanças (status do módulo)
5. **IMPLEMENTACAO_MANIFEST.md deve ser atualizado** ao concluir cada etapa (status + data)
6. **Se descobrir algo novo durante a implementação**, adicionar ao MANIFEST.md primeiro

### Prioridade de Implementação

```
PRIMEIRO: FASE A1 (1-7) → pipeline híbrido
  Motivo: Conselho + Orquestrador + Reconstructor são os conceitos mais validados

SEGUNDO: FASE A2 (8-10) → qualidade + ferramentas
  Motivo: validar_codigo universal + auto_repair + cloud fallback

TERCEIRO: FASE B (11-13) → limpeza
  Motivo: código morto não afeta performance, mas limpeza facilita manutenção

QUARTO: FASE C (14-27) → background + PLANO_FINAL
  Motivo: pendências do plano original, menor impacto

QUINTO: FASE D (28-33) → conceitos reavivados
  Motivo: conceitos avançados do MASTER_AGENT, dependem da base pronta
```

---

## ✅ Checklist Pré-Implementação

**LEIA E MARQUE ANTES DE QUALQUER IMPLEMENTAÇÃO:**

### 1. Leitura Obrigatória
- [ ] Li o `docs/MANIFEST.md` **COMPLETO**?
- [ ] Li o `docs/IMPLEMENTACAO_MANIFEST.md` **COMPLETO**?

### 2. Planejamento
- [ ] Identifiquei qual etapa estou implementando (ex: "FASE A1 — Etapa 1")?
- [ ] Verifiquei dependências (etapas anteriores concluídas)?
- [ ] Identifiquei barreiras/bloqueios para esta etapa?

### 3. Preparação
- [ ] Preparei o teste de validação (comando para rodar)?
- [ ] Se etapa > 20 linhas, quebrei em sub-etapas?
- [ ] Atualizei o status da etapa para "⏳ Em andamento"?

### 4. Pós-Implementação
- [ ] Teste de validação PASSOU?
- [ ] Atualizei `IMPLEMENTACAO_MANIFEST.md` (status → ✅)?
- [ ] Atualizei `MANIFEST.md` se necessário (status de módulo mudou)?
- [ ] Registrei lição no KG? (`python scripts/mcr_devia/MCR_DevIA-Kernel.py ensinar ...`)

---

## 📊 Estado Atual

```
╔══════════════════════════════════════════════════════════════════╗
║  STATUS: 38/38 etapas concluidas (100%) — PLANO COMPLETO!       ║
║                                                                  ║
║  ✅ FASE A1: 7/7 — Roteamento Aprendido                         ║
║  ✅ FASE A2: 3/3 — Qualidade + Ferramentas                      ║
║  ✅ FASE B:  6/6 — Limpeza e Legado                             ║
║  ✅ FASE C: 16/16 — Background + Otimizações                    ║
║  ✅ FASE D:  6/6 — Conceitos Reavivados                         ║
║                                                                  ║
║  PROXIMA ACAO: Rodar test_verdade.py para validar               ║
╚══════════════════════════════════════════════════════════════════╝
```
