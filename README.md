# MCR — Motor Cognitivo Universal

> **1 Equação. 1 Entropia. 1 Markov. N domínios.**

MCR é um framework cognitivo que usa cadeias de Markov de 1ª ordem como substrato para perceber, decidir, executar, avaliar e aprender. A mesma Equação MCR avalia qualquer saída — NPC de Tibia, sprite PNG, texto, ou qualquer outro domínio.

**Sem GPU. Sem nuvem. Sem LLM obrigatório.**

```python
from mcr import MCR
mcr = MCR()
mcr.auto_treinar()
npc = mcr.processar("Crie um ferreiro anão")      # gera Lua válido
sprite = mcr.processar("Gere um sprite de escudo") # gera PNG
```

---

## Arquitetura

```
                EQUAÇÃO MCR + ENTROPIA + MARKOV
                          │
                          ▼
              ┌───────────────────────┐
              │         MCR           │
              │   Cognição Universal  │
              │                       │
              │  perceber → decidir   │
              │  → executar →         │
              │  avaliar → aprender   │
              └───────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
      ┌───────┐     ┌──────────┐     ┌─────────┐
      │ TIBIA │     │  VISUAL  │     │ (áudio, │
      │  (prova)   │  (prova) │     │  outro  │
      │        │     │          │     │  jogo…) │
      └───────┘     └──────────┘     └─────────┘
```

3 domínios atualmente funcionais. O motor é o mesmo — só as ferramentas mudam.

---

## O Núcleo

### Equação MCR

```
PONTE_OTIMA = (divergência × 2 + especificidade × 3 + profundidade × 2) / 10
NOTA_FINAL  = PONTE_OTIMA × (1 − PENALIDADE)
```

A mesma equação avalia tudo:
- **NPC Tibia:** é único? é bem definido? é detalhado?
- **Sprite:** é original? é nítido? é complexo?
- **Texto:** é novo? é preciso? é profundo?

### Motor Markov Multi-Nível (Kernel)

| Componente | Arquivo | Função |
|-----------|---------|--------|
| `MCR` | `motor/engine.py` | Markov 1ª ordem: aprender, predizer, entropia, Jaccard |
| `MCRFingerprint` | `motor/signature.py` | Assinatura 8D de qualquer dado |
| `EquacaoMCR` | `equacao/equacao_mcr.py` | Avaliação universal (div×2 + esp×3 + prof×2) |

### Pipeline Unificado

| Estágio | Descrição |
|---------|-----------|
| **Perceber** | Extrai fingerprint 8D + palavras-chave → estado composto |
| **Decidir** | Markov prediz ação + fallback por similaridade de componentes |
| **Executar** | Registry seleciona ferramenta por matching de nome |
| **Avaliar** | Equação MCR mede divergência, especificidade, profundidade |
| **Aprender** | Markov reforça transições bem-sucedidas (3× se nota > 0.7) |

---

## Estrutura do Projeto

```
mcr/
├── mcr.py                     ← Cognição unificada (657 linhas)
├── motor/                     ← Núcleo Markov (intacto)
│   ├── engine.py              ← MCR: aprender, predizer, entropia
│   └── signature.py           ← MCRFingerprint, MCRSignature
├── equacao/                   ← Equação MCR (intacta)
│   └── equacao_mcr.py         ← calcular_ponte, get_penalidade
├── ferramentas/               ← Plugins de domínio
│   ├── tibia/                 ← NPC, monstro, quest, diálogo
│   └── visual/                ← Sprite, regiões, template
├── autonomia/                 ← Auto-estudo, auto-evolução
├── qualidade/                 ← Metacognição, verificação, cache
├── servicos/                  ← SSE Server, Bridge API, Observer
├── infra/                     ← Paths, registry, bootstrap, SQLite
│
devia/kernel/mcr_kernel/       ← Kernel legado (preservado)
│   ├── engine.py
│   ├── decisor.py
│   ├── memory.py
│   └── ...
│
tools/grimorio/                ← Painel admin C# WPF
docs/                          ← Documentação
tests/                         ← Testes
```

