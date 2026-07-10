# MCRHiperesferaAutoExpansiva — Design

## Problema

Hoje o `MCREsfera` tem **dimensões fixas**:
```python
# Escolhidas pelo humano, nao pelo MCR:
niveis = ["byte", "palavra", "tven", "intencao", "acao"]
```

Isso é um hardcode arquitetural. O MCR descobre a dimensionalidade dos dados (`MCRSignatureExpansiva.dimensionalidade_ideal()`) mas não aplica isso à própria estrutura.

## Ideia Central

Uma **hiperesfera auto-expansiva** que:

1. Começa com 0 dimensões
2. Adiciona uma dimensão por vez, na direção que MAIS REDUZ a entropia total
3. Para quando a entropia estabiliza
4. Cada dimensão é um `MCR.registrar_nivel()` em tempo real

A pergunta guia não é mais "qual a próxima palavra?" — mas:

> *"Quantas dimensões preciso para explicar estes dados? Qual a PRÓXIMA dimensão a adicionar? Em que DIREÇÃO devo expandir?"*

## Algoritmo

```python
class MCRHiperesferaAutoExpansiva:
    def __init__(self):
        self.dimensoes: Dict[str, MCR] = {}  # nome -> MCR
        self.esfera: MCREsfera = MCREsfera()  # correlacoes N-dim
        self.entropia_historico: List[float] = []
        self.thr_ent = MCRThreshold("hiper_ent")
    
    def alimentar(self, dados):
        """Alimenta todos os niveis existentes + esfera."""
        for nome, mk in self.dimensoes.items():
            mk.aprender_sequencia(dados.get(nome, []))
        
        # Alimenta esfera com correlacoes entre niveis
        for nome_a in self.dimensoes:
            for nome_b in self.dimensoes:
                if nome_a >= nome_b: continue
                self.esfera.alimentar_correlacao(nome_a, nome_b, dados)
    
    def entropia_total(self) -> float:
        """Entropia media de TODAS as dimensoes + correlacoes."""
        if not self.dimensoes:
            return 1.0  # entropia maxima (total desconhecimento)
        
        # Entropia media intra-nivel
        ent_intra = 0
        for nome, mk in self.dimensoes.items():
            ent_intra += mk.entropia_media()
        ent_intra /= len(self.dimensoes)
        
        # Entropia das correlacoes (quao imprevisiveis sao as relacoes entre niveis)
        ent_cross = 0
        count = 0
        for nivel_a in self.dimensoes:
            for valor_a in self.dimensoes[nivel_a].freq:
                for nivel_b in self.dimensoes:
                    if nivel_b == nivel_a: continue
                    r, c = self.esfera.predizer_cross(nivel_b, **{nivel_a: valor_a})
                    if r is None:
                        ent_cross += 1.0  # maxima entropia (nao sabe)
                    else:
                        ent_cross += 1.0 - c  # entropia = 1 - confianca
                    count += 1
        if count > 0:
            ent_cross /= count
        
        return (ent_intra + ent_cross) / 2
    
    def precisa_expandir(self) -> bool:
        """Decide se precisa de mais dimensoes baseado na tendencia de entropia."""
        ent = self.entropia_total()
        self.entropia_historico.append(ent)
        
        if len(self.entropia_historico) < 3:
            return True  # sempre expande no inicio
        
        # Verifica se a entropia ESTABILIZOU
        # (ultimos 3 valores com variacao < threshold)
        recentes = self.entropia_historico[-3:]
        variacao = max(recentes) - min(recentes)
        
        thr = self.thr_ent.obter("estabilizacao", 0.05)
        return variacao > thr
    
    def descobrir_proxima_dimensao(self, dados_raw) -> str:
        """Encontra a DIMENSAO que mais REDUZ a entropia se adicionada.
        
        Para cada tokenizacao candidata:
        1. Simula adicionar a dimensao
        2. Calcula entropia simulada
        3. Retorna a que MAIS reduz entropia
        """
        candidatos = self._gerar_candidatos(dados_raw)
        melhor_nome = None
        melhor_reducao = 0
        
        ent_atual = self.entropia_total()
        
        for nome, tokenizador in candidatos:
            # Simula adicionar esta dimensao
            ent_sim = self._entropia_simulada(nome, tokenizador, dados_raw)
            reducao = ent_atual - ent_sim
            
            if reducao > melhor_reducao:
                melhor_reducao = reducao
                melhor_nome = nome
        
        return melhor_nome
    
    def _gerar_candidatos(self, dados_raw) -> List[Tuple[str, Callable]]:
        """Gera possiveis novas dimensoes.
        
        Candidatos incluem:
        - Tokenizacoes do proprio dado (bytes, palavras, linhas, etc.)
        - Transformacoes (hashes, fingerprints, entropia local)
        - Derivadas (deltas, acumulados)
        - Projecoes de outras dimensoes (pca-like com fingerprint)
        
        Nao ha limites pre-definidos — qualquer funcao que produza
        uma sequencia de estados e um candidato.
        """
        candidatos = []
        
        # Candidatos universais (sempre disponiveis)
        candidatos.append(("byte", lambda d: [f"B:{b:02x}" for b in d.encode()]))
        candidatos.append(("palavra", lambda d: re.findall(r'\b\w+\b', d.lower())))
        candidatos.append(("linha", lambda d: d.split('\n')))
        candidatos.append(("token_tipo", lambda d: [
            'M' if c.isupper() else 'm' if c.islower() else 'd' if c.isdigit() else 'o'
            for c in d[:1000]
        ]))
        
        # Candidatos derivados do proprio MCR
        if "byte" in self.dimensoes:
            candidatos.append(("byte_delta", lambda d: [
                f"Δ:{abs(d[i+1]-d[i]):02x}"
                for i in range(min(len(d)-1, 500))
            ]))
        
        # Candidatos baseados em entropia local
        candidatos.append(("entropia_local", lambda d: [
            f"E:{int(MCRByteUtils.entropia_bytes(d[i:i+10].encode())*10)}"
            for i in range(0, min(len(d), 1000), 5)
        ]))
        
        return candidatos
    
    def _entropia_simulada(self, nome, tokenizador, dados_raw) -> float:
        """Calcula entropia total se uma nova dimensao fosse adicionada."""
        # Cria MCR temporario para a nova dimensao
        mk_temp = MCR(nome)
        tokens = tokenizador(dados_raw)
        for i in range(len(tokens) - 1):
            mk_temp.aprender(tokens[i], tokens[i+1])
        
        ent_nova = mk_temp.entropia_media()
        ent_atual = self.entropia_total()
        
        # Entropia simulada = media ponderada entre atual e nova
        n = len(self.dimensoes) + 1
        return (ent_atual * (n - 1) + ent_nova) / n
    
    def adicionar_dimensao(self, nome, tokenizador):
        """Adiciona uma nova dimensao a hiperesfera."""
        if nome in self.dimensoes:
            return
        
        mk = MCR(nome)
        self.dimensoes[nome] = mk
        MCR.registrar_nivel(nome, mk)
        
        # Alimenta a nova dimensao com todos os dados existentes
        for nivel_existente in self.dimensoes:
            if nivel_existente == nome: continue
            self.esfera.registrar_correlacao(nome, nivel_existente)
    
    def ciclo(self, dados_raw):
        """Um ciclo completo de expansao.
        
        1. Alimenta niveis existentes
        2. Calcula entropia total
        3. Se precisa expandir: descobre nova dimensao, adiciona
        4. Repete ate entropia estabilizar
        """
        ent_inicial = self.entropia_total()
        expansoes = 0
        
        while self.precisa_expandir():
            nova_dim = self.descobrir_proxima_dimensao(dados_raw)
            if nova_dim is None:
                break  # nenhuma dimensao reduz entropia
            
            self.adicionar_dimensao(nova_dim, ...)
            expansoes += 1
            
            # Seguranca: limite absoluto para evitar loop infinito
            if expansoes > 100:
                break
        
        ent_final = self.entropia_total()
        
        return {
            "expansoes": expansoes,
            "entropia_inicial": round(ent_inicial, 3),
            "entropia_final": round(ent_final, 3),
            "dimensoes": list(self.dimensoes.keys()),
            "reducao": f"{(ent_inicial - ent_final) / ent_inicial * 100:.1f}%" if ent_inicial > 0 else "0%",
        }
```

