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

### Sessão 2026-06-30 — Deep Analysis + Correções
- [x] **Deep Analysis** — anti-patterns (grep) + revisão LLM de funções
- [x] **Correção de contagem** — regex mutuamente exclusivos (9+36=45)
- [x] **Legado filtrado** — mcr_devia.py excluído de sugestões
- [x] **Contexto rico** — mostra linha anterior para cada `except: pass`
- [ ] **EMERGIR Direcionado** — problema do usuario → tags → KG → solucao
- [x] **Dashboard unificado** — SSE server + 3 abas (LIVE/EMERGIR/CONSCIÊNCIA) + SELF
- [x] **API endpoints** — emergir, kg, contexto, conversa, self
- [x] **EMERGIR V4** — fragmentador 4 seções + Z expandido + anti-alucinação
- [x] **Self-Study** — escaneia código, detecta melhorias, gera sugestões
- [x] **KG multi-arquivo** — cada ctx em arquivo separado (22 ctx files)
- [x] **Refatoração master_agent.py** — 1.838 → 894 linhas (emergir, self_study, task_executor)
- [x] **Self-Study com memória** — compara scans para evitar repetir sugestões
- [ ] **EMERGIR Direcionado** — problema do usuario → tags → KG → solucao
