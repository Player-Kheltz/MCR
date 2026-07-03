# Manual de Operação Autônoma — MCR

## Comandos Rápidos

```powershell
# Subir tudo (server + bridge + watchdog)
python scripts\auto.py up

# Status de todos os sistemas
python scripts\auto.py status

# Diagnóstico e sugestões
python scripts\auto.py doctor

# Compilar servidor
python scripts\auto.py compile --server

# Reindexar RAG
python scripts\auto.py reindex
```

## Aliases (PowerShell)

```powershell
oc-dev      # OpenCode local (qwen2.5-coder:7b)
oc-up       # auto.py up
oc-status   # auto.py status
```

## Arquitetura

```
auto.py up
  → Server (canary-sln.exe)
  → Watchdog (bridge_watchdog.py)
    → Bridge v4 (bridge_auto.py)
      → Ollama (local)
        → qwen2.5-coder:7b (padrao)
        → qwen2.5-coder:1.5b (fallback)
        → nomic-embed-text (RAG)
```

## Recuperação

| Problema | Solução |
|---|---|
| Bridge morreu | Watchdog reinicia automaticamente em 15s |
| Servidor caiu | `auto.py up` reinicia tudo |
| Ollama offline | Bridge responde "Assistente indisponivel" |
| RAG desatualizado | `auto.py reindex` (ou watcher automático) |

## Manutenção

- Logs: `bridge_debug.log`, `bridge_watchdog.log`, `rag_watcher.log` (auto-rotacionados)
- RAG: `auto.py reindex` após alterações no código
- Lessons: `python scripts/lesson.py` para registrar decisões
