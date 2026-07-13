>> CATALOG tags=context, identity, definition, mcr updated=2026-07-13
# Identidade do Projeto MCR

## O que MCR é

MCR é um **framework cognitivo universal** baseado em três componentes:
1. **Markov de 1ª ordem** — aprende transições entre estados
2. **Entropia de Shannon** — mede incerteza, detecta loops, avalia diversidade
3. **Equação MCR** — avalia qualidade de qualquer saída (divergência × 2 + especificidade × 3 + profundidade × 2) / 10

A tese: estes três componentes são suficientes para cognição — perceber, decidir, executar, avaliar, aprender — em qualquer domínio.

MCR **não é uma sigla com significado**. É o nome do projeto.

## O que MCR NÃO é

- Não é um servidor de Tibia (Tibia é um domínio de aplicação)
- Não é um wrapper de LLM (LLM é último recurso, não obrigatório)
- Não é uma AGI (é um framework cognitivo limitado a Markov de 1ª ordem)
- Não depende de GPU, nuvem, ou internet (o núcleo é Python stdlib)

## Como o MCR se prova

O MCR se prova gerando conteúdo válido em **dois domínios radicalmente diferentes** usando o MESMO motor:

1. **Tibia (texto estruturado):** NPCs, monstros, quests, diálogos em Lua Canary
2. **Visual (pixels):** Sprites PNG com cores, formas e regiões coerentes

Se o MESMO Markov + MESMA Equação funciona em ambos, o modelo é universal.

## Estrutura

```
mcr/mcr.py  → Cognição unificada (1 classe, 657 linhas)
mcr/motor/  → Markov engine + fingerprint (intacto desde sempre)
mcr/equacao/ → Equação MCR (intacta)
mcr/ferramentas/ → Plugins de domínio (Tibia, Visual, ...)
mcr/autonomia/ → Auto-estudo, auto-evolução
mcr/qualidade/ → Metacognição, verificação, cache
mcr/servicos/ → SSE Server, Bridge API, World Observer
mcr/infra/ → Paths, registry, bootstrap, SQLite
```

## Siglas do ecossistema (contexto Tibia)

- **SPA** = Sistema de Progressão do Aventureiro (habilidades elementais)
- **SHC** = Sistema de Habilidades Contextuais (5 camadas)
- **Canary** = Servidor OTServ usado no projeto
- **OTClient** = Cliente customizado de Tibia
- **Eridanus** = Cidade inicial do mundo MCR

## Limitações

Ver README.md para a lista completa. As principais:
- Markov de 1ª ordem não modela dependências de longo alcance
- Classificação depende de seeds pré-treinadas
- Templates determinísticos (Tier 1) não entendem semântica
- Qualidade máxima em alguns domínios requer LLM (Tier 2-3)
