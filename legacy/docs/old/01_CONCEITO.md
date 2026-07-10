> **Documenta��o hist�rica.** Este documento descreve vers�es anteriores do MCR.
> Para o estado atual, veja [README.md](../README.md) e [MANIFESTO_MCR.md](../MANIFESTO_MCR.md).
# Conceito MCR

## Filosofia

**Tudo é transição entre dois estados consecutivos.**

O que muda é o que entra como "token". O mesmo código aprende bytes, palavras, intenções, decisões e ações.

Um arquivo WAV de silêncio tem uma assinatura de transições (muitos `0x00` seguidos). Um texto em português tem outra (espaços, vogais, consoantes alternando). Uma imagem tem outra. O MCR opera a mesma equação em todos eles.

## Equação MCR

### Ponte Ótima

```
PONTE_OTIMA = (5D + 3E + 2P) / 10
```

Onde:
- **D** (divergência): `1 - Jaccard(transições em A, transições em B)` — quão diferentes são os caminhos a partir da ponte
- **E** (especificidade): raridade da palavra no repertório — penaliza palavras genéricas
- **P** (profundidade): tamanho da cadeia gerada após a ponte — recompensa riqueza de conteúdo

A divisão por 10 normaliza o resultado para o intervalo 0-1, invariante à escala das variáveis.

### Nota da Conexão

```
NOTA = (BYTE + PALAVRA + TOKEN) × (1 - PENALIDADE)
```

Onde:
- **BYTE** (0-2): coerência de transições de bytes na sequência gerada
- **PALAVRA** (0-5): palavras de conteúdo dos dois tópicos presentes na sequência
- **TOKEN** (0-3): coerência de tipos (primeira letra de cada palavra)

PENALIDADE varia conforme o tipo de ponte encontrada:

| Tipo de ponte | PENALIDADE | Efeito |
|---|---|---|
| `conteudo_compartilhado` | 0.0 | 0% de desconto |
| `conteudo_mas_parcial` | 0.3 | 30% de desconto |
| `byte_only` | 0.7 | 70% de desconto |
| `none` | 0.9 | 90% de desconto |

### Geração por Assinatura

Em vez de Markov `P(próximo | último)` (ordem 1), a geração pergunta:

> "Dado o que veio até agora, qual próximo token maximiza a assinatura (Equação MCR) com tudo que eu conheço?"

A cada passo:
1. Coleta candidatos dos 3 níveis (byte, palavra, token)
2. Avalia cada candidato pela Equação MCR contra a sequência completa
3. Escolhe o que maximiza a assinatura
4. Repete até assinatura cair abaixo do threshold

## 8 Níveis

| Nível | Tokeniza | Para quê |
|---|---|---|
| `byte` | `B:XX` (hex) | Análise binária, estrutura, fingerprint |
| `palavra` | palavras do texto | Compreensão semântica, geração |
| `token` | primeira letra de cada palavra | Padrões estruturais, tipo de frase |
| `intencao` | categoria + verbo principal | Detecção de intenção |
| `decisao` | estado codificado | Decisão do agente |
| `acao` | ação executada | Sequência de ações |
| `assinatura` | fingerprint do texto | Comparação entre textos |
| `qualidade` | métricas extraídas | Autoavaliação |

## Por que isso é novo

Cada peça isolada é velha (Markov, 1913; Jaccard, 1901; Shannon, 1948). O que não existia é:

1. **Seleção de candidatos em 3 níveis simultâneos** para geração
2. **Autoavaliação pela mesma equação usada na análise** — o gerador se autoavalia a cada passo
3. **Decisão do método por entropia normalizada** — escolhe markov/byte/emergência dinamicamente
4. **Arquitetura completa (MCR.py: ~438KB)** — do aprendizado à geração à memória de sessão
