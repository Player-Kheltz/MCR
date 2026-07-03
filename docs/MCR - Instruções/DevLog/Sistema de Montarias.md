>> CATALOG tags=mounts, summon, devlog updated=2026-06-23
# DevLog — Sistema de Montarias (MountSummon)

## Contexto
Montarias no MCR são mais que visuais: ao desmontar, a montaria vira um summon/pet persistente com HP, inventário e IA. O sistema substitui o comportamento padrão do Tibia (montaria some ao desmontar).

## Evolução

### v1.0 (Original)
- Desmontar → criava `CriaturaSPA` em tile livre adjacente
- Montar → removia o summon
- Eventos C++: `CREATURE_EVENT_DISMOUNT/MOUNT`
- `hasFreeAdjacentTile()` no C++
- Persistência básica (KV mount-summon: active, mount-id, mount-client-id)

### v2.0 (Atual — versão expandida)
**O que foi adicionado:**

| Funcionalidade | Descrição |
|---|---|
| **HP tracking** | Salva/restaura HP da montaria entre sessões |
| **Estado moribundo** | Quando a montaria morre, 60s de timer antes da morte definitiva |
| **!montarias** | Comando que lista montaria atual, estado, HP, total no estábulo |
| **!portal** | Placeholder para troca de montaria com popup |
| **!todasmontarias** | Comando GM para dar todas as montarias (1-150) |
| **force=true** | Montaria nasce no tile do jogador ignorando colisão |
| **teleportTo** | Move para tile livre (em vez de `startAutoWalk` que não existe na API) |
| **Persistência expandida** | KV salva mount-state (mounted/summoned), mount-hp, pet-id |

### O que tentamos e não deu certo
- `startAutoWalk` no summon — API não existe em `Monster`, deu erro "attempt to call method 'startAutoWalk' (a nil value)"
- `isWalkingToPosition` para follow do mount — removido em favor do movimento nativo

### Pendências
- Troca de montaria via portal com animação (anda até o portal, entra, nova sai)
- Transferência de itens entre montarias
- Loadouts salvos por montaria
- Interface OTUI para o estábulo

## Comandos
- `!todasmontarias` — GM, concede montarias 1-150
- `!montarias` — lista estado atual
- `!portal` — troca de montaria (placeholder)
