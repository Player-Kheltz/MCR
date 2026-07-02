# Validacao MCR — Relatorio Automatico

Gerado em: 2026-07-02T01:36:06.562008
Amostras: 12

## 1. Metricas por Amostra

| Amostra | Tipo | Bytes | Entropia (bytes) | Estados MK | Transicoes MK | Entropia MK |
|---------|------|------:|-----------------:|-----------:|--------------:|------------:|
| binario_aleatorio.bin          | bin   |   1000 |           7.556 |       253 |          990 |      1.756 |
| audio_barulho.wav              | wav   |  88244 |           7.383 |       253 |         1946 |      2.629 |
| audio_tom_440hz.wav            | wav   |  88244 |           7.374 |       252 |         1948 |      2.610 |
| texto_lorem.txt                | txt   |    576 |           4.241 |        39 |          178 |      1.238 |
| imagem_gradiente.ppm           | ppm   |  30015 |           4.174 |       106 |          779 |      2.489 |
| texto_curto.txt                | txt   |     29 |           3.702 |        15 |           26 |      0.550 |
| imagem_preto_branco.ppm        | ppm   |  30015 |           1.248 |        10 |           17 |      0.592 |
| binario_padrao.bin             | bin   |   1000 |           1.000 |         2 |            2 |      0.000 |
| texto_repetitivo.txt           | txt   |   1999 |           1.000 |         2 |            2 |      0.000 |
| audio_silencio.wav             | wav   |  88244 |           0.606 |        21 |           32 |      0.193 |
| imagem_branca.ppm              | ppm   |  30015 |           0.278 |         9 |           14 |      0.454 |
| binario_zeros.bin              | bin   |   1000 |          -0.000 |         1 |            1 |      0.000 |

## 2. Fingerprint (8 dimensoes)

| Amostra | D0 | D1 | D2 | D3 | D4 | D5 | D6 | D7 |
|---------|----|----|----|----|----|----|----|----|
| audio_barulho.wav              | 3.400 | 0.920 | 0.580 | 0.660 | 3.040 | 0.660 | 0.480 | 0.260 |
| audio_silencio.wav             | 7.000 | 0.260 | 0.060 | 0.040 | 2.480 | 0.040 | 0.080 | 0.040 |
| audio_tom_440hz.wav            | 3.680 | 1.060 | 0.660 | 0.500 | 2.740 | 0.460 | 0.620 | 0.280 |
| binario_aleatorio.bin          | 3.160 | 1.080 | 0.600 | 0.700 | 2.720 | 0.680 | 0.680 | 0.380 |
| binario_padrao.bin             | 4.980 | 0.000 | 0.020 | 0.000 | 2.500 | 0.000 | 2.480 | 0.020 |
| binario_zeros.bin              | 7.460 | 0.000 | 0.020 | 0.000 | 2.500 | 0.000 | 0.000 | 0.020 |
| imagem_branca.ppm              | 2.520 | 0.040 | 0.040 | 0.000 | 2.460 | 0.040 | 4.880 | 0.020 |
| imagem_gradiente.ppm           | 6.500 | 0.280 | 0.140 | 0.160 | 2.400 | 0.180 | 0.220 | 0.120 |
| imagem_preto_branco.ppm        | 4.920 | 0.040 | 0.040 | 0.000 | 2.460 | 0.040 | 2.480 | 0.020 |
| texto_curto.txt                | 2.500 | 1.250 | 0.625 | 2.500 | 0.625 | 1.250 | 0.000 | 1.250 |
| texto_lorem.txt                | 1.820 | 1.500 | 0.460 | 1.080 | 1.300 | 1.920 | 0.940 | 0.980 |
| texto_repetitivo.txt           | 4.980 | 4.980 | 0.020 | 0.000 | 0.000 | 0.000 | 0.000 | 0.020 |

## 3. Top 5 Estados (bytes mais frequentes)

**audio_barulho.wav:**
  - `B:00` (0x00) x 23
  - `B:38` ('8') x 20
  - `B:c3` ('Ã') x 19
  - `B:05` (0x05) x 19
  - `B:2e` ('.') x 19

**audio_silencio.wav:**
  - `B:00` (0x00) x 1967
  - `B:01` (0x01) x 5
  - `B:58` ('X') x 3
  - `B:46` ('F') x 2
  - `B:ac` ('¬') x 2

**audio_tom_440hz.wav:**
  - `B:3f` ('?') x 59
  - `B:c0` ('À') x 55
  - `B:3e` ('>') x 28
  - `B:c1` ('Á') x 27
  - `B:00` (0x00) x 21

**binario_aleatorio.bin:**
  - `B:87` (0x87) x 13
  - `B:c2` ('Â') x 11
  - `B:8e` (0x8E) x 10
  - `B:23` ('#') x 10
  - `B:e8` ('è') x 9

