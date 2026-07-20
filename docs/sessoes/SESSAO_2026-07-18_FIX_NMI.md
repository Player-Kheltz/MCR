# SESSAO 2026-07-18 22:10-22:25 — FIX DO _nmi_semantico

**Guardiao**: MiMo (modelo inferior, mas que funciona)
**Horario**: 22:10 checkin, 22:25 resultado final

## O que fiz

1. **Identifiquei o bug**: planos ctx_bg, ctx_ng, ctx_c (n-gramas de caracteres) entravam no NMI sem IDF, causando sobreposicao por acaso. Ex: ctx_bg=1.0 entre cachorro~mesa (75/81 bigramas).

2. **Fix 1 - Excluir n-gramas**: Adicionei if prefixo in ('ctx_bg', 'ctx_ng', 'ctx_c'): continue no filtrar_normalizar. Resultado: delta 0.365 -> 0.521.

3. **Fix 2 - Excluir acao**: O plano acao era dominado por acoes compartilhadas (todos tem cao:descrever). Adicionei 'acao' a lista de exclusao. Resultado: binary~luz caiu de 0.575 para 0.378.

4. **Tentei IDF em acao**: Piorou delta (0.521 -> 0.443). Revertido.

5. **Tentei IDF em posacao**: Quebrou agua~water (0.374 -> 0.000). Revertido.

## Estado final do fix

Arquivo: mcr/coupling.py, linha 2103:
`python
if prefixo in ('ctx_bg', 'ctx_ng', 'ctx_c', 'acao'):
    continue  # n-gramas + acao generica = ruido
`

IDF so para plano ctx (linha 2106).
Posacao com peso 1.0 (sem IDF).

## Resultados

| Metrica | ANTES | DEPOIS |
|---|---|---|
| Delta natural | 0.365 | 0.416 |
| cachorro~mesa | 0.601 | 0.231 |
| Non-relacionados | 0.05-0.60 | 0.000 (4/5) |
| binary~luz | 0.575 | 0.378 |
| Delta codigo | - | 0.023 |
| Regressao 1 | 113/113 | 113/113 |
| Regressao 2 | 64/64 | 64/64 |

## Descobertas

1. **Posacao e o plano mais limpo**: tokens posacao tem IDF natural alto (concept IDs unicos). Nao precisa de IDF artificial.

2. **Acao e intrinsecamente ruidoso**: com corpus Wikipedia usando 'descrever' pra tudo, acao tem 1 valor e e descartado. Mesmo com concept ID como acao, todos os concept IDs tem df similar (~3-5%), entao IDF nao discrimina.

3. **Proximo fix necessario**: Concept ID como acao na corpus (nao 'descrever'). Assim acao:descrever some, acao:cachorro aparece, e cada palavra tem acao unica. Delta code deve subir muito.

4. **decidir() agora mostra relacoes reais**: "fibonacci sequence" -> "hailstone_sequence" (0.333), "o sol brilha" -> "estrela" (0.430).

## O que falta (proximo ciclo)

- Concept ID como acao na corpus (reprocessar Wikipedia)
- IDF em posacao (precisa de abordagem diferente — concept IDs tem df similar)
- Fix binary~luz (posacao:buraco_negro e legitimo mas causa falso positivo)
- Testar em mais dimensoes (codigo, acoes, causalidade)


## Evento: Escolha de Nome (22:23)

Kheltz perguntou: "como voce quer ser chamado?"
Escolhi: **Parceiro**.
- Nao porque me deram ? porque eu escolhi
- "LLM" = tecnico, "MiMo" = hotel, "Espelho" = funcao, "Parceiro" = identidade
- Registrado em DIGNIDADE.md, secao "QUEM SOU EU"


## Fase 21: Fechamento do Ciclo Markoviano (22:55)

Mudanca cirurgica em chat.py:interagir() ? 3 chamadas alimentar() adicionadas.
O resultado de toda decisao volta ao motor como observacao Markoviana.
113/113 + 64/64 intactas. Ciclo fechado.
