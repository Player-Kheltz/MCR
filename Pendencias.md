# Pendências.md — Estado do Projeto MCR

> Leia este arquivo no início de toda conversa para saber onde parou.
> Consulte também `docs/rules/checkpoint.md` e `docs/CHECKPOINT_SESSAO.md`.

## Última Sessão: 27/06/2026 (TARDE)

## ✅ Concluído na Sessão de Hoje

### Teste de Modelos - Parte 1 (27/06/2026 manhã)
- [x] **Baixar mistral:7b** (4.4GB baixado com sucesso)
- [x] **Testar llama3.1:8b** — ✅ Melhor para texto PT-BR (1472c, 23 nomes próprios, 6.1s)
- [x] **Testar mistral:7b** — ✅ Melhor para raciocínio/análise (3579c, 11.2s)
- [x] **Testar deepseek-r1:7b** — ⚠️ Problemas: thinking tokens consomem limite (falhou em código, 0c) e responde em inglês
- [x] **Testar qwen2.5-coder:7b** — ✅ Melhor para código (2571c, 10.0s)
- [x] **Script de teste** `sandbox/testes_modelos/executar_testes.py`
- [x] **12 arquivos individuais** de resultado
- [x] **Relatório automático** (`RELATORIO_COMPARATIVO.md`)
- [x] **Análise real** (`ANALISE_REAL.md`)

### Teste de Modelos - Parte 2: Melhor de 5 Mistral vs Qwen (27/06/2026 tarde)
- [x] **Script melhor de 5** `sandbox/testes_modelos/melhor_de_5.py`
- [x] **10 chamadas Ollama** (5 testes × 2 modelos)
- [x] **Resultado heurístico**: Mistral 6.1/10 vs Qwen 5.5/10 (Mistral vence)
- [x] **Resultado REAL**: Qwen 3-0-2 Mistral (Qwen vence em análise qualitativa)
- [x] **Análise real detalhada** (`MELHOR_DE_5_ANALISE_REAL.md`)

### Integração Context Infinity + WebLearn + Debate Protocol + Loop OODA (27/06/2026)
- [x] **Context Infinity Global** no kernel (ctx_max 8192, hooks pre/post)
- [x] **Loop OODA via kernel** (mcr_loop.py reescrito para usar MCRKernel)
- [x] **WebLearn como comando** (cmd_weblearn.py)
- [x] **Debate Protocol v2** integrado ao Conselho (callback gerar + tempdir)
- [x] **ctx_crew implementado** (kernel carrega ContextCrew V3 como módulo)
- [x] **aprender_conceito universal** (sem palavras fixas, ranking por densidade+local)
- [x] **aprender_conceito em lote**: SPA, SHC, Canary, Eridanus, Dominios, OTClient, MCR (8 conceitos)

### Dívida Técnica Resolvida (27/06/2026)
- [x] **10 scripts duplicados removidos** de scripts/mcr_devia/
- [x] **KG limpo**: 2 lessons alucinadas removidas (L1807, L1820)
- [x] **Conselho**: qwen2.5-coder > deepseek para veredito (0 alucinações em 2.5s)
- [x] **Conselho**: não gera personagens para perguntas factuais
- [x] **cmd_conselho**: filtra alucinações antes de salvar no KG

### Teste de Modelos - Parte 3: Deepseek R1 em profundidade (27/06/2026 noite)
- [x] **Teste com raw:true** - ❌ QUEBROU (resposta vazia, 0 chars em todos os 6 testes)
- [x] **Teste com raw:false + num_predict:8192** - ✅ FUNCIONOU
- [x] **CAP Theorem**: 1346 chars em 8.5s - explicacao clara (mas em ingles)
- [x] **Code Review**: 675 chars em 6.3s - **achou bug de seguranca** (amount negativo)
- [x] **Python Code**: 1514 chars em 26.1s - codigo funcional mas 2-3x mais lento que Qwen
- [x] **CONFIGURACAO CORRETA descoberta**: `raw:false` + `num_predict:8192`
- [x] **KG atualizado** com ~23 lições (1750→1773)

### Arquitetura (sessões anteriores)
- [x] Conselho V8 (4 fixos + psicólogo + honorários sob demanda + auto-revisão)
- [x] Pipeline V4 (contexto flutuante, temperatura por etapa, zero prompts fixos)
- [x] ContextCrew V3 (5 fontes: KG, WebLearn, Docs, Código, Web)
- [x] LessonsBuffer (buffer de conhecimento, detecta/resolve contradições)
- [x] Toolkit documentado (injetado nos prompts do Conselho)
- [x] Explorar otimizado (6s vs timeout, categorização 0 IA)
- [x] Verificar mudanças (detecta alterações em 107 arquivos)
- [x] 44 comandos modulares

