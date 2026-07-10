# Workflow.md — Fluxo de Trabalho MCR

> Parte do sistema modular `docs/rules/`. Consulte `../AGENTS.md` para visão geral.
> **📌 Fluxo da equipe (quem faz o quê):** `docs/rules/equipe.md`

---

## Antes de Tudo: Team Check-in

> **Sempre que iniciar uma tarefa, os 3 estão presentes:**
> - Cloud (orquestrador)
> - MCR-DevIA (executor)
> - Usuário (direção)

```bash
# Checklist obrigatório (início de sessão)
python scripts/mcr_devia/MCR_DevIA-Kernel.py status   # capacidade atual
# Leia AGENTS.md (raiz) e docs/rules/licoes.md
```

---

## 📡 COMUNICAÇÃO: JSON IPC (NUNCA shell com aspas)

```python
import json, subprocess
cmd = {"cmd": "perguntar", "args": ["pergunta"]}
with open("sandbox/.mcr_cmd.json", "w", encoding="utf-8") as f:
    json.dump(cmd, f, ensure_ascii=False)
r = subprocess.run(["python", "scripts/mcr_devia/MCR_DevIA-Kernel.py",
    "--json", "sandbox/.mcr_cmd.json"], capture_output=True, text=True, timeout=300)
resposta = r.stdout  # COMPLETO, sem truncamento
```

## 🧠 FLUXO MENTE-CORPO (toda execução)

```
USUÁRIO → perguntar("algo")
    ↓
[1] KG PRE-CHECK: se < 2 lessons → weblearn pesquisa
[2] MENTE.think(): conselho delibera com memória pessoal
[3] ORQUESTRADOR: template universal + fragmentação
[4] AUTO-REVISOR: heurística verifica classes suspeitas
[5] AUTO-WEB: se resposta errada → weblearn + regenera
[6] MENTE.learn(): autoavalia qualidade + atualiza scores
[7] AUTO-REVIEW: 20% chance → analisa código fonte
    ↓
RESPOSTA ← Completa, verificada, aprendizado registrado
```

## Durante o Desenvolvimento

### Regra: MCR-DevIA é o executor padrão

| Tarefa | Quem executa | Se falhar |
|--------|-------------|-----------|
| Criar arquivo | `MCR: write` (JSON IPC) | Cloud faz manual |
| Editar código | `MCR: edit` (JSON IPC) | Cloud `edit` manual |
| Analisar código | `MCR: analisar` | Cloud analisa |
| Buscar em arquivos | `MCR: grep`/`glob` | Cloud tool |
| Perguntar/Explicar | `MCR: perguntar` (JSON IPC) | Cloud explica |
| Aprender da web | `MCR: weblearn` (pesquisa + KG) | Cloud websearch |
| Auto-revisão | `Auto-Revisor` (heurística, pós-resposta) | Automático |
| Registro no KG | `MCR: ensinar` | **NUNCA pular** |

### ⚠️ ARMADILHAS (NUNCA FAZER)

| Armadilha | Consequência | Solução |
|-----------|-------------|---------|
| Shell com aspas | Erro de parsing | Use JSON IPC |
| `resposta[:2000]` | Truncamento | Use resposta COMPLETA |
| FAST como validador | Aceita tudo ("A") | Use heurística |
| Lista fixa de classes | Falso positivo | Contexto determina |
| Template específico | Roteamento errado | Use `perguntar` universal |
| Cache sem revisão | Resposta desatualizada | FAST verifica antes |
| V12 como fallback | Resposta genérica | Use Orquestrador + Mente |
  → Cloud propõe abordagem
  → MCR-DevIA opina (perguntar "o que voce acha?")
  → Time decide
  → MCR-DevIA executa (build/patch)
  → Cloud verifica
  → MCR-DevIA registra no KG (ensinar)
```

---

## Commits

```
git add <arquivos>
git commit -m "tipo(escopo): descricao"
```

- Uma alteração por commit
- Não misture correções
- Se alterar comportamento, atualize docs no mesmo commit

---

## Limpeza de Processos — REGRA ABSOLUTA

### Checklist Obrigatório

**No INÍCIO de toda resposta (antes de QUALQUER outra ação):**
```python
import subprocess, os
subprocess.run(["taskkill", "/f", "/im", "canary-sln.exe"], capture_output=True)
subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True)
for f in [".bridge_pid", ".watchdog_pid"]:
    if os.path.exists(f): os.remove(f)
```

**Ao FINAL de toda resposta:**
1. Verificar se servidor foi desligado (`python scripts/server_manager.py status`)
2. Verificar se bridge foi desligado
3. Remover arquivos PID órfãos

### Regra de Ouro
> Se alguém do time iniciou um processo, DEVE matá-lo antes de encerrar.
> O servidor e bridge SÓ rodam quando explicitamente solicitado pelo usuário para TESTE.

---

## Troubleshooting

Problemas comuns estão em `docs/TROUBLESHOOTING.md`.
Antes de investigar do zero, pergunte ao MCR-DevIA: `perguntar "ja viu este erro X?"`. O KG pode ter a solução.
