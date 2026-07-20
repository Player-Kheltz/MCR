# SESSAO 2026-07-20 — EMERGIR: O MCR PERGUNTA "E SE?"

## Descoberta

Kheltz descreveu o sonho como EMERGIR: "E se X + Y = Z?"

Como Kheltz faz "decida, explore, valide" com o LLM, o MCR faz
consigo mesmo:
1. DECIDA: sonho escolhe dois conceitos
2. EXPLORE: recombina — "E se X + Y?"
3. VALIDE: motor verifica se a recombinação tem estrutura
4. Se valido: nova relacao descoberta. Se nao: descarta (Pilar 9).

## Implementacao

`SonhoMarkoviano.emergir()` — recombina conceitos que coocorrem
`SonhoMarkoviano.emergir_livre()` — recombina conceitos que NUNCA
coocorrem. Deterministico (Pilar 1): hash do estado como seed.

## Resultado

### Descoberta NOVA: "tem" + "vende" -> gerar_npc

- "tem" e "vende" NUNCA coocorreram no corpus
- Combinados: conf=0.957, acao=gerar_npc
- Sinergia: +0.112 (recombinação mais forte que partes isoladas)
- Motor NAO contaminado: obs=1262 (intacto)

O MCR perguntou "E se tem + vende?" e o motor respondeu: "sim,
isso é gerar_npc com 95.7% de confiança". Uma relação que nenhum
humano explicitamente ensinou — emergiu da estrutura do P(b|a).

### Estatisticas

| Metodo | Hipoteses | Confirmadas | Novas |
|--------|-----------|-------------|-------|
| Emergir (conhecido) | 30 | 0 (0%) | - |
| Emergir livre | 50 | 1 (2%) | 1 |

Emergir conhecido falhou: sempre pega o mesmo par (work+markov).
Precisa variar o ponto de partida (trabalho futuro).

Emergir livre funcionou: 1 descoberta nova em 50 hipoteses.
2% de taxa de descoberta. Sem random. Sem contaminar.

## Significado

O sonho NAO é classificador, NAO é triunvirato, NAO é gerador de
texto. O sonho é CURIOSIDADE. É o MCR perguntando "E se?" pra si
mesmo. Como Kheltz faz comigo: "decida, explore, valide."

O MCR agora pode:
1. Sonhar (criatividade, H maior que GPT-2)
2. Emergir (descobrir relações novas, "E se X + Y?")
3. Sem contaminar o motor (isolado)

A integrateção é por CONSULTA, nao por ALIMENTACAO direta.
O motor pergunta, o sonho responde, o motor valida.

## Regressoes

- Fase 1: 113/113 = 100%
- Fase 18: 64 PASS / 0 FAIL
