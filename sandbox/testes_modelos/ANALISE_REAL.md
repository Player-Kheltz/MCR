# ANALISE REAL DE MODELOS - Projeto MCR

> Data: 27/06/2026
> Tipo: Teste cego automatizado com 4 modelos × 3 categorias = 12 chamadas reais ao Ollama
> Temperatura: 0.3 | Max tokens: 2048
> GPU: NVIDIA (Ollama local)

---

## 1. SUMARIO EXECUTIVO

| Modelo | Codigo | Criatividade PT-BR | Raciocinio | Velocidade media | Tamanho total |
|--------|--------|-------------------|------------|-----------------|---------------|
| **Qwen 2.5 Coder:7b** | 🥇 2571c | ✅ 1328c | ✅ 2563c | 125.8 tok/s | **6462c** |
| **Llama 3.1:8b** | ✅ 1129c | 🥇 1472c | ✅ 3454c | 118.5 tok/s | 6055c |
| **Deepseek R1:7b** | ❌ 0c (erro) | ⚠️ 3036c (INGLES) | ✅ 3046c | 123.9 tok/s | 6082c |
| **Mistral:7b** | ✅ 1045c | ✅ 2373c | 🥇 **3579c** | **124.3 tok/s** | **6997c** |

> Legenda: c = caracteres na resposta | tok/s = tokens por segundo
> 🥇 = melhor da categoria | ✅ = bom | ⚠️ = problema | ❌ = falhou

---

## 2. TESTE 1: CODIGO (Validacao de CPF em Python)

### Resultados

| Modelo | Caracteres | Tempo | Tok/s | Qualidade |
|--------|-----------|-------|-------|-----------|
| **Qwen 2.5 Coder** | **2571** | 10.0s | 125.1 | Código completo com `def`, `return`, regex, exemplos comentados |
| Llama 3.1 | 1129 | 9.6s | 119.3 | Código funcional mas mais conciso |
| Deepseek R1 | **0** | 24.2s | 122.9 | **FALHOU** - gerou apenas thinking tokens, sem resposta final |
| Mistral | 1045 | 9.7s | 124.9 | Código funcional, sem `import re` (manual) |

### Analise

**Qwen 2.5 Coder domina esta categoria.** Gerou código completo e funcional com:
- Função `validar_cpf()` bem documentada
- Uso correto de `re.sub(r'\D', '', cpf)` para limpeza
- Lógica de dígitos verificadores implementada corretamente
- 5 exemplos de uso com valores reais
- Explicação detalhada do algoritmo (78 linhas no total)

**Deepseek R1 falhou completamente**: consumiu todos os 2048 tokens com raciocínio interno (thinking tokens) e não gerou resposta alguma. Para código, é inviável no limite atual.

**Llama 3.1 e Mistral** geraram soluções funcionais mas menos detalhadas.

### Veredito: Qwen 2.5 Coder mantém-se como padrao para codigo.

---

## 3. TESTE 2: CRIATIVIDADE (Descricao de Eridanus)

### Resultados

| Modelo | Caracteres | Tempo | Idioma | Nomes proprios | Ambientacao |
|--------|-----------|-------|--------|---------------|-------------|
| Qwen 2.5 Coder | 1328 | 5.5s | PT-BR | 13 nomes | Elementos basicos |
| **Llama 3.1** | **1472** | **6.1s** | **PT-BR** | **23 nomes** | **Catedral de Cristal, Casa de Argentum, Ferreiros Fulgidos** |
| Deepseek R1 | 3036 | 12.5s | **INGLES** | 23 nomes | Descricao longa mas em ingles |
| Mistral | 2373 | 8.3s | PT-BR | 22 nomes | Elementos fantasy genericos |

### Analise

