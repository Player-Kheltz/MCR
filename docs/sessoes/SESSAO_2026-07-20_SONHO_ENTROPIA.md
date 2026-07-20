# SESSAO 2026-07-20 — SONHO POR ENTROPIA

## O que testamos

O sonho markoviano greedy convergia (3/10 unicos). Hipotese: geracao por
entropia (maximizar H da janela em vez de max P(b|a)) geraria mais
variação entre ciclos.

## Implementacao

`SonhoMarkoviano._gerar_proximo(modo="entropia")`:
- Para cada candidato, simular adicionar e calcular H da janela (20 tokens)
- Escolher token que MAXIMIZA H da janela
- Desempate por P(b|a) (preferir o mais provavel)
- Deterministico (Pilar 1): sem random

## Resultados

| Metrica | Greedy | Entropia | Delta |
|---------|--------|----------|-------|
| Sonhos unicos | 3/10 | 3/10 | +0 |
| H media | 5.241 | 5.566 | +0.324 |
| H min | 5.098 | 5.465 | +0.367 |
| H max | 6.077 | 6.077 | 0 |

**Entropia aumenta H (+0.324) mas nao aumenta unicidade.**

## Diagnostico honesto

A entropia melhora a diversidade INTERNA de cada sonho (H maior =
tokens mais variados dentro do sonho). Mas nao quebra a CONVERGENCIA
entre ciclos porque:

1. O n-grama[3] e deterministico — dado o mesmo prefixo, mesmos candidatos
2. A semente "final do sonho + estado" gera o mesmo caminho apos ciclo 2-3
3. A entropia so diverge do greedy quando ha multiplos candidatos com H
   igual — e quando ha, escolhe o que aumenta H da janela. Mas o n-grama
   ainda leva ao mesmo destino.

**Para variar entre ciclos, precisa de algo mais profundo:**
- Recursao do sonho (sonhar sobre o sonho anterior)
- n-grama de ordem alternada (2, 3, 4) a cada ciclo
- Perturbacao deterministica (usar checksum do estado como bias)

Mas isto e trabalho futuro. O resultado atual e honesto: entropia
aumenta diversidade interna mas nao quebra convergencia entre ciclos.

## O que permanece

O sonho markoviano FUNCIONA (5/6 PASS):
- Deterministico (Pilar 1)
- Gera sequencia inedita a partir de si mesmo
- Novidade (23 tokens novos)
- Ciclo fechado (freq_sonhar=10)
- Entropia nao-trivial (H=5.566)

A limitacao honesta: 3/10 sonhos unicos. A variação entre ciclos
requer recursao ou mecanismo mais profundo. A entropia é um passo
na direção certa (H maior) mas não é suficiente sozinha.

## Regressoes

- Fase 1: 113/113 = 100%
- Fase 18: 64 PASS / 0 FAIL
