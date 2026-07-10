# 2026-06-23 — RAG + Encoding

## Decisao
Indexar o codigo fonte (Canary/src, OTClient, scripts) em chunks de 2000 chars com overlap de 200, usando nomic-embed-text para embeddings. Saida do bridge em Latin-1 para compatibilidade com o protocolo.

## Motivo
- RAG permite busca semantica no codigo: perguntas em linguagem natural encontram chunks relevantes
- nomic-embed-text: 768 dimensoes, roda localmente (274MB), precisa o suficiente para o projeto
- Latin-1 na saida: o servidor e o protocolo Tibia usam Latin-1 (toLatin1()), UTF-8 causava caracteres garbados
- Leitura do chat_in.txt como UTF-8: o servidor escreve UTF-8 no arquivo

## Alternativas rejeitadas
- ChromaDB: mais complexo, exigiria instalar pacotes. JSON + numpy resolve para 2000 chunks
- Apenas tf-idf: menos preciso que embeddings semanticos
- UTF-8 na saida: causava � nos acentos no jogo

## Referencias
- `scripts/rag_indexer.py` — indexador
- `scripts/rag_query.py` — consulta
- `scripts/bridge_auto.py` — encoding Latin-1 na funcao send_out