**binario_padrao.bin:**
  - `B:00` (0x00) x 500
  - `B:ff` ('ÿ') x 499

**binario_zeros.bin:**
  - `B:00` (0x00) x 999

**imagem_branca.ppm:**
  - `B:ff` ('ÿ') x 1984
  - `B:30` ('0') x 4
  - `B:0a` (0x0A) x 3
  - `B:31` ('1') x 2
  - `B:35` ('5') x 2

**imagem_gradiente.ppm:**
  - `B:80` (0x80) x 661
  - `B:0a` (0x0A) x 110
  - `B:00` (0x00) x 107
  - `B:02` (0x02) x 107
  - `B:05` (0x05) x 107

**imagem_preto_branco.ppm:**
  - `B:ff` ('ÿ') x 993
  - `B:00` (0x00) x 991
  - `B:30` ('0') x 4
  - `B:0a` (0x0A) x 3
  - `B:31` ('1') x 2

**texto_curto.txt:**
  - `B:20` (' ') x 6
  - `B:73` ('s') x 4
  - `B:53` ('S') x 2
  - `B:65` ('e') x 2
  - `B:43` ('C') x 2

**texto_lorem.txt:**
  - `B:20` (' ') x 90
  - `B:65` ('e') x 74
  - `B:6f` ('o') x 50
  - `B:61` ('a') x 43
  - `B:6e` ('n') x 34

**texto_repetitivo.txt:**
  - `B:61` ('a') x 999
  - `B:20` (' ') x 999

## 4. Matriz de Similaridade (Jaccard)

