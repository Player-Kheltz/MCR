# PLANO MCR — VERSÃO FINAL

## Estado Atual (v4.8)

**ColdStart**: 95.2% com 12 ações (562 entradas)
- gerar_npc: 100%, gerar_monstro: 100%, gerar_quest: 100%, planejar: 100%
- gerar_sprite: 97.9%, responder: 95.6%, validar: 80%
- analisar: 70%, buscar: 70%, editar: 70%, conectar: 60%, aprender: 40%
- Persistência: zero delta (Rodada 2 = Rodada 1)

**Conectado**: 13 módulos MCR (coupling, esfera, superposicao, esquecimento, hiperesfera, conexao, bridge, mundo, genesis, observador, descobridor, variador, gerador)

**Zero hardcode**: sem prefixo `gerar_`, sem tuples de ações, sem paths hardcoded, sem extensões hardcoded

## Fases

### Fase 1 (in_progress): Expandir _decidir para todas as ações
- Dataset estendido com 7 novas ações (analisar, buscar, editar, validar, conectar, aprender, planejar)
- Wrappers registrados com ferramentas MCR
- _self_feedback generalizado (sem `gerar_` hardcode)
- Auto-leitura implementada (Fase 0 — MCR lê seus próprios .py)
- Validar ColdStart com 12 ações → objetivo: >95% em todas

### Fase 2: Conectar Esfera no _gerar_universal
- Gaps preenchidos por esfera.predizer_cross

### Fase 3: Conectar Conexao + Bridge no processar
- Ponte entre domínios quando input contém conceitos de 2 domínios

### Fase 4: Conectar Genesis no auto_treinar
- Auto-expande para novos diretórios

### Fase 5: Conectar Hiperesfera no _perceber
- Descobre melhor tokenização para cada input

### Fase 6: Conectar Observador no _decidir
- Cluster boost

### Fase 7: Conectar Mundo no _aprender + _decidir
- Simulação causal

### Fase 8: Cold start inteligente com ferramentas MCR
- MCR usa suas próprias ferramentas para explorar

## Princípios
- Zero hardcode, zero if/else de domínio, universal, agnóstico
- Tudo é P(b|a) — transição entre dois estados consecutivos
- Equação MCR avalia, Entropia descobre, Markov aprende
- N-níveis se aplicam em qualquer escala
- O MCR descobre tudo sozinho
