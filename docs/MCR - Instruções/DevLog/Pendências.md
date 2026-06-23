>> CATALOG tags=todo, next-steps, roadmap, pendencias updated=2026-06-23
# Pendências — 23 de Junho de 2026

## 🟢 Concluído Hoje
- **AGENTS.md**: enxuto + seções 9-11 (TROUBLESHOOTING, Task Agent, auto.py)
- **CATALOG.md + doc-sync.py**: sistema de catálogo de docs
- **6 docs corrigidos**: info obsoleta atualizada (Multi-Piso, Para Amanhã, Perseguição, MountSummon, Guia [2], SPA)
- **Infraestrutura do assistente**:
  - `auto.py` (compile, status, verify, commit, sync, server)
  - `bridge.py` (chat bidirecional jogo ↔ assistente)
  - `test.py` (cmd, los, walk, attack, pos, assert, suite)
  - `create.py` (dominio, habilidade, monster, item, spell, npc, quest, quest-stage)
  - `info.py` (search, doc, grep, index, tree, session, status)
- **Bridge chat**: `chat_bridge.lua` com TalkAction `!assistente` + polling de `chat_out.txt` ✅
  - APIs corrigidas: `pairs(Game.getPlayers())`, `MESSAGE_GAMEMASTER_CONSOLE`
- **Test bot**: `test_bot.lua` executando comandos via `test_in.txt` → `test_out.txt` ✅
  - APIs corrigidas: `from:isSightClear(to, true)`, `pairs(Game.getPlayers())`
- **Conta de teste**: `test_account` / `test123`, personagem `TestChar` (GM lv 100) ✅
- **Servidor**: canary-sln.exe rodando, Criador online

## 🔴 Pendente

### 1. Ranged Weapon Range
- Modificar `navigateTo` ou `playerSetAttackedCreature` para verificar `shootRange`

### 2. Runas via BattleList cross-floor
- `[MCR-USE]` log não apareceu — OTClient pode não enviar o pacote

### 3. Clique Direto no Monstro em outro piso
- Menu direito funciona, clique direto não (hit-test projeta no piso do jogador)

### 4. Limpar Logs de Debug
- Remover/toggle `[MCR-DEBUG-CLIENT]`, `[MCR-DEBUG-DOWN]`, `[MCR-ATTACK]`, etc

### 5. Bridge: validar bidirecional
- Logar Criador, digitar `!assistente ola` e ver se bridge.py recebe

### 6. Test bot: validar com TestChar online
- Logar TestChar, rodar `test.py cmd "!pos"`, `test.py los` e `test.py walk`

### 7. Documentação
- [ ] `[10] Guia de Tradução.txt` — encoding rules
- [ ] `[1] Guia de Compilação Servidor.txt` — encoding rules
- [ ] `[2] Guia de Compilação Cliente.txt` — encoding rules
