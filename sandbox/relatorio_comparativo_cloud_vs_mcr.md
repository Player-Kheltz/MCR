# 🧪 RELATÓRIO COMPARATIVO: Cloud (70b) vs MCR-DevIA (7b + Pipeline)

**Data:** 27/06/2026
**Metodologia:** Teste cego — cada modelo respondeu SEM ler a resposta do outro. 3 perguntas.

---

## Resumo

| Métrica | Cloud (70b) | MCR-DevIA (7b + Pipeline) | Vencedor |
|---------|-------------|---------------------------|----------|
| Precisão factual (siglas) | 3/3 ✅ | 3/3 ✅ | Empate |
| Tempo médio | ~3s (estimado) | 26.4s | Cloud |
| Nomes próprios (total) | 36 | 25 | Cloud |
| Extensão média | 890 chars | 1.258 chars | MCR-DevIA |
| Contexto MCR (Tibia) | 3/3 ✅ | 3/3 ✅ | Empate |
| Custo computacional | Alto (70b) | Baixo (7b) | MCR-DevIA |

---

## TESTE 1: "O que é SPA no MCR?"

### Cloud (70b)
**Tempo:** ~3s | **Tamanho:** 480 chars

> "SPA no projeto MCR significa **Sistema de Progressão do Aventureiro**. É um sistema de evolução de personagem baseado em **domínios elementais** (Fogo, Gelo, Terra, Energia), onde cada um tem 25 níveis de progressão. Diferente de sistemas tradicionais de leveling, o SPA permite que o jogador especialize em áreas específicas de conhecimento, acumulando experiência por domínio e desbloqueando habilidades contextuais (SHC) conforme avança. Foi projetado para o servidor Canary (OTServ) do projeto MCR — um servidor customizado de Tibia."

✅ SPA = Sistema de Progressão do Aventureiro
✅ Menciona domínios (Fogo, Gelo, Terra, Energia)
✅ Menciona SHC
✅ Menciona Canary/OTServ/Tibia
❌ Não menciona 23/24/25 números dos domínios

### MCR-DevIA (7b + Pipeline)
**Tempo:** 23.6s | **Tamanho:** 356 chars

> "SPA (Sistema de Progressão do Aventureiro) no Projeto MCR é um sistema interativo que ajuda os jogadores a avançar e melhorar suas habilidades em um servidor baseado em Canary (OTServ). Este sistema gerencia o progresso dos jogadores, permitindo que eles ganhem experiência, aumentem seus níveis e aprimorem suas competências conforme interagem com o jogo."

✅ SPA = Sistema de Progressão do Aventureiro
✅ Menciona Canary/OTServ
⚠️ Mais genérico, sem detalhes dos domínios
❌ Resposta mais curta

**Veredito:** ✅ Cloud vence em profundidade de detalhes

---

## TESTE 2: "O que é .lua?"

### Cloud (70b)
**Tempo:** ~3s | **Tamanho:** 520 chars

> "No projeto MCR, `.lua` refere-se a **scripts na linguagem Lua** usados pelo OTClient. O OTClient utiliza Lua como linguagem de script para interface do usuário (OTUI), eventos do cliente, personalização de layouts e ações do jogador. Os arquivos `.lua` estão principalmente em `OTClient/src/` e `OTClient/data/`. Diferente do servidor (Canary, em C++), o OTClient expõe APIs em Lua para modding e customização. Não confundir com 'Lua' (satélite)."

✅ .lua = linguagem de programação
✅ Menciona OTClient especificamente
✅ Menciona diretórios reais
✅ Alerta sobre confusão com satélite

### MCR-DevIA (7b + Pipeline)
**Tempo:** 28.4s | **Tamanho:** 292 chars

> "O arquivo `.lua` no Projeto MCR é uma linguagem de programação usada para criar scripts personalizados e funções dentro do servidor. Lua é conhecida por sua simplicidade e eficiência, tornando-a ideal para desenvolver funcionalidades adicionais ou modificar comportamentos existentes do jogo."

✅ .lua = linguagem de programação
⚠️ Genérico — não menciona OTClient
⚠️ Fala "servidor" mas Lua é mais usado no cliente

**Veredito:** ✅ Cloud vence em precisão técnica

