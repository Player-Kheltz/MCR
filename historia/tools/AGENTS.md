# AGENTS.md — Regras Absolutas do Assistente MCR

> **LEIA O ARQUIVO INTEIRO ANTES DE QUALQUER AÇÃO.**
> Estas regras foram APRENDIDAS na prática, não inventadas.
> Violá-las causa retrabalho, alucinação ou perda de contexto.

---

## 🚨 CHECKLIST OBRIGATÓRIO — INÍCIO DE SESSÃO

```python
# 1. Matar processos anteriores (sempre!)
import subprocess, os
subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True)
subprocess.run(["taskkill", "/f", "/im", "canary-sln.exe"], capture_output=True)
for f in [".bridge_pid", ".watchdog_pid"]:
    if os.path.exists(f): os.remove(f)

# 2. Verificar estado do MCR-DevIA
# python MCR_DevIA-Kernel.py status

# 3. Ler AGENTS.md (este arquivo) e LEMBRETE.md
```

## 🚨 CHECKLIST OBRIGATÓRIO — FIM DE SESSÃO

```python
# 1. Registrar lição no KG
python MCR_DevIA-Kernel.py ensinar "<resumo>" "<oque>" "<solucao>" "<categoria>"

# 2. Limpar processos
taskkill /f /im python.exe; taskkill /f /im canary-sln.exe
```

---

## 📡 COMUNICAÇÃO — JSON IPC (SEMPRE)

**NUNCA** use shell com aspas, escaping ou pipes. Sempre use **JSON IPC**:

```python
import json, subprocess

# Criar comando
cmd_data = {"cmd": "perguntar", "args": ["minha pergunta"]}
with open("sandbox/.mcr_cmd.json", "w", encoding="utf-8") as f:
    json.dump(cmd_data, f, ensure_ascii=False)

# Executar via kernel
r = subprocess.run(
    ["python", "scripts/mcr_devia/MCR_DevIA-Kernel.py",
     "--json", "sandbox/.mcr_cmd.json"],
    capture_output=True, text=True, timeout=300
)
stdout = r.stdout  # Sempre completo, sem truncamento
```

**Regras:**
- `sandbox/.mcr_cmd.json` = comando de entrada
- `sandbox/.mcr_result.json` = status da execução
- `sandbox/.mcr_resposta.txt` = resposta completa (quando aplicável)
- Zero shell escaping, zero truncamento, UTF-8 seguro.

---

## 🧠 ARQUITETURA MENTE-CORPO

```
USUÁRIO → perguntar("algo")
    ↓
[1] KG PRE-CHECK: se < 2 lessons → weblearn pesquisa
[2] MENTE.think(): conselho delibera com memória pessoal
[3] ORQUESTRADOR: template universal "perguntar" + fragmentação
[4] AUTO-REVISOR: heurística verifica classes suspeitas
[5] AUTO-WEB: se FAST disser "resposta NAO atende" → weblearn + regenera
[6] MENTE.learn(): autoavalia qualidade + atualiza scores
[7] AUTO-REVIEW: 20% chance → MCR analisa próprio código fonte
    ↓
RESPOSTA ← Completa, verificada, aprendizado registrado
```

### Módulos principais

```
scripts/mcr_devia/
  MCR_DevIA-Kernel.py   ← Entry point (uso diário)
  kernel.py             ← Núcleo: CommandLoader + EventBus
  modulos/
    orquestrador.py     ← Motor de templates + fragmentação
    supervisor.py       ← Classificador + roteador universal
    mente.py            ← Conselho + memória + aprendizado
    memoria_conselho.py ← Memória individual com SCORE por membro
    auto_revisor.py     ← Revisão heurística pós-resposta
    conselho.py         ↑ Personalidades com memória
    kg.py               ↑ Knowledge Graph
    ia.py               ↑ Interface Ollama
    context_crew.py     ↑ 5 fontes de contexto (KG, Web, Docs, Código, WebLearn)
    watchdog.py         ↑ Monitora comandos/ + sandbox/
  comandos/             ↑ 46 comandos modulares
```

---

## 🔴 REGRAS DE OURO

### 1. USE JSON IPC PARA TUDO
Nunca use shell diretamente. Sempre crie `.mcr_cmd.json` e use `--json`.
Exceção: comandos simples como `status` ou `ensinar`.

