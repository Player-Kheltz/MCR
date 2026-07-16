# PLANO MCR — Estado Atual

## Princípio Fundamental
Tudo é P(token_n | token_n-1). Se não é P(b|a), não é MCR.
Um motor, uma equação, entropia, Markov. Domínio irrelevante.

---

## O Que Foi Feito

### Infraestrutura
- **13 módulos conectados** via `_lazy()`: coupling, esfera, superposicao, esquecimento, hiperesfera, conexao, bridge, mundo, genesis, observador, descobridor, variador, gerador
- **mcr.py v4.7**: zero hardcodes, superposition, universal `_gerar`, feedback contextual
- **devia/ arquivado** em `E:/Coisas/devia_archive/`
- **mcr/kernel/ achatado** para mcr/ (64 imports atualizados)
- **`__init__.py`**: lazy imports (zero I/O pesado no init)
- **Init time**: 0.45s (era 19s)
- **255 tools** no registry

### Fase 0 — Auto-leitura (implementada)
- MCR **lê seus próprios .py primeiro** antes de explorar workspace
- Extrai tokens de docstrings, classes, funções → seeds para Markov + Coupling
- Aprende P(stem→módulo) e P(palavra→módulo) de si mesmo
- Catálogo estudado: CATALOGO_MCR.md (24 tools, 52 commands, 60+ classes),
  MANIFEST.md (52 modules, 30 tools, 54 commands),
  AGI_ARCHITECTURE.md (5 layers SENSE→THINK→ACT→VALIDATE→LEARN),
  WHITEPAPER (framework matemático formal)

### Fase 1 — Exploração + Decisão (implementada)
- **Glob rápido**: scandir, timeout 5s, depth 3
- **Entropia dos stems** decide quais dirs são domínios
- **Dataset estendido**: 562 entradas, 12 ações (gerar_npc, gerar_monstro, responder,
  gerar_sprite, gerar_quest, analisar, buscar, editar, validar, conectar, aprender, planejar)
- **Wrappers** registrados para todas as 12 ações
- **Prefixo `gerar_` removido** — nomes = diretórios
- **_decidir**: superposition (Markov + Coupling + mk_palavra), self-feedback via P0 entropy
- **Feedback contextual**: usa _contexto_conversa + intervalo de tempo
- **receive_feedback**: aprende com max nota

### Auto-treino
- **4 fases paralelas** via ThreadPoolExecutor: auto_estudo, dialogos, padroes, dbs
- **_pre_treinar_markov**: seeds de dirs_por_tool + dataset → mk + coupling + mk_palavra
- **coupling persistence**: save/load JSON
- **ColdStart**: 95.2% com 12 ações (98.4% com 5 ações antes da extensão)

---

## Estado Atual — Bloqueio
- **95.2%** com 12 ações
- **Ações fortes**: gerar_npc 100%, gerar_monstro 100%, gerar_quest 100%,
  gerar_sprite 97.9%, responder 95.6%, planejar 100%, validar 80%
- **Ações fracas**: analisar 70%, buscar 70%, editar 70%, conectar 60%, aprender 40%
- Novas ações precisam de dados de treino mais diversos

---

## Módulos NÃO Conectados no Pipeline
- **Esfera**: só alimenta items.xml, não usado na geração
- **Conexão**: não chamada em processar
- **Bridge**: não chamado
- **Genesis**: não chamado
- **Hiperesfera**: não chamada em _perceber
- **Observador**: conectado mas cluster boost não ativado

---

## Próximas 8 Fases

| Fase | Módulo | Local | Função |
|------|--------|-------|--------|
| 0 | Auto-leitura | `_inicializar_templates` | MCR lê a si mesmo — **FEITO** |
| 1 | Dataset + Wrappers | `_decidir` + `_inicializar` | 12 ações, 562 entradas — **EM PROGRESSO** |
| 2 | Esfera | `_gerar_universal` | Gaps preenchidos por `predizer_cross` |
| 3 | Conexão + Bridge | `processar` | Bridges cross-domain |
| 4 | Genesis | `auto_treinar` | Auto-expansão para novos domínios |
| 5 | Hiperesfera | `_perceber` | Melhor tokenização por descoberta |
| 6 | Observador | `_decidir` | Cluster boost X→Y |
| 7 | Mundo | `_aprender` + `_decidir` | Simulação causal antes de agir |
| 8 | Cold start inteligente | ferramentas MCR | Grep, Read, Glob usados pelo próprio MCR |

---

## Filosofia
- **Zero hardcoded**: tudo descoberto dos dados
- **Zero if statements**: decisões via Equação MCR (superposição)
- **Zero LLM**: MCR decide sozinho
- **Zero GPU**: roda em qualquer hardware
- **Universal**: mesmo motor, N domínios
- **Template + gaps**: `extrair_template_entropico()` descobre estrutura vs variável
- **Tibia é a prova**, não o objetivo

> "TUDO é P(token_n | token_n-1), se não é P(b|a) não é MCR.
> ENTROPIA descobre estrutura vs ruído.
> MESMO motor, N domínios.
> Template + gaps. Fecha o loop.
> O MCR descobre seus próprios níveis."
