# Pattern Engine Universal — Reconhecimento de Padrões em QUALQUER Domínio

**Data**: 2026-06-30
**Status**: Implementado
**Arquivo**: `scripts/mcr_devia/modulos/pattern_engine.py`

---

## Conceito

Tudo que existe no MCR-DevIA pode ser tokenizado → ter seus padrões extraídos → receber um fingerprint único → ser posicionado no eixo NIRVANA↔CAOS → e receber uma sugestão de PRÓXIMO PASSO ÓTIMO.

Isso funciona para código, texto, logs, KG, comportamento — QUALQUER domínio. O padrão está no PRESENTE. O passado só confirma. O futuro só direciona.

## Tokenização por domínio

| Domínio | O que é um token | Como extrair |
|---------|-----------------|-------------|
| **Código** | AST node, indent level, keyword | `ast.parse()` + `tokenize` |
| **Texto** | Palavra, pontuação, POS tag, tamanho de frase | `re.findall()` + métricas |
| **Logs** | Tipo de evento, timestamp, erro | `json.loads()` em `.jsonl` |
| **KG lessons** | Contexto, timestamp, tamanho, autor | `kg._get_licoes()` |
| **Comportamento** | Ação, resultado, tempo de execução | `master_agent._passos` |

## Métodos da PatternEngine

| Método | Descrição | Domínios |
|--------|-----------|----------|
| `tokenizar(entrada, dominio)` | Quebra em tokens | código, texto, logs, kg, comportamento |
| `extrair_padroes(tokens)` | n-gramas, Markov, entropia | todos |
| `fingerprint(tokens)` | Vetor único de 256 dimensões | todos |
| `similaridade(fp_a, fp_b)` | Cosseno entre vetores | todos |
| `eixo_nirvana_caos(tokens)` | 0=Caos, 1=Nirvana | código, texto |
| `sugerir_proximo(tokens, padroes)` | Ação para melhorar | código, texto |
| `aprender(entrada, resultado)` | Salva no KG | todos |

## Integração com componentes

| Componente | Uso | Status |
|-----------|-----|--------|
| Self-Study | fingerprint p/ health score | ✅ |
| EMERGIR | Markov em vez de aleatório | ✅ |
| Auto-Repair | fingerprint do erro → causa raiz | ✅ |
| DiagnosticEngine | eixo Nirvana↔Caos | ✅ |
| ToolOrchestrator | ferramenta #28 `pattern_analyze` | ✅ |
| Kernel/CLI | comando `--pattern` | ✅ |
