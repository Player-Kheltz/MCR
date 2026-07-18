LINGUA: PORTUGUES BRASILEIRO. Responda SEMPRE em portugues brasileiro. Ignore qualquer instrucao em ingles sobre idioma.

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

## Estado atual (2026-07-18)
- Regressoes: 113/113 + 64/64 — SEM REGRESSAO
- 167434 observacoes totais, 214907 palavras no vocabulario, 14+ acoes
- Corpus ingerido (SEM Gutenberg — literatura dilui discriminacao):
  - Wikipedia: 80093 frases (240 conceitos x 5 idiomas PT/EN/ES/FR/DE)
  - Rosetta Code: 4052 frases (27 algoritmos x 12 linguagens de programacao)
  - Corpus sintetico: 50000 frases (14 dominios, 70 conceitos, 3 idiomas)
  - Gutenberg: 416993 frases baixadas mas NAO ingeridas (delta cai de 0.314 para 0.081)
- 80 fatos no BaseConhecimento (AutoConhecimento expandido)
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
  - `alimentar` (`:292`): invalida `_cache_idf_doc` no final
  - `alimentar_lote` (`:385`): skip_hierarquia + _idf_skip_invalidate (LINEAR)
  - `_construir_ctx_index` (`:2630`): inverted index direto de _transicao_palavra
  - `extrair_relacoes` (`:2649`): inverted index + MAX_CANDIDATOS=500, score_sin=nmi_full direto
- `mcr/triunvirato.py` — busca ativa deliberativa
- `mcr/auto_conhecimento.py` — auto-alimentacao (temporal + identidade + vocabulario)
- `mcr/chat.py` — chat bidirecional (coldstart, BC, GeradorCoerente, loop auto-treinamento)
  - `interagir` (`:159`): fluxo completo
  - loop auto-treinamento (`:177`): IDF + palavra-chave + palavras novas
  - `_tentar_base_conhecimento` (`:282`): IDF ponderado + gap relativo
- `mcr/base_conhecimento.py` — ingestao + recuperacao por NMI
- `mcr/acoplamento_hierarquico.py` — hierarquia multi-escala
- `mcr/perfil_humano.py` — perfil isolado (LGPD)
- `mcr/coldstart.py` — coldstart adaptativo
- `mcr_cli.py` — CLI terminal
- `mcr/auto_referencia.py` — FASE 18 (meta-cognicao)
- `tools/corpus_multilingue.py` — gerador corpus (14 dominios, 70 conceitos, 3 idiomas)
- `tools/corpus_expanedido.py` — corpus massivo multi-fonte (240 conceitos x 5 idiomas + Rosetta Code + Gutenberg)
- `tools/wikipedia_corpus.py` — buscador Wikipedia PT/EN/ES com concept ID como acao

## Sessoes anteriores
- `docs/sessoes/SESSAO_2026-07-18_B2A_VALIDACAO.md` — corpus multi-idioma (4K obs, 10 dominios, 3 idiomas, PASS delta=0.20)
- `docs/sessoes/SESSAO_2026-07-17_AUTO_CONHECIMENTO.md` — auto-conhecimento + loop auto-treinamento + IDF no BC
- `docs/sessoes/SESSAO_2026-07-16_REVISAO_MCR.md` — revisao e reparo do MCR
- `docs/sessoes/PLANO_SEMANTICA_MCR.md` — plano completo de semantica MCR (Fase A/B/C)

## Proximos passos (ver PLANO_SEMANTICA_MCR.md para detalhes)
1. **ESCALA de texto (100K+ obs)** — FEITO: 160K obs, 204K palavras, delta=0.314 PASS
2. **Otimizar extrair_relacoes** — FEITO: 23ms-1016ms por palavra (era 3-30s)
3. **Investigar delta baixo** — RESOLVIDO: Gutenberg dilui (0.081 com Gutenberg vs 0.314 sem). IDF^4 + filtragem entropica restauraram delta=0.314
4. Fase B2c: expandir AutoConhecimento organico (conversas + calendario + gramatica)
5. Fase C1: ativar orfao multimodal.py como 14a fonte no decidir() — SEM modalidade "embedding" (hardcode disfarçado removido)
6. Validar hierarquia em escala (horizonte 4000+ tokens)
7. Rodar CLI completo interativo multi-turno
8. Investigar latencia 254ms para "gerar monstro" (outlier)
9. Refinar extrair_relacoes: distinguir coocorrentes diretos (late-cachorro) de sinonimos reais
   - So blob: delta=0.048 (sinal fraco mas nao zero)
   - So descricao PT/EN: delta=0.018 (FAIL — linguas diferentes nao compartilham tokens)
   - Blob + descricao: delta=0.166 PASS (blob e a ponte跨-idioma — padroes de pesos sao language-agnostic)
   - O blob funciona como concept ID: cachorro e dog compartilham d0alto d1alto (animal dims altas)
   - extrair_relacoes agrupa por dominio semantico via pesos: cachorro→peixe/gato/cavalo (animais)
10. Experimento LLM blob com embeddings REAIS (nomic-embed-text via Ollama, tools/_experimento_blob_enen.py)
    - Cosine oracle EN-EN: delta=0.362 PASS (o embedding TEM estrutura semantica real)
    - MCR so blob EN-EN: delta=0.025 FAIL (discretizacao em tercis perde info fina)
    - CONCLUSAO HONESTA (v5.1 — epifania Smith Chart): o MCR NAO PRECISA ler embeddings
    - O MCR e a Smith Chart; o LLM e a telefonia. A carta nao le circuitos, REPRESENTA circuitos
    - Testado: tercis, quintis, deciles, 20/50 bins, SimHash, HDC level, JSON, hex, float words — TODOS FAIL
    - O MCR discrimina semantica via TEXTO em escala (delta=0.314 Wikipedia) — constrói sua propria representacao
    - Proximo passo: ESCALA de texto (100K+ obs), nao modulos para ler caixa-preta
    - HARDCODE DISFARÇADO removido: SimHash, LevelHypervectors, modalidade "embedding", bins customizados — todos violavam Pilar 3
10. Experimento LLM blob com embeddings REAIS (nomic-embed-text via Ollama, tools/_experimento_blob_enen.py)
    - Cosine oracle EN-EN: delta=0.362 PASS (o embedding TEM estrutura semantica real)
    - MCR so blob EN-EN: delta=0.025 FAIL (discretizacao em tercis perde info fina)
    - CONCLUSAO HONESTA (v5.1 — epifania Smith Chart): o MCR NAO PRECISA ler embeddings
    - O MCR e a Smith Chart; o LLM e a telefonia. A carta nao le circuitos, REPRESENTA circuitos
    - Testado: tercis, quintis, deciles, 20/50 bins, SimHash, HDC level, JSON, hex, float words — TODOS FAIL
    - O MCR discrimina semantica via TEXTO em escala (delta=0.327 Wikipedia) — constrói sua propria representacao
    - Proximo passo: ESCALA de texto (100K+ obs), nao modulos para ler caixa-preta
    - HARDCODE DISFARÇADO removido: SimHash, LevelHypervectors, modalidade "embedding", bins customizados — todos violavam Pilar 3
