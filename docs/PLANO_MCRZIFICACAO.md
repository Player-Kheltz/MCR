# 📋 PLANO MCR'ZIFICAÇÃO — Aplicando o Conceito MCR ao Próprio MCR

> **Data:** 2026-06-30
> **Conceito:** Tudo é Markov de transições. Mesmo algoritmo. N níveis. Zero hardcode.

---

## O Conceito MCR (Regra de Ouro)

```
TODO padrão é uma TRANSIÇÃO entre dois estados consecutivos.
O MCR descobre a transição → aprende o padrão → usa para decidir.
Aplica-se a: bytes, letras, palavras, tokens, intenções, ações, decisões.

MarkovUniversal: 1 classe, 1 algoritmo, N níveis.
  mk_byte → mk_palavra → mk_token → mk_intencao → mk_acao → loop
```

### Pilares validados nos protótipos

| # | Pilar | Protótipo | Status |
|---|-------|-----------|--------|
| 1 | **MarkovByte** — transições de bytes discriminam intenção | `prototipo_mcr_byte_unico.py` | ✅ CREATE vs EXPLAIN: 0.026 (10x melhor que bytes brutos) |
| 2 | **MarkovUniversal** — 1 classe, N níveis | `prototipo_mcr_loop_infinito.py` | ✅ Mesmo código para byte, palavra, token, intenção, ação |
| 3 | **Zero INTENT_*/DOM_*/PAL_*** — fingerprint por palavras reais | `prototipo_mcr_puro.py` | ✅ 11 dimensões, 0% tipos meus |
| 4 | **Fingerprint dinâmico** — N varia com entropia | `prototipo_regra_de_ouro.py` | ✅ 16-32 dims (vs 64 fixo) |
| 5 | **Threshold adaptativo** — mediana dos dados | `prototipo_regra_de_ouro.py` | ✅ 0.085 baseado em 10 amostras |
| 6 | **Ações agrupadas** — ferramentas por contexto de uso | `prototipo_regra_de_ouro.py` | ✅ 3 grupos: buscar_kg, buscar_estrategico, ler_arquivo |
| 7 | **MCR Conectado** — aprende com sandbox real | `prototipo_mcr_conectado.py` | ✅ 369 itens, 4 fontes, 7 Markove |
| 8 | **MarkovDecisor** — MCR decide qual ferramenta usar | `prototipo_mcr_decision.py` | ✅ 5 execuções, 5 decisões coerentes, 0 if/else |
| 9 | **Auto-Loop** — executa → nota < 10 → expande → repete | `prototipo_mcr_autoloop.py` | ✅ Ciclo funciona (mas métrica precisa de Jaccard) |
| 10 | **Filtro MCR** — Jaccard de bytes avalia relevância de lessons | `prototipo_filtro_mcr.py` | ✅ Lesson ruim foi de #1 para #9. Boa foi para #1. |

---

## O que MUDA com a MCR'zificação

### Módulos que PODEM ser substituídos por MCR.py

| Módulo Atual | Linhas | O que faz | MCR.py substitui por |
|-------------|--------|-----------|----------------------|
| `lexico_v2.py` | ~350 | INTENT_*, DOM_*, PAL_* hardcoded | MarkovByte + MarkovToken descobrem padrões sozinhos |
| `intention_engine.py` | ~340 | 3 camadas com regras | MarkovPalavra + MarkovToken agrupam por transição |
| `auto_trigger.py` | ~250 | Ações fixas (buscar_kg, etc.) | MarkovDecisor escolhe ação por Markov de execução |
| `pipeline_executor.py` (decisões) | ~500 | if/else de entropia, níveis fixos | AutoLoop + Autoavaliação decidem o fluxo |
| `aprendiz_de_padroes.py` | ~550 | Aprende mas não re-treina | Re-treino automático a cada N execuções |
| **Total substituído** | **~1990** | | **~350 linhas em MCR.py** |

### Módulos que RECEBEM MCR internamente

| Módulo | O que ganha |
|--------|-------------|
| `kg.py` | **Filtro MCR**: `buscar()` avalia Jaccard de bytes antes de retornar |
| `validation_pipeline.py` | **Autoavaliação por Jaccard**: nota real baseada em transições, não em cobertura de tipos |
| `auto_repair.py` | **MarkovByte de código válido** para detectar e regenerar anomalias |
| `pattern_engine.py` | **FingerprintByte + FingerprintDinâmico**: N dimensões calculado por entropia |
| `pi_engine.py` | **Predizer universal**: funciona para qualquer nível (byte, token, ação) |

### Módulos que SÃO SUBSTITUÍDOS pelo conceito MCR

| Conceito antigo | Substituído por |
|----------------|-----------------|
| Conselho V10 (conselho.py) | Inception: N workers com N temperaturas |
| TreeOfThought (3 perspectivas fixas) | N workers com N temperaturas (MCR descobre quantas) |
| Reconstructor (KG Weaver) | MarkovByte + Jaccard encontra lessons similares |
| V12 Contexto (supervisor.py) | MarkovDecisor decide se precisa de mais contexto |
| BlankFiller (LLM preenche blanks) | MarkovByte gera conteúdo do blank (0 LLM) |

