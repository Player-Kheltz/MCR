# MCR — Markov Chain Refactor

## Goal
Desenvolver um gerador procedural de conteúdo para Tibia/Canary TFS usando cadeias de Markov (stdlib apenas, zero GPU/LLM). O sistema extrai padrões de 2.689+ arquivos reais de treino (monstros + NPCs) e gera arquivos `.lua` originais e funcionais.

## Arquitetura

### 1. Extractors (`nichos/tibia/extract_monster.py`, `extract_npc.py`)
- Varrem recursivamente `data-otservbr-global/monster/` e `npc/`
- Extraem ~40 campos por monstro: experiência, health, outfit, loot, attacks, voices, etc.
- Resultado: `monster_db.json` (1652 monstros) e `npc_db.json` (989 NPCs)

### 2. Gerador Híbrido (`nichos/tibia/gerador_hibrido.py`)
- **Valores exatos**: os campos críticos (experience, health, outfit, raceId, etc.) vêm de templates reais do JSON DB, com ±15% de variação
- **Criatividade Markov**: loot (amostragem do pool real), voices/diálogo (Markov word-level bigram), nomes (Markov character-level 4-gram)
- **Estrutura**: segue exatamente o padrão Lua do TFS Canary (`Game.createMonsterType`, `Game.createNpcType`, `npcHandler:setMessage`, etc.)

### 3. Exemplos gerados

**Monstros**: Bulltauro, Arcador, Clompiro, Elemento, Crebre Colmenta
**NPCs**: Oliver Tybald, Woblind Sage, Dermoth, Scrusheryn, Quandur

Cada arquivo gerado é estruturalmente válido, com valores realistas e texto original.

## Arquivos do protótipo

| Arquivo | Função |
|---|---|
| `extract_monster.py` | Extrai dados de monstros para JSON |
| `extract_npc.py` | Extrai dados de NPCs para JSON |
| `gerador_hibrido.py` | Gera arquivos .lua usando DB real + Markov |
| `monster_db.json` | Base de conhecimento de 1652 monstros |
| `npc_db.json` | Base de conhecimento de 989 NPCs |
| `gerado/monster/*.lua` | Monstros gerados |
| `gerado/npc/*.lua` | NPCs gerados |