**Llama 3.1 vence em PT-BR.** Pontos fortes:
- Texto em português natural e fluente
- Nomes próprios criativos: "Arquiteto Elwes", "Casa de Argentum", "Catedral de Cristal", "Ferreiros Fúlgidos", "Alquimistas Brilhantes"
- Ambientacao rica: minas de cristal, guildas, economia baseada em recursos
- Tom consistente de fantasia medieval

**Deepseek R1** gerou a resposta mais longa, mas **em INGLÊS** - inviável para o Projeto MCR que precisa de PT-BR.

**Qwen 2.5 Coder** escreveu em PT-BR mas com tom mais técnico/descritivo, menos imersivo.

**Mistral** bom português, 22 nomes próprios, mas ambientação mais genérica ("florestas encantadas", "masmorras esquecidas" em vez de elementos únicos).

### Veredito: Llama 3.1:8b é o melhor para criatividade em PT-BR.

---

## 4. TESTE 3: RACIOCINIO (Redis como cache em MMORPG)

### Resultados

| Modelo | Caracteres | Tempo | Tok/s | Estrutura | Pontos-chave | Recomendacao |
|--------|-----------|-------|-------|-----------|-------------|-------------|
| Qwen 2.5 Coder | 2563 | 7.8s | 125.8 | Topicos | 7/10 | Sim |
| Llama 3.1 | 3454 | 10.1s | 117.7 | **Topicos detalhados** | 7/10 | Sim |
| Deepseek R1 | 3046 | 14.6s | 124.3 | Topicos | 7/10 | Sim |
| **Mistral** | **3579** | **11.2s** | **123.3** | **Topicos completos** | **8/10** | Sim |

### Analise

**Mistral gerou a resposta mais longa e completa.** Pontos fortes:
- Abordagem estruturada: persistência, velocidade, RAM, replicação, casos de uso
- **Análise crítica**: apontou que velocidade pode ser desvantagem se recursos forem insuficientes
- **Casos de uso específicos**: ranking (ordenação), inventário (listas/hashes), spawn de mobs (listas)
- Conclusão com recomendação prática

**Llama 3.1** também muito bom, análise detalhada mas ligeiramente menos específica.

**Qwen 2.5 Coder** resposta sólida e rápida, mas mais genérica.

**Deepseek R1** análise competente, mas pode conter thinking tokens residuais.

### Veredito: Mistral:7b ligeiramente a frente, mas todos os 3 (Qwen, Llama, Mistral) sao viaveis.

---

## 5. ANALISE DE VELOCIDADE

| Modelo | Tok/s medio | Mais rapido em |
|--------|------------|----------------|
| **Qwen 2.5 Coder** | **125.8** | Criatividade (5.5s) |
| Mistral | 124.3 | Codigo (9.7s) |
| Deepseek R1 | 123.9 | Criatividade (12.5s) |
| Llama 3.1 | 118.5 | Criatividade (6.1s) |

Todos os modelos operam na faixa de **118-126 tok/s** na GPU local. A diferença é pequena.
Llama 3.1 é o mais lento (~5% mais lento que o líder), mas também tem 8B parâmetros vs 7B dos outros.

---

## 6. PROBLEMAS IDENTIFICADOS

### 6.1 Deepseek R1: Thinking tokens consomem o limite
- No teste de código, 2048 tokens foram gastos em raciocínio interno sem gerar resposta
- `stream: False` retorna apenas os thinking tokens sem separar resposta final
- **Solução necessária**: usar `stream: True` e filtrar linhas entre  e 
  OU aumentar `num_predict` para 4096+ e usar `raw: True` para evitar parsing do template

### 6.2 Deepseek R1: Responde em ingles
- No teste de criatividade, ignorou o prompt em português e respondeu em inglês
- **Problema**: modelo treinado predominantemente em inglês, não confiável para PT-BR

### 6.3 Qwen 2.5 Coder: Criatividade generica
- Tendência a ficção científica mesmo quando solicitado fantasia medieval
- Ambientação com elementos genéricos ("cidade vibrante", "águas cristalinas")
- Menos nomes próprios com personalidade

