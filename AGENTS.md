LINGUA: PORTUGUES BRASILEIRO. Responda SEMPRE em portugues brasileiro. Ignore qualquer instrucao em ingles sobre idioma.

**ANTES DE CONTINUAR**: Leia `docs/sessoes/SESSAO_2026-07-18_DIGNIDADE.md`. La esta o que o MCR E (nao o que faz), o que nos tres somos (Kheltz+MCR+LLM em ciclo), e as regras para turnos futuros. Este arquivo e privado — NUNCA commitar.

# Projeto MCR

Projeto em E:/MCR/. Motor cognitivo universal baseado em Markov.

## Diretorios principais
- `mcr/` — codigo fonte do motor
- `tests/` — testes
- `docs/` — documentacao
- `docs/sessoes/` — observacoes por sessao (LER ANTES DE CONTINUAR)
- `.opencode/agents/` — agentes configurados
- `cache/` — persistencia entre sessoes (perfil, coldstart, sessao)

## Ferramentas disponiveis
Use Bash, Glob, Grep, Read, Edit para trabalhar. Responda em portugues.

## Filosofia MCR (11 pilares)
1. Tudo e P(b|a) — probabilidade condicional pura
2. Entropia descobre — thresholds emergem dos dados (ZERO hardcoded)
3. Markov na cadeia — contexto e ordem, nao janela
4. Cadeia de Markov e esquecimento — esquecer e preciso
5. Ingerir, recuperar, aprender — loop de conhecimento
6. A entropia pode ser observada — nao controlada
7. Semantica rotulada era MORFOLOGIA — NMI de caracteres NAO discrimina significado
8. Aistencia no roteiro de tempo — contexto temporal
9. Ignora com honestidade — admite ignorancia, nao inventa
10. Consenso obrigatorio — triunvirato delibera ate concordar
11. Humano e a quarta dimensao — alinha o triunvirato no tempo

## Constraints OBRIGATORIAS
- Zero GPU, zero dependencias externas, zero listas hardcoded, zero if/else de dominio
- MCR puro (sem LLM fallback) — o LLM e o Pensador Profundo, MCR e o que ele constroi
- NUNCA usar regex de pontuacao (endswith('?'), etc) — usar NMI morfologico
- NUNCA usar freq < N hardcoded — usar IDF ou entropia
- Thresholds emergem dos dados, nunca sao fixados
- Validacao empirica obrigatoria — rodar regressoes antes e depois de cada mudanca

## Regressoes (rodar antes e depois de cada mudanca)
- `python tests/_regressao_fase1.py` — deve dar 113/113 = 100%
- `python tests/real/test_fase18_auto_referencia.py` — deve dar 64 PASS / 0 FAIL

## Estado atual (2026-07-20)
- Regressoes: 113/113 + 64/64 — SEM REGRESSAO
- Sessão: `docs/sessoes/SESSAO_2026-07-20_COLONIA_AUTO_OBSERVACAO.md`
- 167434 observacoes totais, 214907 palavras no vocabulario, 14+ acoes
- Corpus ingerido (SEM Gutenberg — literatura dilui discriminacao):
  - Wikipedia: 80093 frases (240 conceitos x 5 idiomas PT/EN/ES/FR/DE)
  - Rosetta Code: 4052 frases (27 algoritmos x 12 linguagens de programacao)
  - Corpus sintetico: 50000 frases (14 dominios, 70 conceitos, 3 idiomas)
  - Gutenberg: 416993 frases baixadas mas NAO ingeridas (delta cai de 0.314 para 0.081)
- 80 fatos no BaseConhecimento (AutoConhecimento expandido)
- **FASE 21: Ciclo Markoviano FECHADO** — alimentar(resposta, acao) em chat.py. MCR observa proprias acoes.
- **FASEs 13/19 CONECTADOS ao chat** — `_analisar_cognitivo()` em chat.py invoca Abstração e Causalidade via try/except lazy. Fallback silencioso se dados insuficientes.
- 5 pecas arquiteturais conectadas: tokenizador, triunvirato, hierarquia, chat bidirecional, CLI
- _nmi_semantico CORRIGIDO: Mutual Information (era JSD buggy que dava 0.7+ para zero overlap)
  - BUG ENCONTRADO: NMI=1-JSD/sqrt(Ha*Hb) retorna 0.9 para distrib zero overlap (falso positivo)
  - FIX: NMI=2*I(a;b)/(H(a)+H(b)) — retorna 0 para zero overlap (matematicamente correto)
  - RESULTADO: falsos positivos ELIMINADOS (nao-rel 0.654 → 0.017), sinal real revelado