---

## Domínios Comprovados

### Prova 1: Tibia (Geração de Conteúdo)

| Ferramenta | Descrição | Tier |
|-----------|-----------|------|
| `gerar_npc_lua` | NPC Canary via template (zero LLM, 0ms) | 1 |
| `gerar_monstro_lua` | Monstro Canary via template | 1 |
| `mcr_world_builder` | Geração LLM com validação Sanity+Shadow | 2-3 |
| `dialogue_trainer` | Treino Markov com 448 NPCs, 4529 diálogos | — |
| `lua_validator` | Validação sintática + SQL injection + boas práticas | — |
| `sanity_validator` | 6445 APIs Canary conhecidas (zero hardcode) | — |

### Prova 2: Visual (Geração de Sprites)

| Ferramenta | Descrição |
|-----------|-----------|
| `sprite_corpus` | Corpus de sprites categorizados + extração B/L/F |
| `MCRDiscriminador` | Avalia qualidade via P(token | contexto) |
| `mcr_sprite_motor` | Motor 4-níveis Markov (byte, palavra, token, cor) |
| `template_entropico` | Template Shannon: baixa H = fixo, alta H = criativo |
| `regioes_anatomicas` | Segmentação projeção 1D + clusterização CIELAB |

---

## Setup

```powershell
# Núcleo (zero dependências):
python -c "from mcr import MCR; print('MCR pronto')"

# Com auto-treinamento:
python -c "from mcr import MCR; m = MCR(); m.auto_treinar()"

# Aplicação Tibia (requer Ollama para Tier 2-3):
# 1. ollama pull qwen2.5-coder:7b
# 2. ollama pull mistral:7b
# 3. python mcr/servicos/sse_server.py
# 4. http://localhost:8765

# Servidor NPC (zero LLM):
# python mcr/ferramentas/tibia/servidor.py
```

---

## Estado Atual

| Métrica | Valor |
|---------|-------|
| Classificação de ações | 14/14 (100%) |
| Ferramentas registradas | 285 |
| NPCs treinados (diálogo) | 448 |
| Diálogos aprendidos | 4529 |
| Vocabulário único | 4959 |
| APIs Canary conhecidas | 6445 |
| Imports verificados | 20/20 |
| Código Lua gerado | ✅ Estruturalmente válido |

---

## Limitações Honestas

1. **Markov de 1ª ordem.** O motor só vê o estado atual. Não modela dependências de longo alcance. `compose_state()` mitiga isso compondo contexto no nome do estado, mas o limite é fundamental.

2. **Classificação depende de seeds.** O MCR classifica entradas comparando com estados pré-treinados. Sem seeds suficientes, a confiança é baixa e o sistema usa fallbacks. Quanto mais exemplos, melhor funciona.

3. **Templates são determinísticos.** `golden_templates.py` (Tier 1) gera código estruturalmente válido mas não entende semântica. "Crie um ferreiro que vende armaduras" gera um NPC chamado "Ferreiro Vende Armaduras" — sem shop_items preenchidos automaticamente.

4. **Semântica complexa requer LLM.** Para descrições ricas (quests, diálogos, lore), o pipeline Tier 2-3 (`mcr_world_builder`) usa Ollama. O MCR decide SOZINHO quando usar LLM (via `hybrid_router`), mas o LLM é necessário para qualidade máxima em alguns domínios.

5. **Equação com parâmetros calibrados.** Os pesos (div×2, esp×3, prof×2) foram calibrados em um commit específico. O `mcr_auto_evolution` pode reajustá-los, mas o processo é lento e requer muitas iterações.

6. **Nome extraído por heurística.** `_extrair_nome()` remove stopwords e concatena palavras restantes. Funciona para entradas simples, falha para descrições complexas.

---

## Licença

**AGPL v3** ou licença comercial. Veja [LICENCA_COMERCIAL.md](LICENCA_COMERCIAL.md).

---

## Autor

**Kheltz** — Pesquisador independente.
