# Fase 2 — Ensemble de Modelos 7B + Chain-of-Verification

**Data:** 2026-07-09

## F2.1 — Ensemble de Modelos 7B

**O quê:** 3 modelos 7B (Qwen, Mistral, DeepSeek) geram respostas em paralelo.
O juiz simbólico (Jaccard + entropia) seleciona a melhor.

**Modelos criados com janela 32K:**
- `qwen2.5-coder:7b-32k`
- `mistral:7b-32k`
- `deepseek-r1:7b-32k`

**Arquivo:** `mcr/ensemble_7b.py`

**Resultado do teste:**
```
Pergunta: Explique o que e SPA em uma frase curta.
Qwen:     344 chars, H=1.167
Mistral:  197 chars, H=1.130 ← selecionada (menor entropia)
DeepSeek: 273 chars, H=1.135
Consenso: False (sim max 0.245)
Tempo:    24.55s (3 modelos em paralelo)
```

## F2.2 — Chain-of-Verification (CoVe)

**O quê:** Extrai termos da resposta, gera perguntas de verificação,
consulta o KG, e detecta alucinações.

**Fluxo:**
```
Resposta LLM → extrair termos com maiúsculas →
gerar 3-8 perguntas de verificação →
consultar KG (Metacognicao) para cada pergunta →
se falhar: registra falha + tenta corrigir com contexto
```

**Arquivo:** `mcr/chain_of_verification.py`

## F2.3 — Integração Completa

**O quê:** Pipeline unificado com roteamento adaptativo.

```
                      MarkovDecider.classificar()
                              │
                    confianca > 0.3?
                      │         │
                    SIM        NÃO
                      │         │
                   Cache      É complexa?
                  L1→L2→L3     │    │
                      │       SIM   NÃO
                    Hit?    ┌─────┐
                    │  │   │     │
                  SIM  NÃO │  LLM Simples
                    │    │ │  (Qwen 7B)
                 Resposta │ │      │
                    │     │ │  CoVe
                    │     ▼ ▼      │
                    │  LLM Simples │
                    │  (Qwen 7B)  │
                    │      │      │
                    │    CoVe    │
                    │      │      │
                    ▼      ▼      ▼
                  Resposta   CoVe falhou?
                               │    │
                             SIM   NÃO → Resposta
                               │
                          Ensemble 7B
                          (3 modelos)
                               │
                             CoVe
                               │
                            Resposta
```

**Seed inicial:** `mcr/seed_markov.py` — 29 exemplos em 6 classes.

## Arquivos Criados

| Arquivo | Descrição |
|---------|-----------|
| `mcr/ensemble_7b.py` | Orquestrador de Ensemble com 3 modelos 7B + juiz simbólico |
| `mcr/chain_of_verification.py` | Verificador de alucinações contra o KG |
| `mcr/pipeline_completo.py` | Pipeline integrado (cache → LLM → Ensemble → CoVe) |
| `mcr/seed_markov.py` | 29 exemplos iniciais para o MarkovDecider |

## Modelos Ollama Criados

| Modelo | Janela | Uso |
|--------|--------|-----|
| `qwen2.5-coder:7b-32k` | 32K | LLM padrão + Ensemble |
| `mistral:7b-32k` | 32K | Ensemble |
| `deepseek-r1:7b-32k` | 32K | Ensemble |
