# Teste Bridge: Alucinações do Qwen 7B em Pergunta Técnica

## Data: 2026-06-23

## Contexto
O usuário fez um teste com o bot (Qwen 2.5 Coder 7B via Bridge), pedindo para
criar um arquivo .lua com TalkAction de fogos de artifício. O objetivo era
avaliar se o bot respondia corretamente sobre o projeto MCR.

## Resultado do Teste — 3 Falhas Críticas

| Falha | Exemplo | Causa Raiz |
|-------|---------|------------|
| **Não criou o arquivo** | Apenas descreveu o que fazer, não executou | Modelo não tem capacidade de criar arquivos, mas tentou fingir |
| **Estrutura errada** | Usou XML (`<talkaction words="...">`) quando o Canary usa revscript Lua | RAG não recuperou exemplos reais; conhecimento base não documenta o sistema |
| **APIs inventadas** | `addEffect()`, `increaseTime()`, `CONST_EFFECT_FIRESWELL`, `getMagicLevel()` como gate | Modelo preencheu lacunas com conhecimento genérico de TFS/OTX |

## Encaminhamento — Correções Aplicadas

1. **Hot Cache** (bridge_auto.py): Substituído word-overlap por Jaccard similarity
   com remoção de stopwords. Exige que a palavra mais longa da pergunta apareça
   na chave do cache para evitar falsos-positivos.
2. **Knowledge Base** (mcr_knowledge.txt): Adicionado:
   - Sistema de TalkActions (revscript, NÃO XML)
   - APIs Lua reais (sendMagicEffect, say, sendTextMessage, sendCancelMessage)
   - Lista de constantes CONST_ME_* para efeitos
   - Seção "O que o MCR NÃO é" para evitar alucinações
3. **Prompt** (bridge_auto.py): Adicionadas regras:
   - "Este é um servidor CUSTOMIZADO. APIs de outros projetos podem não existir"
   - "Use APENAS nomes exatos de funções do CONTEXTO DO CODIGO"
   - "Você NÃO pode criar, editar ou modificar arquivos"
4. **Temperature**: 0.3 → 0.1 (menos criatividade)
5. **Limiar RAG**: 0.55 → 0.65 (só contexto realmente relevante)
6. **Fallback**: qwen2.5-coder:1.5b → deepseek-coder:6.7b (1.5b alucinava muito)
7. **RAG Indexer otimizado**: batch_size 10→100, save a cada 50 arquivos,
   ThreadPoolExecutor com 4 workers para embeddings paralelos
8. **RAG Index corrigido**: adicionados diretórios
   `Canary/data/scripts/talkactions/`, `actions/`, `creaturescripts/` ao escopo
   (antes só indexava `data-canary/scripts/` que não contém talkactions)

## Resultado Final do Teste (23/jun)

Após todas as correções, o teste de integração simulando o fluxo completo
da bridge foi **APROVADO**:
- ✅ Formato revscript correto (TalkAction + onSay + register)
- ✅ Funções reais usadas (sendMagicEffect, CONST_ME_*)
- ✅ NENHUMA alucinação detectada (nem addEffect, XML, PlayerAccess, EffectIds)

## Lições Aprendidas

1. **O modelo 7B não era o problema** — a causa raiz era o RAG não indexar os
   diretórios certos + knowledge base incompleto + hot cache quebrado.
2. **Knowledge base precisa ser indexada no RAG**, não só no prompt — sem
   indexação, o RAG não encontra o conteúdo mesmo estando disponível.
3. **Indexador precisa de batch grande e paralelismo** — com batch_size=100 e
   4 workers paralelos, 3.677 chunks foram embedados em ~20s (vs. 10+ min antes).
4. **deepseek-coder:6.7b é equivalente ao qwen2.5-coder:7b em qualidade** mas
   ~2x mais lento. Manter qwen como principal, deepseek como fallback.
