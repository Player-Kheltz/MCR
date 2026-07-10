# Estados Compostos — Memória Sintática sem Violar Markov 1ª Ordem

## Conceito

Estados Compostos permitem que a cadeia de Markov de 1ª ordem carregue
informação contextual adicional **no próprio rótulo do estado**, sem
aumentar a ordem da cadeia (que continuaria dependendo de 1 estado
anterior).

**Analogia:** Em vez de um estado ser apenas a palavra `"return"`,
ele passa a ser `"return|em_bloco:metodo|tipo_retorno:void"`. A cadeia
aprende transições entre esses rótulos enriquecidos, mantendo a
propriedade Markoviana.

## Implementação

### `compose_state()` em `engine.py`

```python
def compose_state(base: str, context: dict) -> str:
    """Concatena contexto a um estado base. Ex:
    compose_state("return", {"em_bloco": "metodo"})
    → "return|em_bloco:metodo"
    """
    if not context:
        return base
    pares = sorted(f"{k}:{v}" for k, v in context.items())
    return base + "|" + "|".join(pares)
```

- Pares ordenados alfabeticamente para determinismo
- Contexto vazio → retorna base inalterada (compatibilidade total)

### `compor_contexto()` em `engine.py`

Função que evolui o contexto sintático durante a geração, baseada
em delimitadores e keywords **comuns a múltiplas linguagens**:

| Token detectado | Efeito no contexto |
|---|---|
| `{` | `profundidade_bloco+1`, `em_bloco=sim` |
| `}` | `profundidade_bloco-1`, se 0 remove `em_bloco` |
| `class`, `struct`, `interface` | `declarando_tipo=sim` |
| `def`, `function`, `void`, `int`, etc. | `em_declaracao=sim` |
| `return`, `yield`, `break` | `em_fluxo=sim` |
| `;` | `em_declaracao=nao`, `em_fluxo=nao` |

### `MCRConector.alimentar()` modificado

Aceita parâmetro opcional `contexto: dict`. Se fornecido, também
alimenta versões compostas de cada par de palavras na cadeia Markov:

```python
c.alimentar(codigo, "arquivo.cs", contexto={'modo': 'codigo', 'linguagem': 'csharp'})
```

Isto duplica o espaço de estados aprendidos:
- Simples: `public → class`
- Composto: `public|modo:codigo|linguagem:csharp → class|modo:codigo|linguagem:csharp`

### `MCRCadeia.gerar()` modificado

Aceita parâmetro opcional `contexto_sintatico: dict`. Quando fornecido:

1. Cada estado é passado por `compose_state(estado_atual, ctx_sint)` antes
   de ser usado para predizer o próximo token
2. O contexto evolui via `compor_contexto()` a cada token gerado
3. Um registro `_freq_compostos` conta o uso de cada estado composto
4. Alerta no log se ultrapassar 10.000 estados compostos únicos

## Resultados

| Métrica | Valor |
|---------|-------|
| Estados totais (Grimório 15 arquivos) | 1.490 |
| Estados simples | 744 (50%) |
| Estados compostos | 746 (50%) |
| Integração | `compose_state()` + `compor_contexto()` + `alimentar()` + `gerar()` |

## Limitação Reconhecida

A geração de código com Markov 1ª ordem + Estados Compostos continua
produzindo sequências curtas (~3-5 tokens) para código com estrutura
repetitiva (`using System.X; using System.Y;`). A causa é:

1. A cadeia aprende que `; → using` é a transição mais provável
2. O detector de loop identifica a repetição e aborta
3. Estados Compostos enriquecem o vocabulário mas não alteram o
   fato de que transições de curto alcance dominam estatisticamente

Esta limitação é **teórica e aceita** pelo Arquiteto como fronteira
da Markov 1ª ordem. Soluções futuras (fora do escopo atual):
- Estados Compostos com `compose_state()` usando contexto hierárquico
  (ex: `"estado|bloco:nivel1|bloco:nivel2"`)
- Injeção seletiva de contexto via `MCRDecisor` (não aumentar ordem)

## Arquivos Modificados

| Arquivo | Mudança |
|---------|---------|
| `devia/kernel/mcr_kernel/engine.py` | `compose_state()`, `compor_contexto()` |
| `devia/kernel/mcr_kernel/memory.py` | `MCRConector.alimentar()` aceita `contexto`; `MCRCadeia.gerar()` aceita `contexto_sintatico` |
