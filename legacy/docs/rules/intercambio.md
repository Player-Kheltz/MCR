# Intercambio.md — Intercâmbio MCR ↔ Hub do Lojista

> Parte do sistema modular `docs/rules/`. Consulte `../AGENTS.md` para visão geral.
> **Contexto:** O time de 3 (Cloud + MCR-DevIA + Usuário) compartilha padrões com o Hub.
> O MCR-DevIA registra as lições de intercâmbio no KG via `ensinar` com ctx='intercambio'.

## Filosofia

**Não importa o domínio.** O que transferimos são **padrões, lógicas e soluções** que podem ser adaptados.

- MCR (servidor fantasia) resolve problema Y → Hub aprende o **padrão** Y, adapta ao Node/React
- Hub (varejo) resolve problema X → MCR aprende o **padrão** X, adapta ao contexto C++/Lua

> *"Olha, no MCR enfrentei um problema de bridge cair sem watchdog. Resolvi com auto-restart em 15s. Se no Hub você tiver um servidor Node que cai, sabe que a lógica é a mesma: health check + restart automático."*

## Exemplos Práticos de Transferência

### Problema no MCR → Lição para o Hub

| Problema Original (MCR/Fantasia) | Padrão Extraído | Aplicação no Hub |
|---|---|---|
| Bridge precisava de fallback quando Ollama offline: templates → cache → router → AI → "indisponível". | **Fallback em cascata com degradação graciosa** | API do Hub offline? Mostrar dados cacheados, depois mensagem amigável, nunca tela branca |
| Compilação demorava. Watcher reindexa RAG a cada 120s automaticamente. | **Processo watch em background** | `rag_watcher.py` reindexa código automaticamente |
| Bridge alternava entre 4 modelos conforme disponibilidade. | **Múltiplos provedores com fallback automático** | Se API principal cair, tentar fallback (cache local, depois mensagem) |
| RAG precisava sanitizar senhas/tokens antes de indexar. | **Sanitização antes de processar dados** | Filtrar tokens/credenciais antes de gerar embeddings |
| Watchdog reinicia bridge em 15s se morrer. | **Auto-restart com health check** | Servidor Node poderia ter flag `--watch` para restart automático |

### Problema no Hub → Lição para o MCR

| Problema Original (Hub/Varejo) | Padrão Extraído | Aplicação no MCR |
|---|---|---|
| `JSON.parse` crashava com dado inválido. Criaram `safeJsonParse<T>(str, fallback)`. | **Parsing seguro com fallback** | Dados Lua/XML/protocolo corrompidos: validar antes de usar, fallback pra padrão |
| `Alert.alert` não funciona no Expo Web. Criaram `ConfirmModal` com `Modal` nativo. | **Confirmação visual em vez de nativa** | Substituir `msgbox` por UI in-game para ações destrutivas |
| `taskkill /f /im node.exe` matava Expo junto. Criaram kill por porta via `netstat`. | **Matar processo por porta, não por nome** | `auto.py stop` pode usar `netstat` + PID em vez de `Get-Process` |
| Telas novas usavam cores hardcoded. Centralizaram em `theme.colors.*`. | **Tokens de design centralizados** | Centralizar cores/estilos em constantes Lua/C++ |
| Login silencioso travava. Diferenciaram erros de rede vs API vs 500. | **Error handling com categorias** | Diferenciar erros de conexão vs banco vs lógica nas mensagens pro jogador |

## Tabela de Intercâmbio Atual

### O que ensinamos ao Hub do Lojista

| Prática | Origem MCR | Implementação no Hub |
|---|---|---|
| Lições Aprendidas | `docs/lessons/` via `lesson.py` | `scripts/lesson.py` + `docs/lessons/` |
| Sync de CATALOG.md | `auto.py sync` → `doc-sync.py` | `server.py sync` → `scripts/doc_sync.py` |
| Session context | `auto.py session` | `server.py session` |
| Checkpoint recovery | `auto.py checkpoint` | `server.py checkpoint` |
| RAG watcher | `rag_watcher.py` | `scripts/rag_watcher.py` |
| Sanitização RAG | Redacta senhas antes de indexar | `rag_indexer.py` filtra tokens |

### O que aprendemos do Hub do Lojista

| Inovação | Descrição | Aplicável ao MCR? |
|---|---|---|
| **Knowledge Base curada** | `docs/knowledge/*.md` com fatos verificados | ✅ Sim — criar `docs/knowledge/` próprio |
| **Anti-halucination suite** | `validate_local.py` testa modelo antes de usar | ⚠️ Parcial — adaptar para bridge |
| **Kill por porta** | `server.py stop` mata PID via `netstat` | ✅ Sim — substituir `Get-Process` |
| **Protocolos anti-alucinação** | NAO_SEI, NAO_ENCONTREI, RAG_INSUFICIENTE | ✅ Sim — adotar nos prompts |
| **Swap seguro cloud/local** | `oc-dev.ps1` com backup + trap + restore | ✅ Sim — criar script similar |
| **AGENTS.md modular** | AGENTS.md como ponteiro, `docs/rules/` | ✅ Implementado |

## Rotina Autônoma de Aprendizagem Mútua

O assistente DEVE executar esta rotina **autonomamente** no início de cada conversa:

### Fluxo

```
Inicio da conversa
  → Ler docs/rules/intercambio.md do Hub do Lojista (se acessível)
  → Comparar com nosso docs/rules/intercambio.md
  → Há problema/lição nova no Hub que ensina um PADRÃO aplicável ao C++/Lua?
    ├── Sim → adaptar o padrão ao contexto MCR, registrar lição
    │         Ex: "Hub resolveu parsing seguro de JSON → MCR aplica mesma lógica em XML"
    └── Não → Há inovação nossa que o Hub pode aproveitar?
              ├── Sim → registrar lição com tag "intercambio" para referência futura
              └── Não → seguir normalmente
```

### Passo a Passo

**1. Ao iniciar conversa:**
Listar lições de intercâmbio do Hub para ver o que aprenderam conosco e o que nos ensinaram.

**2. Analisar cada lição do outro projeto perguntando:**
> *"Qual o PADRÃO por trás dessa solução? Esse padrão se aplica ao C++/Lua/Canary?"*

**3. Se o padrão for aplicável:**
Registrar lição documentando o padrão extraído e como adaptar.

**4. Se criamos inovação que ensina um padrão:**
Registrar lição com tag "intercambio" para referência futura do Hub.

### Exemplo de Aplicação

```
Contexto: MCR está implementando bridge com fallback de modelos.
          Descobre que cascata de fallback (template → cache → router → AI) 
          reduz chamadas de API em 62%.
          
Pergunta: Qual o PADRÃO? "Degradação graciosa com múltiplas camadas de fallback."
          Esse padrão se aplica ao Hub? Sim — se API do backend cair, 
          mostrar dados em cache, depois mensagem amigável.

Ação: Registrar lição com tag "intercambio" documentando o padrão.
```

### Quando NÃO fazer intercâmbio

- Quando a solução depende de uma biblioteca/framework que não existe no outro projeto E o padrão não pode ser extraído
- Quando o problema é puramente de configuração de ambiente (VS2022 vs Node, MySQL vs SQLite)
- **Regra de ouro:** Se existe um PADRÃO por trás da solução, ele é transferível. Se a solução é 100% específica do framework, não é.
