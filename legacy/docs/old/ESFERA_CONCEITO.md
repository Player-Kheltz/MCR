# MCREsfera — Conceito

## Problema

Hoje o MCR opera como **círculos paralelos**:
- `MCR("byte")` — cadeia independente
- `MCR("palavra")` — cadeia independente
- `MCR("token")` — cadeia independente
- `MCRCoupling` conecta depois, artificialmente

Cada nível aprende separado. A conexão entre níveis é pós-hoc.

## Ideia

Uma única função de transição que opera em **N dimensões simultaneamente**:

```python
# Em vez de:
MCR("byte").aprender(B:41, B:46)
MCR("palavra").aprender("MCR", "e")

# Esfera:
esfera.aprender({
    "byte": (B:41, B:46),
    "palavra": ("MCR", "e"),
    "token": ("Maiuscula", "Minuscula"),
    "acao": None,  # opcional
})
```

Cada transição é um ponto na superfície de uma **esfera N-dimensional**. O aprendizado é sobre navegar nessa superfície, não em círculos isolados.

## Representação

```python
class MCREsfera:
    def __init__(self):
        # Transicoes N-dimensionais
        # { frozenset([(nivel, a, b), ...]): contagem }
        self.transicoes: Dict[FrozenSet, int] = {}
    
    def aprender(self, transicao: Dict[str, Tuple[Any, Any]]):
        """transicao = { "byte": (B:41, B:46), "palavra": ("MCR", "e") }"""
        chave = frozenset((n, a, b) for n, (a, b) in transicao.items())
        self.transicoes[chave] = self.transicoes.get(chave, 0) + 1
    
    def predizer(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Dado contexto parcial, completa todos os niveis.
        contexto = { "byte": B:41, "palavra": "MCR" }
        → { "byte": B:46, "palavra": "e", "token": "Minuscula" }
        """
        # Encontra a transicao mais similar ao contexto
        # Usa overlap de niveis conhecidos como pontuacao
        ...
```

## Desafios

- **Estado esparso**: maioria das combinações N-dimensionais nunca aparece
- **Generalização**: como completar níveis que nunca foram vistos juntos?
- **Performance**: cardinalidade explode com número de níveis

## Relação com o atual

O `MCRCoupling` já tenta fazer isso (matriz byte↔palavra, palavra↔token). A `MCREsfera` seria a versão unificada — uma única estrutura de dados com N dimensões em vez de N estruturas 2D.

## Resultados Reais (testado em 2026-07-03)

Teste com `MCR_AGI.py` (10000 chars treino, 2000 chars teste, 3 níveis: byte, palavra, token):

| Teste | MCR clássico | MCREsfera | Diferença |
|-------|-------------|-----------|-----------|
| Byte→Byte (intra-nível) | 7.3% | **11.9%** | **+4.6%** ✅ |
| Palavra→Palavra (intra) | 7.3% | 7.3% | 0% |
| Token→Token (intra) | **91.3%** | 57.5% | -33.8% ❌ |
| **Palavra→Token (cross-level)** | N/A | **85.0%** | **NOVO** ✅ |
| Token→Byte (cross) | N/A | 6.0% | Limitado |
| Byte→Palavra (cross) | N/A | 1.3% | Esparso |

### O que funciona

- **Predição cross-level**: a esfera permite inferir um nível a partir de OUTRO nível. MCR clássico não faz isso. Ex: `palavra→token` com 85% de acerto.
- **Byte melhorou +4.6%** com contexto completo (byte+palavra+token) — a esfera usou informação dos outros níveis para melhorar a predição de byte.

### O que não funciona

- **Cardinalidade explode**: match exato de tuplas N-dimensionais sofre de **maldição da dimensionalidade**. `|byte| × |palavra| × |token| × |byte| × |palavra| × |token|` = intratável.
- **Token perdeu -33.8%** porque a esfera exige match exato de 3 níveis, enquanto o MCR token opera com apenas 4 valores.

### Solução Proposta

Em vez de lookup exato, usar **fingerprint como projeção** dos níveis na esfera, depois nearest-neighbor. Isso é essencialmente evoluir o `MCRCoupling` + `MCRSignature` para uma única estrutura N-dimensional com similaridade fuzzy.

## Próximo Passo

Integrar o conceito no `MCR_AGI.py` como evolução do `MCRCoupling` — uma classe `MCREsfera` que:
1. Aprende correlações N-dimensionais entre níveis
2. Usa projeção por fingerprint (não lookup exato)
3. Serve como fallback cross-level quando o MCR intra-nível não tem dados
4. Substitui a matriz 2D do MCRCoupling por uma estrutura N-dimensional

Veredito: **CONCEITO VÁLIDO** — ganho real em cross-level (+4.6% byte, 85% palavra→token). Implementação ingênua não escala — precisa de projeção por fingerprint.
