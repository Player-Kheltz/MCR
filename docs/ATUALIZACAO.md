# ATUALIZAÇÃO — Julho 2026 (Unificação)

## v2.0 — "Unificação" (2026-07-13)

### Arquitetura

- **1 pipeline unificada** substitui 5 pipelines competidoras
- Nova classe `MCR` em `mcr/mcr.py` (657 linhas)
- 5 estágios: perceber → decidir → executar → avaliar → aprender
- Motor Markov intacto (movido para `mcr/motor/`)
- Equação MCR intacta (movida para `mcr/equacao/`)

### Estrutura

- 6 novos diretórios: `motor/`, `equacao/`, `ferramentas/`, `autonomia/`, `qualidade/`, `servicos/`
- Tibia e Visual são plugins em `ferramentas/`
- Bootstrap inclui nova estrutura

### Limpezas

- `MCRFilosofia` removido (autocomplete Markoviano, não reflexão real)
- Dispatch `if/elif` → `dict` em `mcr_world_system.py`
- `vocabulario_unico` corrigido em `dialogue_trainer.py` (0 → 4959)
- `MCRThreshold` decorativo simplificado

### Deletados

- `logwatcher_bridge.py`, `shadow_dotnet.py` (zero imports)
- `fix_mcr_devia_v2.py`, `npc_vivo.py` (dead code / imports quebrados)

### Testes

- 14/14 classificação de ações
- 20/20 imports verificados
- Geração de código Lua válido confirmada
- SanityValidator: 6445 APIs, 0 desconhecidas

### Limitações Conhecidas

Ver `README.md` e `MCR_WHITEPAPER_PT.md` §12 para lista completa.
