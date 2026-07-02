# Bateria de Testes MCR

**Formula:** `1*by + 3*pa`


### TESTE 1: Entropia de 12 formatos
  [PASSOU] Escala: -0.000 a 7.990 (diferenca=7.990) | Esperado > 5, got 7.990
  [PASSOU] Entropia minima (zeros): -0.000
  [PASSOU] Entropia maxima (aleatorio): 7.990
| Amostra | Entropia |
|---------|:--------:|
| gradiente            | 7.990 |
| tom_440hz            | 7.564 |
| ruido                | 7.556 |
| aleatorio            | 7.548 |
| lorem                | 3.986 |
| checkerboard         | 1.000 |
| repetitivo           | 1.000 |
| padrao_00ff          | 1.000 |
| silencio             | -0.000 |
| branca               | -0.000 |
| zeros                | -0.000 |

### TESTE 2: 5 sequencias matematicas
  [PASSOU] Fibonacci: MCR disse 21 esperado 21
  [PASSOU] Quadrados: MCR disse 64 esperado 64
  [PASSOU] Primos: MCR disse 19 esperado 19
  [PASSOU] Pot2: MCR disse 128 esperado 128
  [PASSOU] Binario: MCR disse 1000 esperado 1000
  [PASSOU] Total: 5/5

### TESTE 3: Conexoes entre topicos
  [PASSOU] spa+shc: nota=7.0 1*by + 3*pa=10.00x(1-0.3)=7.0
  [PASSOU] spa+natal: nota=7.0 1*by + 3*pa=10.00x(1-0.3)=7.0
  [PASSOU] npc+eridanus: nota=6.8 1*by + 3*pa=9.71x(1-0.3)=6.8
  [PASSOU] spa+npc: nota=6.1 1*by + 3*pa=8.69x(1-0.3)=6.1
  [PASSOU] natal+eridanus: nota=7.0 1*by + 3*pa=10.00x(1-0.3)=7.0

### TESTE 4: Auto-diagnostico
  [PASSOU] Nota geral: 5.59/10
  [PASSOU] Gap: shc
  [PASSOU] Sugestao: 
  [PASSOU] Auto-avaliacao MCR.py: entropia=5.307 dim=128
  [PASSOU] Hardcodes detectados: 1

### TESTE 5: Geracao de texto
  [PASSOU] "SPA e o sistema": gerou 73 chars, H=3.90
  [PASSOU] "O SHC tem 5": gerou 78 chars, H=3.98

### TESTE 6: Assinatura expansiva
  [PASSOU] "a a a a a a a a a a": dim=2 entropia_fp=1.978
  [PASSOU] "1 2 4 8 16 32 64": dim=64 entropia_fp=2.906
  [PASSOU] "SPA e o sistema de progressao": dim=64 entropia_fp=2.728

### TESTE 7: Collatz + Primos
  [PASSOU] Collatz(27): 50 termos, entropia=3.203
  [PASSOU] Primos: 100 primos, gaps entropia=2.286

## Resumo

| Total | Passaram | Taxa |
|:----:|:--------:|:----:|
| 26 | 26 | 100.0% |
