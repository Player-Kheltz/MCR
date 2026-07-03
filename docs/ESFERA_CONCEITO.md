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

## Status

**Conceito apenas.** Não implementado. Próximo passo: protótipo com 3 níveis (byte, palavra, token) em um domínio pequeno (ex: 100 palavras) para ver se a cardinalidade explode.
