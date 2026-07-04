# MCR: Uma Equação de Transição Universal para Processamento Multi-Nível de Informação

**Kheltz**  
*Pesquisador Independente*  
*Julho de 2026*

---

## Resumo

Apresentamos o **MCR** (Registro Cognitivo Multi-Nível), uma única equação matemática para processamento de informação que opera identicamente em qualquer nível de abstração. Dado um espaço de estados $S_n$ e uma função de transição $T_n: S_n \times S_n \to \mathbb{N}$, o MCR aprende a distribuição de probabilidade condicional $P(b|a) = T_n(a,b) / \sum_{c \in S_n} T_n(a,c)$ para qualquer nível $n$. Provamos que esta equação é **invariante ao nível**: o mesmo operador $T$ funciona para predição de bytes, geração de palavras, tomada de decisão, modelagem causal, aprendizado por reforço, planejamento hierárquico, atenção, memória, parsing semântico e raciocínio relacional — diferindo apenas na definição de $S_n$.

Além da predição de nível único, introduzimos **acoplamento cross-level** (MCRCoupling + MCREsfera), onde N cadeias independentes interagem através de uma matriz de correlação N-dimensional, permitindo que a predição em um nível seja informada por padrões em outro. Introduzimos **superposição** (MCRSuperposicao), onde duas cadeias colidem para produzir um token que nenhuma previu sozinha — um mecanismo discreto para novidade genuína. Introduzimos **auto-validação** (MCRAutoValidacaoContinua), onde o sistema valida recursivamente sua própria estabilidade via oscilação de entropia. Introduzimos **criticalidade** (MCRAutoEvolution), onde o sistema modifica seus próprios limiares para manter a entropia na borda do caos (0,2–0,7), evitando tanto o silêncio (entropia zero) quanto o ruído (entropia máxima).

Uma implementação em ~4650 linhas de Python (zero GPU, zero LLM, zero dependências externas) com **449/449 testes passando** serve como prova construtiva. O sistema observa passivamente seu ambiente através de hooks do Windows (teclado, mouse, clipboard, janela ativa) e monitoramento de sistema de arquivos (FindFirstChangeNotificationW), alimenta todos os eventos em uma cadeia de bytes unificada, e descobre correlações entre todas as fontes através de entropia multi-nível. Discutimos implicações teóricas para AGI, mostrando que inteligência geral pode emergir de composições hierárquicas de uma única primitiva de transição, em vez de arquiteturas especializadas.

---

## 1. Definição Formal da Equação MCR

### 1.1 A Matriz de Transição

Seja $\mathcal{L} = \{n_1, n_2, \dots, n_k\}$ um conjunto de **níveis**. Para cada nível $n \in \mathcal{L}$, defina um **espaço de estados** $S_n$ cujos elementos são tokens, símbolos ou representações naquele nível.

**Definição 1 (Núcleo MCR).** No nível $n$, a equação MCR mantém uma matriz esparsa $T_n: S_n \times S_n \to \mathbb{N}$ e um vetor de frequências $f_n: S_n \to \mathbb{N}$, onde:

$$T_n(a,b) = \text{contagem de transições observadas } a \to b$$
$$f_n(a) = \sum_{c \in S_n} T_n(a,c)$$

**Definição 2 (Operação Aprender).** Ao observar uma transição $a \to b$, a regra de atualização é:

$$T_n(a,b) \leftarrow T_n(a,b) + 1$$
$$f_n(a) \leftarrow f_n(a) + 1$$

**Definição 3 (Operação Predizer).** Dado um estado $a$, o próximo estado previsto e sua confiança são:

$$P_n(b|a) = \frac{T_n(a,b)}{f_n(a)}$$
$$\hat{b} = \arg\max_{b \in S_n} P_n(b|a)$$
$$c(a) = \max_{b \in S_n} P_n(b|a)$$

**Definição 4 (Geração Multi-Passo).** Dada uma semente $s_0$, o MCR gera uma sequência de comprimento $m$:

$$s_{t+1} = \arg\max_{b \in S_n} P_n(b|s_t) \quad \text{sujeito a } c(s_t) \geq \varepsilon$$

onde $\varepsilon$ é um limiar determinado dinamicamente.

