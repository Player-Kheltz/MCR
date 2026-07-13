# Fase 0 — Descobertas do PipelineUniversal

## Data: 11/07/2026
## Agente: Mimo V2.5 (Arquiteto)

---

## O que foi construído

### `mcr/pipeline_universal.py` (orquestrador 6 estágios)
- `PipelineUniversal` classe com 6 estágios: LOAD → TOKENIZE → TEMPLATE → FILL → VALIDATE → LEARN
- Todos os thresholds via `MCRThreshold` (zero hardcode)
- Detecção de loop via `MCREntropia`
- Nota composta via `MCRPesoNota`
- Decisão de fluxo via `MCRDecisor`
- Auto-melhoria via `MCRAutoMelhoria`
- Relatórios salvos em `poc_output/pipeline_universal/`

### `mcr/dominios/` (4 domínios registrados)
- **texto**: tokenizer = split() palavras — existente
- **codigo**: tokenizer = delimitadores universais (sem parser) — adaptado de `raw_token_set`
- **api**: tokenizer = delimitadores universais — adaptado de `raw_token_set`
- **sprite**: tokenizer = extrair_grid_papel → flatten B/L/F — existente

---

## O que funcionou

| Domínio | Score | Nota | Status |
|---------|-------|------|--------|
| texto | 1.000 | 1.010 | ✅ aceito |
| codigo | 1.000 | 1.010 | ✅ aceito |
| api | 1.000 | 1.010 | ✅ aceito |
| sprite | 0.000 | 0.710 | ⚠️ aceito (nota alta por PesoNota) |

## O que foi descoberto

### 1. `raw_token_set` retorna SET (perde ordem)
- API mining usa sets porque só importa QUAIS tokens existem, não a ordem
- PipelineUniversal precisa de SEQUÊNCIAS ORDENADAS para Markov
- **Solução**: usar mesmos delimitadores, mas preservar ordem (lista, não set)

### 2. Template entrópico em sequência 1D de pixels perde contexto 2D
- `extrair_template_entropico()` trata cada posição independentemente
- Para texto (1D), isso funciona perfeitamente
- Para sprite (2D flat em 1D), as relações espaciais são perdidas
- **Solução**: `MCRMetaNivel.auto_expandir()` descobre níveis superiores que capturam 2D

### 3. Thresholds estão em estado inicial
- `temperatura=0.5`, `limiar=0.5` — valores default
- Precisam de mais iterações para convergir para valores ótimos

---

## Módulos Órfãos — Status

| Módulo | Caminho | Conectado? | Como |
|--------|---------|------------|------|
| `template_entropico` | mcr/template_entropico.py | ✅ | Estágio 3 |
| `MCRThreshold` | devia/kernel/decisor.py | ✅ | Transversal |
| `MCRDecisor` | devia/kernel/decisor.py | ✅ | Transversal |
| `MCREntropia` | devia/kernel/decisor.py | ✅ | Transversal |
| `MCRPesoNota` | devia/kernel/decisor.py | ✅ | Estágio 5 |
| `MCRAutoMelhoria` | devia/kernel/evolution.py | ✅ | Estágio 6 |
| `MCRSignatureExpansiva` | mcr-universal/signature.py | ✅ | Estágio 2 (fingerprint) |
| `MCRMetaNivel` | devia/kernel/meta.py | ⚠️ | Importado, não chamado |
| `RadarMCR` | mcr/mcr_radar.py | ❌ | Pendente Fase 5 |
| `MCRDiscriminador` | mcr/meus_olhos.py | ❌ | Pendente Fase 1 (sprite refine) |
| `SignatureAnalyzer` | mcr/signature_cluster.py | ❌ | Pendente Fase 5 |
| `emergir_crossmodal` | mcr/emergir_crossmodal.py | ❌ | Pendente Fase 5 |
| `LuaValidator` | devia/modules/ | ❌ | Pendente |
| `npc_generator` | devia/modules/ | ❌ | Pendente |
| `fuel` | devia/kernel/evolution.py | ❌ | Pendente Fase 3 |
| `blank_filler` | devia/knowledge/ | ❌ | Pendente |

---

## Próximo Passo (Fase 1)

Refinar **domínio sprite**:
1. Usar `MCRMetaNivel` para descobrir níveis automáticos do sprite
2. Conectar `MCRDiscriminador` como validador
3. Template entrópico sobre NÍVEIS descobertos (não sobre pixels crus)
4. Gerar com temperatura adaptativa via `MCRThreshold`
