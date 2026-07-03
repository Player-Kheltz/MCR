# Comparação MCR vs Outros Sistemas

## Tabela Comparativa

| Característica | MCR | LLM (GPT/Claude) | Llama 3 Local | scikit-learn HMM | Numenta HTM |
|---|---|---|---|---|---|
| **Peso** | **17 KB** | ∞ (cloud) | 4-70 GB | ~100 MB | ~200 MB |
| **Dependências** | **0** (stdlib) | API key | llama.cpp | numpy | NuPIC |
| **GPU necessária?** | **Não** | Sim (cloud) | Sim (ou RAM 16GB+) | Não | Não |
| **Geração de texto** | **Sim** (assing) | Sim | Sim | Não | Não |
| **Autoavaliação** | **Sim** (Eq. MCR) | Não intrínseca | Não intrínseca | Não | Não |
| **Multi-nível** | **8 níveis** | Não | Não | Não | 1 nível |
| **Emergência** | **Sim** (cruzamento) | Via LLM | Via LLM | Não | Parcial |
| **Memória/sessão** | **Sim** | Sim | Não | Não | Não |
| **Offline** | **Sim** | Não | Sim | Sim | Sim |
| **Custo operacional** | **R$ 0** | $$ por chamada | $$ eletricidade | R$ 0 | R$ 0 |
| **Interpretável** | **Sim** (transições) | Não (caixa preta) | Não (caixa preta) | Parcial | Parcial |

## Quando usar cada um

### Use MCR quando:

- Precisa rodar em hardware limitado (chip de US$ 2, Raspberry Pi, roteador)
- Não pode depender de internet ou nuvem (air-gapped, IoT, militar)
- Precisa de autoavaliação sem oracle externo
- Quer entender exatamente **por que** o sistema tomou uma decisão
- Precisa analisar múltiplos formatos com a mesma ferramenta

### Use LLM quando:

- Precisa de compreensão semântica profunda (metáforas, ironia, tradução)
- Pode pagar por API ou tem GPU disponível
- Precisa de respostas em linguagem natural de alta qualidade
- O problema exige conhecimento enciclopédico

### Use HMM (Hidden Markov Model) quando:

- O problema é modelável como estados ocultos (reconhecimento de fala, bioinformática)
- Precisa de implementação otimizada com décadas de pesquisa
- Dados de treinamento são abundantes e rotulados

## Por que MCR existe

LLMs são excelentes em tarefas gerais mas são **caros, pesados e não se autoavaliam**. HMMs e HTM são eficientes mas **não geram nem emergem**. O MCR preenche o espaço vazio entre "regra fixa burra" e "rede neural de 100GB" — ocupando 17KB.

## O que MCR NÃO substitui

- Compreensão semântica profunda
- Conhecimento enciclopédico
- Raciocínio multi-passo complexo
- Tradução entre idiomas
- Geração de imagens ou áudio

O MCR **complementa** esses sistemas, não compete com eles.
