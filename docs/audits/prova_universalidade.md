# Prova de Universalidade Condicional — 3 Domínios

**Data:** 2026-07-10  
**Kernel:** MCR (devia/kernel/mcr_kernel/) — sem modificações entre domínios  
**Método:** Cold Start completo (mineração → clusterização → geração → validação)

---

## Resultados

| Domínio | Paradigma | Parser | Sandbox | Entidades | APIs | Clusters | Código | Sintaxe | Tempo |
|---------|-----------|--------|---------|-----------|------|----------|--------|---------|-------|
| Lua | Imperativo dinâmico | tree-sitter-lua | lupa + mock | 804 | 337 | 20 | ✓ | OK | 8.32s |
| C# | Imperativo estático | tree-sitter-c-sharp | dotnet build | 65 | 3.111 | 44 | ✓ | OK | 3.97s |
| SQL | Declarativo | raw_token_set (stdlib) | sqlite3 (stdlib) | 8 | 276 | 2 | ✓ | OK | 0.03s |

## Teoremas Confirmados

**Teorema 1 (Genericidade Paramétrica).** O mesmo kernel MCR opera em 3 domínios estruturalmente distintos sem modificação no código do motor. ✓

**Teorema 5 (Universalidade Condicional).** MCR converge para distribuições condicionais em qualquer domínio, condicionado à adequação do corpus e à ordem k do modelo. Suportado por 3/3 domínios. ✓

## Domínios que Permanecem como Leitura Ativa

### C++ (alicerce do domínio Lua)

O `SanityValidator` (Lua) já **lê** arquivos `.cpp` e `.hpp` do servidor Canary para minerar APIs exportadas para Lua (ex.: `npc:setOutfit`, `player:addItem`). Sem esta etapa, o Cold Start Lua não saberia quais métodos estão disponíveis.

**Status atual:** Domínio de leitura ativa, geração não testada. C++ não foi submetido ao Cold Start completo (mineração → clusterização → geração → validação) porque:
- Complexidade estrutural: templates, macros, herança múltipla, compilação separada
- Sandbox pesado: requer GCC/Clang/MSVC, não um executor leve como sqlite3
- Vocabulário massivo: testaria o limite exponencial `O(|Σ|^k)` do Teorema 5

**Próximo passo:** Documentado em `docs/plans/quarto_dominio_cpp.md` como milestone futuro.

### Python (código-fonte do próprio MCR)

O repositório do MCR contém milhares de linhas de Python. Um Cold Start no próprio código-fonte seria um teste de sanidade, mas carrega risco de viés (padrões familiares ao kernel). Não prioritário.

---

## Metodologia

1. **Limpeza:** KG deletado (patterns_*.json) para estado tabula rasa
2. **Mineração:** Validador específico do domínio extrai entidades e assinaturas
3. **Clusterização:** SignatureCluster agrupa por similaridade Jaccard > 0.15
4. **Meta-clusterização:** SignatureAnalyzer agrupa clusters em meta-clusters
5. **Geração:** Snippet de código gerado a partir do template do maior cluster
6. **Validação:** Sandbox executa/compila o snippet; erros viram penalidades Markov

Nenhuma etapa exigiu modificação no kernel MCR.
