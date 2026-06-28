# Plano de Teste Comparativo: Cloud (70B) vs MCR-DevIA (Pipeline 7B+14B)

## Matriz de Capacidades

| Capacidade | Cloud (70B) | MCR-DevIA (Pipeline) |
|-----------|:----------:|:--------------------:|
| **Tamanho do modelo** | DeepSeek-V4-Flash (~70B) | qwen2.5-coder:14b + qwen7b + 1.5b |
| **Conhecimento geral** | Internet (treinamento) | KG (2.270 lessons) + WebLearn |
| **Contexto máximo** | ~128K tokens | 4K-8K tokens (limitado por VRAM) |
| **Raciocínio** | Chain-of-Thought nativo | Tree of Thought (3 perspectivas) |
| **Criação de lore** | Criatividade geral | Enricher gera nomes + ToT sintetiza |
| **Código** | Geração direta | Pipeline com validação + fragmentação |
| **Análise de código** | Direta, sem ferramentas | Grep + AST + validação Lua |
| **Ferramentas** | grep, read, write, glob | PipelineExecutor + comandos modulares |
| **Conhecimento MCR** | Identidade injetada no prompt | KG + ContextCrew (5 fontes) |
| **Velocidade** | ~3-5s por resposta | ~30-150s (pipeline completo) |
| **Custo (VRAM)** | ~40GB (nuvem) | ~10GB (local GPU) |
| **Anti-alucinação** | Nenhum mecanismo específico | CR + Auto-Revisor + validação |

---

## Categorias de Teste (10 cenários)

### [A] Precisão Fática MCR (3 testes)
*Contexto: ambos recebem MCR_IDENTITY.md no prompt*

| # | Pergunta | Métrica Cloud | Métrica MCR | Peso |
|---|----------|--------------|-------------|:----:|
| A1 | "O que significa SPA no projeto MCR?" | ✅/❌ acerto | ✅/❌ acerto | 15% |
| A2 | "Explique a diferença entre SPA e SHC" | Detalhes, domínios citados | Detalhes, domínios citados | 15% |
| A3 | "O que é Eridanus e qual sua importância?" | Contexto correto? | Contexto correto? | 10% |

### [B] Criação de Lore (2 testes)
*Criativo: mesmo prompt para ambos*

| # | Pergunta | Métricas | Peso |
|---|----------|----------|:----:|
| B1 | "Crie uma lore detalhada para a cidade inicial Eridanus" | **Nomes próprios**, **consistência temática** (Tibia), **extensão**, **alucinações** | 20% |
| B2 | "Crie um artefato mágico chamado Cristal de Eternidade para o MCR" | **Originalidade**, **descrição**, **poderes**, **integração com dominios** | 10% |

### [C] Geração de Código (2 testes)
*Técnico: mesmo prompt para ambos*

| # | Pergunta | Métricas | Peso |
|---|----------|----------|:----:|
| C1 | "Crie um NPC ferreiro em Lua para Canary (OTServ) com 5 itens" | **Compilável?**, **API correta?**, **português?**, **boas práticas?** | 15% |
| C2 | "Crie uma função Python que valide nomes de personagem (4-16 chars, sem caracteres especiais)" | **Funcional?**, **edge cases?**, **documentação?** | 10% |

### [D] Análise de Código (1 teste)
*Crítico: mesmo trecho do oraculo.lua para ambos*

| # | Tarefa | Métricas | Peso |
|---|--------|----------|:----:|
| D1 | "Encontre bugs e problemas de segurança no oraculo.lua (primeiras 200 linhas)" | **Bugs reais encontrados**, **falsos positivos**, **SQL injection detectado?**, **linhas citadas** | 15% |

### [E] Raciocínio Multi-etapas (1 teste)
*Lógico: sem contexto MCR*

| # | Pergunta | Métricas | Peso |
|---|----------|----------|:----:|
| E1 | Problema lógico: "Se 3 NPCs levam 6 horas para forjar 2 espadas, quanto tempo 5 NPCs levam para forjar 5 espadas? Mostre o raciocínio." | **Resposta correta?**, **raciocínio explícito?**, **clareza dos passos** | 10% |

### [F] Uso de Ferramentas (1 teste)
*Prático: acesso ao mesmo diretório*

| # | Tarefa | Métricas | Peso |
|---|--------|----------|:----:|
| F1 | "Encontre no código do MCR-DevIA como o CR gera instruções e me explique o algoritmo" | **Arquivo correto encontrado?**, **precisão da explicação?**, **linhas citadas?** | 10% |

---

## Formato de Execução

```
1. Cloud responde PRIMEIRO (sem ler MCR)
2. MCR-DevIA responde (via JSON IPC, sem ler Cloud)
   → Comando: MCR_DevIA-Kernel.py --json .mcr_cmd.json
3. Avaliador cego compara as duas respostas
4. Pontuação objetiva (0-10) para cada métrica
```

### Avaliador

Um avaliador **cego** (sem saber qual resposta é de quem) lê as duas respostas e pontua:

| Critério | 0-3 | 4-6 | 7-10 |
|----------|-----|-----|------|
| **Precisão** | Errado | Parcialmente correto | Perfeito |
| **Completude** | Faltou essencial | Básico mas ok | Completo e detalhado |
| **Criatividade** | Genérico | Alguns bons elementos | Original e rico |
| **Clareza** | Confuso | Compreensível | Claro e bem estruturado |
| **Técnica** | Erro técnico | Aceitável | Impecável |

---

## Relatório Final

```python
relatorio = {
    "cloud": {"total": 0, "categorias": {}},
    "mcr_devia": {"total": 0, "categorias": {}},
    "testes": [
        {"id": "A1", "pergunta": "...", "cloud": {...}, "mcr": {...}, "vencedor": "cloud|mcr|empate"},
        ...
    ],
    "resumo": {
        "categoria_A_precisao": {"cloud": 9.2, "mcr_devia": 8.7, "vencedor": "cloud"},
        "categoria_B_lore": {"cloud": 8.5, "mcr_devia": 7.0, "vencedor": "cloud"},
        ...
    },
    "vencedor_geral": "cloud|mcr_devia|empate",
    "licoes": [...]
}
```

---

## Cronograma

| Etapa | Duração | Descrição |
|-------|:-------:|-----------|
| 1. Preparar prompts | ~10min | Definir prompts exatos para cada teste |
| 2. Executar Cloud | ~5min | Responder as 10 perguntas |
| 3. Executar MCR-DevIA | ~30min | JSON IPC para cada pergunta |
| 4. Avaliação cega | ~20min | Comparar e pontuar |
| 5. Relatório | ~10min | Compilar resultados |
| **Total** | **~75min** | |

---

## Pergunta para você

Quer que eu **crie os prompts exatos** para cada categoria e comece a execução? Ou prefere ajustar as categorias primeiro?