### 2. RESPOSTAS SÃO COMPLETAS (sem [:2000])
O `cmd_perguntar.py` NÃO pode truncar respostas. Se vir `[:2000]`, remova.
A resposta completa é salva em `.mcr_resposta.txt`.

### 3. AUTO-REVISOR É HEURÍSTICO (não FAST)
O FAST é muito permissivo ("A" para tudo). Use heurística:
- Classe dentro de ```code``` = válida
- Classe contextualizada ("A classe X faz") = válida
- Nome composto 10+ chars com 3+ maiúsculas = suspeita

### 4. APRENDIZADO CONTÍNUO
- `weblearn` pesquisa web e salva no KG
- `Mente.think()` carrega memórias de ALTO SCORE
- `Mente.learn()` autoavalia e atualiza scores
- Se resposta < 500 chars ou FAST disser "errada" → weblearn + regenera

### 5. COMPARAÇÕES SEGUEM TESTE CEGO
```
1. Cloud escreve resposta PRIMEIRO (sem ler MCR)
2. MCR escreve resposta (sem ler Cloud)
3. SÓ ENTÃO comparar
```

### 6. ENSINE SEMPRE NO KG
Toda ação relevante DEVE ser registrada:
```bash
python MCR_DevIA-Kernel.py ensinar "<oque>" "<contexto>" "<solucao>" "<categoria>"
```

### 7. SUPERVISIONE, NÃO ASSUMA
Se MCR-DevIA errar: Cloud dá feedback específico (onde e por que errou).
MCR se auto-repara. NUNCA assuma sem o HUMANO autorizar.

---

## 📊 CAPACIDADES ATUAIS

| Componente | Qtde | Descrição |
|-----------|------|-----------|
| Comandos | 46 | `comandos/` modulares |
| Módulos | 18 | orquestrador, supervisor, mente, kg, ia, etc |
| Templates | 8+ | perguntar (universal), analisar_codigo, analisar_bug, conceito, lore |
| Fragmentação | Auto | Quebra respostas longas em seções (12+ fragmentos) |
| Mente | 9 membros | analista, critico, estrategista, arquiteto, etc |
| Memória | ∞ | Individual por membro, com SCORE de qualidade |
| Auto-revisor | Heurístico | Detecta classes suspeitas sem FAST |
| Auto-web | Gatilho | Pesquisa quando resposta é fraca ou errada |
| Watchdog | Sandbox | Monitora respostas e dispara auto-revisor |
| KG | 1900+ lessons | Conhecimento acumulado do projeto |
| ContextCrew | 5 fontes | KG, WebLearn, Docs, Código, Web |

---

## ⚠️ ARMADILHAS CONHECIDAS (NUNCA CAIR)

| Armadilha | Consequência | Como evitar |
|-----------|-------------|-------------|
| Shell com aspas | Erro de parsing, comando falha | Use JSON IPC |
| FAST como validador | Aceita tudo ("A" sempre) | Use heurística |
| Lista fixa de classes | Falso positivo | Use heurística contextual |
| `resposta[:2000]` | Resposta truncada | Remova o slice |
| Template específico | Roteamento errado | Use `perguntar` (universal) |
| V12 como fallback | Resposta genérica | Use Orquestrador + Mente |
| Cache sem revisão | Resposta desatualizada | FAST verifica antes de usar |

---

## 📁 ARQUIVOS DE SUPORTE

| Arquivo | Função |
|---------|--------|
| `docs/MCR_IDENTITY.md` | Identidade do projeto (injetada em templates) |
| `docs/lessons/recentes.md` | Lições recentes aprendidas |
| `sandbox/.mcr_cmd.json` | Comando JSON IPC |
| `sandbox/.mcr_result.json` | Resultado da execução |
| `sandbox/.mcr_resposta.txt` | Resposta completa |
| `sandbox/.mcr_metricas.json` | Métricas do Orquestrador |
| `sandbox/.mcr_devia/conselho_memoria/` | Memória individual dos membros |

---

## 💡 FLUXO PARA NOVAS TAREFAS

```
1. PARE e pergunte: "O MCR-DevIA pode fazer isso?"
2. Se SIM: use o comando apropriado (analisar, perguntar, etc)
3. Se NÃO: implemente, registre no KG, atualize AGENTS.md
4. Sempre use JSON IPC para comunicação
5. Sempre registre lições aprendidas
6. Sempre verifique se respostas não estão truncadas
```