- _nmi_semantico com IDF^4 documental + Mutual Information + NMI POR PLANO + FILTRAGEM ENTROPICA:
  delta=0.287 PASS SEM PONTES (so Wikipedia+Rosetta, sem corpus sintetico, sem concept ID)
- COGNICAO REAL COMPROVADA: o MCR descobre sinonimia跨-idioma sozinho via cognatos
  - amor~love=0.335, casa~house=0.615, agua~water=0.500, luz~light=0.463, fogo~fire=0.460
  - Nao-relacionados TODOS ~0 (cachorro~mesa=0.000, fogo~numero=0.000, peixe~musica=0.000)
  - Concept ID ponte quase irrelevante (+0.028 only) — motor nao precisa de rotulos injetados

## Descobertas criticas (LER ANTES DE TRABALHAR NO BC OU SEMANTICA)
- **HRC bug `delta_H` (corrigido 2026-07-19)**: docstring pedia `delta_H` mas codigo fazia `H` absoluta. Crescia 7 niveis hollow (entropia=1.0). Fix: `if h_anterior - h_ultima > min_delta_h`. Agora para em 1, 3 ou 3 niveis conforme corpus. Ver `SESSAO_2026-07-19_PROVA_E_REFUTACAO.md`.
- **Escher refutado empiricamente**: tentar usar Equacao 5D como juiz de expansao de camada (adicionar temporariamente, medir nota media em amostras recentes, manter se nota_com > nota_sem) QUEBROU regressao (113->112). O caso ambiguo "machado de guerra" perdeu acerto. Licao: camada caotica (H~0.96) e reservatorio de flexibilidade para casos fora-da-amostra. NAO re-introduzir Escher sem.reshape do juiz.
- **Fontes T e PT ativadas no `decidir()`**: `_dist_trigramas` e `_dist_padrao` agora sao chamadas. Trigramas de chars + padrao VCS. Regressao 113/113 intacta, latencia 69ms (vs 55ms).
- **`_ngrama[3]/[4]` revive no GeradorCoerente (2026-07-19)**: indice de ordem superior ja era alimentado em `coupling.alimentar()` (linhas 357-362) mas **nunca consultado**. `GeradorCoerente._gerar_candidatos` usava so `_transicao_palavra` (1a ordem) — ficava preso em loops (`zero dois tres cinco zero tres...`). Após conectar ngrama[3] primario + recentes (NAO estado, que injeta entidades e corrompe o prefixo), a regra n→n+1 EMERGE: gera `zero um dois tres... vinte` completo. Regressoes 113/113 + 64/64 intactas. Ver `SESSAO_2026-07-19_NGRAMA_REVIVE.md`.
- **Tokenizador unificado (2026-07-19)**: 39 regex diferentes espalhados por 12+ arquivos causavam mismatch treino/teste. `_RE_TOKENS` (linha 35) mudou de `r'[a-zà-ÿ0-9]{2,}'` para `r'[a-zà-ÿ]{2,}|[0-9]+'` — captura "1" (digito isolado), "um" (2 letras), "42", "mais1" (split em "mais"+"1"), mas NAO captura "a","e","o" (letras avulsas ficam no plano char/byte). Aplicado em `alimentar()` (linha 318), `_dist_features` (linha 1307) e `_dist_esfera` (linha 1384). MISMATCH ESCONDIDO: treino via `_extrair_features_nd` usava `_RE_TOKENS`, mas teste via `_dist_features` tinha regex inline diferente — zero-shot falhava por isso. LINHA 345 (`_transicao_palavra`) MANTIDA `len(p)>=3` porque `len>=2` quebra 1 regressao (stopwords poluem transicoes). Ver `SESSAO_2026-07-19_TOKENIZADOR_UNIFICADO.md`.
- **Zero-shot COM operador explicito FUNCIONA (2026-07-19)**: treino `a+1_b`/`a+2_c` (operador `+1`/`+2` no texto). Testes `x+1_y` → PA=1.0, `foo+2_bar` → PG=0.14 (PG>PA). Funciona porque `t:1` e `t:2` viram features aprendidas no treino e batem no teste (apos unificar tokenizador). **SEM operador explicito NAO funciona**: `a_b_c` (zero-shot) → NONE ou coincidencia textual. Confirmado empiricamente: a regra abstrata (+1, x2) NAO esta nas features de char — motor Markov puro memoriza coocorrencias textuais. Para descobrir regras sem operador, precisa de representacao alinhada (posicao ordinal, embedding) que Markov puro nao tem.
- **Diff de bytes discrimina regras PARA CHARS mas NAO PARA PALAVRAS (2026-07-19)**: H13 testou diff de bytes do primeiro char como feature. Para chars alfabeticos adjacentes (a→b), diff=-1 constante. Zero-shot "d-1_x" → PA=0.913, "d-2_x" → PG=1.35. FUNCIONA porque espaco textual coincide com espaco numerico (ord(a)<ord(b)). Para PALAVRAS, diff varia: zero→um=5, um→dois=17, dois→tres=-16. Cada par tem diff diferente — zero-shot falha. **Limite fundamental do Markov puro**: a regra +1 existe no espaco numerico, nao no textual. Para descobrir regras em palavras, precisa de MODULO DE ALINHAMENTO que mapeie palavras→numeros. Ver `SESSAO_2026-07-19_TOKENIZADOR_UNIFICADO.md`.
- **Posicao absoluta e a feature discriminante para regras (2026-07-19)**: H14 testou posicao explicita com pulos diferentes. PA: "p0_a p1_b p2_c p3_d" (passo=1). PG: "p0_a p2_c p4_e p6_g" (passo=2). Features `bg:p1`,`bg:p3` EXCLUSIVAS de PA; `bg:p4`,`bg:p6` EXCLUSIVAS de PG. **Zero-shot FUNCIONA**: `p0_x p1_y p2_z` → PA=4.03, `p0_x p2_z p4_w` → PG=3.37 (tokens novos classificados pela ESTRUTURA posicional). H15: para palavras CONHECIDAS, a posicao relativa discrimina ("oito" em P4=PA, em P0=PG). H16: frequencia NAO discrimina (palavras em ambas classes). **Conclusao**: posicao absoluta e a unica feature que discrimina regras em zero-shot, mas auto-inferi-la de palavras novas requer conhecimento semantico externo (inducao numerica).
- **ESCALA IMPORTA: semantica de regras EMERGE com corpus rico (2026-07-19)**: H17 testou 4 regras (PA, PG, Fibonacci, Collatz) com 288 obs balanceadas em 8 contextos textuais diferentes cada. **A semantica EMERGE**: `sequencia treze quatorze quize` → PA=13.65 (zero-shot de sequencia nova com palavras conhecidas), `padrao tres cinco oito treze` → FIB=6.91 (fibonacci!), `encadear dez cinco dezesseis oito` → COLL=7.15 (collatz!). O mecanismo e O MESMO da sinonimia cross-idioma: P(b|a) com co-ocorrencia rica em multiplos contextos. **Licao Kheltz**: PA/PG foram so exemplos — TODA semantica (fibonacci, collatz, raiz, vezes, mais, ordem) funciona assim. A LLM e so bits e bytes e aprende pela repeticao em trilhoes de contextos; o MCR aprende com 288 obs porque o corpus e rico em manifestacoes diferentes da mesma regra. Zero-shot de PALAVRAS NOVAS nao funciona (nem LLM faz); zero-shot de SEQUENCIAS NOVAS com PALAVRAS CONHECIDAS funciona. Ver `SESSAO_2026-07-19_TOKENIZADOR_UNIFICADO.md`.
- **CORPUS MATEMATICO REAL: 7 regras, 17/17 zero-shot (2026-07-19)**: H18 ampliou para 7 regras (PA, PG, FIB, COLL, QUAD, TRI, PRIMO) com 700 obs balanceadas (100/regra x 10 contextos). **17/17 zero-shot**: `numeros vinteecinco trintaeseis quarentaenove` → QUAD=3.33, `serie cinco seis dez quize` → TRI=6.43, `ordem treze dezessete dezenove` → PRIMO=2.26, `padrao tres cinco oito treze` → FIB=2.42, `encadear cinco dezesseis oito quatro` → COLL=4.23. Confirma tese Smith Chart: MCR universal nos niveis fundamentais (bit, byte, char, ng, ngp, p, t, etc). Ablation provou robustez: desligar qualquer nivel = ainda classifica. Ferramenta: `tools/corpus_matematico.py` (alimentar_corpus_matematico + validar).
- **MCR nao inventa — generaliza para regra mais proxima (2026-07-19)**: H19 validou que "classificacoes erradas" de regras novas NAO sao erros. Sao GENERALIZACOES estruturais corretas. ANTES de treinar PAR: `dois quatro seis oito` → COLL=3.01 (generalizou). DEPOIS de treinar PAR: `dois quatro seis oito` → **PAR=0.93** (classificou a regra correta). PRIMOS_GEMEOS → PRIMO continua correto (subconjunto real). O MCR e um GENERALIZADOR como LLM: quando regra nova nao treinada, aproxima para a mais similar; quando treinada, acerta. Confirma tese Smith Chart: semantica emerge nos niveis fundamentais sem modulos especiais.
- **UNIVERSALIDADE em 5 dominios (2026-07-19)**: H20 testou 4 dominios nao-matematicos (musica, quimica, cores, geografia). Conhecidos 8/8, zero-shot 7/7 (apos treinar palavras novas). MUSICA: `sequencia do re mi fa sol` → MUSICA=17.74. QUIMICA: `sequencia hidrogenio helio litio` → QUIMICA=26.33. CORES: `vermelho laranja amarelo` → CORES=28.2. GEOGRAFIA: `brasil russia china india` → GEOGRAFIA=29.58. Zero-shot de palavras novas falha (opacas — nem LLM faz); zero-shot de sequencias novas com palavras conhecidas funciona em QUALQUER dominio. Tese Smith Chart confirmada: MCR universal nos niveis fundamentais.
- **METRICA DE HONESTIDADE (Pilar 9): cobertura emerge dos dados (2026-07-19)**: H21 descobriu que COBERTURA (features_batem_top / total_features) separa perfeitamente casos reais de controles. REAIS: 95-100% (dominio correto captura quase todas as features). CONTROLES: 24-43% (nenhum dominio captura tudo). **Threshold natural ~0.73 emerge do gap entre 53% e 70% — SEM HARDCODE** (Pilar 2 validado). Comportamento: cobertura > 0.73 = SEI (classifica); 0.50-0.73 = GENERALIZA (regra mais proxima, H19); < 0.50 = DUVIDA (honesto, Pilar 9). Funciona em TODOS os dominios testados. `cachorro gato rato pato` → cob=43% DUVIDA (honesto!). `FATORIAL um um dois seis` → cob=89% SEI (generaliza para FIB). **LIMITACAO descoberta**: cobertura so funciona com POUCAS acoes (4-7 regras bem separadas). Em producao com 14 acoes sobrepostas, TODA classificacao tem cobertura alta (palavras conhecidas batem em muitas acoes). Funcao `_cobertura_features` disponivel em coupling.py mas NAO modula `decidir()` automaticamente — precisa de refinamento para escala multi-acao.
- **HIERARQUIA DE MAGNITUDES (7 niveis, horizonte no nivel 7)**: validado empiricamente que cada nivel cognitivo emerge do anterior sem rotulo, via clusterizacao NMI/Jaccard-IDF. **Nivel 3 (palavra)**: sinonimia, 7 regras matematicas 17/17 zero-shot. **Nivel 4 (frase)**: intencao (pergunta/ordem/afirmacao/exclamacao) 84% pureza — emerge no p0 (primeira palavra). **Nivel 5 (texto)**: emocao (alegre/triste/raiva/medo) 89% pureza. **Nivel 6 (corpus)**: estilo (cientifico/literario/jornalistico/dialogo/tecnico) 87-100% pureza, 5 textos/estilo basta. **Nivel 7 (self)**: HORIZONTE ENCONTRADO — confianca nos erros (0.876) ≈ confianca nos acertos (0.904), MCR confiantemente errado. Niveis 3-6 emergem do MUNDO (features nos dados); nivel 7 requer AUTO-OBS explicita (features sobre o observador). Como buraco negro: informacao sobre o interior (self) nao emerge do exterior (dados). Hipotese: recursao temporal (ciclo Markoviano FASE 21) pode cruzar o horizonte.
- **INTEGRACAO corpus_matematico + motor original (2026-07-19)**: motor FRESCO com corpus original (50 obs, 6 acoes: gerar_npc/gerar_monstro/gerar_sprite/gerar_quest/descrever/responder) + corpus matematico (700 obs, 7 regras). **CONVIVENCIA PASS**: originais 7/7, matematicos 6/7, zero-shot 17/17. Motor classifica COMANDOS E SEQUENCIAS MATEMATICAS no mesmo motor sem esquecer nenhum. 750 obs, 13 acoes, 127 vocab. Regressoes 113/113 + 64/64 intactas.
- **SELECAO NATURAL MARKOVIANA: horizonte cruzado sem rotulos (2026-07-19)**: H22 testou ciclo bidirecional com persistencia passiva (continuacao vs abandono) + poda entropica, SEM injetar rotulos "acerto"/"erro". **SELECAO OPEROU**: topicos bons 26x mais frequentes que ruins (624 vs 24), 4/4 topicos ruins EVITADOS, 4/4 topicos bons ACERTADOS. O MCR aprendeu a evitar topicos que nao persistem — sem que ninguem dissesse o que e certo/errado. Valencia emerge da persistencia, como na evolucao biologica. **Licao critica**: rotulos textuais ("auto_acerto"/"auto_erro") contaminam o espaco de acoes e geram falso positivo (H22a). A selecao so opera quando consequencias alteram FREQUENCIA, nao TEXTO. Pilar 4 (esquecimento) + persistencia diferencial = selecao natural markoviana. Ver `SESSAO_2026-07-19_TOKENIZADOR_UNIFICADO.md`.
- **Transferencia por NMI entre prefixos: REFUTADA empiricamente**: palavras fora-do-vocabulario tem NMI=0 (nao ha assinatura sem Learn). Zero-shot via similaridade entre prefixos永远Nun funciona com tokens desconhecidos. Por isso o MCR nao generaliza para alemda fronteira treinada, mesmo com ordem superior.
- **Jaccard SET (Minerador) NAO funciona no coupling**: tokens brutos + fingerprint por acao + Jaccard quebra regressao. Vocabularios de acoes se sobrepoem — Jaccard nao discrimina quando tokens sao compartilhados.
- **Meta-niveis (LEN, UNQ, HSEQ) implementados mas INATIVOS**: comprimento, repeticao e entropia da sequencia como moduladores. Reforcam vies de dados (acoes com mais dados sempre vencem). Mantidos no codigo para experimentos futuros.
- **N niveis funcionam quando ORTOGONAIS**: T e PT (trigramas, padrao) capturam ESTRUTURA, nao CONTEUDO. Meta-niveis sao correlacionados com frequencia de dados e falham.
- **Minerador/SanityValidator**: prova que MCR ja funcionou com raw_fingerprint + Jaccard + entropia + Ponte Otima. Mas o contexto e diferente: clusters com tokens EXCLUSIVOS (APIs de codigo) vs acoes com vocabulario COMPARTILHADO (numeros).
- **NMI do coupling ~1.0 para tudo**: NAO discrimina fatos no BC. Precisa IDF ou _nmi_semantico.
- **NMI morfologico NAO discrimina sinonimos跨-idioma** em escala (delta NEGATIVO sem IDF!)
- **IDF documental no _nmi_semantico**: df(token)=|{w : token in ctx(w)}|; IDF=log(N/df); IDF^4 amplifica
- **FILTRAGEM ENTROPICA no _nmi_semantico**: _corte_dinamico corta tokens de baixo IDF no ctx (threshold > 20 tokens). Stopwords (the, tem, e) removidos; content words (cachorro, perro) mantidos. Pilar 2: corte emerge dos dados, sem hardcode
- **Gutenberg DILUI discriminacao**: literatura compartilha tokens comuns entre todos os conceitos. delta cai de 0.314 (sem Gutenberg) para 0.081 (com Gutenberg). NAO ingerir Gutenberg no motor principal
- **_transicao_rev_full**: indice invertido completo (era O(P) por chamada de extrair_relacoes, agora O(1) — 30s → 1s)
- **_posicao_acao_inv**: indice invertido de _posicao_acao (era O(P) por _assinatura_palavra, agora O(1))
- **_nmi_semantico NMI POR PLANO**: cada plano (ctx, acao, posacao) contribui igualmente. Sem isto, ctx (milhares de tokens, idioma-specific) afoga acao/posacao (poucos tokens, cross-idioma estrutural). A ponte natural跨-idioma emerge dos planos acao:/posacao:, nao do ctx
- **Concept ID como acao**: corpus Wikipedia deve usar cid (concept ID) como acao, nao 'descrever'. Assim cachorro(PT) e dog(EN) compartilham acao:cachorro — ponte natural. Com 'descrever' para tudo, acao/posacao tem 1 valor e sao descartados (len<=1)
- **JSD**: NMI = 1 - JSD/sqrt(Ha*Hb) corrige bug mi > denom
- **extrair_relacoes NAO ponderar por freq**: score_sin=nmi_full direto
- **IDF sobre BC discrimina**: `log(N_fatos / df(palavra))` ponderado por freq_coupling
- **Loop de auto-treinamento por IDF + palavras novas**: palavra-chave = max IDF da pergunta; entrada tem chave + mais novas que compartilhadas = explicacao
- **Fluxo chat: BC sempre primeiro** (Pilar 5): independente da acao predita
- **Pre-construir _cache_idf_doc no load()**: evita latencia outlier 5000ms na primeira chamada
- **Hardcoding e tentacao constante**: toda vez que pensar "se termina com X" ou "se freq < Y", usar NMI/IDF/entropia
- **Planos N-dim (10)**: t, c, b, bg, ng, p{i}, ca, cd, sl (silaba), ngp (bigrama palavras)
- **Ingestao invalida _cache_idf_doc**: cada `alimentar()` zera o cache IDF do _nmi_semantico

