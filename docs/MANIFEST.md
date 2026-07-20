# Manifeso MCR — Catálogo Vivo do Ecossistema

> **LEIA SEMPRE** antes de planejar ou executar qualquer tarefa.
> **ATUALIZE** ao descobrir algo novo.
> Versão: 3.0 | Data: 2026-07-20

---

## O que é o MCR (agora)

MCR é um **motor cognitivo Markoviano** que aprende por P(b|a) puro em múltiplas escalas.

- 133 módulos em `mcr/` (46.286 linhas)
- Núcleo: `mcr/coupling.py` (4381 linhas, 13 fontes + HRC)
- Chat: `mcr/chat.py` com ciclo Markoviano fechado
- Sem GPU, sem LLM obrigatório, sem dependências externas

**Não existe mais MCR-DevIA.** O ecossistema antigo (MCRSpriteMotor, PipelineUniversal, devia/kernel, 54 comandos cmd_*) foi substituído pelo motor unificado.

---

## Resumo do ecossistema

| Item | Quantidade |
|------|-----------|
| Módulos no `mcr/` | 133 |
| Linhas totais | 46.286 |
| Arquivos de teste | 164 |
| Regressão Fase 1 | 113/113 = 100% |
| Regressão Fase 18 | 64/64 PASS |
| Observações máx. | 167.434 |
| Vocabulário máx. | 214.907 palavras |
| Ações | 14+ |

---

## Módulos do núcleo (indispensáveis)

| Módulo | Linhas | Função |
|--------|--------|--------|
| `coupling.py` | 4381 | Motor principal: alimentar, decidir, extrair_relacoes, _nmi_semantico, HRC |
| `chat.py` | 611 | Chat bidirecional com coldstart, BC, GeradorCoerente, auto-treinamento |
| `triunvirato.py` | 239 | Busca ativa com 3 membros + consenso |
| `gerador_coerente.py` | 368 | Geração longa com n-grama[3/4] |
| `auto_conhecimento.py` | 118 | Auto-alimentação temporal + identidade |
| `auto_referencia.py` | 509 | FASE 18: 5 capacidades meta-cognitivas (64/64) |
| `auto_composicao.py` | 391 | Clusterização NMI → especialistas |
| `auto_expansao.py` | 458 | Expansão automática de conceitos |
| `base_conhecimento.py` | 190 | BC com NMI semântico |
| `acoplamento_hierarquico.py` | 326 | Hierarquia multi-escala (níveis 3-7) |

## Pilares (11)

1. **Tudo é P(b|a)** — probabilidade condicional pura
2. **Entropia descobre** — thresholds emergem dos dados (zero hardcoded)
3. **Markov na cadeia** — contexto e ordem, não janela
4. **Cadeia de Markov é esquecimento** — esquecer é preciso
5. **Ingerir, recuperar, aprender** — loop de conhecimento
6. **A entropia pode ser observada** — não controlada
7. **Semântica rotulada era morfologia** — NMI de chars não discrimina
8. **Aistência no roteiro de tempo** — contexto temporal
9. **Ignora com honestidade** — admite ignorância
10. **Consenso obrigatório** — triunvirato delibera até concordar
11. **Humano é a quarta dimensão** — alinha o triunvirato no tempo

## O que NÃO existe mais

- MCR-DevIA (substituído por coupling + chat)
- MCRSpriteMotor / MCRSpriteUniversal (domínio Tibia removido)
- PipelineUniversal / PipelineConectado (substituído por chat.py)
- 54 comandos cmd_* (eram do sistema LLM antigo)
- ToolOrchestrator / 30 ferramentas
- devia/kernel/ (desmembrado em módulos mcr/)
- MCR_legacy.py / MCR_AGI.py
- MCRFingerprint / MCRSignatureExpansiva / MCRByteUtils
- visual_coupling / regioes_anatomicas / olhos_mcr
- MCRDiscriminador / RadarMCR / meus_olhos.py
- Referências a Tibia/SPA/SHC/MountSummon/OTServ

## Regras operacionais

1. **Sempre rodar regressões** antes e depois de qualquer mudança:
   - `python tests/_regressao_fase1.py` — 113/113
   - `python tests/real/test_fase18_auto_referencia.py` — 64/64
2. **Nunca injetar rótulos** — thresholds e descobertas emergem dos dados
3. **Honestidade** — documentar limitações explicitamente
4. **Provas, não promessas** — toda descoberta deve ser validada empiricamente
5. **AGENTS.md** contém as regras absolutas do assistente MCR

## Documentos de referência

| Documento | Função |
|-----------|--------|
| `README.md` | Visão geral do projeto (raiz) |
| `docs/CATALOGO_MCR.md` | Catálogo completo de 133 módulos |
| `docs/HISTORIA_MCR.md` | Cronologia completa (23 fases) |
| `docs/MCR_IDENTITY.md` | Identidade, limites, definição |
| `docs/sessoes/` | Registros diários de descobertas |
| `AGENTS.md` | Regras do assistente (raiz) |

## Próximas ações

1. Propagar `_RE_TOKENS` para 34 lugares restantes
2. Conectar níveis 4-6 ao chat (intenção/emoção/estilo)
3. Integrar lift como método nativo do coupling
4. Conectar colônia auto-observadora ao motor principal
5. Treinar Abstração em escala (O(N²) → otimizar)
6. Conectar Teoria da Mente como 3º módulo cognitivo
