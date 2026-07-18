# Sessao: Auto-Conhecimento e Loop de Auto-Treinamento
**Data**: 2026-07-17

## Goal
- MCR se auto-alimenta com conhecimento (data, identidade, vocabulario)
- Loop de auto-treinamento: MCR admite ignorancia -> humano explica -> MCR ingere como fato
- BC (BaseConhecimento) deve recuperar fatos corretos para perguntas como "que dia e hoje"

## Constraints & Preferences
- Zero GPU, zero dependencias externas, zero listas hardcoded, zero if/else de dominio
- MCR puro (sem LLM fallback) — o LLM e o Pensador Profundo, MCR e o que ele constroi
- Pilar 1: tudo e P(b|a) — sem regex de pontuacao, sem freq < 200 hardcoded
- Pilar 2: thresholds emergem dos dados
- Pilar 7: NMI mede morfologia por caracteres, NAO semantica
- Pilar 9: admite ignorancia com honestidade
- Responder SEMPRE em portugues brasileiro
- Validacao empirica obrigatoria — rodar regressoes antes e depois de cada mudanca

## Progress

### Done
- **AutoConhecimento criado**: `mcr/auto_conhecimento.py` — ingere 39 fatos (6 temporal + 13 identidade + 20 vocabulario) no BC e no coupling
- **Bug `agoro.year` corrigido**: `agora.year` em auto_conhecimento.py linha 85
- **Bug "through" corrigido**: "por observacao" em auto_conhecimento.py linha 149
- **AutoConhecimento integrado ao chat**: lazy init via `_get_auto_conhecimento()`, metodo `inicializar_conhecimento()`
- **Loop de auto-treinamento integrado**: `interagir()` detecta ignorancia → marca `_ultima_ignorancia` → proxima entrada do humano e avaliada
- **CLI detecta transicao coldstart→chat**: apos coldstart completo, inicializa conhecimento automaticamente
- **Regressoes**: FASE 1 113/113 = 100% (latencia 22ms) + FASE 18 64/64 = 100% — SEM REGRESSAO
- **Sessao salva**: perfil, coldstart, sessao em cache/

### In Progress (NAO TERMINADO — continuar amanha)
- **Loop de auto-treinamento versao MCR pura**: implementado NMI morfologico + threshold emergente do historico (versao anterior usava `freq < 200` e `endswith('?')` — hardcoded). NAO TESTADO ainda.
- **`_tentar_base_conhecimento()` refatorado com IDF**: substitui desempate por `1/freq` (hardcoded) por IDF classico: `log(N_fatos / df(palavra))`. Threshold emergente: melhor >= 2x segundo. NAO TESTADO ainda.

### Blocked
- (none)

## Observacoes da Sessao (DESCOBERTAS IMPORTANTES)

### Descoberta 1: NMI de assinatura NAO discrimina
- `bc.recuperar()` retorna NMI ~0.997-1.000 para TODOS os fatos
- NMI de caracteres (Pilar 7) mede morfologia, nao significado
- "que dia e hoje" tem NMI 0.997 com "agora sao 02 horas e 13 minutos" E com "minha latencia e constante"
- **Conclusao**: NMI do coupling nao serve para desempatar fatos no BC. Precisa de outra metrica.

### Descoberta 2: IDF sobre o BC discrimina corretamente
- IDF(palavra) = log(N_fatos / N_fatos_com_palavra)
- "hoje" aparece em 3 fatos → IDF alto → discriminativo
- "que" aparece em muitos fatos → IDF baixo → nao discriminativo
- "dia" aparece em poucos fatos → IDF alto → discriminativo
- **Implementado** em `_tentar_base_conhecimento()` mas NAO TESTADO

### Descoberta 3: Priorizacao coldstart descarta fatos corretos
- Versao anterior priorizava fatos do coldstart sobre outros
- "que dia e hoje" tem overlap real ("dia", "hoje") com fatos temporais
- Mas coldstart foi priorizado e nao tinha overlap → retornava None
- **Corrigido**: removida priorizacao coldstart, IDF puro decide

### Descoberta 4: Hardcoding e tentacao constante
- Versao 1 do loop: `endswith('?')` — Pilar 7 violado (pontuacao e caractere, nao regra)
- Versao 1 do BC: `freq < 200` — Pilar 2 violado (threshold hardcoded)
- **Licao**: Toda vez que pensar "se termina com X" ou "se freq < Y", usar NMI/IDF/entropia
- **Principio**: MCR aprende pela estatistica, nao por regras. LLM sabe que e pergunta pela estatistica aprendida, nao por regex de pontuacao.