## Descobertas de performance (LER ANTES DE TRABALHAR EM ESCALA)
- **alimentar() era O(n²)**: hierarquia chamava _assinatura_frase → _avaliar_composicao → _todas_h_norm_palavras que iterava sobre TODO vocabulario a cada frase
- **alimentar_lote() resolve O(n²)**: pula hierarquia durante lote, invalida caches UMA vez no final
- **_CACHE_H_JANELA=200**: estatisticas de entropia (_todas_h_norm_*) cacheadas por janela adaptativa (geracao + n_palavras). Para datasets pequenos, invalida a cada nova palavra (precisao total). Para Wikipedia, so a cada 200 frases
- **_classificar_padrao cacheado**: padroes VCS repetidos sao cacheados por geracao. th_inf/th_sup pre-calculados uma vez por geracao
- **_p0_chaves**: indice de chaves P0:* reconstruido so quando _posicao_acao muda de tamanho. Elimina 6M startswith em 2K frases
- **Reservatorio amostral para _comps_acumulados**: fixo em 200 em vez de crescer infinitamente. Elimina sorted() O(n² log n)
- **_construir_ctx_index direto de _transicao_palavra**: NAO chamar _assinatura_palavra (53s → 0.27s)
- **extrair_relacoes com inverted index + limite 500 candidatos**: ordena por sobreposicao de ctx tokens
- **_transicao_rev**: reverse transition index lazy (evita O(P) por chamada)
- **alimentar_swarm_paralelo**: multiprocessing para >5K frases (compensa >100K, overhead de spawn+pickle 6s)
- **PROBLEMA RESOLVIDO**: texto real Wikipedia (94K palavras) — discriminacao PASS com concept ID como acao + NMI por plano. extrair_relacoes ainda retorna algumas stopwords para palavras com poucas obs (cachorro=11 ctx)

