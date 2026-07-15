# AGENTS.md — Regras para agentes no projeto MCR

## Economia de tokens

- Use o MCR para trabalho interno. `python -c "from mcr.mcr import MCR; m=MCR(); m.processar('...')"` faz o trabalho de dezenas de tool calls.
- Prefira 1 comando Bash que executa um script Python a 10 chamadas Read/Edit sequenciais.
- Use subagentes (Task) para auditorias e buscas longas — o resultado volta em 1 mensagem.
- Não leia arquivos inteiros. Use Grep para encontrar linhas específicas, depois Read com offset/limit.
- Não repita contexto. Se já leu um arquivo nesta sessão, referencie o que viu.
- Commite e pushe frequentemente — protege o trabalho e reduz contexto acumulado.

## Filosofia MCR (NUNCA violar)

- **Zero hardcode**: sem strings de domínio (`'npc'`, `'monstro'`, `'sprite'`, `'lua'`, `'tibia'`), sem listas fixas, sem prefixos hardcoded (`'gerar_'`).
- **Zero if/else de domínio**: decisões por entropia + superposição + equação, nunca `if acao == 'gerar_npc'`.
- **Universal e agnóstico**: qualquer idioma, qualquer domínio, qualquer formato. O MCR descobre tudo do dado.
- **Tudo é P(b|a)**: transição entre dois estados consecutivos. Equação avalia, Entropia descobre, Markov aprende.
- **N-níveis**: byte, palavra, trigrama, padrão, entropia, assinatura — aplicam-se em qualquer escala.
- **O MCR descobre tudo sozinho**: domínios por assinatura, verbos por entropia de P0, thresholds por MCRThreshold.

## Estrutura do projeto

- `mcr/mcr.py` — pipeline principal (perceber → decidir → executar → avaliar → aprender)
- `mcr/engine.py` — Markov 1ª ordem (núcleo, intacto)
- `mcr/equacao_mcr.py` — fonte da verdade da Equação 5D
- `mcr/coupling.py` — acoplamento multi-nível (palavra→ação, posição→ação)
- `mcr/esfera.py` — correlação N-dimensional entre níveis
- `mcr/superposicao.py` — colisão de cadeias Markov
- `mcr/signature.py` — fingerprint 8D + assinatura
- `mcr/descobridor.py` — frequência diferencial para âncoras
- `mcr/decisor.py` — MCRThreshold (thresholds adaptativos)
- `mcr/observador.py` — observador universal X→Y
- Demais módulos: ver `docs/CATALOGO_MCR.md`

## Testes

- `tests/experimento_rigoroso/03_coldstart.py` — ColdStart (deve dar 100% com self-feedback)
- `tests/experimento_rigoroso/09_teste_fogo.py` — bateria pesada multi-domínio
- `tests/experimento_rigoroso/10_teste_real_comparativo.py` — MCR vs TF-IDF+LR
- Dataset: `tests/experimento_rigoroso/dataset_500.json` (562 entradas, 8 ações normalizadas)

## Boas práticas de código

- Lazy imports dentro de métodos para evitar ciclos e acelerar init.
- `_lazy(attr, cls_path)` para módulos MCR opcionais.
- `_th(chave, fallback)` para thresholds — nunca hardcoded.
- `_normalizar_acao(acao)` — verbos descobertos por entropia do coupling, nunca lista fixa.
- Persistência: `mk.save()`, `mk_palavra.save()`, `coupling.save()` — JSON legível.
- `_extrair_niveis(entrada)` — 31 níveis de fingerprint do mesmo input.
- Self-feedback: `receber_feedback(entrada, acao)` — reforço 5x, aprende do erro.

## O que NÃO fazer

- Não adicionar embeddings contínuos — vira LLM híbrido, perde o nicho.
- Não adicionar regex de idiomas — quebra universalidade.
- Não adicionar lista de sinônimos — quebra agnosticismo.
- Não adicionar `if "português"` — quebra filosofia MCR.
- Não usar `git checkout --` em arquivos não commitados — destrói trabalho não salvo.
- Não reescrever módulos existentes sem ler o catálogo primeiro.
- Não criar módulos novos sem verificar se já existe equivalente.