### Descoberta 5: `recuperar()` retorna 3 valores, nao 4
- Assinatura: `recuperar(pergunta, top_n) -> List[Tuple[str, str, float]]`
- Retorna: (fato, fonte, score_nmi)
- Bug `ValueError: too many values to unpack` corrigido

### Descoberta 6: 39 fatos ingeridos pelo AutoConhecimento
- 6 temporal: data, dia da semana, formato dd/mm/yyyy, horas, ano, mes
- 13 identidade: o que e MCR, diferencas vs LLM, pilares, arquitetura
- 20 vocabulario: dia, hora, minuto, tempo, data, nome, calendario, etc
- Todos ingeridos no BC (para recuperar) e no coupling (para aprender padroes)

### Descoberta 7: Teste rapido mostrou resultados parciais
- "qual meu nome" → "kheltz" (coldstart funcionou)
- "voce sabe meu nome" → "kheltz" (coldstart funcionou)
- "que dia e hoje" → ignorancia (BC nao encontrava — IDF fix pendente)
- "o que e mcr" → ignorancia (BC nao encontrava — IDF fix pendente)
- "que horas sao" → tratado como explicacao (loop bug — fix pendente)

## Key Decisions
- **IDF > NMI para desempate no BC**: NMI de caracteres nao discrimina fatos. IDF de palavras sim. IDF e MCR puro: P(palavra|fato) vs P(palavra|todos_fatos).
- **Loop de auto-treinamento por NMI**: NMI morfologico entre pergunta original e entrada atual decide se e explicacao (NMI alto = mesma coisa) ou nova pergunta (NMI baixo = assunto diferente). Threshold emerge do NMI medio do historico.
- **Sem priorizacao coldstart**: IDF puro decide qual fato e mais relevante. Coldstart nao tem prioridade especial.
- **Threshold emergente 2x**: melhor IDF deve ser >= 2x o segundo. Se empate → sem evidencia → ignorancia (Pilar 9).

## Next Steps (continuar amanha)

1. **Testar `_tentar_base_conhecimento()` com IDF**:
   - Rodar `test_bc.py` (em `C:\Users\Kheltz\AppData\Local\Temp\opencode\test_bc.py`)
   - Verificar se "que dia e hoje" retorna "hoje e dia 17 de julho de 2026"
   - Verificar se "o que e mcr" retorna "eu sou o MCR — motor cognitivo universal"
   - Verificar se "que horas sao" retorna "agora sao 02 horas e 13 minutos"

2. **Testar loop de auto-treinamento com NMI**:
   - Perguntar "o que e python" → MCR admite ignorancia
   - Explicar "python e uma linguagem de programacao" → MCR ingere
   - Perguntar "o que e python" novamente → MCR responde com o fato ingerido
   - Perguntar "que dia e hoje" (NMI baixo com "python") → NAO e tratado como explicacao

3. **Testar deteccao pergunta vs explicacao sem hardcode**:
   - "que dia e hoje" (sem "?") deve ser tratado como pergunta, nao explicacao
   - "python e uma linguagem" deve ser tratado como explicacao se pergunta anterior foi sobre python
   - Validar que NMI morfologico decide corretamente

4. **Rodar regressoes FASE 1 + FASE 18** apos testes

5. **Teste end-to-end no CLI**:
   - `python mcr_cli.py`
   - 5+ turnos com perguntas reais
   - Verificar coerencia

6. **Alimentar MCR com conhecimento em escala** (media prioridade):
   - Ingerir 10K+ observacoes de corpus real
   - Testar geracao de 4000+ tokens
   - Validar hierarquia em escala

## Relevant Files Modified This Session
- `mcr/auto_conhecimento.py`: criado — 39 fatos ingeridos (temporal + identidade + vocabulario); bugs `agoro` e `through` corrigidos
- `mcr/chat.py`: AutoConhecimento integrado (lazy init), loop de auto-treinamento (NMI morfologico), `_tentar_base_conhecimento()` refatorado com IDF
- `mcr_cli.py`: detecca transicao coldstart→chat e inicializa conhecimento automaticamente

## Critical Context
- **NMI do coupling ~1.0 para tudo**: nao discrimina fatos no BC. IDF necessario.
- **IDF sobre BC**: `log(N_fatos / df(palavra))` — palavras que aparecem em poucos fatos valem mais
- **Loop de auto-treinamento**: NMI morfologico entre pergunta e entrada decide explicacao vs nova pergunta
- **39 fatos no BC**: 6 temporal + 13 identidade + 20 vocabulario
- **14856 observacoes totais no coupling, 395 palavras no vocabulario**
- **Regressoes**: 113/113 + 64/64 — SEM REGRESSAO (validado antes de salvar)
- **Sessao salva em cache/**: perfil, coldstart, sessao