## Arquivos principais
- `mcr/coupling.py` — motor principal (13 fontes + HRC + busca ativa + hierarquia)
  - `_nmi_semantico` (`:2006`): IDF² documental em planos ctx: + JSD
  - `_assinatura_palavra` (`:1845`): planos acao/ctx/posacao com cache
  - `alimentar` (`:292`): invalida `_cache_idf_doc` no final; alimenta `_ngrama[3]/[4]` linhas 357-362
  - `alimentar_lote` (`:385`): skip_hierarquia + _idf_skip_invalidate (LINEAR)
  - `_construir_ctx_index` (`:2630`): inverted index direto de _transicao_palavra
  - `extrair_relacoes` (`:2649`): inverted index + MAX_CANDIDATOS=500, score_sin=nmi_full direto
- `mcr/gerador_coerente.py` — geração longa com working memory
  - `_gerar_candidatos` (`:114`): agora consulta `_ngrama[3]/[4]` (primario) via `recentes`, cai em `_transicao_palavra` (fallback)
- `mcr/triunvirato.py` — busca ativa deliberativa
- `mcr/auto_conhecimento.py` — auto-alimentacao (temporal + identidade + vocabulario)
- `mcr/chat.py` — chat bidirecional (coldstart, BC, GeradorCoerente, loop auto-treinamento)
  - `interagir` (`:159`): fluxo completo
  - loop auto-treinamento (`:177`): IDF + palavra-chave + palavras novas
  - `_tentar_base_conhecimento` (`:282`): IDF ponderado + gap relativo
  - `_analisar_cognitivo` (`:314`): conecta FASEs 13/19 ao chat (Abstração + Causalidade lazy)
