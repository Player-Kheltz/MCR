# 2026-06-23 — Anti-alucinacao e Seguranca

## Decisao
Implementar sistema de bloqueio de perguntas sobre credenciais/senhas no template do bridge, e prompt de IA com regras estritas para nunca inventar dados.

## Motivo
- O modelo 1.5b inventou usuario e senha do MySQL quando perguntado (risco GRAVE de seguranca)
- Template bloqueia ANTES da IA processar (impede alucinacao na raiz)
- Prompt explicito "NUNCA invente dados, senhas, usuarios"
- .gitignore cobre arquivos sensiveis (bridge_*.txt, chat_*.txt, .rag_db)
- RAG sanitizado: remove linhas com password=, apiKey=, etc antes de indexar

## Alternativas rejeitadas
- Confiar apenas no prompt: insuficiente para modelo pequeno (1.5b)
- Remover IA totalmente: perderia qualidade das respostas
- Usar modelo maior sempre: 7b reduz mas nao elimina alucinacao

## Referencias
- `scripts/bridge_auto.py` — template_reply() com bloqueio + ANTI_HALLUCINATION_PROMPT
- `scripts/rag_indexer.py` — sanitize_text() + EXCLUDE_PATTERNS
- `.gitignore` — exclusao de arquivos sensiveis
