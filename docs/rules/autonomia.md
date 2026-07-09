# Autonomia.md — Funções Autônomas do Time

> Parte do sistema modular `docs/rules/`. Consulte `../AGENTS.md` para visão geral.
> **Contexto:** O time de 3 (Cloud + MCR-DevIA + Usuário) executa ações autônomas,
> mas NUNCA sem o conhecimento registrado no KG.

## Capacidades Autônomas

### MCR-DevIA (executa sozinho)
- `perguntar`, `analisar` — consulta inteligente (via JSON IPC)
- `ensinar` — registro no KG (obrigatório)
- `weblearn` — aprendizado da web (pesquisa → fragmenta → KG)
- `grep`, `read`, `write` — manipulação de arquivos
- `auto_revisor` — revisão heurística pós-resposta (embutido no Supervisor)
- `mente` — ciclo Mente-Corpo (think → learn → score)
- `compilar` — compilação de Canary e OTClient
- `system_scan`, `bugfinder` — diagnóstico do sistema

### Cloud (assume quando MCR falha 3x)
- `edit`, `write` — edição cirúrgica (quando MCR falha)
- `webfetch` — fallback quando `weblearn` falha
- **Sempre usar MCR-DevIA primeiro** (grep, read, analisar, perguntar)
- Decisões arquiteturais (consultando MCR + usuário)

### Ciclo de Aprendizado Autônomo (NOVO)

```
USUÁRIO → perguntar("algo")
    ↓
[1] PRE-CHECK KG: se < 2 lessons → weblearn pesquisa automaticamente
[2] MENTE.think(): conselho + memória pessoal com SCORE
[3] ORQUESTRADOR: template universal + fragmentação (sem limite)
[4] LLM: gera resposta
[5] AUTO-REVISOR: heurística (código=valido, contexto=valido, composto=suspeito)
[6] AUTO-WEB: se FAST disser "NAO atende" → weblearn + regenera
[7] MENTE.learn(): autoavalia + atualiza SCORE dos membros
[8] AUTO-REVIEW: 20% → MCR analisa próprio código fonte
    ↓
KG + MEMÓRIA atualizados ← Melhor a cada ciclo
```

## Regras de Autonomia

1. **Toda ação é registrada** via `ensinar` no KG
2. **NUNCA modificar fora do sandbox** sem confirmação
3. **JSON IPC é o padrão** para comunicação com MCR-DevIA
4. **Respostas SEMPRE completas** — truncamento `[:2000]` é proibido
5. **Auto-revisor usa heurística** (não FAST) — classes em código = válidas, contextualizadas = válidas
6. **Aprendizado web é automático** — se KG < 2 lessons sobre o tópico, weblearn dispara
7. **NUNCA deixar processos em background** — limpeza no início/fim