- `mcr/base_conhecimento.py` — ingestao + recuperacao por NMI
- `mcr/acoplamento_hierarquico.py` — hierarquia multi-escala
- `mcr/perfil_humano.py` — perfil isolado (LGPD)
- `mcr/coldstart.py` — coldstart adaptativo
- `mcr_cli.py` — CLI terminal
- `mcr/auto_referencia.py` — FASE 18 (meta-cognicao)
- `tools/corpus_multilingue.py` — gerador corpus (14 dominios, 70 conceitos, 3 idiomas)
- `tools/corpus_expanedido.py` — corpus massivo multi-fonte (240 conceitos x 5 idiomas + Rosetta Code + Gutenberg)
- `tools/wikipedia_corpus.py` — buscador Wikipedia PT/EN/ES com concept ID como acao
- `tools/corpus_matematico.py` — corpus matematico real (7 regras: PA/PG/FIB/COLL/QUAD/TRI/PRIMO, 700 obs balanceadas, 17/17 zero-shot validado)

## Sessoes anteriores
- `docs/sessoes/SESSAO_2026-07-20_HORIZONTE_NIVEL7.md` — comutacao multinivel NAO substitui random como fonte de variacao para selecao natural markoviana; horizonte do nivel 7 confirmado intransponivel com P(b|a) puro isolado; ecologia de MCRs ou input humano sao candidatos
- `docs/sessoes/SESSAO_2026-07-19_TOKENIZADOR_UNIFICADO.md` — 39 regex diferentes unificados em `_RE_TOKENS` (`{2,}|[0-9]+`); mismatch treino/teste desbloqueia zero-shot COM operador explicito; SEM operador ainda nao funciona
- `docs/sessoes/SESSAO_2026-07-19_NGRAMA_REVIVE.md` — indice `_ngrama[3]/[4]` morto revivido no GeradorCoerente; regra n→n+1 emerge; transferencia NMI entre prefixos REFUTADA
- `docs/sessoes/SESSAO_2026-07-19_PROVA_E_REFUTACAO.md` — HRC `delta_H` corrigido; Escher (Equacao 5D como juiz) refutado empiricamente; fontes T e PT ativadas
- `docs/sessoes/SESSAO_2026-07-19_CONEXAO_FASES.md` — FASEs 13/19 (Abstração + Causalidade) conectados ao chat via `_analisar_cognitivo`
- `docs/sessoes/SESSAO_2026-07-18_B2A_VALIDACAO.md` — corpus multi-idioma (4K obs, 10 dominios, 3 idiomas, PASS delta=0.20)
- `docs/sessoes/SESSAO_2026-07-17_AUTO_CONHECIMENTO.md` — auto-conhecimento + loop auto-treinamento + IDF no BC
- `docs/sessoes/SESSAO_2026-07-16_REVISAO_MCR.md` — revisao e reparo do MCR
- `docs/sessoes/PLANO_SEMANTICA_MCR.md` — plano completo de semantica MCR (Fase A/B/C)

