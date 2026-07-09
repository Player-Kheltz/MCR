# MCR Grimório

Ferramenta desktop para administração de servidores OTServ (Canary/OTServBR).

## Módulos

- **Dashboard** — Status, start/stop, log ao vivo
- **Database** — MySQL browser + busca de jogadores
- **Monsters** — 1656 monstros, 30 categorias, balance z-score
- **NPCs** — 1027 NPCs + gerador visual
- **Scripts** — TreeView, busca, linter Lua
- **Config** — Editor do config.lua
- **Spawns** — Scanner OTBM/XML
- **Items** — Catálogo de itens
- **Protocol** — Opcodes + info servidor
- **Tools** — BalanceAnalyzer + Lua Validator
- **Logs** — Filtros erro/warning/all
- **Deploy** — Git + cmake + restart 1-clique
- **MCR Skills** — Domínios SPA + scanner
- **MCR Multi-Piso** — Config pursuit
- **MCR MountSummon** — Mount/summon scan
- **MCR NPCDialogue** — Gerador de diálogo
- **Quest Designer** — Criador SQH

## Build

```bash
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -o publish/
```

Gera `MCR.Grimorio.exe` em `publish/` — copie e execute em qualquer Windows.
