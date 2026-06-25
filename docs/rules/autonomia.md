# Autonomia.md — Capacidades Autônomas MCR

> Parte do sistema modular `docs/rules/`. Consulte `../AGENTS.md` para visão geral.

O assistente possui capacidade autônoma de:
- Compilar servidor e cliente (VS 2022 / VS 2026)
- Gerenciar bridge e watchdog
- Indexar RAG automaticamente
- Criar lições aprendidas
- Gerenciar checkpoint de sessão
- Alternar entre modo cloud e local (via `opencode.local.json`)
- Buscar em arquivos via `scripts/local_search.py` (substituto local do grep)

> **⚠️ Regra:** Prefira SEMPRE `scripts/local_search.py` ao grep built-in.
> O grep só deve ser usado quando o local_search falhar ou não der conta.

Ver `Scripts/README_AUTONOMY.md` para documentação completa do sistema autônomo.
