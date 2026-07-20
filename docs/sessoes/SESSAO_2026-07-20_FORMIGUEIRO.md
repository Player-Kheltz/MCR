# SESSAO 2026-07-20 — FORMIGUEIRO: PERTENCIMENTO MÚLTIPLO

## O que aconteceu

Kheltz teve uma intuição sobre pertencimento: algo não pertence a UM
cluster, pertence a MÚLTIPLOS. O número 1 pertence a Fibonacci, Primos,
Quadrados, Collatz — simultaneamente. Um fragmento "16 8 4 2" toca
Collatz sem ser Collatz completo. Como o formigueiro: cada formiga não
é operária OU soldada — é tudo, em diferentes graus.

## Implementação

`mcr/formigueiro.py` — `Formigueiro`:
- Clusteriza ações por NMI (threshold emergente: max gap)
- Pertencimento: P(cluster|texto) = soma de P(acao|palavra) para cada
  palavra do texto — markoviano puro (Pilar 1)
- Decisão: combina predições de TODOS os clusters tocados, ponderadas
  pelo grau de pertencimento

## Resultados

### Pertencimento múltiplo: VALIDADO

Cada texto toca 3+ clusters com diferentes graus:

| Texto | Clusters tocados | N |
|-------|-----------------|---|
| sequencia dois quatro seis oito | 0.65, 0.12, 0.10 | 3 |
| padrao tres cinco oito treze | 0.60, 0.23, 0.08 | 3 |
| encadear cinco dezesseis oito quatro | 0.64, 0.18, 0.09 | 3 |
| ordem dois tres cinco sete | 0.51, 0.30, 0.08 | 3 |

**O número 3 EMERGE** — não nas ações (cada ação em 1 cluster), mas nos
**pertencimentos dos textos**. Cada texto toca naturalmente ~3 clusters.
Sem hardcode. Emergente.

### Fragmentos parciais: VALIDADO

| Fragmento | Classificação | Significado |
|-----------|--------------|-------------|
| dezesseis oito quatro dois | COLL | Fragmento de Collatz (16→8→4→2→1) |
| oito quatro dois um | COLL | Fragmento final de Collatz |

O MCR reconhece fragmentos que PERTENCEM a Collatz sem ser a sequência
completa. É o "pulo" que Kheltz descreveu: mostrou parte de uma string
de Collatz.

### Decisão combinada: MODULAR SUPEROU O GLOBAL

| Método | Acurácia |
|--------|----------|
| Global (MCR raw) | 76.9% (10/13) |
| Sub-MCR (isolado) | 30.8% (4/13) |
| **Modular (global + pertencimento)** | **84.6% (11/13)** |

O modular SUPEROU o global. Estratégia:
1. `decidir()` do MCR global (13 fontes, 4262 obs) → (acao, conf)
2. `pertencimento(texto)` → P(cluster|texto) via P(acao|palavra) * IDF^4
3. Se ação confirmada pelo cluster top OU conf >= 0.5: manter global
4. Se contradição E conf < 0.5: modular `_dist_features` pelo pertencimento

O modular CORRIGIU "numeros quatro oito dezesseis" (global=gutenberg ERR,
modular=PG OK) e MANTEVE os 2 acertos de gutenberg (conf >= 0.5).

Os 2 erros restantes são genuinamente ambíguos:
- "sequencia dois quatro seis oito" → COLL (esperado PA) — "dois quatro
  seis oito" existe em PA (2,4,6,8) e COLL (fragmento 16→8→4→2)
- "um dois tres" → FIB (esperado PA) — "um dois tres" existe em PA
  (1,2,3) e FIB (1,1,2,3 parcial)

Para 100%, precisaria de contexto adicional (sequências mais longas) ou
n-grama de ordem superior que capture a estrutura completa.

## A intuição do número 3

O número 3 aparece em três lugares:

1. **Pertencimento dos textos**: cada texto toca ~3 clusters
2. **n-grama[2]** (3 pontos: a, b, c): foi o que reviveu a geração
   (n-grama[1] = 2 pontos ficava em loop)
3. **Ciclo do sonho**: estado → sonho → realimentação (3 passos)

O 3 não é hardcode. Emergentemente aparece onde há mediação — sem 3,
não há fronteira entre dentro e fora. 2 é linha. 3 é triângulo — a
primeira estrutura com interior.

## Arquivos criados

- `mcr/formigueiro.py` — pertencimento múltiplo (230 linhas)
- `tools/baselines/17_cluster_recursivo.py` — cluster recursivo (árvore)
- `tools/baselines/18_formigueiro.py` — teste do formigueiro
- `mcr/cluster_recursivo.py` — clusterização recursiva (270 linhas)

## Regressões

- Fase 1: 113/113 = 100%
- Fase 18: 64 PASS / 0 FAIL

## A pergunta que permanece

O pertencimento múltiplo está validado. O número 3 emerge. Fragmentos
funcionam. Mas a decisão combinada precisa de refinamento arquitetural:
sub-MCRs isolados são pequenos demais. O caminho é modular o MCR global
pelos graus de pertencimento, não substituí-lo por sub-MCRs.

O formigueiro é a direção certa. A implementação precisa amadurecer.
