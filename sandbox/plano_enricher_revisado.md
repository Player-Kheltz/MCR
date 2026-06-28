# 📋 PLANO REVISADO: Context Enricher Universal
**Versão:** 1.1 (revisado após consulta ao MCR-DevIA + análise real do código)
**Data:** 27/06/2026

---

## 🔍 O que aprendemos com a consulta ao MCR-DevIA

| Fonte | Achado | Impacto no plano |
|-------|--------|-----------------|
| KG query | Nenhuma lição sobre enriquecimento de contexto | Precisamos construir do zero |
| _componentes() análise | Só ativa para keywords de lore | Enricher deve funcionar para QUALQUER pergunta |
| Alucinação "Minecraft C++ Reloaded" | 7b ainda alucina mesmo com contexto | Enricher factual usa FERRAMENTAS, NÃO FAST |
| "3 maiores problemas" genéricos | O modelo fabrica problemas que não existem | Nunca confiar 100% na análise do MCR-DevIA |

## 📐 Arquitetura Final

```
PERGUNTA → CR (desambigua) → ENRICHER (gera conteudo) → ORQUESTRADOR (responde)
                                |
                    ┌───────────┴───────────┐
                    ↓                       ↓
           FAST classifica           FERRAMENTAS geram
           o que está faltando:      o conteudo:
           - nomes proprios?    →    FAST (criativo)
           - dados tecnicos?    →    grep + leitura de arquivos
           - curiosidades?      →    weblearn + KG
           - codigo exemplo?    →    grep + leitura de arquivos
           - comparacao?        →    FAST estrutura dados
                    |
                    ↓
           BLOCO [CONTEXTO ENRIQUECIDO] injetado no prompt
           (Orquestrador NAO sobrescreve este bloco)
```

## 🔴 Prioridade 1: Módulo `context_enricher.py`

### Estrutura

```python
class ContextEnricher:
    def enriquecer(pergunta, termos, ctx_crew, kg) -> dict:
        """
        Retorna:
        {
            'tipo': 'lore_nomes' | 'tecnico_dados' | 'factual_curiosidade' | 'generico_reforco',
            'conteudo': 'bloco formatado para injecao no prompt',
            'valido': bool,  # False se gerou algo muito generico
        }
        """
```

### Método `_classificar_carencia(pergunta)` → tipo

FAST classifica em UM de:

| Tipo | Exemplo de pergunta | O que gera | Como gera |
|------|--------------------|-----------|-----------|
| `lore_nomes` | "crie lore para Eridanus" | NPCs, lugares, artefatos | FAST (criativo) com template específico + validação |
| `lore_eventos` | "história de Eridanus" | Fundação, eras, batalhas | FAST + weblearn (inspiração) |
| `tecnico_detalhes` | "o que é .lua?" | Caminhos reais de arquivos, funções, APIs | **grep** no código + leitura de arquivos |
| `tecnico_dados` | "como funciona o SPA?" | Números, versões, domínios, níveis | KG + grep + scripts Python |
| `factual_curiosidade` | "conte algo sobre MCR" | Fatos do projeto, contexto histórico | KG + weblearn |
| `comparacao` | "diferença SPA vs SHC?" | Tabela comparativa | FAST estrutura dados do KG |
| `generico_reforco` | qualquer pergunta genérica | Combinação de todos acima + verificação de qualidade | Pipeline completo |

### Método `_gerar_lore(tema)` → bloco de nomes

```python
# NÃO usa prompt hardcoded "em Tibia"
# Usa MCR_IDENTITY para determinar o contexto temático
# Gera 3 rodadas e escolhe a melhor (com mais nomes proprios)
```

### Método `_gerar_tecnico(termos)` → bloco técnico

```python
# USA FERRAMENTAS: grep no codigo, leitura de arquivos
# 0 chamadas FAST para dados factuais
# Ex: para ".lua" → grep "\.lua" --include="*.py" encontra usos reais
```

### Validação obrigatória

TODO conteúdo gerado passa por validação:
- **Se factual** (tool-based): verificar se o arquivo/caminho existe de verdade
- **Se criativo** (FAST-based): contar nomes próprios. Se < 3, regenerar
- **Se alucinou Minecraft/Docker/Kubernetes/SPA=SinglePage**: descartar

---

## 🟡 Prioridade 2: Pipeline (`pipeline_executor._executar_ia()`)

### Fluxo revisado

```python
def _executar_ia(self, solicitacao, indice=0):
    # 0. CR (existente) → desambigua
    # 0.5. ENRICHER (NOVO) → gera conteudo
    enricher = ContextEnricher()
    enriquecimento = enricher.enriquecer(solicitacao, termos, ctx_crew, kg)
    if enriquecimento['valido']:
        params['contexto_enriquecido'] = enriquecimento['conteudo']
    
    # 1. ctx_infinity (existente)
    # 2. Orquestrador com params enriquecidos
```

