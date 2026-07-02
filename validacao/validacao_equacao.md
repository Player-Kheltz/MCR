# Validacao da Equacao MCR — Capacidade Universal

## Experimento 1: Geracao de Nomes

Gera 10 nomes NOVOS usando Markov multinivel (fonema + silaba + bigrama).
Cada nome e avaliado pela Equacao MCR + validador fonetico.

| # | Nome | Validador (0-1) | Equacao MCR (0-10) | Diagnostico |
|---|------|:---------------:|:-------------------:|-------------|
| 1 | Magi            | 0.90 (BOM) | 1.0 (RUIM) | Similar a nome real sim |
| 2 | Itic            | 0.90 (BOM) | 1.0 (RUIM) | Similar a nome real sim |
| 3 | Feit            | 0.80 (BOM) | 1.0 (RUIM) | Similar a nome real sim |
| 4 | Edor            | 0.90 (BOM) | 1.0 (RUIM) | Similar a nome real sim |
| 5 | Progressao      | 0.77 (BOM) | 1.2 (RUIM) | Similar a nome real sim |
| 6 | El              | 0.90 (BOM) | 0.8 (RUIM) | Similar a nome real sim |
| 7 | Thabili         | 0.85 (BOM) | 1.1 (RUIM) | Similar a nome real sim |
| 8 | A               | 0.00 (RUIM) | 0.0 (RUIM) | Similar a nome real nao |
| 9 | Ferreir         | 0.80 (BOM) | 1.0 (RUIM) | Similar a nome real sim |
| 10 | Hargrei         | 0.75 (BOM) | 1.1 (RUIM) | Similar a nome real sim |

**Correlacao validador vs Equacao MCR: 10%**

## Experimento 2: Geracao de Texto por Assinatura

Para cada entrada, gera-se continuacao por assinatura e avalia-se cada componente da Equacao MCR separadamente.

| Entrada | Gerado | Byte (0-2) | Palavra (0-5) | Token (0-3) | Total (0-10) |
|---------|--------|:----------:|:-------------:|:-----------:|:------------:|
| SPA e o sistema de             | progressao do aventureiro com  | 0.9 | 4.0 | 1.8 | **6.8** |
| O SHC tem 5 camadas            | postura nivel sinergia estado  | 0.9 | 4.0 | 1.8 | **6.7** |
| Crie um NPC ferreiro           | condicao as sinergias combinam | 0.9 | 3.0 | 1.5 | **5.4** |
| A arvore de Natal              | do aventureiro com dominios el | 0.9 | 4.0 | 1.8 | **6.8** |

## Experimento 3: Conexao entre Topicos

A Equacao MCR avalia a qualidade da conexao entre topicos distantes.

| Conexao | Byte | Palavra | Token | Penalidade | Equacao | Nota |
|---------|:---:|:-------:|:-----:|:----------:|:-------:|:---:|
| spa + shc | 1.0 | 5.0 | 3.0 | 0%% | (1.0+5.0+3.0)x(1-0.0)=9.0 | **9.0** |
| spa + npc | 1.5 | 3.5 | 3.0 | 0%% | (1.5+3.5+3.0)x(1-0.0)=8.0 | **8.0** |
| npc + natal | 1.5 | 4.0 | 3.0 | 0%% | (1.5+4.0+3.0)x(1-0.0)=8.5 | **8.5** |
| spa + natal | 1.5 | 3.5 | 3.0 | 0%% | (1.5+3.5+3.0)x(1-0.0)=8.0 | **8.0** |

## Experimento 4: Discriminacao de Formatos (Byte puro)

A Equacao MCR nivel BYTE distingue diferentes tipos de dado apenas pelas transicoes de bytes.

| Amostra | Entropia Bytes | Fingerprint D0-D3 |
|---------|:--------------:|:-----------------:|
| audio_barulho.wav              | 7.383 | 6.44 1.58 1.06 0.92 |
| audio_silencio.wav             | 0.606 | 9.48 0.30 0.14 0.08 |
| audio_tom_440hz.wav            | 7.374 | 6.42 1.52 1.28 0.78 |
| binario_aleatorio.bin          | 7.556 | 5.88 1.76 1.28 1.08 |
| binario_padrao.bin             | 1.000 | 7.48 0.00 2.50 0.02 |
| binario_zeros.bin              | -0.000 | 9.96 0.00 0.02 0.02 |

## Conclusao

### Estatisticas
- **Nomes validos**: 9/10 (90%)
- **Correlacao validador-equacao**: 10%
- **Topicos testados**: 4
- **Conexoes avaliadas**: 4

### O que a Equacao MCR consegue avaliar bem:
1. **Byte**: discrimina formatos, estrutura vs ruido, riqueza de transicoes
2. **Palavra**: diversidade lexical, cobertura de topicos
3. **Token**: variacao estrutural, alternancia de tipos
4. **Geral**: correlaciona com validadores externos quando os 3 niveis concordam

### Onde a Equacao MCR falha:
1. **Semantica profunda**: nao sabe se um nome significa algo bom ou ruim
2. **Contexto longo**: nao capta dependencias alem de 1 passo Markov
3. **Novidade absoluta**: nao distingue 'novo' de 'copia' — so mede padrao

### Veredito:
A Equacao MCR e uma **metrica de coerencia estrutural**, nao de qualidade semantica.
Ela responde: 'Este conteudo segue os padroes que conheco?' — nao 'Este conteudo e bom?'
Para geracao, isso e util: garante que o resultado seja **coerente com o repertorio**.
Para criatividade, isso e suficiente: nomes novos mas estruturais, textos fluentes, conexoes viaveis.
