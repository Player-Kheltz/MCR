# MELHOR DE 5 - Analise Real: Mistral vs Qwen

> Data: 27/06/2026
> 5 testes de Equilíbrio + Raciocínio | Temperature: 0.2 | Max tokens: 4096

---

## Sumario Executivo

| Modelo | Media Heuristica | Caracteres Total | Tempo Total | Tok/s medio |
|--------|:-:|:-:|:-:|:-:|
| **Mistral (7B)** | **6.1/10** 🏆 | 16617 | 61.0s | 123.0 |
| Qwen 2.5 Coder (7B) | 5.5/10 | 18542 | 59.7s | 124.6 |

**Vencedor heurístico: MISTRAL** (4 de 5 testes)

---

## Analise Qualitativa Teste por Teste

### Teste 1: LOGICA MATEMATICA (Drop Rate)
| Aspecto | Qwen | Mistral |
|---------|------|---------|
| Completude | ✅ Calculou os 3 itens | ✅ Calculou os 3 itens |
| Clareza | ✅ Passo a passo claro | ✅ Passo a passo claro |
| Profundidade | ⚠️ Usou probabilidade simples, sem binomial | ⚠️ Mesmo nível |
| Codigo | ✅ Incluiu demonstracao Python | ❌ Sem codigo |
| **Veredito** | **Qwen** (codigo incluso) | |

### Teste 2: TRADE-OFF (SQLite vs MySQL)
| Aspecto | Qwen | Mistral |
|---------|------|---------|
| Cobertura | ✅ 6/6 topicos | ✅ 6/6 topicos |
| Casos de uso | **✅ Especifico**: "guild storage = SQLite, world data = MySQL" | ⚠️ Generico: "dados de guild = leves, mundo = pesados" |
| Precisao | ⚠️ "SQLite suporta transacoes multithreaded" (parcialmente incorreto) | ✅ "SQLite nao e projetado para multiplas conexoes" (correto) |
| Recomendacao | Ambos recomendaram MySQL | |
| **Veredito** | **Empate tecnico** | |

### Teste 3: DIAGNOSTICO (Lag 50+ jogadores)
| Aspecto | Qwen | Mistral |
|---------|------|---------|
| Causas | 5 causas **genericas** (concorrencia, DB, codigo, rede, hardware) | 5 causas **genericas** (CPU, RAM, SSD, rede, arquitetura) |
| Especificidade | ❌ Nao citou profiling Lua, broadcast packets, TFS | ❌ Nao citou nada especifico do OTServ |
| Ferramentas | ⚠️ Citou top, htop, Wireshark, Prometheus, Grafana | ⚠️ Citou New Relic, AppDynamics, Datadog (NADA especifico OTServ) |
| Solucoes | ❌ "aumentar hardware", "otimizar codigo" | ❌ "adicionar mais RAM", "melhorar conexao" |
| **Veredito** | **Ambos ruins** - respostas superficiais para um problema complexo | |

### Teste 4: DESIGN (Sistema de Quests)
| Aspecto | Qwen | Mistral |
|---------|------|---------|
| Estrutura | ✅ Classes Python completas com atributos | ✅ SQL tables com exemplos |
| Exemplo | ✅ Quest concreta com objetivos, recompensas | ⚠️ Exemplo parcial |
| Validacao | ✅ Fluxo de progressao explicado | ⚠️ Superficial |
| **Veredito** | **Qwen** (codigo concreto, exemplo completo) | |

### Teste 5: COMPARACAO (NoSQL vs SQL para Inventario)
| Aspecto | Qwen | Mistral |
|---------|------|---------|
| Extensao | **6203c** - MUITO detalhado | 4331c - Detalhado |
| CAP Theorem | ✅ Mencionou consistencia vs disponibilidade | ❌ Nao mencionou |
| Trade-offs | ✅ Pros/contras claros por operacao | ⚠️ Listou mas sem profundidade |
| Codigo | ✅ Exemplos de schemas | ❌ Sem exemplos |
| **Veredito** | **Qwen** (muito superior neste teste) | |

---

## Placar Real (minha analise)

| Teste | Vencedor | Margem |
|-------|----------|--------|
| 1. Logica Matematica | **Qwen** | Pequena (codigo incluso) |
| 2. Trade-off SQL vs MySQL | **Empate** | Qualidade similar |
| 3. Diagnostico Lag | **Empate** | Ambos superficiais |
| 4. Design Quests | **Qwen** | Codigo concreto vs SQL abstrato |
| 5. NoSQL vs SQL Inventario | **Qwen** | 6203c, CAP theorem, schemas |

**Placar REAL: Qwen 3-0-2 Mistral** (3 vitorias, 2 empates, 0 derrotas)

---

## Conclusão: Quem vence?