## Como Se Compara ao Atual

| Aspecto | MCREsfera (atual) | MCRHiperesferaAutoExpansiva |
|---------|-------------------|---------------------------|
| Dimensões | Fixas (byte, palavra, etc.) | **Descobertas por entropia** |
| Tokenização | Humano escolhe | **MCR decide entre candidatos** |
| Limite | 5 dimensões | **∞ (até estabilizar)** |
| Critério de parada | Nenhum | **Entropia estabiliza < threshold** |
| Direção de expansão | N/A | **Gradiente de menor entropia** |
| Auto-reflexão | Não | **Aplica equacao sobre si mesmo** |

## Relação com o que já existe

A hiperesfera não substitui nada — ela ORQUESTRA:

```
MCRSignatureExpansiva  → descobre dimensionalidade dos DADOS
MCREsfera              → correlaciona DIMENSOES
MCRHiperesferaAutoExpansiva → descobre quais DIMENSOES criar
MCRDecisorUniversal    → decide thresholds
MCRGenesis             → gera código para novas dimensões
```

## Exemplo de Execução

```python
hiper = MCRHiperesferaAutoExpansiva()

# Alimenta com texto
hiper.alimentar({"raw": "O MCR e um experimento em minimalismo"})

# Ciclo de expansao
resultado = hiper.ciclo("O MCR e um experimento em minimalismo")

print(resultado)
# → {
#     "expansoes": 4,
#     "entropia_inicial": 1.0,
#     "entropia_final": 0.312,
#     "dimensoes": ["byte", "palavra", "token_tipo", "byte_delta"],
#     "reducao": "68.8%"
# }
```

A ordem de descoberta seria:

1. **byte** — sempre a primeira (dado bruto)
2. **palavra** — reduz entropia (texto tem estrutura)
3. **token_tipo** — reduz mais (maiuscula/minuscula ajuda)
4. **byte_delta** — reduz um pouco (transicoes de byte tem padrao)
5. **para** — entropia estabilizou em 0.312, threshold 0.05

## Status

**Conceito.** Proximo passo: protótipo funcional que demonstre o ciclo de expansão em um dataset real (ex: artigo científico, código fonte, ou conversa).

Implementação estimada: ~300 linhas, utilizando MCR existente + MCREsfera + MCRSignatureExpansiva.