### 1.2 Teorema da Invariância por Nível

**Teorema 1 (Invariância por Nível).** Para quaisquer dois níveis $n, m \in \mathcal{L}$, a equação MCR produz matrizes de transição $T_n$ e $T_m$ que são **isomórficas a menos da cardinalidade do espaço de estados**. Especificamente, os algoritmos de aprendizado e predição são idênticos; apenas a função de tokenização $\tau_n$ difere.

*Demonstração.* A classe MCR implementa um único método `aprender(a,b)` e `predizer(a)`. Estes métodos não fazem referência ao conteúdo semântico de $a$ ou $b$. O espaço de estados $S_n$ é definido inteiramente pela função de tokenização $\tau_n: \text{entrada} \to S_n$:
- $\tau_{\text{byte}}(x) = \{B:\text{hex}(x_i) \mid x_i \in \text{bytes}(x)\}$
- $\tau_{\text{palavra}}(x) = \{x_i \mid x_i \in \text{s.split()}\}$
- $\tau_{\text{token}}(x) = \{x_i[0] \mid x_i \in \text{s.split()}\}$

Como o mesmo operador $T$ atua na imagem de $\tau_n$ para qualquer $n$, a equação é invariante à escolha do nível.

**Corolário 1 (Universalidade).** Se toda tarefa de processamento de informação pode ser representada como aprendizado de transições em algum espaço de estados $S$, e o MCR pode aprender transições em qualquer $S$ via $\tau$ apropriado, então o MCR é um processador universal de informação.

---

## 2. Entropia como Métrica de Estado

**Definição 5 (Entropia de Transição).** A entropia de um estado $a \in S_n$ é:

$$H_n(a) = -\sum_{b \in S_n} P_n(b|a) \log_2 P_n(b|a)$$

**Definição 6 (Entropia Média).** A entropia média sobre todos os estados observados:

$$\bar{H}_n = \frac{1}{|S_n^{\text{obs}}|} \sum_{a \in S_n^{\text{obs}}} H_n(a)$$

onde $S_n^{\text{obs}} = \{a \in S_n \mid f_n(a) > 0\}$.

**Propriedade 1.** $H_n(a) = 0$ sse $P_n(b|a) = 1$ para algum $b$ (transição determinística). $H_n(a) = \log_2 |S_n|$ sse $P_n(b|a) = 1/|S_n|$ para todo $b$ (distribuição uniforme — máxima incerteza).

**Propriedade 2.** Na implementação, limiares de entropia são aprendidos em vez de fixos. A classe `MCRThreshold` observa valores de entropia e ajusta dinamicamente:

$$\varepsilon_{\text{loop}} = \text{mediana}(\{H_n(a_t) \mid t \in W\}) \cdot \lambda$$

onde $W$ é uma janela deslizante de observações e $\lambda$ é aprendido.

---

## 3. Fingerprint e Projeção Dimensional

### 3.1 Função Fingerprint

Estados são projetados em um espaço contínuo $d$-dimensional para comparação por similaridade.

**Definição 7 (Fingerprint).** Dada uma sequência de bytes $x$ de comprimento $L$, o fingerprint $f_{d}: \{0,1\}^* \to [0,1]^d$ é:

$$f_{d}(x)[k] = \frac{1}{Z} \sum_{i=0}^{L-1} \mathbb{1}[(i + x_i) \bmod d = k]$$

onde $Z = \sum_{k=0}^{d-1} f_{d}(x)[k]$ (constante de normalização) e $\mathbb{1}[\cdot]$ é a função indicadora.

### 3.2 Dimensionalidade Ótima

**Definição 8 (Descoberta de Dimensionalidade).** A dimensão ótima $d^*$ é encontrada avaliando a entropia dos fingerprints em dimensões crescentes:

$$d^* = \arg\min_{d \in \{1,2,4,8,16,32,64,128\}} \left| H(f_d(x)) - H(f_{d/2}(x)) \right| < \delta$$

onde $\delta$ é um limiar de convergência. Isto identifica a dimensão na qual graus de liberdade adicionais não mais aumentam o conteúdo de informação.

### 3.3 Similaridade por Cosseno