---

## TESTE 3: "Crie uma lore para a cidade inicial Eridanus"

### Cloud (70b)
**Tempo:** ~5s | **Tamanho:** 1.670 chars

> **Eridanus — A Cidade do Rio Flamejante**
> Personagens: Mestra Aurélia, Kael o Cartógrafo, Irmã Lúmen
> Elementos: Fogo, Gelo, Terra, Energia (4 torres)
> Geografia: Rio Líquido, pontes de cristal
> História: Primeira Convergência Elemental

✅ 11+ nomes próprios (Eridanus, Pyralis, Glaciara, Terramar, Venthus, etc.)
✅ Temática elemental consistente com MCR
✅ Estrutura: Fundação → Aparência → Perigo → Personagens

### MCR-DevIA (7b + Pipeline)
**Tempo:** 31.8s | **Tamanho:** 3.128 chars

> Geografia, História detalhada, personagens (Sir Elric de Terraformar)
> Rio Eridano e Rio Mariana

✅ Muito mais longo (3.128 vs 1.670 chars)
✅ Estrutura clara com seções
⚠️ Nomes genéricos ("Sir Elric", "Lorentia") — não remetem ao MCR
⚠️ Temática mais genérica (colonial/indígena) — menos fiel ao MCR/Tibia
❌ Não menciona os 4 domínios elementais

**Veredito:** ⚠️ Cloud vence em fidelidade temática, MCR-DevIA vence em extensão

---

## Métricas Agregadas

### Qualidade (0-10)

| Critério | Peso | Cloud | MCR-DevIA | Nota |
|----------|------|-------|-----------|------|
| Precisão de siglas (SPA, .lua) | 30% | 10 | 10 | Empate |
| Contexto correto do projeto | 25% | 10 | 9 | Cloud +1 |
| Profundidade/detalhes | 20% | 9 | 7 | Cloud +2 |
| Extensão/conteúdo | 10% | 7 | 9 | MCR +2 |
| Velocidade | 10% | 10 | 3 | Cloud +7 |
| Originalidade/criatividade | 5% | 9 | 6 | Cloud +3 |

**Score ponderado:**
- **Cloud:** 0.30×10 + 0.25×10 + 0.20×9 + 0.10×7 + 0.10×10 + 0.05×9 = **9.55**
- **MCR-DevIA:** 0.30×10 + 0.25×9 + 0.20×7 + 0.10×9 + 0.10×3 + 0.05×6 = **8.15**

### Eficiência

| Métrica | Cloud | MCR-DevIA |
|---------|-------|-----------|
| Modelo | DeepSeek-V4-Flash (70b) | qwen2.5-coder:7b |
| Consumo VRAM | ~40GB | ~5GB |
| Inferências | 3 diretas | 3 pipeline (CR + Orquestrador) |
| Chamadas FAST adicionais | 0 | ~12 (CR + ContextCrew) |
| Latência média | ~3.6s | ~26.4s |

---

## Conclusão

**Cloud vence em qualidade (9.55 vs 8.15)**, principalmente devido a:
1. **Velocidade**: 26s vs 3s — o pipeline de 7b adiciona latência
2. **Profundidade técnica**: Cloud conhece detalhes de implementação (diretórios, APIs)
3. **Fidelidade temática**: Lore do Cloud usa elementos corretos do MCR (domínios, personagens temáticos)

**MCR-DevIA vence em eficiência:**
1. **Custo**: 7b usa ~5GB VRAM vs ~40GB
2. **Extensão**: Lore 87% mais longa que Cloud
3. **Execução local**: Roda em qualquer máquina com GPU modesta

**Lições:**
1. O **Context Reinforcer** funcionou perfeitamente — 0 alucinações de siglas no teste final
2. A correção final (forçar desambiguação na pergunta) foi **crítica** — sem ela, o 7b ignorava instruções
3. O pipeline adiciona ~23s de overhead que não existem no modelo grande
4. Para lore, o 7b tende ao genérico; Cloud consegue manter identidade temática

> **Recomendação:** Usar MCR-DevIA para tarefas factuais (onde CR garante precisão) e Cloud para tarefas criativas (lore, narrativa) que exigem consistência temática.