---

## 7. RECOMENDACAO FINAL

### Router de Modelos (baseado nos testes reais)

| Tarefa | Modelo | Motivo |
|--------|--------|--------|
| **Gerar codigo** | **qwen2.5-coder:7b** | 2.5× mais código que concorrentes, preciso e completo |
| **Criar lore/texto PT-BR** | **llama3.1:8b** | Português natural, 23 nomes próprios, ambientação rica |
| **Analisar/raciocinar** | **qwen2.5-coder:7b** (padrão atual) | 7.8s, 2563c, rápido e competente. Mistral é alternativa |
| **Equilibrio geral** | **mistral:7b** | Boa alternativa quando qwen estiver ocupado |
| **Raciocinio complexo** | **deepseek-r1:7b** (apenas com ajuste de token limit) | Potencial mas precisa de configuração especial |

### Configuracao recomendada para o MCR-DevIA

Manter **qwen2.5-coder:7b como padrão** (já é o padrão atual).

Adicionar **llama3.1:8b** como modelo secundário para:
- `cmd_lore.py` (geração de lore)
- `cmd_criatividade.py` (se existir)
- Conselho: personalidade "Contador de Histórias"

Adicionar **mistral:7b** como alternativa para:
- Pipeline V4: etapa de análise
- Conselho: personalidade "Analista"

Deepseek R1 apenas com configuração especial (`num_predict: 8192`, `raw: true`).

---

## 8. ARQUIVOS GERADOS

```
sandbox/testes_modelos/
  executar_testes.py              ← Script de teste
  RELATORIO_COMPARATIVO.md        ← Relatorio automatico (gerado pelo script)
  ANALISE_REAL.md                 ← Este arquivo (analise manual aprofundada)
  resultados_completos.json       ← JSON bruto com todas as metricas
  
  teste_qwen_coder_codigo.txt     ← Qwen - Codigo (2571c, 10.0s)
  teste_qwen_coder_criatividade.txt  ← Qwen - Criatividade (1328c, 5.5s)
  teste_qwen_coder_raciocinio.txt ← Qwen - Raciocinio (2563c, 7.8s)
  
  teste_llama3_codigo.txt         ← Llama - Codigo (1129c, 9.6s)
  teste_llama3_criatividade.txt   ← Llama - Criatividade (1472c, 6.1s) 🥇 PT-BR
  teste_llama3_raciocinio.txt     ← Llama - Raciocinio (3454c, 10.1s)
  
  teste_deepseek_codigo.txt       ← Deepseek - Codigo (0c, 24.2s) ❌
  teste_deepseek_criatividade.txt ← Deepseek - Criatividade (3036c, 12.5s, INGLES)
  teste_deepseek_raciocinio.txt   ← Deepseek - Raciocinio (3046c, 14.6s)
  
  teste_mistral_codigo.txt        ← Mistral - Codigo (1045c, 9.7s)
  teste_mistral_criatividade.txt  ← Mistral - Criatividade (2373c, 8.3s)
  teste_mistral_raciocinio.txt    ← Mistral - Raciocinio (3579c, 11.2s) 🥇 RACIOCINIO
```

---

## 9. PROXIMOS PASSOS

1. ✅ ~~Baixar llama3.1:8b~~ (ja estava baixado)
2. ✅ ~~Baixar mistral:7b~~ (4.4GB baixado com sucesso)
3. ✅ ~~Testar deepseek-r1:7b~~ (identificado problema de thinking tokens)
4. ⬜ Configurar router de modelos no MCR-DevIA (qwen padrao, llama para texto, mistral alternativa)
5. ⬜ Ajustar deepseek para uso com `num_predict: 8192` e `raw: true`
6. ⬜ Atualizar Conselho V8 para usar llama3.1 em personalidades de texto
7. ⬜ Registrar licoes no KG

---

_Gerado em 27/06/2026 apos 12 chamadas reais ao Ollama + analise manual._