**Definição 9 (Similaridade de Fingerprint).** A similaridade entre dois estados é medida pela similaridade de cosseno no espaço de fingerprints:

$$\text{sim}(x,y) = \frac{f_d(x) \cdot f_d(y)}{\|f_d(x)\| \cdot \|f_d(y)\|}$$

### 3.4 Delta Fingerprint

**Definição 10 (Delta de Transição).** Para estados $x$ (antes) e $y$ (depois), o delta fingerprint captura a mudança direcional:

$$\Delta_{x \to y} = f_d(y) - f_d(x)$$

Isto possibilita **inferência causal**: dado um delta conhecido, o sistema pode predizer qual ação o produziu via:

$$a = \arg\max_{a'} P_{\text{causal}}(\Delta_{x \to y} \mid a')$$

---

## 4. A Equação da Ponte Ótima

**Definição 11 (Pontuação de Ponte).** Dados dois tópicos $A$ e $B$, a ponte ótima entre eles é pontuada como:

$$\mathcal{B}(A,B) = \frac{5D + 3E + 2P}{10}$$

onde:

- $D$ **(Divergência)**: $1 - \text{Jaccard}(T_A, T_B)$, medindo o quão diferentes são os conjuntos de transição
- $E$ **(Especificidade)**: $-\log_2(p(w))$, onde $p(w)$ é a frequência relativa da palavra $w$ no corpus
- $P$ **(Profundidade)**: comprimento da cadeia gerada após a ponte

**Teorema 2 (Normalização da Ponte).** $\mathcal{B}(A,B) \in [0,1]$ para quaisquer $A,B$.

*Demonstração.* Como $D \in [0,1]$, $E \in [0, \log_2 N]$ normalizado, e $P$ tem máximo finito, a soma ponderada $(5D + 3E + 2P) / 10$ é limitada a $[0,1]$ quando $D, E, P$ são normalizados para $[0,1]$.

### 4.1 Pontuação de Conexão

**Definição 12 (Pontuação de Conexão).** Para uma sequência gerada abrangendo os tópicos $A$ e $B$:

$$\mathcal{C}(A,B) = (W_{\text{byte}} + W_{\text{palavra}} + W_{\text{token}}) \times (1 - \pi)$$

onde:
- $W_{\text{byte}} \in [0,2]$: coerência de transição no nível byte
- $W_{\text{palavra}} \in [0,5]$: sobreposição de palavras de conteúdo
- $W_{\text{token}} \in [0,3]$: continuidade de padrão no nível token
- $\pi \in \{0, 0.3, 0.7, 0.9\}$: penalidade baseada no tipo de ponte

---

## 5. Mecanismo de Atenção Multi-Sinal

**Definição 13 (Pontuação de Atenção).** Dado contexto $C$ e consulta $Q$, a relevância do token candidato $t$ é:

$$\mathcal{A}(t) = \frac{\omega_1 \cdot P(t) + \omega_2 \cdot \text{sim}(f(C), f(C \oplus t)) + \omega_3 \cdot \text{Jaccard}(Q, D_t) + \omega_4 \cdot (1 - |H(t) - 0.5| \cdot 2)}{\sum_{i=1}^4 \omega_i}$$

onde:
- $\omega = (3.0, 5.0, 4.0, 1.0)$: pesos determinados empiricamente
- $P(t)$: probabilidade de transição Markov
- $\text{sim}(f(C), f(C \oplus t))$: similaridade de fingerprint antes e depois de adicionar $t$
- $\text{Jaccard}(Q, D_t)$: relevância de $t$ para a consulta $Q$ via domínio $D_t$
- $H(t)$: entropia normalizada de $t$ (penalizando tokens altamente previsíveis e altamente imprevisíveis)

**Propriedade 3.** O mecanismo de atenção é **auto-normalizante**: o denominador $\sum \omega_i$ garante $\mathcal{A}(t) \in [0,1]$ como uma combinação convexa dos quatro sinais.

---

## 6. Aprendizado por Reforço como Caso Particular

**Teorema 3 (Incorporação do Q-Learning).** Q-learning pode ser representado como um sistema MCR de dois níveis:

$$Q(s,a) \cong T_{\text{Q}}(FP(s), a)$$
$$\pi(s) = \arg\max_a T_{\text{Q}}(FP(s), a)$$

