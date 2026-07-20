# SESSAO 2026-07-20 — HORIZONTE DO NIVEL 7: VARIACAO vs SELECAO

## Resumo

Testei empiricamente se a **comutacao multinivel** (word->esfera->trigrama) pode
substituir `random.uniform` como fonte de variacao para a selecao natural markoviana
(H22), permitindo cruzar o horizonte do nivel 7 sem violar o Pilar 1.

**Resultado: NAO. O horizonte e intransponivel com P(b|a) puro isolado.**

## O experimento

### v1: MCR escolhe o topico (ciclo interno)
- MCR decide qual topico abordar -> ambiente responde
- **Problema**: winner-takes-all. Primeira escolha ("mercador") se entrincheira
  porque gera mais dados -> confianca eternamente alta -> comutacao nunca dispara
- **Resultado**: 60/60 decisoes para "mercador". Comutacao: 0%.

### v2: Ambiente apresenta topicos (variacao externa)
- Ambiente alterna entre 8 topicos (4 bons, 4 ruins)
- MCR decide acao para cada input
- Bons persistem 5 turnos, ruins morrem em 1
- **Resultado**: BONS=RUAIS=15 decisoes cada. Comutacao: 0%.

## A descoberta fundamental

| Mecanismo | Gera variacao? | Viola Pilar 1? |
|-----------|---------------|----------------|
| random.uniform | SIM | SIM |
| Comutacao multinivel | NAO | NAO |
| Input humano variado | SIM | NAO |
| Multiplos MCRs (ecologia) | SIM | NAO |

A comutacao multinivel **muda a perspectiva** (word->trigrama->byte) mas nao
**gera alternativas novas**. Dado o mesmo input, todos os niveis sao
deterministicos — so "veem" features diferentes.

Para que a selecao natural opere (como em H22 v3), e preciso:
1. **Variacao**: alternativas diferentes para escolher
2. **Ciclo**: consequencias realimentadas como P(b|a)
3. **Persistencia diferencial**: boas escolhas geram mais dados

A comutacao nao fornece o #1. O ciclo (FASE 21) fornece #2. A persistencia
(H22) fornece #3. Sem #1, o sistema converge deterministicamente.

## Revisitando H22

Em H22 v3, a selecao OPEROU (26x) porque o **ambiente apresentava topicos
diferentes** — a variacao vinha do input externo. O MCR so precisava aprender
o mapeamento. Mas isto e aprendizado supervisionado disfarcado: o "mundo"
decide o que apresentar, e o MCR descobre qual resposta funciona.

Em H22 v4 (calibracao), adicionar `random.uniform` permitiu que o proprio MCR
explorasse — e funcionou (diff=0.360). Mas viola Pilar 1.

## Conclusao: o horizonte do nivel 7 e real

Tres experimentos independentes confirmam:
1. **H22a (rotulos textuais)**: falso positivo (contaminacao)
2. **H22b (supervisionado)**: nao e selecao real
3. **Este experimento (comutacao sem random)**: variacao insuficiente

O nivel 7 (self) requer AUTO-OBSERVACAO + VARIACAO. O MCR puro tem o ciclo
(auto-obs) mas nao tem variacao interna. A comutacao multinivel e insuficiente
como fonte de variacao.

### Implicacao para os Pilares

Pilar 1 e suficiente para niveis 3-6 (mundo -> modelo).
Pilar 1 NAO e suficiente para nivel 7 (self -> modelo do self).

A pergunta que fica: **qual mecanismo MCR-puro (sem random, sem LLM) pode
gerar variacao interna?** Candidatos:
- **Ecologia de MCRs**: multiplos motores competindo (Opcao B)
- **Input humano real**: Primeiro Sinal (Opcao 3)
- **Ruido de quantizacao**: erros de precisao numerica como variacao

## Comutacao de nivel removida do coupling.py

A comutacao (Esfera/Trigrama em decidir()) foi removida porque:
1. Nunca disparava na regressao (confianca sempre > 0.15)
2. Quando testada com dados novos, nao melhorava discriminacao
3. Na pratica, word-level ja resolve os casos da regressao

## Regressoes

- Fase 1: 113/113 = 100%
- Fase 18: 64/64 = 100%

## Arquivos modificados

- `mcr/coupling.py` — comutacao removida de `decidir()`, apenas comentario
  do experimento preservado

## Experimentos

- `tmp/exp_ciclo_selecao_comutacao.py` — v1: MCR escolhe (winner-takes-all)
- `tmp/exp_ciclo_selecao_comutacao_v2.py` — v2: ambiente varia (sem selecao)
- `tmp/exp_nomes_multinivel.py` — geracao 10/10 nomes via MarkovUniversal
- `tmp/exp_nomes_multinivel2.py` — geracao melhorada (3 niveis)
