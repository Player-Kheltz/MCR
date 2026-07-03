# MCRAutoValidacaoContinua — O Loop Que Se Valida

## O Problema

Hoje o MCR **aprende** continuamente mas **valida** sob demanda:

```
aprender() → alimentar() → ...

diagnosticar() → "gap detectado"  ← so quando chamado
test_mcr_veracidade() → 134/134   ← so quando rodado
```

A validação nunca é **contínua**, **recursiva**, ou **auto-referente**. O código pergunta "estou funcionando?" apenas quando um humano manda.

## A Ideia

Cada `MCR(nivel)` valida a si mesmo, valida os outros, e é validado — num loop recursivo que só para quando a entropia do próprio validador estabiliza.

```
Nivel 0 → Nivel 1 → ... → Nivel N
   ↓         ↓           ↓
Validador → Validador → Validador  (valida cada nivel)
   ↓
Meta-Validador                  (valida os validadores)
   ↓
Loop                            (repete ate entropia do meta < threshold)
```

## O Algoritmo

```python
class MCRAutoValidacaoContinua:
    """Cada cadeia valida a si mesma, valida as outras, e e validada.
    
    O loop recursivo so para quando a entropia do proprio
    validador esta abaixo do threshold — ou seja, quando
    o sistema esta confiante sobre seu proprio estado.
    """
    
    def __init__(self):
        self.cadeias: Dict[str, MCR] = {}
        self.historico: Dict[str, List[float]] = {}
        self.meta_validadores: Dict[str, MCR] = {}
        self.entropia_anterior: Dict[str, float] = {}
        self.instavel: Set[str] = set()
        self.frequencia = 1.0  # Hz real (ciclos por alimentar())
    
    def registrar_cadeia(self, nome: str, mk: MCR):
        self.cadeias[nome] = mk
        self.historico[nome] = []
        self.entropia_anterior[nome] = 1.0
    
    def ciclo(self):
        """Um ciclo completo de auto-validacao.
        
        1. Valida cada cadeia (intra)
        2. Valida pares de cadeias (cross)
        3. Meta-valida os validadores
        4. Ajusta frequencia
        5. Repete se necessario
        """
        if not self.cadeias:
            return {"status": "sem_cadeias"}
        
        # 1. Intra-validacao: cada cadeia se valida
        intra = self._validar_intra()
        
        # 2. Cross-validacao: cadeias validam umas as outras
        cross = self._validar_cross()
        
        # 3. Meta-validacao: os validadores sao validados
        meta = self._validar_meta(intra, cross)
        
        # 4. Frequencia adaptativa
        self._ajustar_frequencia(meta)
        
        # 5. Instabilidade detectada?
        if self.instavel:
            self._recalibrar()
        
        return {
            "intra": intra,
            "cross": cross,
            "meta": meta,
            "instaveis": list(self.instavel),
            "frequencia": self.frequencia,
        }
    
    def _validar_intra(self) -> Dict[str, float]:
        """Cada cadeia valida a si mesma.
        
        Metrica: variacao da entropia media.
        Se entropia subiu >50% em relacao ao anterior,
        a cadeia esta 'desaprendendo' — algo mudou nos dados.
        """
        resultados = {}
        for nome, mk in self.cadeias.items():
            if mk.total == 0:
                resultados[nome] = 1.0
                continue
            
            ent_atual = mk.entropia_media()
            ent_ant = self.entropia_anterior.get(nome, ent_atual)
            
            # Variacao relativa
            variacao = abs(ent_atual - ent_ant) / max(ent_ant, 0.001)
            
            resultados[nome] = round(variacao, 4)
            
            if variacao > 0.5:
                self.instavel.add(nome)
            elif nome in self.instavel and variacao < 0.1:
                self.instavel.discard(nome)
            
            self.historico.setdefault(nome, []).append(ent_atual)
            if len(self.historico[nome]) > 100:
                self.historico[nome] = self.historico[nome][-100:]
            self.entropia_anterior[nome] = ent_atual
        
        return resultados
    
    def _validar_cross(self) -> Dict[str, float]:
        """Cadeias validam umas as outras.
        
        Metrica: variacao da correlacao entre pares.
        Se a correlacao entre byte e palavra caiu muito,
        a relacao entre eles mudou — re-alimentar necessario.
        """
        resultados = {}
        pares = list(self.cadeias.keys())
        
        for i in range(len(pares)):
            for j in range(i + 1, len(pares)):
                a, b = pares[i], pares[j]
                
                # Tenta predizer b a partir de a
                amostra_a = list(self.cadeias[a].freq.keys())
                if not amostra_a:
                    continue
                
                # Usa alguns valores de a para predizer b
                acertos = 0
                total = 0
                for valor_a in amostra_a[:20]:
                    pred, _ = self.cadeias[a].predizer(valor_a)
                    # Simplificacao: verifica se o valor de a
                    # aparece no vocabulario de b
                    if pred and pred in self.cadeias[b].freq:
                        acertos += 1
                    total += 1
                
                correlacao = acertos / max(total, 1)
                resultados[f"{a}->{b}"] = round(correlacao, 3)
                
                if correlacao < 0.1 and total > 10:
                    # Correlacao muito baixa — cadeias dessincronizadas
                    self.instavel.add(f"{a}<->{b}")
        
        return resultados
    
    def _validar_meta(self, intra: dict, cross: dict) -> float:
        """Meta-validador: valida os proprios validadores.
        
        As metricas de validacao (intra, cross) sao alimentadas
        em cadeias Markov separadas. A entropia dessas cadeias
        mede o quanto o validador esta 'confuso'.
        
        Se o meta-validador tem entropia alta, ele mesmo
        precisa se recalibrar — antes de validar qualquer
        outra coisa.
        """
        # Cria meta-cadeias se necessario
        if "meta_intra" not in self.meta_validadores:
            self.meta_validadores["meta_intra"] = MCR("meta_intra")
            self.meta_validadores["meta_cross"] = MCR("meta_cross")
        
        # Alimenta meta-cadeias com as metricas de validacao
        meta_intra = self.meta_validadores["meta_intra"]
        meta_cross = self.meta_validadores["meta_cross"]
        
        for nome, variacao in intra.items():
            estado = f"intra:{nome}:{int(variacao*100)}"
            if meta_intra.total > 0:
                ultimo = list(meta_intra.freq.keys())[-1] if meta_intra.freq else estado
                meta_intra.aprender(ultimo, estado)
            else:
                meta_intra.aprender("_init_", estado)
        
        for par, correlacao in cross.items():
            estado = f"cross:{par}:{int(correlacao*100)}"
            if meta_cross.total > 0:
                ultimo = list(meta_cross.freq.keys())[-1] if meta_cross.freq else estado
                meta_cross.aprender(ultimo, estado)
            else:
                meta_cross.aprender("_init_", estado)
        
        # Entropia do meta-validador = quao confuso ele esta
        ent_meta = meta_intra.entropia_media() if meta_intra.total > 0 else 1.0
        
        return round(ent_meta, 4)
    
    def _ajustar_frequencia(self, ent_meta: float):
        """Frequencia adaptativa: entropia decide o clock.
        
        Quanto mais confuso o meta-validador, mais rapido
        o ciclo de validacao roda. Quanto mais estavel,
        mais lento — economiza recursos.
        """
        # Frequencia varia de 0.1 Hz (estavel) a 10 Hz (caotico)
        self.frequencia = max(0.1, min(10.0, ent_meta * 10))
    
    def _recalibrar(self):
        """Recalibra cadeias instaveis.
        
        Quando uma cadeia esta instavel (entropia variou >50%),
        ela e 'resetada' parcialmente: as transicoes mais
        antigas sao esquecidas, dando peso maior ao novo
        padrao dos dados.
        """
        for nome in list(self.instavel):
            mk = self.cadeias.get(nome)
            if not mk:
                continue
            
            # Esquece transicoes com frequencia 1 (ruido)
            # e mantem so o que se repetiu
            transicoes_para_remover = []
            for a, trans in mk.transicoes.items():
                for b, count in list(trans.items()):
                    if count < 2:
                        transicoes_para_remover.append((a, b))
            
            for a, b in transicoes_para_remover:
                del mk.transicoes[a][b]
                if not mk.transicoes[a]:
                    del mk.transicoes[a]
                    mk.freq.pop(a, None)
            
            # Recalcula total
            mk.total = sum(sum(t.values()) for t in mk.transicoes.values())
    
    def status(self) -> dict:
        """Estado atual do sistema de auto-validacao."""
        return {
            "n_cadeias": len(self.cadeias),
            "n_instaveis": len(self.instavel),
            "instaveis": list(self.instavel),
            "frequencia_hz": round(self.frequencia, 2),
            "entropia_media": round(
                sum(self.entropia_anterior.get(n, 0) for n in self.cadeias)
                / max(len(self.cadeias), 1), 4
            ),
        }
```