---

## Arquitetura do MCR.py (o módulo único)

```python
class MCR:
    """Módulo ÚNICO. Substitui lexico_v2 + IE + AutoTrigger + Aprendiz + Decisor.
    
    5 Markove integrados no mesmo conceito:
      mk_byte → mk_palavra → mk_token → mk_intencao → mk_acao → loop
    """
    
    def __init__(self):
        # Markove de percepção
        self.mk_byte = MarkovUniversal("byte")      # Transições de bytes
        self.mk_palavra = MarkovUniversal("palavra") # Transições de palavras
        self.mk_token = MarkovUniversal("token")     # Transições de tipos PE
        
        # Markove de decisão
        self.mk_intencao = MarkovUniversal("intencao")  # Intenção → grupo
        self.mk_acao = MarkovUniversal("acao")          # Ação → resultado
        self.mk_decisor = MarkovUniversal("decisor")    # Estado → ação
        
        # Markove de aprendizado
        self.mk_filtro = MarkovUniversal("filtro")      # Pergunta → relevância
    
    def processar(self, pergunta) -> str:
        """Ciclo completo: executa → nota < 10 → expande → executa de novo."""
        ...
    
    def avaliar(self, resposta, pergunta) -> float:
        """Autoavaliação por Jaccard de transições de bytes."""
        ...
    
    def filtrar(self, pergunta, lessons) -> List:
        """Filtra lessons por relevância (Jaccard de bytes)."""
        ...
    
    def decidir(self, estado) -> str:
        """MarkovDecisor escolhe ação baseado no estado."""
        ...
    
    def aprender(self, execucao):
        """Registra execução e re-treina Markove."""
        ...
```

---

## O que NÃO muda (compatibilidade mantida)

| Item | Motivo |
|------|--------|
| `kernel.py` | Entry point — bootstrap, não lógica |
| `ia.py` | Interface com Ollama — hardware, não padrão |
| `tool_orchestrator.py` | Bridge para ferramentas — executa, não decide |
| `kg.py` (API pública) | `buscar()`, `aprender()` continuam existindo — só ganham filtro MCR |
| `pattern_engine.py` | `tokenizar_universal()` continua — só adiciona FingerprintByte |
| `pipeline_executor.py` | Pipeline continua — só decisões viram MarkovDecisor |
| `comandos/` (54 comandos) | Todos continuam funcionando — MCR só melhora as decisões internas |
| `sandbox/` | Todos os dados continuam sendo lidos — MCR passa a USÁ-LOS |

---

## Plano de Implementação (ordem recomendada)

| Fase | O quê | Baseado em | Risco | Esforço |
|------|-------|-----------|-------|---------|
| **1** | `MCR.py` — classe MarkovUniversal + Autoavaliação + Filtro | Todos os protótipos | Baixo | ~350 linhas |
| **2** | Integrar FiltroMCR no `kg.buscar()` | `prototipo_filtro_mcr.py` | Baixo | ~20 linhas no kg.py |
| **3** | Substituir `_decidir()` no pipeline por MarkovDecisor | `prototipo_mcr_decision.py` | Médio | ~30 linhas |
| **4** | Autoavaliação por Jaccard substituir cobertura de tipos | `prototipo_mcr_autoloop.py` | Médio | ~25 linhas |
| **5** | Re-treino automático dos Markove a cada N execuções | `prototipo_mcr_conectado.py` | Médio | ~40 linhas |
| **6** | FingerprintByte no `pattern_engine.py` | `prototipo_mcr_puro.py` | Baixo | ~30 linhas |
| **7** | Remover `lexico_v2.py` + `intention_engine.py` (opcional) | Só após Fase 1-6 estáveis | Alto | ~0 linhas (só deletar) |

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| MCR.py substitui módulos existentes e algo quebra | Módulos antigos CONTINUAM EXISTINDO. MCR.py é ADD-ON. Só remove quando 100% estável. |
| Autoavaliação por Jaccard pode ser baixa para textos curtos | Usar JANELA: comparar pergunta com primeiros 50 chars da resposta |
| MarkovDecisor precisa de muitas execuções para aprender | Fallback plano por intenção (CREATE → buscar_estrategico, EXPLAIN → buscar_kg) até Markov aprender |
| Threshold de relevância (Jaccard) pode variar muito | Threshold = MEDIANA das similaridades observadas + 0.05 (descoberto, não fixo) |

---

## Métricas de Sucesso

| Métrica | Atual | MCR'zificado | Meta |
|---------|-------|-------------|------|
| Linhas de código de decisão | ~1990 (4 módulos) | ~350 (1 módulo) | **-82%** |
| Hardcode de tipos | INTENT_*, DOM_*, PAL_* (centenas) | Zero | **100% eliminado** |
| if/else de decisão | Dezenas no pipeline | Zero | **100% eliminado** |
| Thresholds fixos | 0.5, 0.85, 0.3 | Medianas dos dados | **100% adaptativo** |
| Relevância do KG | Qualquer lesson com a palavra | Só lessons com Jaccard > threshold | **10x mais relevante** |
| Decisão de ferramenta | if/else no pipeline | MarkovDecisor aprende | **Zero hardcode** |