### Proteções
- Se Enricher falhar ou retornar inválido → pipeline continua SEM enriquecimento
- Cache LRU: mesma pergunta = mesmo enriquecimento (5 min TTL)
- Timeout: 15s no total para toda a etapa de enriquecimento

---

## 🟡 Prioridade 3: Orquestrador (template)

### Mudança MÍNIMA: só adicionar placeholder

```python
"perguntar": """{identidade}
{ctx_infinity}
{contexto_extra}
{instrucao_contexto}
{contexto_enriquecido}     # <<< NOVO

Pergunta: {pergunta}
..."""
```

### Por que posicionar AQUI?
- `{contexto_extra}` = o que ContextCrew BUSCOU (fontes)
- `{contexto_enriquecido}` = o que Enricher GEROU (conteúdo novo)
- O LLM vê o GERADO por último antes da pergunta → maior chance de usar

### Default vazio
```python
defaults = {
    ...
    'contexto_enriquecido': '',  # NOVO
}
```

---

## 🟢 Prioridade 4: Conselho — substituir `_componentes()`

### Diagnóstico do código ATUAL (conselho.py linhas 191-223)

| Problema | Local | Impacto |
|----------|-------|---------|
| Só ativa com keywords fixas ("historia", "lore", "npc"... ) | Linha 202-207 | Perguntas como "descreva Eridanus" não ativam |
| Gera com `_fast()` (1.5b) | Linha 220 | Nomes genéricos, sem validação |
| Salva no KG mesmo ruins | Linha 222 | Erro propagado para consultas futuras |
| Só 3 tipos (personagens, locais, artefatos) | Linha 215-219 | Sem eventos, facções, datas |

### Solução

```python
def _enriquecer_conselho(self, pergunta):
    """Substitui _componentes(). Usa Enricher universal."""
    from modulos.context_enricher import ContextEnricher
    enricher = ContextEnricher(ctx_crew=self.ctx_crew, kg=self.kg)
    resultado = enricher.enriquecer(pergunta, ...)
    if resultado['valido']:
        return resultado['conteudo']
    return ""
```

### Fallback
Se Enricher não disponível → chama `_componentes()` antigo (compatibilidade)

---

## 🟢 Prioridade 5: Mente + Supervisor + Auto-Revisor

### Mente (`think()`)
- **Antes** de carregar memórias: Enricher valida se o tema tem contexto suficiente
- Se não tem → weblearn é disparado (já existe no CR, mas reforçado aqui)

### Supervisor (`classificar()`)
- **Antes** de rotear: Enricher verifica se a classificação está correta
- Ex: se pergunta é factual e Enricher detectou que precisa de dados → confirma rota `factual/dado`

### Auto-Revisor (`revisar()`)
- **Depois** da resposta: verifica se ENRIQUECIMENTO foi usado
- Se contexto_enriquecido tinha 5 nomes e resposta usou 0 → marcar como genérica
- Se for genérica → pipeline pode regenerar automaticamente

---

## 📊 Matriz de Risco Revisada

| Risco | Prob | Impacto | Mitigação |
|-------|------|---------|-----------|
| **7b alucina enriquecimento factual** (ex: inventa caminho de arquivo) | ALTA | Crítico | **Ferramentas (grep, leitura) para tudo factual. FAST 0 para dados** |
| **Enricher gasta +15s por requisição** | Alta | Médio | Cache LRU + timeout 15s + fallback sem enriquecimento |
| **FAST gera nomes/lugares ruins** | Média | Baixo | Validação: < 3 nomes próprios = descarta e regenera |
| **Orquestrador sobrescreve contexto_enriquecido** | Média | Alto | Usar param NOVO (`contexto_enriquecido`) que Orquestrador não toca |

---

## ✅ Resumo do que MUDA em relação ao plano original

| Aspecto | Plano original | Plano revisado (v1.1) |
|---------|---------------|----------------------|
| Geração factual | FAST decide | **Ferramentas apenas** (grep, leitura, KG) |
| Injeção no template | `{contexto_enriquecido}` após pergunta | `{contexto_enriquecido}` **antes** da pergunta |
| Substituir `_componentes()` | Substituir imediatamente | **Chamar Enricher primeiro**, fallback para _componentes() |
| Validação de qualidade | Não prevista | **Obrigatória**: nomes próprios < 3 descarta |
| Cache | Não previsto | LRU 5 min (evita regenerar mesma pergunta) |
| Tempo máximo | Não definido | **15s timeout** para toda etapa |

---

## Próximos passos

1. ✅ Consulta ao MCR-DevIA concluída
2. ✅ Análise cruzada com código real concluída
3. ✅ Plano revisado e documentado
4. ⬜ **Aguardando autorização para implementar**