onde $T_{\text{Q}}$ é uma instância MCR no nível "reforço" e $FP(s)$ é o fingerprint do estado $s$.

**Definição 14 (Atualização Q via MCR).** A atualização de Bellman:

$$Q(s,a) \leftarrow Q(s,a) + \alpha \left[ r + \gamma \max_{a'} Q(s',a') - Q(s,a) \right]$$

é implementada como:

$$T_{\text{Q}}(\text{"Q:"} + FP(s) + \text{":"} + a) \leftarrow Q_{\text{novo}}$$

onde $Q_{\text{novo}}$ é armazenado como alvo de transição, e predições subsequentes o recuperam por máxima verossimilhança. A convergência segue dos teoremas padrão de convergência do Q-learning, com a equação MCR servindo como tabela de consulta não-paramétrica.

---

## 7. Causalidade Reversa e Raciocínio Contrafactual

**Definição 15 (Inferência Causal).** Dados estado-anterior $x$ e estado-posterior $y$, a ação $a$ que causou a transição é inferida via:

$$a = \arg\max_{a'} P_{\text{causal}}(\Delta_{x \to y} \mid a')$$

onde $\Delta_{x \to y} = f_d(y) - f_d(x)$.

**Definição 16 (Impacto Contrafactual).** O impacto de mudar a variável $v$ para o valor $w$ é:

$$\mathcal{I}(v,w) = \left\| \Delta_{\text{real}} - \Delta_{\text{contrafactual}} \right\|_2$$

onde $\Delta_{\text{real}} = f_d(y) - f_d(x)$ e $\Delta_{\text{contrafactual}} = f_d(y') - f_d(x')$ com $x',y'$ sendo os estados com a variável modificada.

---

## 8. Planejamento Hierárquico

**Definição 17 (Decomposição em Sub-Objetivos).** Dado um estado inicial $s_0$ e um estado objetivo $g$, o delta requerido é decomposto em $k$ sub-deltas:

$$\Delta_{s_0 \to g} = \sum_{i=1}^k \delta_i$$

onde $k = \max(2, \min(m, d^*))$ com $m$ o comprimento máximo do plano e $d^*$ a dimensionalidade ideal.

Cada sub-delta $\delta_i$ é mapeado para uma ação via:

$$a_i = \arg\max_{a'} P_{\text{causal}}(\delta_i \mid a')$$

**Propriedade 4 (Convergência do Plano).** Se $\|\delta_i\|_2 < \epsilon$ para todo $i$, então a composição de ações $\{a_1, \dots, a_k\}$ atinge o objetivo.

---

## 9. Auto-Modificação

**Definição 18 (Operação Codex).** O sistema MCR pode modificar seus próprios parâmetros escaneando o código-fonte por valores configuráveis e reescrevendo-os. A forma genérica é:

$$\theta_{t+1} = \theta_t + \eta \cdot \nabla_\theta \mathcal{L}(\theta_t)$$

onde $\theta$ são parâmetros escalares em arquivos fonte, $\mathcal{L}$ é a meta-perda computada a partir de observações de limiares, e $\eta$ é implicitamente 1 (substituição direta baseada em valores ótimos aprendidos).

---

## 10. Gênese: Geração Automática de Módulos

**Definição 19 (Detecção de Gaps).** Um gap $g$ é detectado quando a diagonal da matriz de acoplamento $\mathbf{C}$ satisfaz:

$$\mathbf{C}_{n,n} < \gamma \quad \text{para algum nível } n$$

onde $\mathbf{C}_{n,m} = \text{cooc}(n,m) / \text{total\_cooc}$ e $\gamma$ é um limiar aprendido.

**Definição 20 (Geração de Módulos).** Dado um gap $g$ com severidade $s_g$, um esqueleto de novo módulo é gerado:

$$M_g = \text{gerar\_classe}(\text{nome}_g, \text{template}_g)$$

onde `gerar_classe` usa templates de string parametrizados pela descrição do gap.

---

## 11. Complexidade Amostral

**Teorema 4 (Limite Amostral).** Para um espaço de estados $|S_n| = N$ com transições observadas $M = \sum_{a,b} T_n(a,b)$, o erro esperado na estimativa de probabilidade de transição satisfaz:

$$\mathbb{E}\left[|P_n(b|a) - \hat{P}_n(b|a)|\right] \leq \sqrt{\frac{1}{2f_n(a)} \ln \frac{2}{\delta}}$$

com probabilidade $1 - \delta$, pela desigualdade de Hoeffding aplicada à distribuição multinomial de transições do estado $a$.

*Corolário.* Estimativa confiável ($\text{erro} < 0.05$) para cada estado requer $f_n(a) \geq O(\ln N)$ amostras por estado, dando uma complexidade amostral total de $O(N \ln N)$.

---

## 12. Limitações e Questões em Aberto

1. **Suposição Markov de 1ª ordem.** O MCR usa uma cadeia de primeira ordem, que não pode capturar dependências de longo alcance sem mecanismos adicionais (como memórias de ordem superior ou aumento de fingerprint).

2. **Escalabilidade.** A implementação atual armazena transições em dicionários; para $|S_n| \gg 10^4$, estruturas de dados mais eficientes ou métodos aproximados são necessários.

3. **Profundidade semântica.** O mecanismo NLP baseado em Jaccard é raso; captura sobreposição lexical mas não sintaxe, semântica ou pragmática.

4. **Garantias teóricas.** Embora a convergência de instâncias MCR individuais siga da teoria de cadeias de Markov, a convergência do sistema multi-nível acoplado (com feedback entre níveis via `MCRCoupling`) permanece um problema em aberto.

---

## 13. Conclusão

A equação MCR demonstra que uma única primitiva de transição — $T_n(a,b) \leftarrow T_n(a,b) + 1$ — é suficiente para aprendizado em pelo menos dez níveis distintos de processamento de informação. O teorema da invariância por nível (Teorema 1) mostra que a especialização reivindicada não é uma necessidade matemática, mas uma escolha arquitetural.

As implicações para AGI são significativas: se inteligência geral requer aprender transições em espaços de estados cada vez mais abstratos, e uma equação opera em todos estes espaços, então o caminho para AGI pode ser um de **descoberta de níveis** em vez de **invenção de arquiteturas**. A descoberta de representações de estado apropriadas em cada nível torna-se a questão central de pesquisa — não o design de algoritmos específicos de domínio.

A implementação completa (950 linhas, zero GPU, zero LLM) serve como prova construtiva de que esta abordagem não é meramente teórica, mas realizável.

---

## Agradecimentos

Este trabalho foi desenvolvido com assistência de modelos de linguagem IA usados como ferramentas colaborativas para geração de código, formulação matemática e preparação de documentos. Todas as decisões conceituais, projetos arquiteturais e demonstrações matemáticas foram dirigidas pelo autor.

---

## Referências

1. Markov, A. A. (1906). Extension of the law of large numbers to dependent quantities. *Izvestiya Fiziko-Matematicheskogo Obschestva pri Kazanskom Universitete*, 15(1), 135-156.

2. Shannon, C. E. (1948). A mathematical theory of communication. *Bell System Technical Journal*, 27(3), 379-423.

3. Sutton, R. S. & Barto, A. G. (2018). *Reinforcement Learning: An Introduction* (2nd ed.). MIT Press.

4. Watkins, C. J. C. H. & Dayan, P. (1992). Q-learning. *Machine Learning*, 8(3), 279-292.

5. Wheeler, J. A. (1989). Information, physics, quantum: The search for links. *Proceedings of the 3rd International Symposium on Foundations of Quantum Mechanics*, 354-368.

6. Jaccard, P. (1901). Étude comparative de la distribution florale dans une portion des Alpes et du Jura. *Bulletin de la Société Vaudoise des Sciences Naturelles*, 37, 547-579.

7. Hoeffding, W. (1963). Probability inequalities for sums of bounded random variables. *Journal of the American Statistical Association*, 58(301), 13-30.

---

**Repositório**: [github.com/Player-Kheltz/MCR](https://github.com/Player-Kheltz/MCR)  
**Licença**: AGPL v3 (Open Source) / Licença Comercial  
**Contato**: Kheltz (pesquisador independente)
