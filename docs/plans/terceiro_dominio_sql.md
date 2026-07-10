# Plano: Terceiro Domínio — SQL

**Aprovação:** Arquiteto  
**Prazo:** 5 dias  
**Objetivo:** Provar a Universalidade Condicional (Teorema 5) em um terceiro domínio estruturalmente distinto de Lua e C#, sem modificar o kernel MCR.

---

## 1. Por que SQL?

| Critério | SQL |
|----------|-----|
| Estruturalmente distinto de Lua e C# | Declarativo vs imperativo. Sem loops, sem atribuições sequenciais — cláusulas aninhadas (`SELECT`, `FROM`, `WHERE`, `JOIN`). |
| Vocabulário Σ grande e diverso | Palavras-chave fixas + infinitos identificadores de tabelas/colunas. Testa o limite `O(|Σ|^k ln |Σ|^k)`. |
| Corpus aberto disponível | Stack Overflow, WikiSQL, schemas de projetos open-source. |
| Utilidade prática | Geração de queries, otimização de schemas, assistente de banco de dados. |

---

## 2. Abordagem Técnica

### 2.1 Parser

**Decisão:** Usar o tokenizador universal existente (espaço + pontuação). **Sem tree-sitter.**

Isso reforça o Teorema 1 (Genericidade Paramétrica): se o mesmo tokenizador burro que parseia `function...end` e `public class...` também clusteriza `SELECT...FROM...WHERE`, a genericidade é do kernel, não do parser.

Tratamento especial: strings literais entre aspas simples (`'...'`) serão mantidas como um token único, preservando o texto interno. O tokenizador atual já agrupa entre aspas.

### 2.2 Cold Start

Pipeline idêntico ao usado em Lua e C#:

1. `IngestionAgent` varre arquivos `.sql`
2. `raw_token_set` extrai tokens via tokenizador universal
3. `SignatureAnalyzer` agrupa por assinatura de transição + entropia
4. Geração de snippet SQL sintaticamente válido

### 2.3 Sandbox (ShadowSQLite)

Executor determinístico e seguro:

| Permitido | Bloqueado |
|-----------|-----------|
| `SELECT` | `DROP` |
| `CREATE TABLE` | `ALTER` |
| `INSERT` | `TRUNCATE` |
| `UPDATE` | `EXEC`, `xp_cmdshell` |
| `DELETE` | `PRAGMA` (perigoso) |

- SQLite em memória (`:memory:`)
- `PRAGMA journal_mode=OFF`
- Timeout de 500ms por query
- Saída capturada como string (erro de sintaxe = anomalia)

### 2.4 Métricas de Sucesso

1. **Cold Start < 2s:** O sistema minera corpus SQL, extrai assinaturas, agrupa por entropia e gera snippet válido
2. **Detecção de anomalias:** `WorldAnomalyDetector` distingue `SELECT` válida de query com tokens inventados (sem ajuste manual)
3. **Geração funcional:** Prompt "Crie uma tabela de usuários com nome, email e senha" → `CREATE TABLE` executável no sandbox
4. **Sem modificação no kernel:** O `mcr_kernel` opera em SQL com os mesmos binários de Lua e C#

---

## 3. Cronograma

### Dia 1 — Corpus e Validador

**Entregas:**
- Corpus de ~100 arquivos `.sql` coletados (schemas open-source, queries do Stack Overflow, WikiSQL)
- `SanityValidatorSQL` implementado usando o tokenizador universal
- Teste: validador reconhece estrutura mínima de `SELECT`, `CREATE TABLE`, `INSERT`

**Riscos:** Corpus muito homogêneo (só `SELECT` simples). Mitigação: incluir schemas reais de projetos como WordPress, Django, Rails.

### Dia 2 — Cold Start e Assinaturas

**Entregas:**
- `cold_start` executado com domínio SQL
- Clusters de assinaturas correspondendo a `CREATE TABLE`, `SELECT...FROM...WHERE`, `INSERT INTO`
- Relatório de entropia por cluster

**Riscos:** Tokenizador universal não agrupa `SELECT * FROM users WHERE id = 1` adequadamente. Mitigação: verificar se o delimitador `*` e `=` são tratados como tokens separados (esperado: sim, pontuação).

### Dia 3 — Integração ao Pipeline

**Entregas:**
- `PipelineCompleto` adaptado para gerar SQL
- Prompt "Crie uma tabela de log de eventos" → `CREATE TABLE events (id INTEGER, ...)` válido
- Prompt "Busque todos os usuários ativos" → `SELECT * FROM users WHERE active = 1`

**Riscos:** Prompt muito aberto gera SQL sem sentido. Mitigação: templates de prompt minimalistas (o mesmo approach usado para Lua e C#).

### Dia 4 — Sandbox e Shadow Learning

**Entregas:**
- `ShadowSQLite` implementado e integrado
- Queries geradas são executadas; erros de sintaxe viram penalidades simbólicas
- Ciclo de aprendizado: query → execução → erro → ajuste de pesos

**Riscos:** Timeout de 500ms muito curto para queries complexas. Mitigação: queries geradas são simples (1-2 cláusulas), dentro do limite.

### Dia 5 — Prova de Universalidade

**Entregas:**
- Três Cold Starts lado a lado: Lua, C#, SQL
- Tabela comparativa: entropia média, número de clusters, tempo de convergência, diversidade de tokens
- Relatório final

---

## 4. Arquivos a Modificar/Criar

| Arquivo | Ação |
|---------|------|
| `docs/plans/terceiro_dominio_sql.md` | ✅ Este documento |
| `src/validation/sanity_validator_sql.py` | Criar (validador usando tokenizador universal) |
| `src/sandbox/shadow_sqlite.py` | Criar (sandbox SQLite em memória) |
| `tests/test_domain_sql.py` | Criar (testes de cold start, geração, sandbox) |
| `src/pipeline/pipeline_completo.py` | Modificar (registrar domínio SQL) |

Nenhuma modificação no `mcr_kernel` — essa é a condição da prova.

---

## 5. Validação Cruzada

Após o Dia 5, executar:

```
python -c "from mcr_kernel import MCR; m = MCR(); m.cold_start('lua'); m.cold_start('cs'); m.cold_start('sql')"
```

Se os três rodarem com o mesmo binário, a tese está provada.
