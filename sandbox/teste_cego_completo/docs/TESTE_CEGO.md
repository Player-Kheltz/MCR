# 🧪 Protocolo de Teste Cego — MCR vs Cloud

## 1. O que é o Teste Cego?

O Teste Cego é um protocolo de **comparação justa** entre dois agentes:

- **Cloud** = LLM (qwen2.5-coder:7b) rodando **sem pipeline**, resposta direta
- **MCR** = Orquestrador + templates + KG + ContextCrew V3 (pipeline completo)

Ambos recebem **exatamente a mesma pergunta/prompt** e respondem de forma independente,
**sem saber** a resposta do outro.

O foco é **CAPACIDADE TÉCNICA UNIVERSAL** — análise de código, arquitetura, raciocínio,
geração de código, refatoração, debugging. **Nenhum domínio é favorecido.**

## 2. Critérios de Avaliação (Universais)

| Prioridade | Critério | Descrição |
|-----------|----------|-----------|
| 1 | **Validade** | Resposta não está vazia, quebrada ou é um erro |
| 2 | **Não-genericidade** | Resposta não usa frases de "encher linguiça" (em suma, vale ressaltar, etc.) |
| 3 | **Riqueza vocabular** | Mais palavras significativas (não-stopwords) = mais substância |
| 4 | **Completude** | Mais caracteres úteis (sem ser genérico) |

**Não são critérios:** conhecimento de domínio específico, keywords de projeto, nomes próprios.
O teste mede capacidade de **engenharia de software geral**.

## 3. Protocolo (passo a passo)

### 3.1 Preparação

```bash
# 1. Limpar processos
taskkill /f /im python.exe; taskkill /f /im canary-sln.exe

# 2. Verificar estado
python MCR_DevIA-Kernel.py status

# 3. Copiar arquivos de teste para sandbox (proteção)
copy "projeto/real/arquivo.py" "sandbox/teste_cego/arquivos/"

# 4. Criar diretórios
mkdir sandbox/teste_cego/respostas_cloud/
mkdir sandbox/teste_cego/respostas_mcr/
```

### 3.2 Execução (para CADA pergunta)

```
1. 📝 Cloud lê a pergunta (SEM acesso ao MCR)
2. 📝 Cloud escreve resposta em respostas_cloud/test_N.txt
3. 🤖 MCR-DevIA recebe a MESMA pergunta (SEM acesso à resposta do Cloud)
4. 🤖 MCR-DevIA escreve resposta em respostas_mcr/test_N.txt
5. 🔄 Repetir para todas as N perguntas
6. 📊 SÓ ENTÃO comparar
```

**REGRAS ABSOLUTAS:**
- ❌ Cloud NUNCA lê a resposta do MCR antes de escrever a sua
- ❌ MCR NUNCA recebe contexto extra que o Cloud não teve
- ✅ Ambos recebem EXATAMENTE o mesmo prompt
- ✅ Cloud escreve PRIMEIRO, MCR depois (cego)
- ✅ O comparador só é executado DEPOIS que todos os testes foram feitos

### 3.3 Arquivos de Teste

Arquivos reais do projeto são COPIADOS para `sandbox/teste_cego_completo/arquivos/`
para que modificações nunca afetem o projeto real.

## 4. Categorias de Teste

| # | Categoria | Capacidade medida |
|---|-----------|------------------|
| 1 | **grep_busca** | Encontrar padrões e bugs em código alheio |
| 2 | **leitura_analise** | Compreender e explicar código |
| 3 | **correcao_bug** | Identificar e corrigir bugs reais |
| 4 | **geracao_codigo** | Escrever código novo e funcional seguindo padrões |
| 5 | **arquitetura** | Projetar sistemas extensíveis |
| 6 | **raciocinio** | Explicar conceitos complexos e relações entre componentes |
| 7 | **revisao** | Code review: apontar problemas de segurança, perf, manutenção |
| 8 | **criacao_lore** | Criatividade: gerar narrativa coerente com personagens |
| 9 | **diagnostico** | Diagnosticar causas raiz de problemas reportados |
| 10 | **refatoracao** | Melhorar código existente sem quebrar funcionalidade |
| 11 | **planejamento** | Planejar implementação de features complexas |
| 12 | **escrita_racionio** | Sintetizar conhecimento e lições aprendidas |

## 5. Placar

```
MCR: N   Cloud: M   Empates: P
```

Cada teste dá 1 ponto para o vencedor. Critérios universais, sem favorecimento de domínio.
Empate técnico = nenhum ponto.

## 6. Como Criar um Novo Teste Cego

1. Escolher **arquivos reais** do projeto (copiar para sandbox)
2. Definir **prompt universal** (não depende de conhecimento de domínio)
3. Criar entrada em `bateria.json` com: id, categoria, titulo, arquivos[], prompt
4. Executar: Cloud responde primeiro, MCR depois
5. Comparar com `comparador.py`

## 7. Lições Aprendidas

1. **Métricas automáticas enganam**: contagem de chars/nomes não mede qualidade
2. **Contexto ajuda mas não é decisivo**: o que importa é a capacidade de raciocínio
3. **Genericidade é o pior defeito**: uma resposta genérica não agrega valor
4. **Domínio não deve ser critério**: o teste mede engenharia, não conhecimento de Tibia
5. **Ambos devem ter o mesmo input**: a única diferença deve ser o pipeline (MCR vs raw)
