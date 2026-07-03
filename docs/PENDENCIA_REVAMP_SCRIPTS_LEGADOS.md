# Pendência: Revamp de Scripts Legados

## Contexto
Durante a padronização do uso de IA no MCR-DevIA, identificamos **11 scripts legados** que fazem chamadas diretas à API do Ollama com modelos hardcoded (`qwen2.5-coder:7b`, `deepseek-r1:7b`).

## Scripts a Revisar

| # | Arquivo | Hardcoded | Função | Suspeita |
|---|---------|-----------|--------|----------|
| 1 | `crew_deepseek.py` | deepseek-r1:7b + qwen7b | Validador com fallback | **Pode ser útil** — substituir por router |
| 2 | `crew_pattern.py` | qwen2.5-coder:1.5b | Pattern matching com IA | Pode ser substituído por CR |
| 3 | `mcr_knowledge.py` | qwen2.5-coder:7b | Gerenciamento de conhecimento | **Pode ser útil** — integrar ao KG |
| 4 | `mcr_agent.py` | qwen2.5-coder:7b | Agente autônomo | Substituído por pipeline |
| 5 | `mcr_autobuild.py` | qwen2.5-coder:7b | Auto build | Legado, não usado |
| 6 | `mcr_supervisor.py` | qwen2.5-coder:7b | Supervisor antigo | Substituído por supervisor.py |
| 7 | `mcr_observatory_v2.py` | qwen2.5-coder:7b | Observatório | Legado? |
| 8 | `super_fragmentador.py` | Multi-modelos | Fragmentação de texto | **Pode ser útil** — integrar ao Orquestrador |
| 9 | `mcr_learning_scan.py` | qwen2.5-coder:7b | Scan de aprendizado | Legado |
| 10 | `mcr_scriptbuilder.py` | qwen2.5-coder:7b | Builder de scripts | Legado |
| 11 | `mcr_ultimate_upgrade.py` | qwen2.5-coder:7b | Upgrade massivo | Legado (uma vez só) |
| 12 | `corrida_final_absoluta.py` | qwen2.5-coder:7b | Teste massivo | Legado |
| 13 | `mcr_auto_improve.py` | qwen2.5-coder:7b | Auto melhoria | **Pode ser útil** |
| 14 | `input_pipeline.py` | OLLAMA_URL | Pipeline de input antigo | Substituído por pipeline_executor.py |

## Ação Necessária
1. Verificar se cada script ainda funciona (teste básico)
2. Se útil: substituir chamadas hardcoded pelo router padronizado
3. Se legado/não usado: arquivar ou remover
4. Se substituído: apontar para o módulo atual
