# API MCR — Referência Completa

## MCR (markov_universal)

```python
mk = MCR(nome="")
mk.aprender(a: str, b: str) -> None
mk.aprender_sequencia(seq: List[str]) -> None
mk.aprender_batch(sequencias: List[List[str]]) -> None
mk.predizer(a: str) -> Tuple[Optional[str], float]
mk.predizer_n(a: str, n: int = 3) -> List[Tuple[str, float]]
mk.gerar(semente: str, passos: int = 10) -> List[str]
mk.entropia(a: str) -> float
mk.entropia_media() -> float
mk.jaccard(outra: MCR) -> float
mk.jaccard_transicoes(outra: MCR) -> float
mk.stats() -> Dict
```

**Exemplo:**
```python
mk = MCR("exemplo")
mk.aprender_sequencia(["o", "gato", "mia", "o", "gato", "dorme"])
print(mk.predizer("gato"))      # ("mia", 0.5)
print(mk.gerar("o", 5))         # ["o", "gato", "mia", "o", "gato"]
print(mk.stats())
# {'nome': 'exemplo', 'estados': 4, 'transicoes': 5, ...}
```

---

## MCRByteUtils

```python
MCRByteUtils.transicoes_bytes(texto: str, max_bytes=500) -> Set[str]
MCRByteUtils.jaccard_bytes(a: str, b: str) -> float
MCRByteUtils.similaridade_cosseno(a: str, b: str, max_bytes=500) -> float
MCRByteUtils.entropia_bytes(dados: str | bytes) -> float
MCRByteUtils.fingerprint(texto: str, dimensoes=8) -> List[float]
```

**Exemplo:**
```python
MCRByteUtils.jaccard_bytes("SPA é progressão", "SPA é sistema")
# 0.25

MCRByteUtils.entropia_bytes(b'\x00\x00\x00\x00')
# 0.0

MCRByteUtils.entropia_bytes("texto em português")
# ~4.2
```

---

## MCRThreshold

```python
th = MCRThreshold(nome="")
th.observar(valor: float) -> None
th.calcular(multiplicador=1.0) -> float
th.obter(chave: str, fallback=0.5) -> float
th.aprender(chave: str, valor: float) -> None
```

**Exemplo:**
```python
th = MCRThreshold()
th.observar(0.8); th.observar(0.7); th.observar(0.9)
th.calcular()     # 0.8 (mediana)
th.calcular(0.5)  # 0.4 (mediana * 0.5)
```

---

## MCREntropia

```python
en = MCREntropia(nome="")
en.alimentar(token: str) -> None
en.esta_em_loop() -> bool
en.variacao() -> float
```

---

## MCRBuffer

```python
buf = MCRBuffer(nome="", limite=20)
buf.adicionar(item: Dict) -> bool
buf.flush() -> bool
buf.pendentes() -> int
buf.stats() -> Dict
```

---

## MCRSession

```python
ses = MCRSession(base_dir=None)
ses.registrar(pergunta: str, resposta: str, metadados=None) -> None
ses.salvar_checkpoint(estado_extra=None) -> bool
ses.carregar_checkpoint() -> Optional[Dict]
ses.auto_retomar() -> Optional[Dict]
ses.historico_recente(n=5) -> List[Dict]
ses.stats() -> Dict
```

**Exemplo:**
```python
ses = MCRSession()
ses.salvar_checkpoint()
# ... (programa reinicia)
estado = ses.auto_retomar()
if estado:
    print(f"Retomando: {estado['ultima_pergunta']}")
```

---

## MCRFragmento / MCRFragmentador

```python
frag = MCRFragmento(nome, funcao, args=None)
frag.executar() -> bool

fr = MCRFragmentador(nome="")
fr.adicionar(nome, funcao, args=None) -> None
fr.executar_todos() -> List[MCRFragmento]
fr.limpar() -> None
fr.stats() -> Dict
```

---

## MCRConexao

```python
cx = MCRConexao(motor: MCRMotor)
cx.analisar(topico_a: str, topico_b: str) -> Dict
cx.melhor_ponte(a: str, b: str) -> Optional[Dict]
cx.relatorio(a: str, b: str) -> str
```

**Exemplo:**
```python
cx = MCRConexao(motor)
r = cx.analisar("spa", "shc")
print(r['melhor']['palavra'], r['melhor']['score'])
```

---

## MCRMotor

```python
motor = MCRMotor()
motor.alimentar(texto: str, nome_topico=None) -> str
motor.alimentar_json(arquivo: str) -> int
motor.conectar(a: str, b: str, forcar=False) -> Optional[Dict]
motor.gerar_por_assinatura(texto: str, passos=10, conf_min=0.15) -> str
motor.explorar_todos() -> List[Dict]
motor.relatorio() -> str
motor.salvar_estado(arquivo: str) -> None
```

**Retorno de `conectar()`:**
```python
{
    'hash': str,
    'topico_a': str,
    'topico_b': str,
    'tipo_ponte': str,       # 'conteudo_compartilhado' | 'conteudo_mas_parcial' | 'byte_only'
    'palavra_a': str,
    'palavra_b': str,
    'sequencia': str,         # sequência emergente gerada
    'nota': float,            # 0-10
    'detalhes': {
        'byte': float,        # 0-2
        'palavra': float,     # 0-5
        'token': float,       # 0-3
        'penalidade': float,  # 0.0 - 0.9
        'desconto': str,      # "0%", "30%", etc.
        'jaccard_a': float,
        'jaccard_b': float,
        'equacao': str,       # "(1.5+4.5+3.0)x(1-0.0)=9.0"
        'nota_final': float,
    },
    'nivel': str,  # 'EMERGENTE_FORTE' | 'EMERGENTE_MEDIO' | ...
}
```

---

## MCRAutoLoop

```python
auto = MCRAutoLoop(motor=None, base_dir=None)
auto.carregar_dados(arquivo: str) -> int
auto.loop(a: str, b: str, max_iter=12, expansoes=None) -> Dict
```

**Exemplo:**
```python
auto = MCRAutoLoop(MCRMotor())
auto.carregar_dados("dados.json")
resultado = auto.loop("spa", "arvore_natal", max_iter=5)
print(f"Melhor nota: {resultado['melhor_nota']}/10")
print(f"Ciclos: {resultado['ciclos']}")
```

---

## MCRPiEngine

```python
MCRPiEngine.avaliar_entropia(texto: str) -> float
MCRPiEngine.decidir_metodo(texto: str) -> str
MCRPiEngine.continuar_padrao(texto: str, motor: MCRMotor, max_passos=10) -> str
MCRPiEngine.relatorio(motor: MCRMotor) -> str
```

**Exemplo:**
```python
h = MCRPiEngine.avaliar_entropia("SPA e o sistema de")
print(h)  # 0.419 → modo 'byte'

resultado = MCRPiEngine.continuar_padrao("SPA e o sistema de", motor, 8)
print(resultado)
# "SPA e o sistema de progressao do aventureiro com dominios elementais..."
```
