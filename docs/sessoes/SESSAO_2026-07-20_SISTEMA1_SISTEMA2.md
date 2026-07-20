# SESSAO 2026-07-20 — SISTEMA 1 + SISTEMA 2 (KAHNEMAN INVERTIDO)

## Correcao de direcao

Kheltz corrigiu duas vezes:
1. "Os sonhos nao devem funcionar como triunvirato, eles devem ser
   a criatividade, o ludico, o vocabulario."
2. "Por voce esta decidindo? O MCR deve decidir."

## Arquitetura

Sistema 1 (motor): rapido, preciso, decidir() em 50ms
Sistema 2 (sonho): livre, criativo, sem objetivo

O motor consulta o sonho SO quando tem baixa confianca.
O threshold NAO e hardcoded — emerge da mediana das confiancas
observadas (Pilar 2: entropia descobre).

O sonho NAO escreve no motor. O motor CONSULTA o sonho.
Como o humano que sonha uma solucao mas verifica com logica ao acordar.

## Resultado honesto

### Arquitetura: FUNCIONA
- Threshold emergente (mediana): 0.5017
- Motor e consultado em casos de baixa confianca: SIM
- Motor NAO contaminado: obs=1262 (intacto)
- Sonho NAO alimenta motor de volta: freq_sonhar=0

### Inspiracao: NAO SUPEROU O MOTOR (ainda)
- Casos consultados: 2/20 (conf < threshold)
- Casos melhorados: 0/20
- Razao: as alternativas do sonho incluem o texto original como
  semente, entao o motor ve as mesmas features e classifica igual

Exemplo:
- Motor: "criar textura agua" -> responder (conf=0.436)
- Sonho alt #1: "criar textura agua dois tres um sequencia..." -> responder (conf=0.203)
- Sonho alt #2: "criar textura agua pa pg fib coll..." -> responder (conf=0.324)
- Sonho alt #3: "criar textura agua buscar editar validar..." -> responder (conf=0.304)

Todas as alternativas tem confianca MENOR que a original porque
incluem o mesmo texto + ruido. O sonho precisa gerar VARIANTES do
texto (recombinar palavras, sinonimos), nao texto+estado.

### Comparacao com teste 22 (contaminacao direta)

| Abordagem | Contamina? | Consulta? | Melhora? |
|-----------|-----------|----------|---------|
| Alimentar sonho direto (teste 22) | SIM (-70.6%) | N/A | NAO |
| Consultar sonho isolado (teste 23) | NAO | SIM | NAO (ainda) |

A arquitetura esta correta (sem contaminacao). A geracao de
alternativas precisa refinamento.

## A pergunta que permanece

Como o sonho deve gerar variantes do texto que sejam genuinamente
diferentes (nao texto+estado)?

Opcoes:
1. Recombinar palavras do texto com vocabulario do estado
2. Gerar sinonimos via _nmi_semantico
3. Gerar a partir do estado SEM o texto original (sonho puro)

A opcao 3 e a mais pura — o sonho sonha sem input, e o motor
verifica se o sonho se aplica ao input. Como o humano que sonha
sem contexto e aplica o insight ao acordar.

## Regressoes

- Fase 1: 113/113 = 100%
- Fase 18: 64 PASS / 0 FAIL