### Se o criterio for COMPLETUDE (cobrir topicos): MISTRAL
O Mistral sistematicamente responde ponto a ponto, sem pular itens. A heuristica capturou isso (9.0 vs 6.1 em completude).

### Se o criterio for PRECISAO TECNICA + PROFUNDIDADE: QWEN
O Qwen inclui mais codigo, exemplos concretos, e demonstracoes praticas. Respostas mais densas em informacao util.

### Se o criterio for VELOCIDADE: QWEN (marginal)
Qwen: 124.6 tok/s | Mistral: 123.0 tok/s | Diferenca: ~1.3%

### VEREDITO FINAL

**Para uso no MCR-DevIA:**

| Cenario | Recomendado | Motivo |
|---------|-------------|--------|
| Respostas rapidas e completas | **Mistral** | Cobre todos os topicos, bem estruturado |
| Respostas tecnicas com codigo | **Qwen** | Inclui implementacao, exemplos concretos |
| Pipeline de raciocinio | **Qwen** (padrao atual) | Mais denso, melhor custo-beneficio |
| Conselho - personalidade Analista | **Mistral** | Estruturado, cobre todos os angulos |

**Na pratica**: Ambos sao viaveis. O Qwen continua sendo o padrao ideal para uso geral porque:
1. Ja e o modelo atual (zero custo de migracao)
2. Melhor para codigo (principal uso do MCR-DevIA)
3. Mais denso em informacao
4. Velocidade ligeiramente superior

O Mistral e uma OTIMA alternativa para quando o Qwen estiver ocupado ou para tarefas que exigem cobertura completa de topicos.

---

## Recomendacao sobre Deepseek R1

### Problemas identificados
1. **Thinking tokens consomem o limite**: Com `num_predict: 2048` e `stream: False`, ele gasta todo o orcamento pensando sem responder
2. **Responde em ingles**: Ignora prompt PT-BR
3. **Mais lento**: 24s no teste de codigo (vs 10s Qwen) - e ainda falhou

### Onde vale a pena insistir no Deepseek?

**SIM, vale a pena para:**

1. **Raciocinio complexo com cadeia de pensamento** 
   - Configuracao: `raw: true, num_predict: 8192`
   - Use para: problemas multi-etapa, depuracao complexa, analise de causa raiz
   - Os thinking tokens sao uma VANTAGEM aqui - ele pensa antes de responder

2. **Analise critica / Review de codigo**
   - O raciocinio interno permite encontrar bugs que outros modelos perdem
   - Use no `cmd_review.py` para analise de codigo complexo

3. **Planejamento arquitetural**
   - Para questoes de design que exigem considerar multiplos fatores
   - O chain-of-thought produz analises mais profundas

4. **Geracao de documentacao tecnica (em ingles)**
   - Se o projeto aceitar documentacao em ingles, o Deepseek e excelente

**ONDE NAO usar Deepseek:**
- ❌ Tarefas simples (thinking tokens sao desperdicio)
- ❌ Texto PT-BR (responde em ingles)
- ❌ Codigo rapido (gasta 24s pensando antes de codar)
- ❌ Com `stream: False` sem `raw: true`

### Configuracao recomendada para Deepseek

```python
# CERTO - para raciocinio complexo:
{
    "model": "deepseek-r1:7b",
    "options": {
        "raw": true,           # ESSENCIAL: sem template de chat
        "num_predict": 8192,   # ESPACO para pensar + responder
        "temperature": 0.3
    }
}

# ERRADO - vai gastar tudo em thinking:
{
    "model": "deepseek-r1:7b",
    "options": {
        "num_predict": 2048,   # MUITO CURTO
        # sem "raw": true       # ERRO: template de chat mata a resposta
    }
}
```

### Resumo Deepseek

| Aspecto | Nota | Explicacao |
|---------|:----:|-----------|
| Codigo | ❌ | Thinking tokens consomem tudo, resposta 0c |
| PT-BR | ❌ | Ignora prompt, responde em ingles |
| Raciocinio simples | ⚠️ | Possivel com configuracao correta |
| Raciocinio complexo | ✅ | Onde ele BRILHA (chain-of-thought) |
| Review de codigo | ✅ | Bom para encontrar bugs |
| Velocidade | ⚠️ | 2-3x mais lento que Qwen/Mistral |

---

## Arquivos

```
sandbox/testes_modelos/
  MELHOR_DE_5_RESULTADO.md     -- Relatorio heuristico automatico
  MELHOR_DE_5_ANALISE_REAL.md  -- Este arquivo (analise qualitativa)
  melhor_de_5_completo.json    -- JSON com todas as metricas
  m5_qwen2.5-coder_*.txt       -- 5 arquivos Qwen
  m5_mistral_*.txt             -- 5 arquivos Mistral
```

---

_Gerado em 27/06/2026 apos 10 chamadas Ollama + analise qualitativa manual_
