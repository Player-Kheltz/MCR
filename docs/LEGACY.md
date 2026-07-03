# LEGACY — Arquivos Movidos para Legado

Este documento registra o que foi movido para `/Legado/` e por quê.
Tudo aqui é **código histórico** — preservado para referência, não para uso ativo.

---

## Legado/sandbox/ — Scripts temporários do sandbox

**501 arquivos movidos** em 2026-06-30.

| Categoria | Quantidade | Exemplos |
|-----------|:----------:|----------|
| `_test*.py` | 37 | Testes descartáveis usados uma vez |
| `fix_*.py` | 47 | Scripts de correção pontual |
| `_fix_*.py` | ~20 | Correções de sintaxe via Python |
| `mcr_crew_v*.py` | 6 | Versões antigas do sistema de crew |
| `corrida_*.py` | 5 | Benchmarks comparativos de modelos |
| `ensinar_*.py` | 10 | Ensino em lote para o Knowledge Graph |
| `bench*.py` | 2 | Benchmarks de performance |
| `_resposta_*.txt` | 14 | Logs de respostas de testes cegos |
| Outros `.py` | ~360 | Scripts diversos de uso único |
| `.txt` | ~46 | Logs, análises, lore gerada |
| `.json` | ~24 | Dados de benchmark e cache |
| `.lua` | 3 | NPCs gerados (mergulhador, comerciante, vendedor) |

**Motivo**: Poluição do diretório de runtime. Esses scripts foram executados
uma vez e nunca mais usados. Mantidos em Legado para referência histórica.

---

## Legado/engine/ — Pipeline engine experimental

**5 arquivos, ~1.457 linhas, 11 classes** — marcado EXPERIMENTAL.

O sistema `engine/` era uma tentativa de criar um pipeline paralelo ao
`agent_loop.py`. A correção real foi de ~30 linhas no `agent_loop.py`,
tornando o engine/ obsoleto.

Arquivos:
- `executor.py` — Executor do pipeline
- `gap_detector.py` — Detector de lacunas
- `meta_creator.py` — Criador de metadados
- `task_analyzer.py` — Analisador de tarefas
- `__init__.py`

---

## Legado/strategies/ — Estratégias de geração

**7 arquivos** — abordagens diferentes para gerar NPCs, itens, etc.
Substituído pelo `agent_loop.py` + `npc_generator.py`.

---

## Legado/personalidades/ — Personalidades do Conselho (antigas)

**9 arquivos** — personalidades fixas em arquivos separados.
Substituído pelo `conselho.py` que gera personalidades sob demanda.

---

## Legado/modulos_antigos/ — Módulos anteriores à refatoração

| Arquivo | Linhas | Destino |
|---------|:------:|---------|
| `context_reinforcer.py` | ~180 | Restaurado em `modulos/context_reinforcer.py` |
| `context_enricher.py` | ~400 | Restaurado em `modulos/context_enricher.py` |
| `supervisor.py` | ~650 | Substituído por `modulos/supervisor.py` (versão atualizada) |
| `orquestrador.py` | ~900 | Substituído por `modulos/orquestrador.py` (versão atualizada) |

---

## Arquivos removidos permanentemente

| Arquivo | Motivo |
|---------|--------|
| `modulos/enricher.py` | Stub de 28 linhas, substituído por `context_enricher.py` |
