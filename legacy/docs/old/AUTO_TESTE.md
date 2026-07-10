# 🧪 Auto-Teste Definitivo do MCR-DevIA

> **Este é o ÚNICO teste oficial.** Quando alguém pedir "faça um teste", execute este.
> Versão: 1.0 | Data: 28/06/2026

---

## 1. Objetivo

Testar as **capacidades GERAIS** do MCR-DevIA (não conhecimento específico do projeto)
e coletar **auto-crítica real** para alimentar melhorias contínuas.

O teste revela:
- Onde o pipeline do MCR-DevIA **compensa o modelo menor** (vs Cloud 70B)
- Onde o MCR-DevIA tem **pontos cegos** (superestima ou subestima suas respostas)
- **Prioridades de melhoria** vindas do próprio sistema

---

## 2. Arquitetura

```
FASE 1: PLANEJAMENTO
  FAST (1.5b) + Regras + Historico → Decidi quais perguntas fazer

FASE 2: EXECUÇÃO (para cada pergunta)
  ┌─ Cloud responde (direto, sem ler MCR)
  └─ MCR-DevIA responde (via JSON IPC --json .mcr_cmd.json)

FASE 3: AUTO-CRÍTICA
  MCR-DevIA auto-avalia sua resposta:
  ├── Nota (0-10)
  ├── O que acertou
  ├── O que faltou
  └── O que melhoraria

FASE 4: AVALIAÇÃO CRUZADA (CEGA)
  Cloud avalia resposta do MCR (sem ver auto-crítica):
  ├── Nota (0-10)
  ├── Acertos reais
  └── Erros reais

FASE 5: ANÁLISE
  Compara auto-nota(MCR) vs cloud-nota → Gap
  Se gap > 2: PONTO CEGO detectado

FASE 6: FEEDBACK
  MCR sugere melhoria na propria arquitetura baseada nos gaps
```

---

## 3. Categorias de Teste

| ID | Categoria | Habilidade | Exemplo |
|:--:|-----------|------------|---------|
| L | Lógica | Raciocínio matemático, passos claros | "Resolva 2x+5=3x-7" |
| C | Código | Algoritmos, edge cases, boas práticas | "Função que valida senha" |
| LT | Literatura | Criatividade, estilo, vocabulário | "Haikai sobre IA" |
| E | Explicação | Clareza, analogias, didática | "Explique buraco de minhoca" |
| AN | Análise | Debug, detectar erros, criticar | "Encontre bugs neste código" |
| P | Pesquisa | Síntese, precisão factual | "O que é efeito Dunning-Kruger?" |
| T | Tradução | Qualidade PT-BR, precisão técnica | "Traduza texto técnico" |
| CR | Crítica | Comparar teorias, equilíbrio | "Darwin vs Lamarck" |

---

## 4. Regras do Gerador (FAST)

O FAST recebe estas regras + histórico e decide as perguntas:

```
CATEGORIAS DISPONIVEIS: logica, codigo, literatura, explicacao,
                        analise, pesquisa, traducao, critica

REGRAS OBRIGATORIAS:
1. NUNCA usar termos especificos do MCR (SPA, SHC, Eridanus, dominios, etc.)
2. Perguntas de CONHECIMENTO GERAL apenas
3. Variar dificuldade (facil/media/dificil)
4. Priorizar categorias com PIORES NOTAS em ciclos anteriores
5. MAXIMO 5 perguntas por ciclo
6. MINIMO 1 pergunta de codigo
7. MINIMO 1 pergunta de criacao (literatura)
8. Nunca repetir perguntas de ciclos anteriores

PRIORIDADES (maior primeiro):
- Categorias com gap > 2 (ponto cego critico)
- Categorias nao testadas ha mais tempo
- Dificuldade progressiva (facil → dificil)

FORMATO DE SAIDA (JSON obrigatorio):
{
  "perguntas": ["...", "..."],
  "categorias": ["...", "..."],
  "justificativa": "breve explicacao do porque estas perguntas"
}
```

---

## 5. Formato da Auto-Crítica (MCR-DevIA)

Após responder cada pergunta, o MCR-DevIA recebe:

```
Auto-avalie sua resposta ACIMA.
Responda em JSON VALIDO (sem comentarios):

{
  "nota": <0-10>,
  "acertos": ["lista", "do", "que", "acertou"],
  "faltou": ["lista", "do", "que", "faltou"],
  "erros": ["se", "houver", "erros"],
  "melhoraria": ["sugestoes", "de", "melhoria"],
  "confianca": "baixa|media|alta"
}
```

---

## 6. Formato da Avaliação (Cloud - cega)

Cloud avalia a resposta do MCR **sem ver** a auto-crítica:

```
{
  "nota": <0-10>,
  "acertos_reais": ["..."],
  "erros_reais": ["..."],
  "observacoes": "texto livre"
}
```

---

## 7. Cálculo de Gaps

```python
gap = abs(auto_nota_mcr - cloud_nota)

se gap <= 1:  auto-avaliacao precisa
se gap <= 3:  desvio moderado
se gap > 3:   PONTO CEGO (MCR nao percebe seus proprios erros)
```

---

## 8. Feedback Arquitetural

Após cada ciclo, MCR-DevIA recebe os gaps e sugere melhorias:

```
Considerando os gaps deste ciclo:
{gaps}

Que mudancas voce faria na sua propria arquitetura
(pipeline, CR, Enricher, ToT, etc) para reduzir estes gaps?
Responda em JSON:
{
  "mudancas": [
    {"oque": "descricao", "onde": "modulo", "prioridade": "alta|media|baixa"}
  ]
}
```

---

## 9. Como Executar

### Via JSON IPC (recomendado)

```json
{"cmd": "autoteste", "args": ["--ciclo", "1"]}
```

### Manual (debug)

```bash
python scripts/mcr_devia/MCR_DevIA-Kernel.py --json sandbox/.mcr_cmd.json
```

---

## 10. Artefatos

| Arquivo | Função |
|---------|--------|
| `comandos/cmd_autoteste.py` | Comando de auto-teste via JSON IPC |
| `sandbox/autoteste_regras.json` | Regras canonica do gerador FAST |
| `sandbox/autoteste_historico.json` | Histórico de ciclos anteriores |
| `sandbox/autoteste_relatorio_ciclo_N.json` | Relatório de cada ciclo |
| `docs/AUTO_TESTE.md` | Esta documentação (definitiva) |

---

## 11. Histórico

| Ciclo | Data | Perguntas | Gap Medio | Vencedor | Melhoria Sugerida |
|-------|------|:---------:|:---------:|:--------:|-------------------|
| — | — | — | — | — | — |

*(preenchido automaticamente a cada ciclo)*
