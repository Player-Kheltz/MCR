# MCR

**1 algoritmo, N níveis, 0 dependências. ~438KB. 0 LLM.**

MCR é um sistema de **reconhecimento de padrões e geração por assinatura** que opera em múltiplos níveis de abstração simultaneamente (byte, palavra, token, intenção, decisão, ação). Tudo num único arquivo Python sem dependências externas.

```python
from MCR import MCRMotor, MCRPiEngine

motor = MCRMotor()
motor.alimentar("SPA e o sistema de progressao do aventureiro", "spa")
motor.alimentar("SHC e o sistema de habilidades contextuais", "shc")

# Conexão entre tópicos
resultado = motor.conectar("spa", "shc")
print(resultado['nota'], resultado['equacao'])  # 9.0 (1.5+4.5+3.0)x(1-0.0)=9.0

# Geração por assinatura
print(MCRPiEngine.continuar_padrao("SPA e o sistema de", motor, 8))
```

## Instalação

Copie `MCR.py` para seu projeto:

```
cp MCR.py meu_projeto/
```

Python puro, stdlib, zero dependências. Funciona em qualquer versão Python 3.8+.

## O que faz

- **Analisa** qualquer dado (texto, áudio, imagem, binário) por entropia de transições de bytes
- **Conecta** tópicos distantes encontrando a ponte ótima entre cadeias Markov independentes
- **Gera** sequências novas escolhendo cada token pela Equação MCR (byte + palavra + token)
- **Autoavalia** cada passo sem depender de modelo externo
- **Memoriza** sessões com checkpoint e auto-retomada

## 8 níveis

byte → palavra → token → intenção → decisão → ação → assinatura → qualidade

## 12 classes

MCR, MCRByteUtils, MCRThreshold, MCREntropia, MCRBuffer, MCRSession,
MCRFragmento, MCRFragmentador, MCRConexao, MCRMotor, MCRAutoLoop, MCRPiEngine

## Documentação

| Arquivo | O que cobre |
|---------|------------|
| `01_CONCEITO.md` | Filosofia, Equação MCR, por que é novo |
| `02_CLASSES.md` | 12 classes explicadas |
| `03_API.md` | Métodos, parâmetros, retornos |
| `04_VALIDACAO.md` | Testes contra 12 formatos |
| `05_COMPARACAO.md` | MCR vs LLM, HTM, HMM |
| `06_TUTORIAL.md` | Exemplos passo a passo |
| `07_LIMITACOES.md` | O que MCR não faz, roadmap |

## Licença

MIT
