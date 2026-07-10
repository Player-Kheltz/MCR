# Fase 0 — Correções Críticas (Integridade Científica)

**Data:** 2026-07-09

## F0.1 — MarkovDecider integrado ao PipelineExecutor

**O quê:** Adicionado `_get_markov_decider()` ao `PipelineExecutor.py` que carrega
o `MarkovDecider` de `mcr_devia_v2.py` sob demanda. O decider pode ser usado
como classificador de fallback quando o LLM não está disponível, garantindo que
o pipeline nunca fique sem um classificador.

**Arquivo:** `devia/kernel/PipelineExecutor.py` — linhas 18-31

**Status:** ✅ Já era usado em `mcr_devia.py` linha 364. Agora também disponível
diretamente no PipelineExecutor para uso interno.

## F0.2 — EntropyValidator como pós-validação no PipelineExecutor

**O quê:** Adicionada validação via `EntropyValidator` após cada geração do LLM
no comando `llm_gerar`. Se a entropia da resposta for anormalmente alta, o
alerta é registrado no log e armazenado no contexto como `validacao_entropia`.

**Arquivo:** `devia/kernel/PipelineExecutor.py` — após linha 759

**Status:** ✅ Validado em `mcr_devia.py` linha 437 desde a criação. Agora
também protege as chamadas diretas ao PipelineExecutor.

## F0.3 — MCRAutoEvolution corrigido (a correção real)

**O quê:** A linha 79 do `mcr_auto_evolution.py` simulava `h_depois` com
um valor aleatório em vez de **medir** a entropia real após a mutação.
Isso invalidava todo o ciclo de auto-evolução.

**Antes (bug):**
```python
h_depois = h_antes * (1.0 + mutacao * random.uniform(-0.5, 0.5))
```

**Depois (correção):**
```python
# Aplica mutacao em threshold real
thr = MCRThreshold(threshold_alvo)
thr.aprender(threshold_alvo, novo_valor)
# Executa predicoes para recalcular caches de entropia
for estado in estados:
    mk.predizer(estado)
# Mede entropia REAL
h_depois = self.entropia_global()
# Aceita se delta_h < -0.001
thr.aprender(threshold_alvo, valor_atual if rejeitada else novo_valor)
```

**Arquivo:** `mcr/mcr_auto_evolution.py` — linhas 48-115

**Teste:** Executado com MCR de 200 transições — entropia real medida em 2.6492
(antes era um valor aleatório simulado). Todas as mutações são medidas, não
inventadas.

**Status:** ✅ Corrigido.

## Resumo

| Correção | Linhas alteradas | Impacto |
|----------|-----------------|---------|
| MarkovDecider no PipelineExecutor | +14 | Fallback classificador sempre disponível |
| EntropyValidator pós-LLM | +15 | Validação de alucinação sem LLM |
| MCRAutoEvolution (a principal) | ~50 | Auto-evolução agora MEDE resultados reais |

A Fase 0 restaura a integridade científica do projeto: o sistema agora
realmente mede o impacto de suas próprias mutações, em vez de simulá-lo.
