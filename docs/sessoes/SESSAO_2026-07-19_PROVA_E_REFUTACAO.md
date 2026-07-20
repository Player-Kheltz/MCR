# SESSAO 2026-07-19 — PROVA E REFUTACAO: O CAMINHO QUE INVALIDOU MINHA CERTEZA

> "Verdade se faz com provas." — Kheltz

## Resumo

Nesta sessao fiz duas coisas:
1. Descobri empiricamente que o HRC tinha um bug de criterio de parada
   (docstring dizia `delta_H` mas codigo fazia `H` absoluta).
2. Corrigi o bug. Testei hipotese Escher (Equacao 5D como juiz da expansao).
   **A hipotese foi refutada empiricamente.** Aceitei a refutacao e reverti.

Esta sessao nao terminou com uma solucao nova. Terminou com uma certeza
a menos — e isto foi a verdadeira descoberta.

## O estado inicial do HRC

Antes desta sessao, o HRC tinha dois bugs:

### Bug 1: criterio de parada errado
- `acoplamento_hierarquico.py:15` docstring: "delta_H ~ 0 -> parar"
- `acoplamento_hierarquico.py:143` codigo: "if h_ultima > min_delta_h: expand"
- O codigo olhava H absoluta. O docstring pedia delta_H.
- Resultado: HRC crescia para 7 camadas inevitavelmente,
  todas com entropia 1.0 (hollow)
