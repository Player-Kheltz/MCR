# Grimório God Client — Plano de Desenvolvimento
> Data de inicio: 2026-07-08
> Objetivo: Transformar OTClient em Grimório (God Client) integrado a MCR-DevIA

---

## Visão Geral

O Grimório unificara tres bases de codigo em um unico cliente todo-poderoso:
- **OTClient** → olhos/camera/rendering
- **RME (Remere's Map Editor)** → maos/edicao de mapa
- **Canary** → leis/servidor (ja temos em server/)
- **MCR-DevIA (Python)** → cerebro (Bridge API :7778)

---

## 4 Marcos

### MARCO 1: Esqueleto e Visao (Apenas Observacao)
OTClient decapitado: GM autologin, camera livre, zero UI de jogador.

### MARCO 2: Ponte da Consciencia (MCR Conectado)
Grimorio fala com Python via Bridge API (:7778). Entropia e eventos do mundo na tela.

### MARCO 3: Poder Divino (Interacao In-Place)
Click no mundo vivo: inspecionar NPC, gerar quest via MCR.

### MARCO 4: Cauldron da Criacao (RME/Mapa)
Edicao de OTBM e Heatmap de Entropia sobre o mapa.

---

## Log de Atividades

### 2026-07-08 — Inicio da auditoria OTClient
[auditoria detalhada acima]

### 2026-07-08 — MARCO 1 IMPLEMENTADO

**Arquivos modificados/criados:**

| Arquivo | Acao | Descricao |
|---------|------|-----------|
| `grimorio_config.lua` | CRIADO | Config central do God Client: autoLogin, host/port, credenciais GM, cameraSpeed, startPosition |
| `init.lua` | MODIFICADO | Carrega `grimorio_config.lua` apos search paths |
| `modules/client_entergame/entergame.lua` | MODIFICADO | `EnterGame.firstShow()` detecta `GrimorioConfig.autoLogin` e bypassa UI de login |
| `modules/game_interface/gameinterface.lua` | MODIFICADO | `show()` usa `setCameraPosition()` em vez de `followCreature()`. `bindKeys()` adiciona WASD (move) e Q/E (piso) |
| 48 `.otmod` files | MODIFICADOS | `autoload: false` adicionado para desativar HUD de jogador |

**Status: MARCO 1 E 2 REVERTIDOS — OTClient restaurado a producao.**

Por decisao arquitetural do Arquiteto, o Grimorio nunca mais residira no mesmo diretorio do OTClient.
Toda administracao MCR sera feita exclusivamente via Grimorio WPF.
O OTClient deve permanecer como cliente de jogo para os jogadores, intocado.

**Arquivos restaurados:**

| Arquivo | Acao |
|---------|------|
| `modules/client_entergame/entergame.lua` | Removido bloco Grimorio autologin |
| `modules/game_interface/gameinterface.lua` | Restaurado `followCreature()`, removido WASD/free camera |
| `init.lua` | Removido `dofile(grimorio_config.lua)` |
| `grimorio_config.lua` | Deletado |
| `modules/mcr_hud/` | Modulo deletado |
| 48 `.otmod` files | `autoload: false` removido, HUD restaurado |

**Licao aprendida:** Regra de Isolamento do Observador — nenhuma ferramenta administrativa MCR deve modificar o cliente de producao. Toda comunicacao via Bridge API (:7778) apenas.

---

## MAPA TECNICO COMPLETO — MARCO 1

### 1. LOGIN (Bypass para GM Autologin)

**Arquivo-alvo:** `E:\MCR\client\modules\client_entergame\entergame.lua` (1206 linhas)

**Fluxo atual de login:**
1. `init.lua` carrega modulos → `client_entergame` mostra janela de login
2. Usuario digita conta/senha → `EnterGame.doLogin()` → HTTP POST para login server
3. Server retorna session + playdata (worlds + characters)
4. Janela de selecao de personagem aparece (`CharacterList.create()`)
5. Usuario seleciona personagem → `CharacterList.doLogin()` → `g_game.loginWorld()`
6. `onGameStart` → `EnterGame.hidePanels()`, `gameMapPanel:followCreature(player)`

**Proposta de bypass (GM autologin):**

Criar um arquivo `grimorio_config.lua` (ou ler do `config.ini`) com:
```lua
GrimorioConfig = {
    host = "127.0.0.1",
    port = 7171,          -- porta do game server (nao HTTP)
    account = "1",
    password = "1",
    character = "God Character",
    autoLogin = true,
}
```

Modificar `entergame.lua` no `EnterGame.init()`:
```lua
function EnterGame.init()
    -- Se autoLogin configurado, pula direto para o jogo
    if GrimorioConfig.autoLogin then
        -- Chama diretamente CharacterList.doLogin() com dados pre-configurados
        -- Pula todo o fluxo HTTP e selecao de personagem
        CharacterList.doLogin({
            world = { host = GrimorioConfig.host, port = GrimorioConfig.port },
            character = { name = GrimorioConfig.character }
        })
        return
    end
    -- ... resto do init normal ...
end
```

**Arquivos a modificar:**
- `modules/client_entergame/entergame.lua` — adicionar bypass no init()
- `modules/client_entergame/entergame.otui` — pode ser mantido, nao sera usado

---

### 2. UI DE JOGO (Desativar HUD do jogador)

**Arquivo-alvo:** `E:\MCR\client\modules\game_interface\gameinterface.lua` (1967 linhas)

**Modulos a desativar no `init.lua`:**

No `init.lua`, modificar a ordem de carregamento para PULAR todos os modulos de UI de jogador. As linhas de descoberta de modulos sao gerenciadas pelo `ModuleManager` em C++, mas a ordem de carregamento e controlada pelo `autoload-priority` nos arquivos `.otmod`.

**Estrategia:** Modificar cada `.otmod` dos modulos de jogador para `autoload: false`:

| Modulo | Otmod | Funcao |
|--------|-------|--------|
| `game_actionbar` | `game_actionbar/game_actionbar.otmod` | Barra de acoes |
| `game_battle` | `game_battle/battle.otmod` | Janela de batalha |
| `game_console` | `game_console/console.otmod` | Chat |
| `game_containers` | `game_containers/containers.otmod` | Inventario |
| `game_healthcircle` | `game_healthcircle/game_healthcircle.otmod` | Circulo de vida |
| `game_healthinfo` | `game_healthinfo/healthinfo.otmod` | Barra de vida |
| `game_hotkeys` | `game_hotkeys/hotkeys_manager.otmod` | Atalhos |
| `game_inventory` | `game_inventory/inventory.otmod` | Inventario |
| `game_minimap` | `game_minimap/minimap.otmod` | Minimapa |
| `game_skills` | `game_skills/skills.otmod` | Skills |
| `game_viplist` | `game_viplist/viplist.otmod` | Lista VIP |
| `game_analyser` | `game_analyser/analyser.otmod` | Analisador |
| `game_market` | `game_market/t_market.otmod` | Mercado |
| `game_store` | `game_store/game_store.otmod` | Loja |
| `game_shop` | `game_shop/game_shop.otmod` | Shop |
| `game_spelllist` | `game_spelllist/spelllist.otmod` | Lista de spells |
| `game_outfit` | `game_outfit/outfit.otmod` | Outfits |
| `game_paperdolls` | `game_paperdolls/paperdolls.otmod` | Paperdolls |
| `game_questlog` | `game_questlog/game_questlog.otmod` | Quest log |
| `game_blessing` | `game_blessing/blessing.otmod` | Blessings |
| `game_prey` | `game_prey/prey.otmod` | Prey system |
| `game_imbuing` | `game_imbuing/imbuing.otmod` | Imbuing |
| `game_stash` | `game_stash/game_stash.otmod` | Stash |
| `game_forge` | `game_forge/game_forge.otmod` | Forge |
| `game_cooldown` | `game_cooldown/cooldown.otmod` | Cooldowns |
| `game_cyclopedia` | `game_cyclopedia/game_cyclopedia.otmod` | Cyclopedia |

**Modulos a MANTER (necessarios para o God Client):**
- `corelib` — biblioteca base
- `gamelib` — logica do protocolo, game.lua
- `modulelib` — biblioteca de modulos
- `startup` — inicializacao
- `client` — modulo cliente base
- `client_entergame` — login (modificado para autologin)
- `game_interface` — tela principal (modificada para remover HUD)
- `game_mainpanel` — painel principal (modificado)
- `game_creatureinformation` — informacao de criaturas (util para GM)
- `game_textmessage` — mensagens de texto (uteis para debug)
- `game_things` — coisas do jogo
- `game_features` — features
- `game_walk` — walking
- `game_shortcuts` — atalhos de teclado
- `game_shaders` — shaders
- `client_styles` — estilos
- `mcr_modules/*` — modulos MCR existentes

---

### 3. CAMERA LIVRE (Free Camera)

**Sistema atual de camera (C++):**

| Arquivo | Classe | Metodo Chave |
|---------|--------|-------------|
| `src/client/mapview.h` | `MapView` | `followCreature()`, `setCameraPosition()`, `getCameraPosition()` |
| `src/client/uimap.h` | `UIMap` | Ponte Lua-C++: `followCreature()`, `setCameraPosition()` |
| `src/client/luafunctions.cpp` | — | Bindings: `UIMap.followCreature`, `UIMap.setCameraPosition` |
| `src/client/creature.h` | `Creature` | `isCameraFollowing()`, `m_cameraFollowing` |
| `src/client/map.cpp` | `Map` | `notificateCameraMove()` |

**Estado atual:**
- Camera segue criatura (`m_follow = true`, `m_followingCreature` setado)
- Quando criatura anda, `onWalk()` → `notificateCameraMove()` → `MapView::onCameraMove()`
- `getCameraPosition()` retorna `m_followingCreature->getPosition()` se seguindo

**Proposta de Free Camera (via Lua — sem modificar C++):**

No `gameinterface.lua`, modificar `onGameStart`:
```lua
-- ANTES (atual):
-- gameMapPanel:followCreature(g_game.getLocalPlayer())

-- DEPOIS (free camera):
-- Nao chama followCreature — camera fica solta
-- Ou chama setCameraPosition para posicao inicial
gameMapPanel:setCameraPosition(Position(1000, 1000, 7))  -- posicao inicial
```

Adicionar controle de camera por teclado (setas WASD):
```lua
-- No init() do gameinterface.lua:
local cameraSpeed = 2
bindKeyDown('W', function() moveCamera(0, -cameraSpeed) end)
bindKeyDown('S', function() moveCamera(0, cameraSpeed) end)
bindKeyDown('A', function() moveCamera(-cameraSpeed, 0) end)
bindKeyDown('D', function() moveCamera(cameraSpeed, 0) end)
```

Onde `moveCamera()` e uma funcao que le a posicao atual da camera, soma o offset, e chama `setCameraPosition()`:

```lua
function moveCamera(dx, dy)
    local pos = gameMapPanel:getCameraPosition()
    gameMapPanel:setCameraPosition(Position(pos.x + dx, pos.y + dy, pos.z))
end
```

**Zoom** (ja existe, so manter):
- `Ctrl +` = zoom in (gameMapPanel:setZoom(zoom + 1))
- `Ctrl -` = zoom out (gameMapPanel:setZoom(zoom - 1))

**Mudanca de piso:**
- Teclas Q/E ou PageUp/PageDown para subir/descer piso
```lua
bindKeyDown('Q', function()
    local pos = gameMapPanel:getCameraPosition()
    gameMapPanel:setCameraPosition(Position(pos.x, pos.y, math.max(0, pos.z - 1)))
end)
bindKeyDown('E', function()
    local pos = gameMapPanel:getCameraPosition()
    gameMapPanel:setCameraPosition(Position(pos.x, pos.y, math.min(15, pos.z + 1)))
end)
```

**Nenhuma modificacao em C++ necessaria para a camera livre** — a API `setCameraPosition()` ja existe no C++ e esta exposta ao Lua. Basta nao chamar `followCreature()` e usar `setCameraPosition()` no lugar.

---

### 4. ARVORE DE DECISAO DO MARCO 1

```
init.lua carrega modulos
    │
    ├─ grimorio_config.lua (NOVO) — configuracoes do Grimorio
    │   └─ host, port, account, password, character, autoLogin
    │
    ├─ client_entergame (MODIFICADO)
    │   └─ EnterGame.init() detecta autoLogin=true
    │       └─ Pula janela de login → chama CharacterList.doLogin() direto
    │       └─ g_game.loginWorld() conecta ao server
    │
    ├─ Modules de jogador DESATIVADOS (ver lista acima, ~25 modulos)
    │   └─ Sem HUD, sem inventario, sem botoes
    │
    └─ game_interface (MODIFICADO)
        ├─ onGameStart: NAO chama followCreature()
        ├─ init(): registra teclas WASD para mover camera
        ├─ init(): registra Q/E para mudar piso
        └─ Tela limpa: apenas o mapa renderizado + camera livre
```

---

## Decisoes Arquiteturais

1. Nenhuma linha de C++ sera alterada sem autorizacao do Arquiteto
2. Todo progresso sera registrado neste arquivo
3. Os 4 Marcos sao estritamente sequenciais
4. **Camera livre sera implementada 100% em Lua** — nao precisa modificar C++
5. **Autologin GM sera implementado 100% em Lua** — modificando entergame.lua
6. **Desativacao de HUD sera por modificacao de .otmod** — `autoload: false`

