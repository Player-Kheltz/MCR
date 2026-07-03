# Plano EMERGIR V5 — Dashboard + Ciclo Completo + Direcionado

**Data**: 2026-06-29
**Status**: Planejado — implementar amanhã

---

## Sumário

1. [O que foi construído hoje (V4)](#-o-que-foi-construido)
2. [O que não funcionou](#-o-que-nao-funcionou)
3. [Ciclo Emergir Completo](#-ciclo-emergir-completo)
4. [Emergir Direcionado](#-emergir-direcionado)
5. [Dashboard — Correções Pendentes](#-dashboard--correcoes-pendentes)
6. [Comparação: Normal vs Direcionado](#-comparacao-emergir-normal-vs-direcionado)
7. [Arquivos que serão modificados](#-arquivos-que-serao-modificados)

---

## ✅ O que foi construído hoje (V4)

| Componente | Status | Descrição |
|-----------|--------|-----------|
| **EMERGIR V4** | ✅ | Fragmentador 4 seções + Z expandido com 3 visões críticas (cenário, padrão, potencial) |
| **ContextCrew** | ✅ | Enriquece tópicos com 5 fontes (KG, Web, Docs, Código, WebLearn) |
| **Anti-alucinação** | ✅ | Regex + FAST (Nível 1 + Nível 2) — verifica expansões erradas de siglas MCR |
| **Zero hardcoded [:N]** | ✅ | Todos os truncamentos removidos em `kg.py`, `master_agent.py`, `decider.py` |
| **SSE Server** | ✅ | Event bus HTTP puro na porta 8765 — distribui eventos para o dashboard |
| **Dashboard HTML** | ✅ | Timeline + narrador + prompt expansível + log completo + reconexão automática |
| **Heartbeat** | ✅ | Mantém conexão SSE viva a cada 10s |
| **Resultado** | ✅ | EMERGIR gera ~21.000 chars, 10/10 nos testes de qualidade, zero alucinações |

### Pipeline V4 completo

```
0. Amostra 2-3 tópicos distantes do KG
1. Fingerprint dedup (MD5 ordem-independente)
2. Decider gera pergunta "E se X + Y?"
3. ContextCrew enriquece cada tópico (5 fontes, paralelo)
4. FRAGMENTADOR:
   ├── Seção 1: Análise individual dos tópicos (modelo 'analisar', temp=0.3)
   ├── Seção 2: Conexão Z criativa (modelo 'leve', temp=0.8)
   │   └── [EXPANSÃO CRÍTICA]:
   │       ├── Visão A: Cenário Concreto
   │       ├── Visão B: Padrão Subjacente
   │       └── Visão C: Potencial Transformador
   ├── Seção 3: Implicações práticas (modelo 'analisar')
   └── Seção 4: Síntese (modelo 'leve', temp=0.5)
5. Autoavaliação: é conexão não-óbvia? (modelo 1.5b, diferente)
6. Verificador de alucinações (regex + FAST)
7. Salva no KG (sem truncamento)
```

---

## 🔴 O que não funcionou hoje

### 1. Streaming token-a-token do Ollama

**Problema**: `gerar_stream()` com `stream:true` + callback HTTP = timeout.
- Cada token é uma requisição HTTP individual
- Com ~28.000 tokens por pipeline, o overhead acumulado estoura o timeout
- Timeout original: 120s (depois aumentado para 300s)

**Solução aplicada**: Fallback para batch mode (gerar() normal, sem streaming)

**Solução planejada para amanhã**:
- Aumentar timeout para 3600s (1 hora)
- Manter streaming como primeira tentativa
- Fallback batch se streaming falhar
- Emitir `narrator` avisando sobre o modo usado

### 2. Dashboard sem ETA

**Problema**: Planejei emitir `elapsed` e `estimated` nos eventos `stage`, mas não implementei.

**Solução planejada**:
```python
emit('stage', {
    'name': 'analise_topicos',
    'label': 'Análise dos tópicos',
    'progress': 0.3,
    'elapsed': round(time.time() - stage_start, 1),
    'estimated': 120  # ~2 min para esta seção
})
```

### 3. Cache .pyc travando código antigo

**Problema**: `__pycache__` com versões antigas do código fazia o EMERGIR completar em 0.0s (executava código stale).

**Solução**: Sempre limpar `__pycache__` antes de testar.

---

## 🆕 Ciclo Emergir Completo

### Conceito

O EMERGIR atual gera Z (insight) e para. O **Ciclo Completo** fecha o loop: GERA → TESTA → VALIDA → REGISTRA.

### Pipeline

```
1. GERA Z (já existe)
   Pergunta "E se X + Y?" → insight criativo

2. AVALIA Z (já existe)
   FAST: "É conexão não-óbvia? SIM/NAO"

3. TESTA Z (NOVO)
   ├── Z é implementável? Como validar?
   ├── Gera mini-plano de implementação
   ├── Verifica se conflita com o KG atual
   └── Identifica pré-requisitos e dependências

4. REGISTRA Z + RESULTADO DO TESTE (NOVO)
   Campos adicionais no KG:
   ├── status: "hipotese" | "validado" | "rejeitado"
   ├── viabilidade: 0-10
   ├── prerequisitos: lista de dependências
   └── conflitos: lessons que contradizem Z
```

### Mudanças no código

#### `master_agent.py` — Novo método `_testar_viabilidade_z()`

```python
def _testar_viabilidade_z(self, z, pergunta, topicos):
    """V5: Testa se o insight Z é implementável no MCR."""
    
    # 1. VERIFICA CONFLITOS NO KG
    conflitos = self.kg.buscar(z, max_r=5)
    conflitos_detectados = []
    for c in conflitos:
        # FAST avalia se essa lesson CONTRADIZ Z
        ...
    
    # 2. IDENTIFICA PRÉ-REQUISITOS
    prompt = (
        f"[Z] {z}\n"
        f"Liste o que seria necessário para implementar Z no MCR:\n"
        f"- Componentes/modulos existentes\n"
        f"- Novos desenvolvimentos\n"
        f"- Dependências externas"
    )
    prereqs = self.ia.gerar(prompt, 0.3, 'analisar')
    
    # 3. AVALIA VIABILIDADE
    prompt = (
        f"[Z] {z}\n"
        f"[PREREQS] {prereqs}\n"
        f"Avalie a viabilidade desta ideia para o MCR (0-10).\n"
        f"Responda APENAS um número."
    )
    viabilidade = int(self.ia.fast(prompt, 0.1, 'ultra_leve').strip() or "5")
    
    return {
        'viabilidade': viabilidade,
        'prerequisitos': prereqs,
        'conflitos': conflitos_detectados,
        'status': 'validado' if viabilidade >= 5 else 'rejeitado'
    }
```

#### `kg.py` — Campos novos no `aprender()`

```python
def aprender(self, erro, causa, solucao, ctx='geral', 
             status='hipotese', viabilidade=0, prerequisitos=''):
    lesson = {
        ...
        'status': status,           # NOVO: hipotese | validado | rejeitado
        'viabilidade': viabilidade, # NOVO: 0-10
        'prerequisitos': prerequisitos, # NOVO
    }
```

#### Estimativa: ~80 linhas no total

---

## 🆕 Emergir Direcionado

### Conceito

O EMERGIR normal amostra tópicos ALEATÓRIOS do KG e gera insights. O **Emergir Direcionado** recebe um PROBLEMA do usuário e busca tópicos RELEVANTES para gerar uma SOLUÇÃO direcionada.

### Pipeline

```
USUÁRIO: "NPC ferreiro não está vendendo itens corretamente"
         ↓
1. EXTRAIR TAGS DO PROBLEMA
   Ferramenta: Decider.classificar (já existe)
   → ["npc", "shop", "bug", "ferreiro", "itens", "venda"]
         ↓
2. BUSCAR NO KG POR TAGS
   Ferramenta: kg.buscar(tag) (já existe)
   → lessons sobre NPCGenerator, loja, CanaryIndexer, itens
         ↓
3. CONTEXT CREW ENRIQUECE
   Ferramenta: ContextCrew (já existe)
   → contexto adicional sobre NPCs, shops, itens
         ↓
4. EMERGIR DIRECIONADO
   → usa APENAS lessons relacionadas às tags
   → pergunta "E se {tag1} + {tag2} resolvesse {problema}?"
   → gera Z + expande + testa
   → Z é uma SOLUÇÃO, não só um insight
         ↓
5. IMPLEMENTA (ferramentas existentes)
   → NPCGenerator, ToolOrchestrator, validadores
   → Gera código + valida
         ↓
6. REGISTRA
   → ctx='solucao_direcionada'
   → Inclui referência ao problema original
```

### Arquitetura

```
EmergirDirecionado(problema)
    ├── _extrair_tags(problema)        → Decider.classificar
    ├── _buscar_licoes_por_tags(tags)  → kg.buscar (já existe)
    ├── _enriquecer_com_contextcrew()  → ContextCrew (já existe)
    ├── _gerar_pergunta_direcionada()  → "E se X+Y resolve {problema}?"
    ├── _gerar_emergencia_fragmentada() → (já existe!)
    ├── _testar_viabilidade_z()        → (NOVO — Ciclo Completo)
    ├── _gerar_solucao()               → IA.gerar com contexto
    └── _registrar_direcionado()       → kg.aprender
```

### Diferença do EMERGIR Normal

| Característica | EMERGIR Normal | EMERGIR Direcionado |
|---------------|:-------------:|:------------------:|
| **Gatilho** | Automático a cada 5 execuções | Manual (usuário pede) |
| **Origem dos tópicos** | Aleatório (KG) | Relevante (tags do problema) |
| **Pergunta** | "E se X+Y?" | "E se X+Y resolve {problema}?" |
| **Saída** | Insight conceitual (Z) | Solução prática + código |
| **Teste** | Autoavaliação (SIM/NAO) | Validação + viabilidade + conflitos |
| **Registro** | `ctx='emergente'` | `ctx='solucao_direcionada'` |
| **Tempo** | ~200s | ~250s (análise extra) |
| **Profundidade** | 20k chars | 25k chars + código |

### Comando do usuário

```python
# Novo comando para o MCR-DevIA
python MCR_DevIA-Kernel.py emergir_direcionado "NPC ferreiro não está vendendo itens corretamente"
```

### Estimativa: ~120 linhas no total

---

## 🔧 Dashboard — Correções Pendentes

| # | Item | O que fazer | Arquivo |
|---|------|------------|---------|
| 1 | **ETA por etapa** | Adicionar `elapsed` + `estimated` no `emit('stage')` | `master_agent.py` + `dashboard.html` |
| 2 | **Streaming real** | Timeout 3600s no `gerar_stream()`, fallback batch se falhar | `ia.py` |
| 3 | **Barra de progresso granular** | Cada sub-etapa (visões A, B, C) avança a barra | `dashboard.html` |
| 4 | **Narrador silencioso no fragmentador** | `_gerar_com_stream()` já emite narrador antes/depois | ✅ Feito |
| 5 | **Log de tokens recebidos** | Mostrar "Recebidos: 4.250 tokens" no log | `dashboard.html` |

---

## 📊 Comparação: EMERGIR Normal vs Direcionado

```
┌─────────────────────────────────────────────────────────────┐
│                    EMERGIR NORMAL (V4)                      │
│                                                             │
│  KG aleatório ──→ Z criativo ──→ Autoavaliação ──→ Salvar │
│                                                             │
│  "O que emerge se X+Y?"                                     │
│  Resultado: insight conceitual                              │
│  Uso: descoberta autônoma                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 EMERGIR DIRECIONADO (V5)                    │
│                                                             │
│  Problema do usuário ──→ Tags ──→ KG relevante             │
│       │                      │                              │
│       └──────────────────────┘                              │
│                  ↓                                          │
│  "E se X+Y resolve {problema}?"                             │
│       ↓                                                     │
│  Z + Expansão + Teste + Solução + Código                    │
│       ↓                                                     │
│  Resultado: plano de ação + implementação                   │
│  Uso: resolver problemas reais                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Arquivos que serão modificados

| Arquivo | O que muda | Linhas |
|---------|-----------|--------|
| `modulos/master_agent.py` | `_testar_viabilidade_z()`, `_extrair_tags()`, `_gerar_pergunta_direcionada()`, `_processar_emergencia_direcionado()`, correções streaming | ~200 |
| `modulos/kg.py` | Campos novos: `status`, `viabilidade`, `prerequisitos` | ~10 |
| `modulos/ia.py` | Timeout 3600s no `gerar_stream()` | 1 |
| `modulos/sse_server.py` | Suppress ConnectionAbortedError | ~5 |
| `sandbox/thought_dashboard.html` | ETA, progresso granular, log de tokens | ~30 |
| `comandos/cmd_emergir_direcionado.py` | **NOVO** — comando para Emergir Direcionado | ~40 |
| **TOTAL** | | **~286 linhas** |

---

## 🎯 Prioridade de implementação

1. **Dashboard correções** (streaming + ETA) — ~30 min
2. **Ciclo Emergir Completo** — ~45 min
3. **Emergir Direcionado** — ~1h

---

**Equipe MCR — Junho 2026**
