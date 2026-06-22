# Para Amanhã — 22 de Junho de 2026

## Contexto Geral
Estamos no meio de uma grande reforma no Projeto MCR. As bases foram estabelecidas:
- Encoding UTF-8 em todo lugar ✅
- AGENTS.md com regras de ouro ✅
- Documentação atualizada (parcialmente) ✅
- Git com commits descritivos ✅

## Estado Atual dos Sistemas

### 🟢 Finalizado / Funcional
- **Encoding**: `/utf-8` + `toLatin1()` pipeline completo — C++ e Lua podem usar UTF-8 literal
- **MountSummon**: HP tracking, moribundo, `!montarias`, `!todasmontarias`
- **Perseguição multi-piso**: Jitter, crowd control, limite de perseguidores, movimento nativo
- **Melee cross-floor bloqueado**: monstros e players
- **MonsterAI**: pensamento do monstro (look directions), throttle adaptativo
- **BattleList opcode**: 57 (GameServerBattleListVisibility) — lado servidor OK

### 🟡 Funcional com problemas
- **Player navigation**: `navigateTo` funciona para ataque/follow cross-floor, mas:
  - Attack teleportava antes de andar (corrigido — agora só teleporta adjacente)
  - Follow não respeita chase mode (corrigido — agora verifica `player->chaseMode`)
  - Ranged weapon não respeita range (NÃO CORRIGIDO)
- **BattleList**: `updateBattleListVisibility` atualiza a cada passo, mas:
  - `isSightClear` causa inconsistência servidor vs cliente
  - Decisão atual: usar `canSee` + `isSightClear` só cross-floor
  - Criaturas no mesmo piso atrás de paredes ainda aparecem (OTClient decide)

### 🔴 Não funcional / Em investigação
- **Runas via BattleList cross-floor**: `[MCR-USE]` log não apareceu — OTClient pode não estar enviando o pacote
- **Clique direto no monstro em outro piso para atacar**: menu direito funciona, clique direto não
- **Clique no mapa para andar em outro piso**: "Não há rota" — OTClient precisa recompilar com `addPosition`
- **OTClient**: não recompilou com a correção do `sendGoTo` (`OutputMessage::addPosition` → `ProtocolGame::addPosition`)

## Tarefas Prioritárias para Amanhã

### 1. OTClient — Recompilar
O cliente precisa ser recompilado (VS 2026) com:
- `sendGoTo` corrigido (usa `addPosition(msg, pos)` em vez de `msg->addPosition(pos)`)
- `uigamemap.lua` com `g_game.navigateTo()` para clique cross-floor
- `protocolcodes.h` com `GameServerBattleListVisibility = 57`
- `creature.h` com `isHiddenFromBattleList`
- `luafunctions.cpp` com bindings

### 2. Ranged Weapon Range
Modificar `navigateTo` ou `playerSetAttackedCreature` para:
- Verificar o range da arma equipada do jogador
- Se ranged (shootRange > 1), parar a navegação a `shootRange` tiles do alvo
- Se melee (shootRange <= 1), ir até adjacente

### 3. Runas via BattleList
- Investigar por que o `[MCR-USE]` log não apareceu
- Verificar se o OTClient está enviando o pacote `parseUseItemEx` para alvos cross-floor
- Verificar se `canUse(player, fromPos)` está falhando

### 4. Clique Direto no Monstro
- Investigar o OTClient: quando o jogador clica em um monstro visível em outro piso, o clique é projetado para o piso do jogador
- Solução: modificar o hit-test do MapView para considerar criaturas em TODOS os pisos visíveis

### 5. Limpar Logs de Debug
- Remover ou mover para toggle `[MCR-ATTACK]`, `[MCR-NAV]`, `[MCR-BATTLE]`, `[MCR-USE]` após confirmação

## Documentação Pendente
- [ ] `[Documentação] MCR - Sistema de Perseguição Multi-Piso.txt` — atualizado com v4.0
- [ ] `[Documentação] MCR - Sistema de Montaria como Summon (MountSummon).txt` — atualizado com v2.0
- [ ] `[10] MCR - Guia de Tradução e Localização (PT-BR).txt` — regras de encoding atualizadas
- [ ] `[1] MCR - Guia de Compilação (Servidor).txt` — encoding rules
- [ ] `[2] MCR - Guia de Compilação (Cliente).txt` — encoding rules

## Regras que Emergiram
- Operações em massa → script Python com `--dry-run`
- Docs primeiro, código depois
- Perguntar antes de compilar
- Alinhar design antes de codificar
- Dry-run obrigatório para scripts em massa
- UTF-8 em todo lugar, `toLatin1()` na saída do protocolo
- Commits pequenos e descritivos
- Crowd control e jitter obrigatórios em sistemas multi-piso
- Uma alteração de cada vez por commit
