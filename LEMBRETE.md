# LEMBRETE.md — Checklist de Abertura

## 🚀 SEMPRE AO INICIAR

```bash
# 1. Matar processos antigos
taskkill /f /im python.exe
taskkill /f /im canary-sln.exe

# 2. Estado do MCR-DevIA
python scripts/mcr_devia/MCR_DevIA-Kernel.py status

# 3. Ler regras (AGENTS.md na raiz do projeto)
```

## 📡 COMUNICAÇÃO COM MCR-DevIA

**NUNCA** use shell com aspas. Use **JSON IPC**:

```python
import json, subprocess
cmd = {"cmd": "perguntar", "args": ["pergunta"]}
with open("sandbox/.mcr_cmd.json", "w", encoding="utf-8") as f:
    json.dump(cmd, f, ensure_ascii=False)
r = subprocess.run(["python", "scripts/mcr_devia/MCR_DevIA-Kernel.py",
    "--json", "sandbox/.mcr_cmd.json"], capture_output=True, text=True, timeout=300)
resposta = r.stdout  # COMPLETO, sem truncamento
```

## ⚠️ ARMADILHAS

- NUNCA usar `resposta[:2000]` — resposta truncada
- NUNCA usar FAST como validador — aceita tudo
- NUNCA usar lista fixa de classes — heurística é melhor
- NUNCA confiar em V12 sozinho — usar Orquestrador + Mente

## 📋 TAREFAS PENDENTES

(Atualizar ao final da sessão)