### Integração (sessões anteriores)
- [x] Dashboard com chat (http://localhost:8765)
- [x] Atalho na área de trabalho
- [x] MCR-DevIA detecta mudanças nos próprios arquivos
- [x] ContextCrew busca em docs + código automaticamente

### Regras/Equipe (sessões anteriores)
- [x] Banner de ativação com 11 regras para Cloud
- [x] LEMBRETE no final de toda execução
- [x] Fluxo de teste cego para comparações
- [x] Regra: Cloud supervisiona, MCR executa
- [x] Regra: Nunca editar arquivos direto
- [x] Regra: IA é ferramenta, não identidade
- [x] Regra: Nada hardcoded

## 🔴 Pendências para PRÓXIMA SESSÃO

### Prioridade Máxima (Decisões sobre Modelos — RESOLVIDO)
- [x] **Discutir gargalo de modelo**: ✅ TESTADO E DECIDIDO
  - **qwen2.5-coder:7b** → PADRÃO para código (🏆 melhor de 5: venceu em análise real)
  - **llama3.1:8b** → TEXTO PT-BR / LORE (🥇 23 nomes próprios, português natural)
  - **mistral:7b** → ALTERNATIVA para equilíbrio (vencedor heurístico, empate técnico real)
  - **deepseek-r1:7b** → ⚠️ APENAS com `raw:true` + `num_predict:8192` para raciocínio complexo
- [x] **Decidir sobre Deepseek R1**: Pensando bem: thinking tokens são VANTAGEM para problemas complexos. Configurar com `raw:true` + `num_predict:8192` para review de código, planejamento arquitetural e debugging. NUNCA para PT-BR ou tarefas simples.

### Alta Prioridade
- [ ] **Configurar router de modelos no MCR-DevIA** (llama3.1 para cmd_lore/Conselho, qwen padrão, deepseek para cmd_review)
  - Estado atual: `modulos/ia.py` e `modulos/util.py` tem dicionário MODELOS mas TUDO aponta para qwen2.5-coder:7b
  - Precisa: adicionar entradas para llama3.1 (texto/lore), deepseek (review), mistral (alternativa)
- [ ] **Criar/expandir cmd_lore.py** usando llama3.1:8b (atualmente só redireciona para LoreGen)
- [ ] **Atualizar Conselho V8** para usar llama3.1 em personalidades de texto (Contador de Histórias)
- [ ] **Ajustar deepseek** no MCR-DevIA: config `raw:false` + `num_predict:8192` para cmd_review (raw:true QUEBRA)
- [ ] **Melhorar LORE**: WebFetch para nomes com significado
- [ ] **Explorar ambiente**: rodar explorar para aprender tecnologias do sistema

### Média Prioridade
- [ ] Dashboard: melhorar chat com streaming e histórico
- [ ] Conselho: personalidade de "revisor de português" para PT-BR
- [ ] Pipeline: etapa de tradução PT-BR no final
- [ ] Explorar: versão background (daemon)
- [ ] Testes: bateria completa de 67 testes no kernel

### Baixa Prioridade
- [ ] Interface web completa com dashboard + chat + status
- [ ] Plugin system para terceiros
- [ ] Documentação automática (cmd_revisar_docs + AGENTS.md)
- [ ] Conselho com memória entre sessões

## 📊 Estado Atual

| Componente | Qtde | Status |
|-----------|------|--------|
| Comandos modulares | 44 | ✅ |
| Módulos | 15 | ✅ |
| Personalidades | 7+ | ✅ |
| Fontes de contexto | 5 | ✅ |
| Modelos IA | 4 (qwen, deepseek, llama, mistral) | ✅ |
| KG lessons | 1825 | ✅ |
| Memória | Infinita | ✅ |
| Dashboard | Funcional | ✅ |
| Context Infinity | Global (8192 ctx) | ✅ |
| scripts/mcr_devia/ | ~28 (sem duplicatas) | ✅ |
| sandbox/ | ~326 (originais) | ✅ |

## 📁 Arquivos-Chave para Revisão
- `LEMBRETE.md` — Regras absolutas
- `AGENTS.md` — Arquitetura
- `docs/rules/` — 8 arquivos de regras
- `docs/CHECKPOINT_SESSAO.md` — Contexto completo da sessão
- `scripts/mcr_devia/modulos/conselho.py` — Conselho V8
- `scripts/mcr_devia/modulos/pipeline.py` — Pipeline V4
- `scripts/mcr_devia/modulos/toolkit.py` — Inventário de ferramentas
- `scripts/mcr_devia/modulos/lessons_buffer.py` — Buffer de conhecimento
- `scripts/mcr_devia/context_crew.py` — ContextCrew V3
