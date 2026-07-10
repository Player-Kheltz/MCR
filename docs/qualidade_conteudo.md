# Teste de Qualidade de Conteudo — Calibracao

**Data:** 2026-07-09
**Fase:** Calibracao de Conteudo (Dia 1)

## Benchmark de Modelos

| Modelo | Tempo | Entropia | Diversid. | Campos | Veredito |
|--------|-------|----------|-----------|--------|----------|
| **Mistral 7B** | 14.3s | 0.996 | 0.949 | 7/7 | Melhor para prosa criativa |
| Qwen 2.5 Coder 7B | 10.3s | 0.990 | 0.896 | 7/7 | Mais rapido, bom para codigo |
| DeepSeek R1 7B | 24.3s | 0.971 | 0.758 | 4/7 | Perdeu campos, lento |

**Decisao:** Mistral é o modelo primário para narrativa. Qwen para código. DeepSeek como fallback no Ensemble.

## Calibracao — Resultados com Prompts Criativos

### NPC 1: Ferreiro Élfico (Mistral, 23.6s)

```
NOME: Eldon Oakheart
RACA: Elfo | SEXO: Masculino | IDADE: 400 anos
HISTORIA: Originário da floresta de Yalahar, conhecido por
forjar armas mágicas. Após a batalha da Caverna das Sombras,
estabeleceu-se em Vesperia.
PERSONALIDADE: Intuitivo, inquieto e solitário.
TRACO_SECRETO: Tem medo de borboletas.
```

### NPC 2: Orc Guarda da Ponte (Mistral, 19.1s)

```
NOME: Grimgor Fangshield
RACA: Orc | SEXO: Masculino | IDADE: 400 anos
HISTORIA: Descendente de uma dinastia real orca antiga,
capturado durante batalha e forçado a servir na Guarda
da Ponte Ebonshard.
PERSONALIDADE: Determinado, tímido, secretamente obcecado
por colecionar itens exóticos.
TRACO_SECRETO: Medo irracional de pássaros.
```

### Quest: A Forja Perdida (Mistral, 27.1s)

```
NPC_ENTREGADOR: Aelindor, o Ferreiro de Thais
DIALOGO_INICIO: "Jovem guerreiro, um segredo misterioso
envolve meu ofício. As minhas melhores ferramentas foram
roubadas! Se puderes recuperá-las, receberia meu eterno
agradecimento."
```

### Lore: Fundação de Eridanus (Mistral, 39.7s)

> Na primeira erupção da aurora no céu de Erenor, um sinal
> divino foi visto pela humanidade. Um arco-íris radiante
> se estendeu sobre as planícies férteis do rio Eridanos,
> unindo o mar de Ardor ao mar de Serpentes.

### Lore: Origem do SPA (Mistral, 41.2s)

> A lenda diz que há uma linha escondida, um caminho oculto
> que atravessa todos os reinos, guardado pelo misterioso
> Conjurador do Caminho Escondido.

## Avaliacao Humana

| Item | Coerencia (1-5) | Criatividade (1-5) | Utilidade (1-5) |
|------|-----------------|--------------------|------------------|
| NPC Ferreiro Elfico (Eldon) |  |  |  |
| NPC Orc Guarda (Grimgor) |  |  |  |
| Quest A Forja Perdida |  |  |  |
| Lore Fundacao de Eridanus |  |  |  |
| Lore Origem do SPA |  |  |  |

---

*Preencha as notas acima apos avaliar cada conteudo.*
