# Identidade do Projeto MCR

## O que MCR é

MCR é um **motor cognitivo baseado em P(b|a) puro**. Aprendizado por contagem
de co-ocorrências em múltiplas escalas simultâneas.

Três componentes, um só motor:
1. **P(b|a)** — probabilidade condicional: tudo é transição entre estados
2. **Entropia de Shannon** — mede incerteza, detecta estrutura, thresholds emergem dos dados
3. **Escala + persistência + feedback** — o padrão se repete em todos os níveis

A tese: P(b|a) + entropia + múltiplas escalas = cognição universal.
Perceber, decidir, executar, avaliar, aprender — em qualquer domínio.

MCR **não é uma sigla**. É o nome do projeto.

## O que MCR NÃO é

- Não é um servidor de Tibia (Tibia foi um domínio de aplicação)
- Não é um wrapper de LLM (LLM é opcional para certos domínios)
- Não é uma AGI (é um motor Markov para P(b|a) + escalas)
- Não é uma rede neural (sem GPU, sem retropropagação)
- Não é um sistema especialista (thresholds emergem, não são codificados)

## Como o MCR se prova

O MCR se prova por **validação empírica contínua**:
- Toda mudança deve passar por 113/113 regressões (Fase 1) + 64/64 (Fase 18)
- Resultados são documentados com números reais, sem hype
- Limitações são documentadas explicitamente (não inventa, não alucina)

Domínios validados:
1. **Comandos gerais** (7 ações: gerar, descrever, responder, etc.) — 113/113
2. **Matemática** (7 regras: PA, PG, Fibonacci, Collatz, Quadrado, Triangular, Primo) — 17/17 zero-shot
3. **Sinonímia cross-idioma** (PT/EN/ES/FR/DE) — amor~love=0.335, casa~house=0.615, sem tradução
4. **Música, química, cores, geografia** — universalidade em 5 domínios
5. **Intenção (84%), emoção (89%), estilo (87-100%)** — níveis 4-6 emergem sem rótulos

## Estrutura atual

```
mcr/
  coupling.py        → Motor principal (4381 linhas, 13 fontes + HRC)
  chat.py            → Chat bidirecional com ciclo markoviano fechado
  triunvirato.py     → Busca ativa deliberativa
  gerador_coerente.py → Geração longa com working memory
  auto_conhecimento.py → Auto-alimentação temporal
  auto_referencia.py  → Meta-cognição recursiva
  auto_composicao.py  → Clusterização NMI → especialistas
  base_conhecimento.py → BC com NMI semântico
  ...
  133 módulos, ~46.286 linhas
```

## Limitações (versão atual)

- Markov de 1ª ordem não modela dependências de longo alcance
- Zero-shot de palavras novas não funciona (nem LLM faz)
- P(b|a) bruto não discrimina auto-conhecimento — precisa lift/NMI/IDF
- Self individual (nível 7) não emerge — só colônia de MCRs auto-observa
- Escala limitada testada: 167K observações
