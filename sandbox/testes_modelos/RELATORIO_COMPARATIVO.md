# RELATORIO COMPARATIVO - Modelos de IA Locais

> Data: 27/06/2026
> Projeto: MCR - Teste de 4 modelos em 3 categorias
> GPU: NVIDIA (Ollama local)

---

## Sumario Executivo

| Modelo | Codigo | Criatividade | Raciocinio | Media Tokens/s |
|--------|--------|--------------|------------|-----------------|
| Qwen 2.5 Coder (7B) | ✅✅ (2571c) | ✅✅ (1328c) | ✅✅ (2563c) | 125.8 |
| Llama 3.1 (8B) | ✅✅ (1129c) | ✅✅ (1472c) | ✅✅ (3454c) | 118.5 |
| Deepseek R1 (7B) | ⚠️ (0c) | ✅✅ (3036c) | ✅✅ (3046c) | 123.9 |
| Mistral (7B) | ✅✅ (1045c) | ✅✅ (2373c) | ✅✅ (3579c) | 124.3 |

---

## Resultados Detalhados por Teste

### Teste: CODIGO - Funcao Python de validacao de CPF

**Prompt:** Crie uma funcao em Python que valide CPF. A funcao deve:
1. Receber uma string de CPF (com ou sem pontuacao)
2. Remover caracteres nao numericos
3. Validar digitos verificadores
4. Retornar True/False...

| Modelo | Tempo | Caracteres | Tokens/s | Analise |
|--------|-------|------------|----------|---------|
| Qwen 2.5 Coder (7B) - ATUAL PADRAO | 10.02s | 2571 | 125.1 tok/s | ✅✅ Resposta robusta e bem desenvolvida; ✅ Contem definicao de funcao (def); ✅ Contem return; ✅ Menciona CPF; ℹ️ Usa import (pode ser desnecessario); ✅ Usa marcacao de codigo |
| Llama 3.1 (8B) - TEXTO PT-BR | 9.63s | 1129 | 119.3 tok/s | ✅✅ Resposta robusta e bem desenvolvida; ✅ Contem definicao de funcao (def); ✅ Contem return; ✅ Menciona CPF; ✅ Usa marcacao de codigo |
| Deepseek R1 (7B) - RACIOCINIO | 24.19s | 0 | 122.9 tok/s | ❌ RESPOSTA MUITO CURTA (provavel erro/falha); ⚠️ Sem marcacao de codigo (```) |
| Mistral (7B) - EQUILIBRIO | 9.66s | 1045 | 124.9 tok/s | ✅✅ Resposta robusta e bem desenvolvida; ✅ Contem definicao de funcao (def); ✅ Contem return; ✅ Menciona CPF; ✅ Usa marcacao de codigo |

### Teste: TEXTO/CRIATIVIDADE - Descricao de Eridanus (cidade do Projeto MCR)

**Prompt:** Descreva a cidade de Eridanus, cidade inicial do Projeto MCR (um servidor customizado de Tibia), em um paragrafo de ambientacao de fantasia medieval. Inclua elementos como: arquitetura, habitantes, gu...

| Modelo | Tempo | Caracteres | Tokens/s | Analise |
|--------|-------|------------|----------|---------|
| Qwen 2.5 Coder (7B) - ATUAL PADRAO | 5.48s | 1328 | 126.4 tok/s | ✅✅ Resposta robusta e bem desenvolvida; ✅ Boa ambientacao (3 elementos); ✅✅ Nomes proprios abundantes (~13) |
| Llama 3.1 (8B) - TEXTO PT-BR | 6.06s | 1472 | 118.4 tok/s | ✅✅ Resposta robusta e bem desenvolvida; ✅ Boa ambientacao (4 elementos); ✅✅ Nomes proprios abundantes (~23) |
| Deepseek R1 (7B) - RACIOCINIO | 12.52s | 3036 | 124.5 tok/s | ✅✅ Resposta robusta e bem desenvolvida; ⚠️ Pouca ambientacao (0 elementos encontrados); ✅✅ Nomes proprios abundantes (~23) |
| Mistral (7B) - EQUILIBRIO | 8.25s | 2373 | 124.6 tok/s | ✅✅ Resposta robusta e bem desenvolvida; ⚠️ Pouca ambientacao (2 elementos encontrados); ✅✅ Nomes proprios abundantes (~22) |

### Teste: RACIOCINIO/ANALISE - Redis como cache em MMORPG

**Prompt:** Analise as vantagens e desvantagens de usar Redis como cache em um servidor de jogo MMORPG (Tibia/OTServ). Considere: persistencia, velocidade, consumo de RAM, replicacao, casos de uso especificos (ra...

| Modelo | Tempo | Caracteres | Tokens/s | Analise |
|--------|-------|------------|----------|---------|
| Qwen 2.5 Coder (7B) - ATUAL PADRAO | 7.75s | 2563 | 125.8 tok/s | ✅✅ Resposta robusta e bem desenvolvida; ✅ Analise razoavel (7 pontos-chave); ✅ Menciona Redis especificamente; ✅ Contextualizado para MMORPG; ✅ Inclui recomendacao |
| Llama 3.1 (8B) - TEXTO PT-BR | 10.11s | 3454 | 117.7 tok/s | ✅✅ Resposta robusta e bem desenvolvida; ✅ Analise razoavel (7 pontos-chave); ✅ Menciona Redis especificamente; ✅ Contextualizado para MMORPG; ✅ Inclui recomendacao |
| Deepseek R1 (7B) - RACIOCINIO | 14.61s | 3046 | 124.3 tok/s | ✅✅ Resposta robusta e bem desenvolvida; ✅ Analise razoavel (7 pontos-chave); ✅ Menciona Redis especificamente; ✅ Contextualizado para MMORPG; ✅ Inclui recomendacao |
| Mistral (7B) - EQUILIBRIO | 11.19s | 3579 | 123.3 tok/s | ✅✅ Resposta robusta e bem desenvolvida; ✅ Analise razoavel (7 pontos-chave); ✅ Menciona Redis especificamente; ✅ Contextualizado para MMORPG |

---

## Conclusoes e Recomendacoes

### Velocidade (tokens/segundo)

1. **Qwen 2.5 Coder (7B) - ATUAL PADRAO**: 125.76666666666667 tok/s
2. **Mistral (7B) - EQUILIBRIO**: 124.26666666666667 tok/s
3. **Deepseek R1 (7B) - RACIOCINIO**: 123.89999999999999 tok/s
4. **Llama 3.1 (8B) - TEXTO PT-BR**: 118.46666666666665 tok/s

### Qualidade das Respostas

| Criterio | Melhor Modelo | Observacao |
|----------|--------------|------------|
| CODIGO - Funcao Python de validacao de CPF | Qwen 2.5 Coder (7B) - ATUAL PADRAO | 2571 caracteres |
| TEXTO/CRIATIVIDADE - Descricao de Eridanus (cidade do Projeto MCR) | Deepseek R1 (7B) - RACIOCINIO | 3036 caracteres |
| RACIOCINIO/ANALISE - Redis como cache em MMORPG | Mistral (7B) - EQUILIBRIO | 3579 caracteres |

### Recomendacao Final

| Uso | Modelo Recomendado | Motivo |
|-----|-------------------|--------|
| Codigo | qwen2.5-coder:7b | Especializado em codigo |
| Texto PT-BR | llama3.1:8b | Melhor para linguas naturais |
| Raciocinio | deepseek-r1:7b | Thinking tokens para logica |
| Equilibrio | mistral:7b | Bom custo-beneficio geral |

---

_Gerado automaticamente em 27/06/2026 pelo MCR-DevIA_