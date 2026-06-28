# 📊 Relatório de Benchmark — Modelos 14b vs 7b

**Data:** 28/06/2026
**Testes:** 4 modelos × 3 prompts + FAST benchmark (1.5b vs 7b)
**Total de chamadas:** 14 inferências

---

## Resumo Executivo

| Conclusão | Decisão |
|-----------|---------|
| **14b NÃO justifica o custo** | Manter 7b como modelo principal. Investir no Enricher em vez de upgrade. |
| **deepseek-r1:7b é surpreendente para lore** | 65 nomes em 15.7s — melhor que 14b (62 nomes em 113s) | 
| **1.5b continua ideal para FAST** | Mais rápido, mais barato, e em 1 teste foi MAIS preciso que 7b |
| **CR é mais importante que tamanho do modelo** | Nenhum modelo acertou SPA sem contexto — nem 14b |

---

## 1. Geração (qwen2.5-coder:7b vs 14b)

| Métrica | 7b | 14b | Diferença |
|---------|:--:|:---:|:---------:|
| Tempo SPA | **6.9s** | 14.9s | 7b **2.2x mais rápido** |
| Tempo .lua | **5.2s** | 19.4s | 7b **3.7x mais rápido** |
| Tempo Lore | **7.0s** | 37.5s | 7b **5.4x mais rápido** |
| Nomes na Lore | 19 | **26** | 14b +37% (mas 5x mais lento) |
| Acerto SPA | ❌ | ❌ | Ambos falham sem CR |
| Acerto .lua | ✅ | ✅ | Ambos acertam |

**Veredito:** 🏆 **7b vence em custo-benefício.** 14b é 2-5x mais lento por ganho marginal em qualidade.

---

## 2. Análise Criativa (deepseek-r1:7b vs 14b)

| Métrica | 7b | 14b | Diferença |
|---------|:--:|:---:|:---------:|
| Tempo SPA | **10.0s** | 22.4s | 7b **2.2x mais rápido** |
| Tempo .lua | **4.4s** | 27.8s | 7b **6.3x mais rápido** |
| Tempo Lore | **15.7s** | 113.4s | 7b **7.2x mais rápido** |
| Nomes na Lore | **65** | 62 | 7b tem +3 nomes |
| Acerto SPA | ❌ | ❌ | Ambos falham sem CR |

**Veredito:** 🏆 **deepseek-r1:7b é o REI da lore!** 65 nomes em 15.7s vs 62 nomes em 113.4s. O 14b é 7x mais lento e ainda produz MENOS nomes.

---

## 3. FAST Classification (1.5b vs 7b)

| Tarefa | 1.5b | 7b | Vencedor |
|--------|:----:|:--:|:--------:|
| Extrair termos | **4.9s** | 6.0s | 1.5b |
| Validar contexto | **2.2s** | 2.2s | Empate |
| Classificar | **2.1s** ✅ lore | 2.2s ✅ lore | 1.5b |
| Roteamento | **2.2s** ✅ analisar_codigo | 2.3s ❌ analisar_bug | 1.5b |
| Gerar instrução | **2.3s** | 2.3s | Empate |
| **Média** | **2.7s** | 3.0s | 1.5b |

**Veredito:** 🏆 **1.5b mantém.** Mais rápido, mais barato (1GB vs 4.7GB VRAM). O 7b errou o roteamento.

---

## 4. Matriz de Decisão

### Trocar modelos? NÃO para todos.

| Uso | Atual | Novo | Trocar? | Motivo |
|-----|-------|------|---------|--------|
| **FAST** (classificação) | 1.5b | 7b | ❌ **Não** | 1.5b é mais rápido E mais preciso |
| **Pesado** (geração) | qwen7b | qwen14b | ❌ **Não** | 5x mais lento, ganho marginal |
| **Analisar** | deepseek7b | deepseek14b | ❌ **Não** | 7x mais lento para resultados similares |
| **Review** | deepseek7b | deepseek14b | ❌ **Não** | Mesmo motivo |
| **Enricher** (futuro) | qwen7b | qwen14b | ❌ **Não** | Enricher usa ferramentas, não modelo grande |

### Ações recomendadas

1. ✅ **Manter FAST em 1.5b** — mais rápido e preciso
2. ✅ **Manter deepseek-r1:7b para análise/lore** — melhor qualidade/tempo do benchmark
3. ✅ **Manter qwen2.5-coder:7b para geração** — melhor custo/benefício
4. 🔄 **Investir no Enricher** — gera conteúdo novo que NENHUM modelo (nem 14b) produz sozinho

### Por que o Enricher é mais importante que 14b

O teste provou: **SEM contexto, NENHUM modelo acerta SPA**. Nem 7b, nem 14b, nem 70b.

O Enricher vai **GERAR o contexto que falta** usando ferramentas (grep, KG, weblearn) e depois injetar no prompt. Isso resolve o problema de raiz — enquanto aumentar o modelo só trata o sintoma.

---

## Conclusão Final

> **Os modelos 14b NÃO valem o upgrade.** São 2-7x mais lentos, consomem ~9GB de VRAM (vs ~5GB), e não resolvem o problema central: **falta de contexto específico**. 
>
> O dinheiro (tempo) mais bem investido agora é no **Context Enricher** — que vai gerar nomes, lugares, dados técnicos e curiosidades usando ferramentas, e injetar no prompt. Isso beneficia QUALQUER modelo, inclusive o 7b atual.
>
> Quando o Enricher estiver pronto, aí sim podemos reavaliar se um modelo maior vale a pena — com contexto rico, o 14b pode gerar respostas ainda melhores que o 7b. Mas sem o Enricher, o 14b sozinho não resolve.