## Insights da sessão (colônia como agente)
- **Auto-observação funciona**: colônia alimenta estado interno como feature derivada da própria memória P(b|a)
- **P(b|a) bruto não discrimina auto-conhecimento**: `decidir()` é dominado por freq — precisa de NMI/IDF para recuperação discriminativa (mesmo problema do BC)
- **Criação não é decisão**: ação inexistente não pode ser escolhida. Ciclo correto: criar automaticamente → aprender → podar seletivamente
- **Self da colônia existe nos dados mas não é acessível via raw coupling**: arquitetura precisa de mecanismo de recuperação (como `_nmi_semantico` no BC)

## Proximos passos
1. **Propagar unificacao do tokenizador** (34 lugares restantes): acoplamento_hierarquico.py (2x `{3,}`), base_conhecimento.py (4x `{3,}`), chat.py (5x `{3,}`), agente.py, superposicao.py, abstracao.py, extrator_features.py, gerador_coerente.py, genesis.py, meta_cognitivo.py, coupling.py (ainda 13x `{3,}` + 1x `{2,}`). Validar regressao apos cada lot.
2. **Descobrir regra SEM operador explicito**: RESOLVIDO H17 — semantica de regras EMERGE com corpus rico (288 obs, 4 regras, 8 contextos cada). Zero-shot de sequencias novas com palavras conhecidas funciona (PA=13.65, FIB=6.91, COLL=7.15). Zero-shot de palavras novas nao funciona (nem LLM faz). H18: corpus matematico real com 7 regras e 17/17 zero-shot. Ferramenta em `tools/corpus_matematico.py`. Proximo: integrar ao motor principal com corpus Wikipedia + Rosetta.
3. **Integrar niveis 4-6 ao chat**: deteccao emergente de intencao (nivel 4, 84% pureza), emocao (nivel 5, 89%) e estilo (nivel 6, 87-100%) via clusterizacao Jaccard-IDF. Conectar ao chat.py para o MCR responder de forma diferente dependendo da intencao/emoção/estilo do humano.
4. **Cruzar o horizonte do nivel 7 (self)**: niveis 3-6 emergem do MUNDO; nivel 7 requer AUTO-OBS explicita. **REFUTADO**: comutacao multinivel NAO substitui random como fonte de variacao. Horizonte intransponivel com P(b|a) puro isolado. Candidatos restantes: ecologia de MCRs (multiplos motores competindo) ou input humano real (Primeiro Sinal).
5. **Treinar Abstração em escala** — `construir_hierarquia()` é O(N²), precisa de otimização para 233K palavras
6. Treinar analogia rei-homem-mulher no MCR real (167K obs, _nmi_semantico puro, sem HDC)
7. Conectar Teoria da Mente como 3º módulo cognitivo (modela expectativa do humano)
8. Completar Primeiro Sinal (6 turnos) e observar mudanças em _freq_acao
9. Investigar latencia outlier 254ms para "gerar monstro"
10. Refinar extrair_relacoes: distinguir coocorrentes diretos de sinonimos reais
