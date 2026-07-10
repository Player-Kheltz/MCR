# Fase 1 — Infraestrutura para Qualidade 70B

**Data:** 2026-07-09

## F1.1 — RoPE Scaling (Janela de Contexto 32K)

**O quê:** Criado modelo Ollama `qwen2.5-coder:7b-32k` com `num_ctx: 32768`.

**Teste:** Prompt de ~80K caracteres (~16K tokens) processado com sucesso:
- `prompt_eval_count: 16063` — confirma avaliação de 16K+ tokens
- Tempo: 13.6s para 16K tokens (aceitável para modelo 7B local)
- Modelo original (4K): 6.1s

**Comando para criar:** `ollama create qwen2.5-coder:7b-32k -f Modelfile_qwen32k`

**Modelfile:**
```
FROM qwen2.5-coder:7b
PARAMETER num_ctx 32768
PARAMETER num_predict 2048
```

**Impacto:** O mesmo pode ser feito para `deepseek-r1:7b`, `mistral:7b`, etc.

## F1.2 — Compressão de Prompt (Selective Context)

**O quê:** Implementado `mcr/prompt_compressor.py` que reduz prompts em 50-80%.

**Estratégia:**
1. Divide prompt em parágrafos (por `\n\n`)
2. Preserva system prompt e pergunta do usuário
3. Remove duplicatas de parágrafos idênticos
4. Filtra parágrafos por similaridade Jaccard com a pergunta
5. Threshold adaptativo: aumenta progressivamente até caber no `max_tokens`

**Resultados:**
| Cenário | Antes | Depois | Compressão |
|---------|-------|--------|------------|
| Texto repetitivo sem `\n\n` | 5.760 tokens | 21 tokens | **99.6%** |
| Múltiplos tópicos | 55 tokens | 14 tokens | **75%** |
| Prompt pequeno | Preservado | Preservado | **0%** |

**Uso:**
```python
from mcr.prompt_compressor import comprimir_e_logar
prompt_comprimido = comprimir_e_logar(prompt, pergunta, max_tokens=24000)
```

**Integração:** Chamar antes de `LLM.gerar()` para reduzir tokens de entrada.

## F1.3 — Cache Hierárquico (L1→L2→L3→LLM)

**O quê:** Implementado `mcr/cache_hierarquico.py` com 3 níveis + fallback LLM.

| Nível | Mecanismo | Tempo | Taxa de acerto esperada |
|-------|-----------|-------|------------------------|
| L1 | Dict: pergunta normalizada → resposta | 0.0001s | 30-40% |
| L2 | MarkovDecider + Jaccard ≥ 0.12 | 0.001s | 20-30% |
| L3 | Raw token set + Jaccard ≥ 0.15 | 0.01s | 10-20% |
| LLM | Fallback via Ollama | 8-12s | 0% (miss) |

**Resultados do teste:**
```
L1 identica: OK (esperado=True, obtido=True)
L2 similar:  OK (esperado=True, obtido=True)
L3 parafrase: OK (esperado=True, obtido=True)
Miss:        OK (esperado=False, obtido=False)
Stats: 75% acerto, l1_hit=1, l2_hit=1, l3_hit=1, miss=1
```

**Características:**
- Persistência em `devia/kernel/cache/cache_hierarquico.json`
- Expiração automática após 24h
- Limite de 2.000 entradas (LRU aproximado)
- Aprende automaticamente com MarkovDecider a cada nova entrada

**Uso:**
```python
from mcr.cache_hierarquico import CacheHierarquico
cache = CacheHierarquico()

resposta = cache.buscar(pergunta)
if resposta:
    return resposta  # Zero LLM!

# ... chama LLM ...
cache.aprender(pergunta, resposta_llm, classe)
```

## Resumo da Fase 1

| Componente | Redução de tokens/LLM |
|-----------|----------------------|
| RoPE 32K | +400% janela de contexto |
| Compressão | -50-80% tokens de entrada |
| Cache (combinado) | -50-75% chamadas ao LLM |
| **Impacto total estimado** | **~80-90% menos chamadas ao LLM** |

## Arquivos Criados/Modificados

| Arquivo | Mudança |
|---------|---------|
| `mcr/prompt_compressor.py` | **NOVO** — compressão de prompt via Selective Context |
| `mcr/cache_hierarquico.py` | **NOVO** — cache L1→L2→L3 com fallback LLM |
| `devia/kernel/mcr_kernel/signature.py` | Adicionado `?` aos delimitadores do `raw_token_set()` |
| Modelo Ollama `qwen2.5-coder:7b-32k` | **NOVO** — janela 32K |
