# Limitações Honestas do MCR

> O que o MCR NÃO faz, o que ele faz mal, e onde você não deve usá-lo.

---

## 1. Não entende linguagem

O MCR aprende transições entre palavras (bigramas). Ele não tem:
- Compreensão semântica
- Gramática (sintaxe, morfologia)
- Conhecimento de mundo
- Capacidade de responder perguntas que exigem raciocínio

A "conversa" no modo chat é Markov puro: ele prevê a próxima palavra mais provável
dada a anterior. Não há entendimento do que foi dito.

## 2. Não raciocina

O MCR não consegue:
- Fazer silogismos (Se A>B e B>C, então A>C?) — a não ser que a sequência exata
  já tenha sido alimentada
- Resolver problemas novos que exigem abstração
- Transferir aprendizado entre domínios não relacionados
- Planejamento de longo prazo coerente

A "inferência transitiva" na `MCRRedeSemantica` é uma BFS num grafo pequeno,
não raciocínio lógico.

## 3. Geração de texto é primitiva

- Repetitiva (o Markov tende a repetir padrões frequentes)
- Sem coerência além de 2-3 palavras
- Facilmente entra em loop
- Não tem "voz" ou estilo — só imitação estatística

## 4. Parsing semântico é frágil

- Rule-based, não aprendido
- Só funciona para português
- Só cobre ~75% das sentenças declarativas simples
- Não resolve anáfora ("João disse que ele vai" → "ele" não é resolvido)
- Não parseia orações subordinadas

## 5. Dependência de plataforma

- **Hooks** (teclado, mouse, clipboard, janela): Windows-only (Win32 API)
- **File Observer** (`FindFirstChangeNotificationW`): Windows-only
- Em Linux/macOS, esses módulos falham silenciosamente

## 6. Web search é frágil

- Usa scraping do DuckDuckGo HTML (sem API oficial)
- Pode quebrar se o HTML do DuckDuckGo mudar
- Limitado a 3 snippets por busca
- Timeout de 5 segundos

## 7. Não escala

- Transições armazenadas em dicionários Python (RAM)
- Sem poda de memória — cresce indefinidamente
- Sem compressão de estados
- Para >10^4 estados, performance degrada

## 8. Sem garantia de convergência

O acoplamento entre múltiplos níveis (coupling + esfera + superposição)
não tem provas matemáticas de convergência. O sistema pode entrar em
ciclos ou atratores dos quais não sai sozinho.

## 9. Testes são autônomos, não independentes

Os testes são executados pelo próprio MCR contra ele mesmo.
Não há validação por terceiros. Os testes verificam que o sistema
faz o que promete, mas não que o que promete é útil ou correto.

---

## Resumo

| Área | Status |
|------|--------|
| Classificação de sequências | ✅ Funciona (bigramas determinísticos) |
| Detecção de anomalias multi-nível | ✅ Funciona (entropia temporal) |
| Extração de triplas semânticas | ⚠️ Funciona parcialmente (PT-BR only, frágil) |
| Geração de texto | ❌ Markov puro, repetitivo, sem coerência |
| Raciocínio lógico | ❌ Não faz |
| Compreensão de linguagem | ❌ Não tem |
| Escalabilidade | ❌ Não escala |
| Portabilidade | ❌ Windows-only para hooks/file observer |

---

*Editado em Julho de 2026 para refletir o estado real do projeto.*
