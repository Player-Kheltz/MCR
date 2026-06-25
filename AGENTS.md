# AGENTS.md — Regras de Ouro do Assistente MCR

> Regras consolidadas baseadas na prática, para maximizar precisão e minimizar retrabalho.
>
> **Este arquivo é um ponteiro.** Cada tópico tem seu próprio arquivo modular em `docs/rules/`.

---

## Antes de Começar

| Passo | Ação |
|---|---|
| 0 | **⚠️ LIMPEZA OBRIGATÓRIA:** `taskkill /f /im canary-sln.exe` + `taskkill /f /im python.exe` + remover `.bridge_pid` e `.watchdog_pid` |
| 1 | Leia `docs/MCR - Instruções/DevLog/Pendências.md` — estado atual do projeto |
| 2 | Verifique `python scripts/auto.py checkpoint show` — sessão anterior |
| 3 | Leia `docs/rules/licoes.md` — lições aprendidas recentes |
| 4 | Execute rotina de intercâmbio → `docs/rules/intercambio.md` |

## Durante o Desenvolvimento

| Contexto | Consulte |
|---|---|
| Fluxo diário (comandos, operações massa, design, validação, commits, limpeza) | `docs/rules/workflow.md` |
| Compilação (Canary VS 2022, OTClient VS 2026) | `docs/rules/compilacao.md` |
| Encoding UTF-8 (C++, Lua, XML, MySQL) | `docs/rules/encoding.md` |
| Dúvidas técnicas do projeto | `docs/CATALOG.md` |
| Problemas conhecidos | `docs/TROUBLESHOOTING.md` |

## Ao Finalizar

| Tarefa | Como |
|---|---|
| Salvar checkpoint | `python scripts/auto.py checkpoint save --auto` |
| Registrar lições | Via `scripts/lesson.py` |
| Compartilhar com Hub do Lojista | Veja `docs/rules/intercambio.md` |
| Sincronizar docs | `python scripts/auto.py sync` |
| Verificar tudo | `python scripts/auto.py verify` |

## Capacidades Autônomas

O assistente pode executar sem supervisão: `docs/rules/autonomia.md`

## Sistema de Auto-Aprendizado (v2.0)

O assistente agora possui um sistema de conhecimento que cresce com o tempo:

| Ferramenta | Função | Como usar |
|:-----------|:-------|:----------|
| `scripts/find_example.py` | Encontra exemplos reais no código | `python scripts/find_example.py "criar NPC" --project . -k 3` |
| `scripts/auto_learn.py` | Registra e recupera aprendizados | `python scripts/auto_learn.py recall "criar dominio"` |
| `scripts/win_tools.py` | Operações Windows seguras | `python scripts/win_tools.py system_info` |
| `scripts/rag_query.py` | Busca semântica no código | `python scripts/rag_query.py "habilidades fire" --context-only` |

**Fluxo Autônomo Completo:**
1. `find_example.py` → encontra exemplos reais do que precisa fazer
2. `read` + `grep` → estuda os exemplos encontrados
3. Gera código seguindo o formato exato dos exemplos
4. `auto_learn.py learn` → registra o aprendizado
5. Da próxima vez, `auto_learn.py recall` → recupera experiências passadas

**Fora do Projeto MCR (qualquer projeto):**
- `find_example.py` detecta automaticamente o tipo de projeto
- `win_tools.py` fornece acesso seguro ao sistema Windows
- `auto_learn.py` acumula conhecimento entre projetos
- O sistema funciona para qualquer linguagem/tecnologia
