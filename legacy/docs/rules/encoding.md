# Encoding.md — Padrão UTF-8 MCR

> Parte do sistema modular `docs/rules/`. Consulte `../AGENTS.md` para visão geral.

| Tipo | Padrão | Ferramenta |
|---|---|---|
| `.cpp`/`.hpp` | UTF-8 literal com `/utf-8` no MSVC | N/A (compilador) |
| `.lua` (servidor e cliente) | UTF-8 sem BOM | Editor |
| `.xml` | UTF-8 real + `encoding="UTF-8"` | Editor |
| Saída protocolo | `toLatin1()` em `sendCancelMessage` e `sendTextMessage` | C++ |
| Banco de dados | `utf8mb4` | Config MySQL |
