# MCRNPCv2 — Plano de Implementação
## NPC Vivo com HDC + SDM + Active Inference

### Filosofia
Preservar a alma do MCR (entropia como coordenada, criticalidade auto-regulada,
zero labels, zero gradientes) mas trocar Markov chain por HDC+SDM+Active Inference
como motor de aprendizado.

---

### Arquitetura

```
Percepção (HDC) → Memória (SDM + MDL) → Ação (Active Inference)
       ↕                                      ↕
    Entropia multi-nível              Criticalidade (0.2 < ent < 0.7)
       ↕                                      ↕
    Rede de NPCs (broadcast local/global)
       ↕
    Mapa do Tibia (regions_map.txt, 33 regiões)
```

### Componentes

| Fase | Arquivo | O que faz | Linhas |
|------|---------|-----------|--------|
| 0 | `hdc_core.py` | HDVector (10K dim, binding, bundle, cosine) | ~200 |
| 0 | `sdm_core.py` | SDM (store/retrieve, MDL, 10K endereços) | ~200 |
| 1 | `mundo_tibia.py` | Parser regions_map.txt, pathfinding A* | ~250 |
| 2 | `percepcao.py` | HDC encoding do momento (posição, fala, hora, etc.) | ~200 |
| 3 | `npc_vivo.py` | MCRNPCv2: tick loop, Active Inference, fala, personalidade | ~300 |
| 4 | `rede_npcs.py` | Broadcast local/global entre NPCs | ~100 |
| - | `main_npc.py` | Game loop principal | ~150 |

### Mapas de Dados Disponíveis
- `E:\Projeto MCR\Canary\data\logs\regions_map.txt` — 33 regiões, coordenadas (x,y,z),
  escadas, ASCII walkable masks
- `cache/npc_knowledge.json` — Conhecimento de NPCs canônicos
- `nichos/tibia/gerados/*.lua` — NPCs gerados existentes
- `E:\Projeto MCR\Canary\data\logs\*.commands.log` — Logs de jogadores reais

### Objetivo Final
NPC que passe no Teste de Turing:
- Memória episódica de conversas (SDM)
- Personalidade consistente (HD base + traits + criticalidade)
- Reação a contexto do mundo (entropia multi-nível)
- Pró-atividade (Active Inference)
- Conhecimento do mapa (regions_map.txt)
- Aprendizado online sem esquecimento (MDL)

### Critério de Sucesso (Fase 0)
- HDC: binding A⊗B, unbind, bundle, cosine similaridade funcionam
- SDM: store/retrieve com >80% fidelidade em 100 episódios
- MDL: memória não cresce infinitamente para dados repetitivos
