# AGENTS.md — Regras de Ouro do Assistente (REDIRECT)

> **Este arquivo foi movido.** Consulte a versão atualizada na raiz do projeto:
> **`E:\Projeto MCR\AGENTS.md`**
>
> As regras modulares continuam em `docs/rules/`.

---

## Atalho Rápido

```bash
# Comunicação com MCR-DevIA (sempre via JSON IPC)
python MCR_DevIA-Kernel.py --json sandbox/.mcr_cmd.json

# Exemplo: perguntar algo
echo '{"cmd":"perguntar","args":["minha pergunta"]}' > sandbox/.mrc_cmd.json
python scripts/mcr_devia/MCR_DevIA-Kernel.py --json sandbox/.mcr_cmd.json

# Estado do sistema
python scripts/mcr_devia/MCR_DevIA-Kernel.py status
```
