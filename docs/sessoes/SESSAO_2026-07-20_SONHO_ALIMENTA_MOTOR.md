# SESSAO 2026-07-20 — SONHO ALIMENTA MOTOR (RESULTADO HONESTO)

## O que testamos

Se o sonho (criatividade) alimenta o motor (logica) de volta via
FASE 21, o motor melhora — ou contamina?

Motor A (controle): corpus base (1262 obs)
Motor B (experimental): corpus base + 10 sonhos alimentados

## Resultado honesto

| Metrica | Motor A | Motor B | Delta | Vencedor |
|---------|---------|---------|-------|----------|
| Regras | 94.1% | 23.5% | **-70.6%** | A |
| Zero-shot | 60.0% | 40.0% | **-20.0%** | A |
| Sonho H | 5.986 | 6.041 | +0.055 | B |
| Sonho unicos | 76 | 77 | +1 | B |
| Sinonimia AUC | 1.000 | 1.000 | 0 | = |
| Vocab | 454 | 472 | +18 | B |

## Diagnostico

**O sonho alimentado diretamente CONTAMINA a logica do motor.**

Regras cairam de 94.1% para 23.5% (-70.6%). O sonho introduz
transicoes que nao pertencem a nenhuma regra matematica —
"sequencia numeros listar ordem serie padrao encadear" nao e PA
nem PG nem FIB. O motor aprende essas transicoes e classifica
errado.

Zero-shot caiu de 60% para 40%. O sonho introduz tokens genericos
que dominam decidir().

O sonho melhora CRIATIVIDADE marginalmente (H +0.055, +1 unico,
+18 vocab). Mas o custo e destruicao da classificacao.

## A licao

Como Kheltz disse: "os sonhos nao devem funcionar como triunvirato,
eles devem ser a criatividade, o ludico, o vocabulario."

O sonho e CRIATIVIDADE. O motor e LOGICA. Misturar os dois
DIRETAMENTE destrui ambos. O sonho contamina o motor porque
introduz transicoes que nao tem relacao com as acoes treinadas.

**O sonho precisa ser ISOLADO do motor.** Nao alimentado de volta
direto. Como o formigueiro: isolamento entre clusters. O sonho
e um cluster separado — "sonhar" — e nao deve transbordar para
"PA", "FIB", "gerar_npc".

## A pergunta que permanece

Como integrar criatividade (sonho) e logica (motor) sem contaminar?

Resposta parcial: ISOLAMENTO. O sonho fica no seu cluster. O motor
consulta o sonho quando precisa de criatividade (vocabulario novo,
recombinacao), mas o sonho nao alimenta o motor diretamente.

Como o subconscious humano: sonha isolado, alimenta a consciencia
indiretamente (atraves de intuicao, nao de dados brutos).

## Regressoes

- Fase 1: 113/113 = 100%
- Fase 18: 64 PASS / 0 FAIL