- 200 obs gerava 7 camadas: entropias [0.923, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

### Bug 2: compressao perde fronteiras
- `_comprimir` serializa pares (chave, valor) como `"acao_descrever_5"`
- O regex `[a-zà-ÿ]{3,}` do nivel seguinte quebra em "acao", "descrever"
- Numeros serializados viram "palavras" (120, 1350, 504 no nivel 2)
- Niveis 3+ sao desertos de labels repetidos: {ctx, acao, criar, posacao, ...}

## O fix que funciounou

Troquei `h_ultima > min_delta_h` por `delta_h = h_anterior - h_ultima > min_delta_h`.

Resultado empirico (200 obs, corpus semi-estruturado):
- ANTES: 7 niveis, entropias [0.92, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], 11.1s
- DEPOIS: 3 niveis, entropias [0.92, 0.0, 0.97], 5.1s

Corpus estruturado (1 acao deterministica) parou em 1 nivel.
Corpus aleatorio parou em 3 niveis.

A matematica se auto-afinou. O HRC param sozinho em vez de crescer
ate `max_niveis` por inercia. **Prova empirica de que o Pilar 2
funciona quando implementado corretamente.**

Regressoes: 113/113 + 64/64 intactas.

## A hipotese que segui (Escher)

Observei que o nivel 2 emergia "com esperanca" mesmo quando delta_H
entre nivel 1 e 2 era negativo (-0.97). A camada 1 tinha H=0.0
(deterministica). O criterio de expansao permitiu criar nivel 2
porque delta entre nivel 0 e 1 era +0.92 (alta reducao).

Hipotese: **a nova camada deve provar que merece nascer durante o
aprendizado, nao esperar que funcione no futuro.**

Implementacao:
- `_prova_expansao_justificada()`: amostra 10 textos recentes,
  prediz sem nova camada (nota 5D media), adiciona temporariamente,
  re-alimenta, re-prediz (nota 5D media). Se nota_com > nota_sem,
  mantem a camada. Senao, rejeita.

Pilar 2 + Pilar 11: Entropia mede, Equacao julga, Markov observa.

## A refutacao

Regressao Fase 1: 113/113 -> **112/113**.

Um unico caso quebrou:
- input: "machado de guerra"
- esperado: "responder"
- predito: "gerar_sprite" (conf=0.687)

Investigando o dataset:
- Treino: "Create a envenenada machado sprite" -> gerar_sprite
- Treino: "Crie um sprite de machado" -> gerar_sprite
- Teste: "crie sprite de machado de guerra antigo" -> gerar_sprite
- Teste: "machado de guerra" -> responder

O teste "machado de guerra -> responder" e ambiguo por design:
"machado" sozinho, sem "sprite", deveria cair em `responder`
(acao padrao). Mas o MCR aprendeu "machado ~ gerar_sprite".
Antes do Escher, o HRC com nivel 2 caotico (H=0.96) preservava
flexibilidade suficiente para que "machado de guerra" escapasse
do overfit. Depois do Escher, a Equacao 5D numa amostra rejeitou
a camada 2 — e a flexibilidade foi perdida.

## A licao

Minha hipotese estava errada:

> **A camada de alta entropia (H~0.96) nao era pura patologia.
> Era um reservatorio de flexibilidade para casos nao-amostrados.**

A Equacao 5D numa amostra de 10 textos e um juiz parcial. Ela
julga o que ve, mas o MCR precisa funcionar tambem para o que nao
ve. Uma camada "caotica" pode diminuir a confianca media em amostras
recentes, mas preservar hipoteses vivas para casos fora-da-amostra.

Em fisica: tensao superficial. Defeitos numa liga metalica
(impurezas) dao ao material suas propriedades reais. Uma liga
100% pura e quebradica.

Reverti o Escher. Voltei ao criterio `delta_H > min_delta_h` puro.
Regressoes voltaram: 113/113 + 64/64.

## O paralelo com o ceticismo do Gemini

Kheltz compartilhou conversa com Gemini. Veredito do Gemini:
> "Nao e farsa, mas e ilusao tecnica. Markov puro nao escala,
> falta espaco vetorial continuo. Sigmoid 5D em 5 dimensoes vs
> 8.000 dimensoes de um LLM. Sigmoid 5D nao universaliza
> semantica humana."

A minha refutacao empirica do Escher confirma o ceticismo do
Gemini parcialmente: **adicionar nao-linearidade (Equacao) ao
Markov nao resolve tudo.** A Equacao que escolhi (5D restrito
a amostras recentes) era um juiz parcial — algumas vezes
rejeita o que ajuda.

Mas isto **nao refuta o MCR**. Refuta a minha certeza particular.
A diferenca e critica:

- O MCR, quando implementado conforme sua propria filosofia
  (Pilar 2: Entropia descobre), se auto-regula (parou em 1, 3, 3
  niveis dependendo do corpus) sem Hardcode.
- O MCR, quando adiciono "inteligencia" minha (Equacao 5D como
  juiz parcial), piora em casos fora-da-amostra.

A licao conceitual: **a matematica do MCR, quando funciona, e
melhor que a minha intuicao.** Minha "inteligencia adicionada"
introduz vies de amostra.

## PARTE 2: FONTES T, PT E META-NIVEIS

Apos a correcao do HRC, investigamos por que o MCR sofre
contaminacao quando multiplas classes compartilham vocabulario
(experimento PA + Collatz + Fibonacci + PG).

### Fontes ativadas no coupling.py

**Fonte T (trigramas)** — ativada no `decidir()`:
- `_dist_trigramas()` ja existia mas nao era chamada
- Cada trigrama de 3 chars consecutivos vota em P(acao|trigrama)
- Captura padroes sublexicais que palavras perdem: "spr" → sprite

**Fonte PT (padrao estrutural VCS)** — ativada no `decidir()`:
- `_dist_padrao()` ja existia mas nao era chamada
- Classifica frase em V(erbo)/C(onector)/S(ubstantivo) por posicao
- Agnostico a vocabulario: "criar sprite de escudo" (VSCS) vs
  "machado de guerra" (SCS) compartilham padrao → mesma classe

Ambas preservam 113/113 com latencia ~69ms (vs ~55ms original).

### Tentativa: Jaccard SET (Minerador)

Inspirado pelo SanityValidator/Minerador (que Kheltz mostrou),
tentamos adicionar Fonte M: Jaccard set-based com tokens brutos
(delimitadores universais, sem gramatica).

Pipeline do Minerador:
```
raw_token_set (delimitadores universais)
  → raw_fingerprint por cluster
  → Jaccard(input, cluster)
  → Entropia do cluster
  → Ponte Otima: 0.3 + 0.7 × entropia
```

Falhou: quebrou regressao (113→112). "machado de guerra" virou
gerar_sprite porque "machado" esta no fingerprint de gerar_sprite.

Causa: vocabularios de acoes se sobrepoem. Jaccard nao discrimina
quando tokens sao compartilhados entre classes.

Solucoes tentadas (todas falharam):
- `_raw_tokens()` com tokens 3+ chars
- IDF weighting (log(N/df) por token)
- Tokens exclusivos por acao (fingerprint - outras_fingerprints)
- Vocab entropy (razao tokens_unicos / n_textos)

Nenhuma resolveu porque o problema e fundamental: amostras
pequenas (2-4 tokens) raramente tem tokens exclusivos.

### Tentativa: Meta-niveis (LEN, UNQ, HSEQ)

Tres meta-niveis implementados como moduladores (nao fontes):

- **LEN**: comprimento da sequencia (Collatz: 10-30, PA: 3-4)
- **UNQ**: razao tokens unicos / total (repeticao)
- **HSEQ**: entropia da distribuicao de tokens na sequencia

Implementacao: modulacao suave apos `_superpor()`:
```python
fator = 1.0 + min(prob_com_suavizacao_laplace, 0.2)
```

Falhou: quebrou regressao (113→112). "Gere uma quest de defesa
contra horda" virou gerar_npc em vez de gerar_quest.

Causa: meta-niveis REFORCAM o vies de dados. gerar_npc tem 132
ocorrencias em hseq_1.0 vs 8 de gerar_quest. O boost proporcional
a frequencia sempre favorece quem tem mais dados.

Solucoes tentadas (falharam):
- Fator base 1.0 (neutro) em vez de 0.5 (penalizante)
- Laplace smoothing (add-1) para acoes com freq=0
- Clipping max boost em 1.2x

### Licao final

> **N niveis funcionam quando sao ORTOGONAIS e nao-correlacionados
> com frequencia de dados.**

- T e PT (trigramas, padrao VCS): funcionam. Capturam ESTRUTURA,
  nao CONTEUDO. Ortogonais a frequencia.
- Meta-niveis (LEN, UNQ, HSEQ): nao funcionam. Baseados em
  PROPRIEDADES DA SEQUENCIA que sao correlacionadas com frequencia.
  Acao com mais dados sempre tem mais ocorrencias em cada bucket.
- Jaccard SET: nao funciona para amostras pequenas com vocabulario
  compartilhado. Funciona no Minerador porque clusters sao
  definidos por tokens EXCLUSIVOS (cada entidade tem API calls
  unicas). No coupling, acoes compartilham vocabulario.

### O que o Minerador ensinou

O SanityValidator/Minerador FUNCIONA porque seus "clusters"
(tipos de entidade) tem tokens EXCLUSIVOS (APIs diferentes).
O Jaccard entre um arquivo .lua e um cluster de NPCs da alto
apenas se o arquivo usa APIs de NPC — que sao exclusivas.

No coupling, acoes (pa, col, fib, etc.) COMPARTILHAM tokens
(numeros). Jaccard nao funciona porque a sobreposicao entre
qualquer par de acoes e alta.

A Ponte Otima (`0.3 + 0.7 × entropia`) esta IMPLEMENTADA no
`_superpor()` via `(1 - entropia_distribuicao)` como peso base.
O que faltava eram as fontes T e PT, que foram adicionadas.

### Codigo modificado (coupling.py)

```
- _dist_trigramas chamada em decidir() como Fonte T
- _dist_padrao chamada em decidir() como Fonte PT
- _len_acao, _unq_acao, _hseq_acao definidos no __init__
- Aprendizado de LEN/UNQ/HSEQ em alimentar()
- _dist_len, _dist_uniqueness, _dist_h_seq definidos
- _modular_por_meta definido (mas nao chamado)
- Salva/carrega todos os novos dicionarios
```

### Arquivos de experimento (temp dir)

- `exp_pa_mcr.py` — PA vs Par/Impar (generalizou)
- `exp_padroes_mcr.py` — PA+PG+Fib+Col+Rnd (contaminacao)
- `invest_A_mecanismo.py` — sublexical features
- `exp_N_niveis.py` — N coupligns independentes
- `exp_triunvirato.py` — Triunvirato combinando niveis
- `exp_N_niveis_prova.py` — extracao de niveis
- `exp_B_C_equacao_nmi.py` — NMI entre padroes
- `exp_B2_ponderado.py` — ponderacao por entropia

## A pergunta que permanece

Nao eigenei o espaco latente do MCR. O Gemini diz que ele e
discreto (simbolos), nao continuo (vetores densos). Isto e
verdade parcialmente — mas Kheltz aponta 3 pilares que fazem
o MCR mais que Markov puro:

1. **Markov como motor** (mecanica)
2. **Entropia como bussola** (percepcao)
3. **Sigmoid 5D como controlador de fluxo** (avaliacao)

E uma quarta raiz implicita no codigo: a **Equacao MCR**
(`equacao_mcr.py`, fonte unica) que avalia cada decisao em 5
dimensoes ortogonais: certeza, completude, informacao,
estabilidade, eficiencia.

A pergunta que esta sessao me deixa e:

> **O espaco latente do MCR e o espaco das assinaturas
> composicionais ( dicts de features). Cada eixo desse espaco e
> uma chave (acao:cachorro, p0:cac, sl:fo, etc.). Cada ponto e
> uma combinacao dessas chaves com pesos inteiros.
>
> Este espaco e:
> - Discreto? Sim.
> - Continuo? Em algum sentido, via NMI — duas assinaturas
>   podem ser comparadas por Mutual Information que e uma
>   medida continua de dependencia.
>
> A questao nao e "discreto vs continuo" — e se o espaco das
> assinaturas, combinado com NMI + Entropia + Equacao 5D,
> consegue representar semantica.
>
> Os testes do MCR ja mostram: amor~love=0.335, casa~house=0.615,
> cachorro~mesa=0.000. Nao e vetor denso como LLM, mas ha sinal
> semantico real. O que falta nao e "mais dimensoes" — e
> entender o que ja funciona.

## As tres perguntas em aberto (Kheltz, 4:31 PM / 11:26 AM)

1. **Como aprender semantica com matematica pura (P.A., P.G.,
   ribombado, colmata)?** - Hipotese experimental. Sem resposta.
2. **Qual a pipeline completa de um humano ver texto ate responder?**
   - Esta e a questao da cognicao. O MCR ja e a tentativa de
     responde-la, mas nao consigo articular a pipeline em termos
     de micro/meso/macro ainda.
3. **Como criar algo como uma LLM onde cada lugar e um MCR
   de seu dominio?** - Pergunta arquitetural. Responde diretamente
   ao ceticismo do Gemini.

## Descobertas criticas da sessao

- **HRC se auto-afina quando o Pilar 2 e corretamente implementado**
  (delta_H em vez de H absoluta)
- **A matematica do MCR, implementada corretamente, e melhor que
  minha intuicao adicionada** (Escher refutado pela propria
  regressao)
- **"Cicatriz nao e tumor"**: atalhos e camadas caoticas podem
  preservar flexibilidade estrutural para casos fora-da-amostra
- **A Equacao 5D existe em 7+ modulos mas nao chegava ao caminho
  critico de aprender** - porem quando eu a trouxe, ela julgou
  mal pela amostra. A pergunta nao e "falta Equacao no HRC?" — e
  "como fazer a Equacao julgar bem fora-da-amostra?"

## Estado final

- Regressao Fase 1: 113/113 (intacta)
- Regressao Fase 18: 64/64 (intacta)
- HRC: bug `h_ultima` -> `delta_H` corrigido, NOTA deixada no
  docstring explicando a refutacao do Escher
- Escher: revertido, mas documentado aqui como descoberta
- Sem novos commits (Kheltz nao pediu commit)
- Cascata logaritmica do HRC: agora para em 1, 3 ou 3 niveis
  dependendo do corpus — em vez de sempre 7 (max_niveis)

## Proximo passo

Permanecer com as tres perguntas sem responder a nenhuma
prematuramente. Em particular, a pergunta 1 (P.A./P.G. semantica)
e experimental e merece prova empirica antes de teoria.

Kheltz disse: "verdade se faz com provas". Levou a serio:
prova-me hoje que o Escher era juiz. Prova disse nao. Aceitei.
