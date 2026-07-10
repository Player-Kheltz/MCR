# Plano: Quarto Domínio — C++

**Status:** Planejado (não implementado)  
**Prioridade:** Baixa (após maturação do Web Console e dos 3 domínios atuais)  
**Objetivo:** Prova de fogo da Universalidade Condicional (Teorema 5) no domínio mais complexo estruturalmente disponível.

---

## 1. Por que C++?

| Critério | C++ |
|----------|-----|
| Estruturalmente distinto de Lua/C#/SQL | C++ tem herança múltipla, templates, macros, pré-processador, compilação separada (.hpp vs .cpp), e gerenciamento manual de memória. Nenhum domínio atual cobre isso. |
| Vocabulário Σ massivo | O servidor Canary tem dezenas de milhares de linhas em C++. Somado a STL/Boost, o alfabeto de tokens explodiria, testando `O(|Σ|^k ln |Σ|^k)` de forma brutal. |
| Corpus aberto disponível | O código-fonte do Canary está no repositório. |
| Utilidade prática imensa | Um MCR que entende C++ poderia gerar correções de bug, sugerir refatorações, e atuar como assistente de desenvolvimento do próprio servidor. |

## 2. Desafios Técnicos Conhecidos

### 2.1 Parser

**Opção A — raw_token_set (stdlib):** O tokenizador universal atual separa por espaços e pontuação. C++ tem muitos operadores ( `::`, `->`, `<<`, `>>`, `++`, `--`, `&&`, `||`, `<=`, `>=`, `==`, `!=` ) que seriam quebrados em tokens individuais. Exemplo:

```
std::cout << "hello" << std::endl;
```
→ `std`, `:`, `:`, `cout`, `<`, `<`, `"hello"`, `<`, `<`, `std`, `:`, `:`, `endl`

Isso pode ser suficiente para clusterização (como foi para SQL), mas perderia informação estrutural importante (escopo de namespace, templates aninhados).

**Opção B — tree-sitter-cpp:** tree-sitter tem grammar para C++. Daria AST completa com escopo, templates, macros. Porém, violaria a condição da prova de universalidade (parser especializado por domínio).

**Recomendação:** Usar `raw_token_set` primeiro (para manter a prova de genericidade), e comparar com tree-sitter-cpp como benchmark.

### 2.2 Sandbox (ShadowCpp)

Diferente de SQLite (stdlib) ou dotnet build (SDK instalável), compilar C++ requer um toolchain completo:

- **Windows:** MSVC (Visual Studio Build Tools, ~5GB)
- **Linux:** GCC/Clang (geralmente pré-instalado)
- **macOS:** Clang (Xcode Command Line Tools)

Opções de sandbox:

1. **GCC/Clang direto:** Compilar arquivo `.cpp` temporário com `g++ -fsyntax-only` ou `-c` (apenas verificação de sintaxe, sem linkedição). Leve e rápido.
2. **CMake + compilação completa:** Mais realista (testa linkedição), mas muito mais lento.
3. **Clangd-based:** Usar `libclang` para Python para parsing e verificação sem compilação. Evita dependência de toolchain.

**Recomendação:** Usar `g++ -std=c++20 -fsyntax-only` para validação rápida (sintaxe + templates básicos), com fallback para compilação completa se necessário.

### 2.3 Macros e Pré-processador

Macros C++ ( `#define`, `#ifdef`, `#include` ) são pré-processadas antes da compilação. O MCR operaria sobre o código **pós-processado** (saída do pré-processador) ou **pré-processado** (código fonte bruto)?

**Recomendação:** Operar sobre código fonte bruto, incluindo diretivas de pré-processador como tokens. O cold start geraria snippets C++ sem macros (código direto), e o sandbox aceitaria código fonte bruto.

### 2.4 Templates

Templates C++ são Turing-complete em tempo de compilação. O MCR não tentaria gerar templates complexos (metaprogramação) — apenas instanciações simples como `std::vector<int>`. O tokenizador universal trataria `<` e `>` como delimitadores, então `vector<int>` viraria `vector`, `int`. Isso pode ser suficiente.

## 3. Plano de Execução

### Fase 0 — Preparação (1 dia)

- Coletar corpus de ~50 arquivos `.cpp`/`.hpp` do servidor Canary (src/ do servidor)
- Verificar se `encoding.py` já trata `.cpp` e `.hpp` (sim, já mapeado para utf-8)
- Implementar `SanityValidatorCpp` usando `raw_token_set` (sem tree-sitter)
- Implementar `ShadowCpp` usando `g++ -fsyntax-only`

### Fase 1 — Cold Start (1 dia)

- Executar Cold Start C++ com `SanityValidatorCpp` + `ShadowCpp`
- Verificar clusterização: espera-se clusters como `class/struct/method/function`
- Gerar snippet C++: struct simples com métodos

### Fase 2 — Pipeline (1 dia)

- Adicionar `criar_cpp` ao MarkovDecider
- Prompt template para geração de código C++
- Pipeline routing para geração C++

### Fase 3 — Prova de Universalidade (1 dia)

- Cold Start lado a lado: Lua, C#, SQL, C++
- Relatório com 4 domínios

## 4. Critérios de Sucesso

1. **Cold Start < 30s:** Mineração de ~50-100 arquivos C++, clusterização, geração de snippet compilável
2. **Snippet válido:** `g++ -fsyntax-only` aceita o código gerado sem erros
3. **Sem modificação no kernel:** O `mcr_kernel` não é alterado
4. **Clusterização significativa:** Pelo menos 3 clusters claros (classes, funções, estruturas de dados)

## 5. Quando Executar

- [ ] Web Console está polido e estável
- [ ] 3 domínios atuais têm cobertura de testes automatizados
- [ ] ShadowCpp pode ser testado em CI (GCC disponível)
- [ ] Esses 3 critérios devem estar verdes antes de iniciar