| imagem_branca.ppm vs imagem_preto_branco.ppm                 | J=0.9524 | C=0.7158 |
| binario_padrao.bin vs binario_zeros.bin                      | J=0.5000 | C=0.7085 |
| texto_curto.txt vs texto_lorem.txt                           | J=0.4815 | C=0.8166 |
| audio_barulho.wav vs audio_tom_440hz.wav                     | J=0.4757 | C=0.8862 |
| audio_tom_440hz.wav vs binario_aleatorio.bin                 | J=0.3960 | C=0.7765 |
| audio_barulho.wav vs binario_aleatorio.bin                   | J=0.3857 | C=0.8146 |
| audio_silencio.wav vs texto_lorem.txt                        | J=0.3788 | C=0.1522 |
| audio_silencio.wav vs texto_curto.txt                        | J=0.3654 | C=0.2357 |
| binario_aleatorio.bin vs imagem_gradiente.ppm                | J=0.3488 | C=0.4400 |
| audio_tom_440hz.wav vs imagem_gradiente.ppm                  | J=0.3292 | C=0.6321 |
| audio_silencio.wav vs audio_tom_440hz.wav                    | J=0.3106 | C=0.6149 |
| audio_barulho.wav vs audio_silencio.wav                      | J=0.2908 | C=0.5664 |
| binario_padrao.bin vs imagem_preto_branco.ppm                | J=0.2857 | C=0.9975 |
| audio_barulho.wav vs imagem_gradiente.ppm                    | J=0.2816 | C=0.5706 |
| imagem_gradiente.ppm vs texto_lorem.txt                      | J=0.2816 | C=0.2316 |
| audio_silencio.wav vs imagem_gradiente.ppm                   | J=0.2812 | C=0.8313 |
| audio_tom_440hz.wav vs texto_lorem.txt                       | J=0.2381 | C=0.3713 |
| binario_padrao.bin vs imagem_branca.ppm                      | J=0.2381 | C=0.7186 |
| binario_aleatorio.bin vs texto_lorem.txt                     | J=0.2346 | C=0.5267 |
| imagem_gradiente.ppm vs imagem_preto_branco.ppm              | J=0.2262 | C=0.6118 |
| audio_barulho.wav vs texto_lorem.txt                         | J=0.2244 | C=0.4292 |
| imagem_branca.ppm vs imagem_gradiente.ppm                    | J=0.2143 | C=0.0418 |
| audio_silencio.wav vs binario_aleatorio.bin                  | J=0.2089 | C=0.2757 |
| texto_curto.txt vs texto_repetitivo.txt                      | J=0.2000 | C=0.6753 |
| imagem_branca.ppm vs texto_repetitivo.txt                    | J=0.1818 | C=0.0155 |
| imagem_gradiente.ppm vs texto_curto.txt                      | J=0.1789 | C=0.3317 |
| imagem_preto_branco.ppm vs texto_repetitivo.txt              | J=0.1739 | C=0.1824 |
| audio_silencio.wav vs imagem_preto_branco.ppm                | J=0.1698 | C=0.7101 |
| audio_tom_440hz.wav vs texto_curto.txt                       | J=0.1655 | C=0.4261 |
| imagem_branca.ppm vs texto_curto.txt                         | J=0.1628 | C=0.0700 |
| imagem_preto_branco.ppm vs texto_curto.txt                   | J=0.1591 | C=0.1961 |
| audio_silencio.wav vs imagem_branca.ppm                      | J=0.1509 | C=0.0202 |
| audio_barulho.wav vs texto_curto.txt                         | J=0.1477 | C=0.5015 |
| binario_aleatorio.bin vs texto_curto.txt                     | J=0.1465 | C=0.5543 |
| audio_silencio.wav vs texto_repetitivo.txt                   | J=0.1463 | C=0.2624 |
| binario_zeros.bin vs imagem_preto_branco.ppm                 | J=0.1429 | C=0.7114 |
| audio_tom_440hz.wav vs imagem_preto_branco.ppm               | J=0.1333 | C=0.5560 |
| imagem_branca.ppm vs texto_lorem.txt                         | J=0.1290 | C=0.0646 |
| imagem_preto_branco.ppm vs texto_lorem.txt                   | J=0.1270 | C=0.1339 |
| audio_tom_440hz.wav vs imagem_branca.ppm                     | J=0.1259 | C=0.1952 |
| binario_zeros.bin vs texto_repetitivo.txt                    | J=0.1250 | C=0.2348 |
| texto_lorem.txt vs texto_repetitivo.txt                      | J=0.1200 | C=0.6523 |
| binario_aleatorio.bin vs imagem_preto_branco.ppm             | J=0.1176 | C=0.3028 |
| binario_aleatorio.bin vs imagem_branca.ppm                   | J=0.1111 | C=0.1827 |
| audio_barulho.wav vs imagem_preto_branco.ppm                 | J=0.1020 | C=0.4749 |
| audio_barulho.wav vs imagem_branca.ppm                       | J=0.0952 | C=0.1399 |
| binario_zeros.bin vs imagem_branca.ppm                       | J=0.0952 | C=0.0197 |
| binario_padrao.bin vs texto_repetitivo.txt                   | J=0.0909 | C=0.1660 |
| audio_silencio.wav vs binario_zeros.bin                      | J=0.0732 | C=0.9971 |
| audio_silencio.wav vs binario_padrao.bin                     | J=0.0682 | C=0.7064 |
| imagem_gradiente.ppm vs texto_repetitivo.txt                 | J=0.0602 | C=0.3366 |
| binario_padrao.bin vs texto_curto.txt                        | J=0.0588 | C=0.1840 |
| binario_padrao.bin vs imagem_gradiente.ppm                   | J=0.0476 | C=0.5939 |
| audio_tom_440hz.wav vs binario_padrao.bin                    | J=0.0455 | C=0.5248 |
| audio_tom_440hz.wav vs texto_repetitivo.txt                  | J=0.0455 | C=0.3438 |
| audio_barulho.wav vs texto_repetitivo.txt                    | J=0.0426 | C=0.3552 |
| binario_aleatorio.bin vs binario_padrao.bin                  | J=0.0400 | C=0.2817 |
| binario_padrao.bin vs texto_lorem.txt                        | J=0.0370 | C=0.1245 |
| binario_zeros.bin vs imagem_gradiente.ppm                    | J=0.0366 | C=0.8240 |
| audio_barulho.wav vs binario_padrao.bin                      | J=0.0352 | C=0.4565 |
| binario_aleatorio.bin vs texto_repetitivo.txt                | J=0.0331 | C=0.3393 |
| binario_zeros.bin vs texto_curto.txt                         | J=0.0312 | C=0.2024 |
| audio_tom_440hz.wav vs binario_zeros.bin                     | J=0.0227 | C=0.5794 |
| audio_barulho.wav vs binario_zeros.bin                       | J=0.0213 | C=0.5279 |
| binario_aleatorio.bin vs binario_zeros.bin                   | J=0.0200 | C=0.2354 |
| binario_zeros.bin vs texto_lorem.txt                         | J=0.0192 | C=0.1204 |

## 5. Validacao das Hipoteses

| H1: entropia(silencio) ≈ 0 (estrutura maxima)                | FALHOU | entropia = 0.606 |
| H2: entropia(ruido) ≈ 8 (aleatoriedade maxima)               | PASSOU | entropia = 7.383 |
| H3: entropia(zeros) ≈ 0 (bytes repetidos)                    | PASSOU | entropia = -0.000 |
| H4: entropia(aleatorio) ≈ 8 (bytes aleatorios)               | PASSOU | entropia = 7.556 |
| H6: jaccard(silencio, barulho) ≈ 0 (diferentes)              | FALHOU | jaccard = 0.2908 |
| H7: jaccard(texto, repetitivo) < 0.3 (estruturas diferentes) | PASSOU | jaccard = 0.1200 |

## 6. Resumo Final

**Hipoteses validadas: 4/6 (67%)**

**Conclusao: O MCR precisa de ajustes para os formatos testados.**