# Transição do Minerador — Fase C → G

## Objetivo

Reduzir a dependência do tree‑sitter (parser baseado em gramática)
substituindo-o progressivamente por um **atalho estatístico**: quando
o Knowledge Graph já conhece um padrão estrutural com confiança
suficiente, o sistema classifica novas entidades **sem invocar o parser**,
usando apenas similaridade Jaccard entre tokens brutos e a entropia
do cluster.

## Arquitetura da Decisão

A decisão de pular o parser é **adaptativa**, guiada por entropia,
sem nenhum limiar fixo:

```
Entrada: arquivo fonte
  │
  ├─ raw_token_set() — tokeniza com delimitadores universais
  │   { } ( ) ; , . : [ ] " ' / \ #  (sem gramática)
  │
  ├─ similaridade Jaccard com raw_fingerprint de cada cluster
  │
  ├─ entropia de Shannon do melhor cluster
  │
  └─ MCRDecisor.decidir_pular_parser(entropia, similaridade)
       │
       │  limiar = 0.3 + 0.7 × entropia  (Ponte Ótima)
       │
       ├─ similaridade >= limiar → PULAR PARSER ✅
       └─ similaridade <  limiar → USAR PARSER (fallback)
```

## Componentes Implementados

### 1. `raw_token_set()` em `mcr_kernel/signature.py`

Tokeniza usando apenas delimitadores comuns a múltiplas linguagens:
```python
_DELIMITADORES_UNIVERSAIS = r'[\s{}();.,:\[\]"\'\`/\\#<>!=+\-*%&|^~@]+'
```
Sem palavras-chave, sem gramática, sem conhecimento prévio.

### 2. `raw_fingerprint` em `SignatureCluster` (`mcr/mcr_signature_cluster.py`)

Cada cluster agora armazena:
- `_raw_fingerprint: Set[str]` — união dos raw_token_sets de todas as suas entidades
- `_entropia: float` — entropia de Shannon da distribuição de tipos no cluster
- `computar_raw_fingerprint()` — varre arquivos fonte e computa retroativamente
- `similaridade_raw(tokens) -> float` — Jaccard entre tokens brutos e o fingerprint

### 3. `decidir_pular_parser()` em `MCRDecisor` (`mcr_kernel/decisor.py`)

Implementa a Ponte Ótima:
```python
limiar = min_similaridade_base + (1 - min_similaridade_base) × entropia
```

- Entropia baixa (cluster homogêneo) → limiar baixo → mais propenso a pular parser
- Entropia alta (cluster diverso) → limiar alto → mais propenso a usar parser
- Cada decisão é aprendida no Markov do decisor para refinamento futuro

### 4. `mcr/raw_miner.py`

Módulo orquestrador:
- `computar_raw_fingerprints(clusters)` — prepara os clusters
- `classificar_sem_parser(arquivo, clusters)` — tenta classificar sem parser
- `validar_pipeline(clusters, arquivos)` — métricas de validação
- `gerar_entidade_de_cluster(arquivo, cluster)` — gera entidade a partir do protótipo

## Resultados — Domínio C# (Grimório WPF)

| Métrica | Valor |
|---------|-------|
| Entidades totais | 65 |
| Clusters formados | 44 |
| **Classificadas sem tree-sitter** | **17 de 20 (85%)** |
| Similaridade Jaccard média | 0.878 |
| Entropia média dos clusters | 0.0 (clusters homogêneos) |
| Tokens brutos totais | 7.440 |

### Casos notáveis

| Arquivo | Decisão | Similaridade | Entropia | Motivo |
|---------|---------|-------------|----------|--------|
| App.xaml.cs | PULAR ✓ | 1.000 | 0.0 | Cluster homogêneo |
| NavButton.cs | PULAR ✓ | 1.000 | 0.0 | Cluster homogêneo |
| DatabaseService.cs | USAR fallback | 0.992 | 1.0 | Alta entropia → decisor cauteloso |

O caso `DatabaseService.cs` (similaridade 0.992, entropia 1.0) demonstra que o
sistema NÃO usa um threshold fixo — mesmo com 99% de similaridade, o decisor
cautelosamente invocou o parser porque o cluster tinha entropia máxima,
indicando que não valeria a pena pular etapas com um cluster tão variado.

## Próximos Passos

1. **Integrar no `cold_start()`** — fazer o pipeline de mineração usar
   `classificar_sem_parser()` antes de invocar o tree-sitter por padrão
2. **Fase G (EntropyMiner)** — substituir completamente o tree-sitter
   por análise de entropia em janelas deslizantes de bytes
3. **Refinamento da Ponte Ótima** — automatizar o ajuste de
   `min_similaridade_base` via `MCRMeta`

## Arquivos Modificados/Criados

| Arquivo | Mudança |
|---------|---------|
| `devia/kernel/mcr_kernel/signature.py` | + `raw_token_set()`, `raw_token_set_from_file()` |
| `devia/kernel/mcr_kernel/decisor.py` | + `MCRDecisor.decidir_pular_parser()` |
| `mcr/mcr_signature_cluster.py` | + `_raw_fingerprint`, `_entropia`, `computar_raw_fingerprint()`, `similaridade_raw()`, `calcular_entropia()` |
| `mcr/raw_miner.py` | **NOVO** — orquestrador da mineração sem parser |
