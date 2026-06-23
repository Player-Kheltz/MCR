>> CATALOG tags=todo, next-steps, roadmap, pendencias updated=2026-06-23
# Para Amanhã — 23 de Junho de 2026

## Contexto Geral
Estamos no meio de uma grande reforma no Projeto MCR. As bases foram estabelecidas:
- Encoding UTF-8 em todo lugar ✅
- AGENTS.md com regras de ouro ✅
- Documentação atualizada (parcialmente) ✅
- Git com commits descritivos ✅

## Estado Atual dos Sistemas

### 🟢 Finalizado / Funcional
- **Encoding**: `/utf-8` + `toLatin1()` pipeline completo — C++ e Lua podem usar UTF-8 literal
- **MountSummon (v2.0)**: HP tracking, moribundo, `!montarias`, `!todasmontarias`
- **Perseguição multi-piso**: Jitter, crowd control, limite de perseguidores, movimento nativo
- **Melee cross-floor bloqueado**: monstros e players
- **MonsterAI**: pensamento do monstro (look directions), throttle adaptativo, try/catch no onThink (anti-reentrancia)
- **BattleList/LOS**: refatorado — `isSightClear` como gatekeeper único. Servidor envia todas como visíveis, cliente decide com `g_map.isSightClear()`
- **OTClient compilável**: VS 2026, OpenGL|x64, 0 erros
- **CATALOG.md + doc-sync.py**: sistema de catálogo de docs implementado
- **AGENTS.md**: enxuto com regras de conduta + compilação
- **Docs atualizados**: 6 docs corrigidos com info obsoleta

### 🟡 Funcional com problemas
- **Player navigation**: `navigateTo` funciona para ataque/follow cross-floor, mas:
  - Ranged weapon não respeita range (NÃO CORRIGIDO)

### 🔴 Não funcional / Em investigação
- **Runas via BattleList cross-floor**: `[MCR-USE]` log não apareceu — OTClient pode não estar enviando o pacote
- **Clique direto no monstro em outro piso para atacar**: menu direito funciona, clique direto não
- **Clique no mapa para andar em outro piso**: "Não há rota" (OTClient já tem `sendGoTo` + bindings, pode ser bug de runtime)

## Tarefas Prioritárias

### 1. Ranged Weapon Range
Modificar `navigateTo` ou `playerSetAttackedCreature` para:
- Verificar o range da arma equipada do jogador
- Se ranged (shootRange > 1), parar a navegação a `shootRange` tiles do alvo
- Se melee (shootRange <= 1), ir até adjacente

### 2. Runas via BattleList
- Investigar por que o `[MCR-USE]` log não apareceu
- Verificar se o OTClient está enviando o pacote `parseUseItemEx` para alvos cross-floor
- Verificar se `canUse(player, fromPos)` está falhando

### 3. Clique Direto no Monstro
- Investigar o OTClient: quando o jogador clica em um monstro visível em outro piso, o clique é projetado para o piso do jogador
- Solução: modificar o hit-test do MapView para considerar criaturas em TODOS os pisos visíveis

### 4. Limpar Logs de Debug
- Remover ou mover para toggle `[MCR-ATTACK]`, `[MCR-NAV]`, `[MCR-BATTLE]`, `[MCR-USE]`, `[MCR-DEBUG-CLIENT]`, `[MCR-DEBUG-DOWN]`

### 5. Documentação Pendente
- [ ] `[10] MCR - Guia de Tradução e Localização (PT-BR).txt` — regras de encoding atualizadas
- [ ] `[1] MCR - Guia de Compilação (Servidor).txt` — encoding rules
- [ ] `[2] MCR - Guia de Compilação (Cliente).txt` — encoding rules
