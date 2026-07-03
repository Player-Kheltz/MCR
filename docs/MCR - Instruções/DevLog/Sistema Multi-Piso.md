>> CATALOG tags=multi-piso, los, battlelist, navigation, combat, monster-ai updated=2026-06-23
# DevLog — Sistema Multi-Piso (Perseguição, Navegação, BattleList, Combate)

## Contexto
O MCR permite combate, perseguição e navegação entre pisos, diferentemente do Tibia padrão (mesmo piso apenas). O sistema usa o GlobalMonsterMap como cache compartilhado de regiões e transições.

## Componentes

### 1. Perseguição de Monstros (MonsterAI)
**Arquivos:** `monster_ai.cpp`, `monster.cpp`, `monster.hpp`, `global_monster_map.cpp`  
**Status:** Funcional, com melhorias aplicadas.

**O que funciona:**
- A* segmentado + escadas como portais entre pisos
- Máquina de estados (Combate, StairPursuit, Retorno, Idle)
- Anti-ping-pong por penalização (+10000 em vez de bloqueio)
- Tratamento diferenciado summons vs hostis
- Sistema híbrido (replaneia rota após transição se 20% mais curta)

**O que foi adicionado recentemente:**
- **Pensamento do monstro** (`m_thinkCycle`, `m_thinkDirs`): ao chegar no destino da escada sem ver o líder, olha para direções candidatas (escadas próximas, última posição do líder) antes de decidir
- **Movimento nativo**: `getNextStep` só usa `isWalkingToPosition` quando em stair pursuit ou retorno — o resto usa `doFollowCreature` nativo (elimina movimento robótico)
- **Melee bloqueado cross-floor**: monstros melee (`targetDistance ≤ 1`) não tentam ataque direto entre pisos; perseguem até o mesmo andar
- **Jitter aleatório** (100-500ms) no stair planning — evita pico de pathfinding
- **Limite de perseguidores** por líder: 15 (hostis), summons ilimitados
- **Congestionamento de escadas**: se 5+ bichos usam a mesma escada, buscam alternativa

**O que tentamos e não deu certo:**
- `isWalkingToPosition` para TODOS os movimentos (causava movimento robótico)
- `sendRemoveTileThing` para limpar BattleList (removia sprite do chão, causava erro "no thing at pos")

### 2. Navegação do Jogador (PlayerNavigation)
**Arquivos:** `player.cpp`, `player.hpp`, `game.cpp`, `protocolgame.cpp`  
**Status:** Parcialmente funcional, em desenvolvimento.

**O que funciona:**
- `Player::navigateTo(Position target)` — usa `GlobalMonsterMap::findPathBetweenRegions` para obter transições de escada
- `onNavigationStep()` — caminha até waypoints, teleporta ao chegar na escada
- Gatilho em `playerSetAttackedCreature` e `playerFollowCreature` quando alvo está em outro piso
- Opcode 59 (custom) para `playerGoTo`

**O que NÃO funciona:**
- Clique para andar em outro piso → "Não há rota" (OTClient precisa recompilar com `sendGoTo` + `addPosition`)
- Follow não respeita chase mode completamente (corrigido parcialmente)
- Attack não respeita range da arma (sempre vai melee)

**O que tentamos:**
- `Tile::getDestination()` retorna (0,0,0) para escadas comuns — tivemos que calcular destino pelas flags FLOORCHANGE, depois trocamos para usar `m_navDestinations` salvas do `findPathBetweenRegions`
- `queryAdd` adaptado para permitir jogadores em navegação pisarem em FLOORCHANGE tiles

### 3. BattleList com Linha de Visão
**Arquivos:** `protocolgame.cpp`, `protocolgame.hpp`, `battle.lua` (OTClient)  
**Status:** Funcional.

**Como funciona (refinado em 23/06/2026):**
- O servidor envia opcode 57 (`GameServerBattleListVisibility`) com `visible=true` para **todas** as criaturas — não filtra mais no servidor
- O cliente (`battle.lua`) usa `g_map.isSightClear(player→creature)` como **gatekeeper único**: se a linha de visão falha, a criatura some da BattleList
- O nome/HP (`drawInformation`) e os projéteis também usam `isSightClear` — tudo passa pelo mesmo check
- A atualização ocorre a cada passo do jogador + movimento de cada criatura

**O que tentamos e não deu certo:**
- Remover sprites via `sendRemoveTileThing` (causava "no thing at pos" e quadrado preto)
- `cleanupBattleList()` com stackpos — stackpos errado, removia chão
- `canSee` como filtro principal (criaturas atrás de paredes no mesmo piso apareciam)
- Opcode 57 com `visible=false` no servidor (discrepância servidor vs cliente)

**Decisão atual:** `isSightClear` é o único gatekeeper — decide BattleList, nome/HP e projéteis. O servidor envia todas as criaturas como visíveis; o cliente refina.

### 4. Runas entre Pisos
**Status:** Não funciona, em investigação.

**O que tentamos:**
- `playerUseItemEx`: bypass cross-floor trata TOOFARAWAY e CANNOTTHROW
- Adicionado `[MCR-USE]` log para debug (não apareceu — OTClient pode não estar enviando o pacote)

**Hipótese atual:** O OTClient pode estar bloqueando o envio do pacote `parseUseItemEx` para alvos em pisos diferentes. Precisa de investigação no lado do cliente.

### 5. Clique Direto para Atacar
**Status:** Funciona via menu direito, não via clique direto.

**O que funciona:**
- Menu direito → "Atacar" → funciona (`parseAttack` envia creature ID)
- BattleList → clique → funciona

**O que NÃO funciona:**
- Clique direto no monstro na tela → erro (OTClient projeta clique no piso do jogador)

**O que tentamos:**
- `uigamemap.lua`: multi-floor scan para `attackCreature` (z-2 a z+2)
- `gameinterface.lua`: removeu Z equality check para creatureThing

## Pendências
1. OTClient precisa recompilar com `sendGoTo` (addPosition)
2. Ranged weapon range no follow/attack
3. Runas via BattleList cross-floor (investigar OTClient)
4. Clique direto no monstro em outro piso