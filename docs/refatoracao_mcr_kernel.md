# Refatoração do MCR.py → Pacote `mcr_kernel/`

## Objetivo

Quebrar o arquivo monolítico `devia/kernel/MCR.py` (7.072 linhas, 49 classes, 7 funções globais) em um pacote Python modular **sem alterar a matemática, a lógica ou os nomes das classes públicas**.

## Estrutura Final

```
devia/kernel/
├── MCR.py              ← Thin wrapper (re-exporta tudo do pacote)
├── mcr_kernel/         ← Pacote com 10 módulos
│   ├── __init__.py     ← Re-exporta todas as classes públicas
│   ├── engine.py       ← Núcleo Markov: MCR, MCRBridge, MarkovUniversal
│   ├── signature.py    ← Assinaturas: MCRFingerprint, MCRSignature, _SIG_CACHE
│   ├── decisor.py      ← Decisão: MCRPeso, MCREntropia, MCRRuido, MCRDecisor,
│   │                     MCRDiagnostico, MCRPesoNota, MCRThreshold e globais
│   ├── memory.py       ← Memória: _get_kg, MCRBufferKG, MCRConector, MCRCruzado,
│   │                     MCRCadeia, MCRKGAuto, CONECTORES
│   ├── persistence.py  ← Persistência: MCRDocIndex, MCRFragmento, MCRFragmentador,
│   │                     MCRSegmentador, MCRPersistencia
│   ├── meta.py         ← Metacognição: MCRMeta, MCRNivel, MCRMetaNivel, MCRMetaGap,
│   │                     MCRSelfIndex, MCRSelfHeal
│   ├── evolution.py    ← Evolução: MCRTarefa, MCRWorker, MCRSpawner, MCRExpansao,
│   │                     MCRFuel, MCRAutoMelhoria
│   ├── feedback.py     ← Feedback: MCRFilosofia, MCRFeedback, MCRSession,
│   │                     MCRAssinatura, MCRWebLearn
│   ├── system.py       ← Sistema: MCRSystem, MCRPergunta, MCRMestre, MCRMestreV2,
│   │                     MCRGeracao, AutoavaliadorSemantico, GeradorNarrativa
│   └── state.py        ← Estado: _MCR_STATE, _MCR_DATA, MCRAutoStart, MCRBoot
```

## Diagrama de Dependências

```
engine.py  ────────────────────────────────── (zero importações do pacote)
    │
    ├──→ signature.py  ──── (engine.MCR)
    │
    ├──→ decisor.py    ──── (engine.MCR)
    │
    ├──→ memory.py     ──── (engine.MCR + signature.MCRSignature + decisor.*)
    │
    ├──→ persistence.py ─── (engine.MCR + signature.MCRSignature)
    │
    ├──→ meta.py       ──── (engine.MCR + decisor.* + memory._get_kg + persistence._get_doc_index)
    │
    ├──→ evolution.py  ──── (engine.MCR + decisor.* + memory._get_kg + persistence._get_doc_index)
    │
    ├──→ feedback.py   ──── (engine.MCR + signature.MCRSignature + memory.MCRCadeia + meta.MCRMetaGap + system.MCRMestreV2)
    │
    └──→ system.py     ──── (engine.MCR + signature.* + decisor.* + memory.* + evolution.* + feedback.MCRFeedback + meta.MCRMetaGap)
         │
         └──→ state.py ──── (engine.MCR + decisor.* + memory.* + persistence.* + meta.* + evolution.*)
```

**Regra de ouro:** Nenhum módulo importa de módulos de nível superior na ordem. A ordem de importação no `__init__.py` respeita a direcionalidade: engine → signature → decisor → memory → persistence → meta → evolution → feedback → system → state.

## Decisões Técnicas

### 1. Duplicata MCRThreshold removida
- **1ª definição** (linha 3408): removida — **nenhum consumidor real**
- **2ª definição** (linha 3457): mantida — inclui método `aprender()` extra
- Todas as instanciações do sistema usam a 2ª definição

### 2. Global _MCR_THRESHOLD_* em decisor.py
As variáveis globais `_MCR_THRESHOLD_FILTRO`, `_MCR_THRESHOLD_CONF`, etc. foram movidas para `decisor.py`. Módulos que as usam importam-nas com:
```python
from .decisor import _MCR_THRESHOLD_TAMANHO
```
Isso evita quebra na interface das funções que as referenciam.

### 3. _SIG_CACHE global em signature.py
O cache global de assinaturas MCR foi movido para `signature.py`, evitando múltiplas definições inconsistentes.

### 4. MCR.Nivel = MarkovUniversal
O alias `MCR.Nivel = MarkovUniversal` está em `engine.py`, mantendo compatibilidade com código que acessa `MCR.Nivel`.

### 5. _autotestar() em __init__.py
A função de auto-teste foi movida para `__init__.py` do pacote, e é re-exportada pelo wrapper `MCR.py`.

## Wrapper MCR.py

O arquivo original `MCR.py` foi substituído por um thin wrapper:
```python
from mcr_kernel import *
from mcr_kernel import _MCR_DATA, _MCR_STATE, _get_kg, _autotestar, MCR_COMPLETO
```

Isso garante que **todos os imports existentes continuam funcionando**:
- `from MCR import MCR, MCRSystem, MCRDecisor` (legado)
- `from devia.kernel.MCR import MCR, MCRFingerprint` (absoluto)
- `import MCR as _MCR; _MCR.MCR(...)` (import do módulo)

## Resultados

- **7072 linhas → 10 módulos gerenciáveis** (média ~500-800 linhas/módulo)
- **Zero alteração na matemática** — jaccard, entropia, predição, thresholds idênticos
- **Zero alteração na API pública** — todos os imports originais preservados
- **Auto-teste** passou: 24/24 testes nucleares OK
- **Pronto para Prioridade 2** (Teste de Domínio Cruzado)

## Observações

- `from modulos.MCR import ...` continua falhando silenciosamente (mesmo comportamento do original, nenhum caminho de código ativo depende disso)
- MCRBufferKG é singleton e não possui método `_get_licoes()` — mesmo comportamento do original (chamadas a este método em MCRMetaGap falham com o mesmo comportamento)
- `MCRBridge.usar_comando()` não existe na classe base — qualquer chamada a ele falha com AttributeError (mesmo comportamento do original)