## Exemplo de Execução

```python
validacao = MCRAutoValidacaoContinua()
validacao.registrar_cadeia("byte", cerebro.mk_byte)
validacao.registrar_cadeia("palavra", cerebro.mk_palavra)
validacao.registrar_cadeia("token", cerebro.mk_tven)

# A cada N alimentos, roda ciclo:
for i in range(100):
    cerebro.alimentar(novo_texto)
    if i % max(1, int(1/validacao.frequencia)) == 0:
        r = validacao.ciclo()
        if r["instaveis"]:
            print(f"Cadeias instaveis: {r['instaveis']}")
        if r["meta"] < 0.05:
            print("Sistema estabilizou — validacao confiavel")
```

## O Loop Recursivo

A profundidade da recursão é determinada pela **entropia do meta-validador**:

```
Entropia do meta > 0.5  →  validador esta confuso
                         →  precisa validar a si mesmo
                         →  cria meta²
                         →  repete ate ent stabilizar

Entropia do meta < 0.05 →  validador confiavel
                         →  validacao e aceita
                         →  meta² nunca e criado
```

Isso significa que a profundidade da validacao **emerge** do estado do sistema — não é fixa. Um sistema estavel tem 1 nível de validação. Um sistema caótico pode ter N níveis, cada um validando o anterior, até que a entropia do validador mais profundo estabilize.

## Relação com o que já existe

| Componente | Hoje | Com auto-validacao continua |
|-----------|-------|---------------------------|
| `MCR.entropia()` | Mede entropia de um estado | **Todas as cadeias, continuamente** |
| `MCREntropia` | Detecta loop no gerador | **Loop adaptativo em todas as cadeias** |
| `MCRCodex` | Escaneia hardcodes no codigo | **Escaneia cadeias por instabilidade** |
| `MCRSelfHeal` | Avalia um resultado | **Ciclo continuo de auto-avaliacao** |
| `test_mcr_veracidade.py` | 134 testes, sob demanda | **Testes continuos em tempo real** |

## Status

**Conceito.** Próximo passo: implementar protótipo que demonstre o ciclo de auto-validação em 3 cadeias (byte, palavra, token) com detecção de instabilidade.

Implementação: ~200 linhas, utilizando MCR existente + integrado ao CerebroAGI.
