# Licoes Recentes

## 2026-06-28 — Sessao Major: qwen14b GPU + Enricher + ToT + Auto-Teste + Framing Positivo

### Resumo do que foi feito
1. **Upgrade qwen14b com GPU forcing**: `main_gpu=0, num_gpu=99` elevou GPU de 15% para 97%. Router de modelos unificado.
2. **Framing positivo (anti-elefante rosa)**: MCR_IDENTITY.md e todos os prompts NUNCA mais mencionam termos errados (Minecraft, Single Page Application). O modelo parou de alucinar "Minecraft C++ Reloaded".
3. **Context Enricher**: Novo módulo que gera conteúdo NOVO (nomes, dados técnicos, comparações) usando ferramentas (grep em Python) + FAST. Cache LRU 5min.
4. **Tree of Thought**: 3 perspectivas paralelas (analítico, criativo, crítico) + síntese final. Pipeline integrado.
5. **Revamp de scripts legados**: 10 scripts arquivados, 3 funções úteis extraídas, 4 scripts externos atualizados para router.
6. **Auto-Teste Definitivo**: Teste universal com gerador FAST, auto-crítica MCR, gaps, feedback arquitetural. Documentado em docs/AUTO_TESTE.md.
7. **Detecção de escopo MCR vs Geral**: Pipeline agora detecta se pergunta é MCR ou conhecimento geral. Para geral, pula todo contexto MCR.

### Problemas Identificados e Soluções

#### 1. qwen14b rodava em CPU (15% GPU)
- **Causa**: Sem `main_gpu`/`num_gpu`, Ollama joga parte das camadas na CPU por safety.
- **Solução**: Adicionar `main_gpu=0, num_gpu=99` às configs dos modelos 14b no router.
- **Resultado**: GPU 97%, VRAM 9.9GB/10GB.

#### 2. Modelo alucinava "Minecraft C++ Reloaded" mesmo com contexto
- **Causa**: Efeito "elefante rosa" — MCR_IDENTITY.md dizia "NUNCA confunda MCR com Minecraft". A palavra "Minecraft" ativava o viés.
- **Solução**: Remover TODAS as negações que mencionam termos errados. Apenas afirmar o correto.
- **Resultado**: Zero ocorrências de "Minecraft" nas respostas após a correção.

#### 3. Modelo ignorava contexto enriquecido (respondia genérico)
- **Causa**: O LLM ignora placeholders separados. Contexto precisa estar DENTRO da pergunta.
- **Solução**: Injetar CR + Enricher na própria `solicitacao_mod` + validação pós-resposta.
- **Resultado**: Respostas passaram de 314 chars para 1834 chars com dados técnicos.

#### 4. Respostas genéricas em perguntas gerais
- **Causa**: Pipeline forçava contexto MCR em TUDO (até "mudanças climáticas" virava "servidor de Tibia").
- **Solução**: Detecção de escopo. Se pergunta não tem termos MCR, pula CR, Enricher, ToT, KG, ContextInfinity.
- **Resultado**: Perguntas gerais recebem respostas neutras e corretas.

#### 5. Tree of Thought reintroduzia alucinações na síntese
- **Causa**: A síntese do ToT juntava as 3 perspectivas sem filtrar, e uma delas podia conter "Minecraft".
- **Solução**: Filtrar perspectivas com alucinações antes de sintetizar + framing positivo no prompt de síntese.

### Lições Aprendidas
> **GPU forcing é obrigatório para modelos 14b em GPU com 10GB.** Sem `main_gpu/num_gpu`, o Ollama usa CPU por safety e o desempenho cai 80%.
>
> **Framing positivo elimina o elefante rosa.** Nunca mencionar o termo errado. Apenas afirmar o correto. Isso se aplica a prompts, identidade e validações.
>
> **LLM ignora contexto separado.** Contexto precisa estar DENTRO da pergunta, não como placeholder, para ser usado.
>
> **Modelos 14b NÃO são sempre melhores que 7b.** deepseek-r1:7b detectou SQL injection que o qwen14b perdeu. O modelo certo depende da tarefa.
>
> **Tempo de pipeline ~150s (com ToT) é aceitável para respostas complexas.** Cache LRU reduz drasticamente para perguntas repetidas.

### Métricas
- Pipeline completo (CR + Enricher + ToT): ~143-181s
- Modo geral (sem MCR): ~26s
- GPU utilization: 97% (antes 15%)
- VRAM: 9.9GB/10GB
- Arquivos modificados: ~30+ (entre ia.py, util.py, pipeline_executor.py, orquestrador.py, context_reinforcer.py, conselho.py, auto_revisor.py, mente.py, supervisor.py, context_enricher.py, tree_of_thought.py, cmd_autoteste.py, MCR_IDENTITY.md, e ~6 arquivos de padronização)

### Pendências Futuras
- CoT (Chain-of-Thought) via deepseek-r1:7b para raciocínio antes da geração
- Ciclo 2 do Auto-Teste com correções de escopo
- Revamp dos 4 scripts remanescentes com hardcoded (finalizado)

## 2026-06-27 — Teste Cego: MCR (orquestrador) vence Cloud 3x0 em precisão

### Problema
Métricas automáticas (nomes próprios, chars) favorecem Cloud mesmo quando Cloud alucina.
Teste cego com 3 perguntas mostrou:
- Pergunta "O que é SPA?": Cloud respondeu "Single Page Application" ❌. MCR: "Sistema de Progressão do Aventureiro" ✅.
- Pergunta "Crie lore Eridanus": MCR 19 nomes (Tibia) vs Cloud 7 nomes (genérico). MCR venceu ✅.
- Pergunta "Diferença SHC vs SPA?": Cloud disse "SHC = Sistema Hospitalar de Classe A" ❌. MCR disse corretamente ✅.

### Causa
O Cloud usa qwen2.5-coder:7b **sem contexto** — não tem MCR_IDENTITY, não tem KG, não tem lessons.
O orquestrador injeta identidade + contexto do KG + lessons em cada template.
Quando o modelo não tem contexto, ele expande siglas para o que parece mais provável (SPA = "Single Page Application", SHC = "Sistema Hospitalar").

### Solução
- Métricas automáticas de teste cego DEVEM incluir verificação semântica (keyword match de conceitos corretos), não apenas contagem.
- Precisa de validador de siglas: se resposta contém "Single Page Application" para SPA no MCR, é automaticamente INVALIDA.
- O orquestrador é estritamente superior em precisão (3x0) mas métricas simples não capturam isso.

### Lição
> Precisão semântica > métricas superficiais. Teste cego precisa de validação semântica,
> não apenas contagem de caracteres/nomes. O orquestrador vence porque TEM contexto;
> Cloud sem contexto alucina siglas mesmo em modelos bons (qwen2.5-coder).

## 2026-06-27 — Conselho: qwen2.5-coder > deepseek-r1 para veredito + dívida técnica

### Problema
Conselho alucinava SPA como "Single Page Application", "Subsystem of Progress and Access",
"Sistema de Controle de Acesso" mesmo com MCR_IDENTITY explícito. Causa: deepseek-r1:7b
tem viés para expandir siglas e ignora instruções "NÃO faça X".

### Solução
- Trocar modelo do veredito no `conselho.py` linha 229: `"conceito" (deepseek) → "pesado" (qwen2.5-coder:7b)`
- Teste controlado provou: qwen acertou SPA em 2.5s com 0 alucinações; deepseek acertou sigla mas inventou modelagem 3D, amuletos (4.3s)
- Conselho agora detecta perguntas factuais e não gera personagens/locais/artefatos para elas
- `cmd_conselho.py` valida resposta antes de salvar no KG (filtra alucinações)

### Solução: Dívida técnica
- Varredura encontrou 24 duplicatas entre sandbox/ e scripts/mcr_devia/
- 7 cópias idênticas + 3 órfãs = 10 removidas de scripts/
- 17 versões diferentes mantidas (propositos distintos)
- `_run_script()` prioriza sandbox, então cópias nunca seriam executadas

## 2026-06-26 — V12 Contexto Agregado + aprender_conceito + SUPERVISAO

### Problema
autoavaliador IA consumia ate 3 fast() calls e ainda retornava respostas
genericas (ex: "SPA = Sistema de Progressao do Aventureiro" sem contexto).
V12 direto retornava lessons cruas sem expansao.

### Solucao: V12 Contexto Agregado
- Acha top lesson por keyword match
- Busca lessons RELACIONADAS no KG pelo titulo (erro) + contexto (ctx)
- Agrupa ate 4 lessons
- Fast expande em resposta contextual (1 fast() vs 2-3 antes)
- 0 retorno de lesson crua — sempre expande

### Solucao: aprender_conceito
- Novo comando MCR-DevIA: `aprender_conceito "<conceito>"`
- Busca codigo fonte no projeto inteiro
- IA sintetiza conhecimento CONCEITUAL (nao codigo)
- Salva no KG com `ctx=conceito_codigo`
- Universal: funciona para qualquer conceito (SPA, SHC, Canary, etc.)
- Prompt inclui identidade MCR para evitar interpretacao generica de siglas

### Solucao: Fragmentos Dinamicos 0 IA
- `_detectar_tamanho()` usa heuristicas Python (palavras-chave na descricao)
- + ContextCrew se disponivel para refinar
- 0 chamadas IA para estimar linhas

### Solucao: ContextCrew cache no build
- `self.contexto_crew` definido em `executar()`, reusado em `_gerar_direto()`
- 1 chamada ContextCrew por build (antes 2)

### Solucao: Patch aceita caminho absoluto
- Se argumento e caminho absoluto existente, usa direto
- Senao, busca em SANDBOX (comportamento anterior)

### Regra SUPERVISAO atualizada em AGENTS.md e equipe.md
- Quando MCR-DevIA erra, Cloud SUPERVISIONA (da prompt especifico), nao assume
- MCR-DevIA se auto-repara com o feedback
- Cloud so assume apos 3 falhas consecutivas
- `ensinar` a licao depois de resolver

## 2026-06-26 — Otimizacao MCR-DevIA: 3 ciclos de melhoria

### Problema
MCR-DevIA lento para testes (879.6s), 44% dos testes usavam IA,
28 subprocess.run com duplo fork em 16 atalhos, loop OODA infinito.

### Ciclo 1 — KG + Review (ganho: -44% a -84% em review)
- Centralizar stop words em `stop_words.py` (antes duplicado em 3 arquivos)
- Cache LRU para `kg.buscar()` (64 entradas, elimina recomputação)
- Pré-popular KG com 13 FAQs (converteu perguntas factuais para V12)
- Dedup KG: 94 lessons duplicadas mescladas
- Review em lote: 1 chamada IA para todos os itens (antes 1/item)
  - review: validador: 42.8s → 7.0s (-84%)
  - review: runas.xml: 21.8s → 12.3s (-44%)

### Ciclo 2 — Loop + Fork Unico (ganho: loop 300s→0.3s)
- Loop OODA aceita `max_ciclos` argumento (antes infinito)
  - loop test: 303.2s → 0.3s (-99.9%)
- 16 atalhos (auditar, autoavaliar, etc.) agora usam fork único
- `_run_script()` helper + dicionário `ATALHOS_DIRETOS`
- Eliminados 16 subprocess.run duplicados (28→12, -57%)
- Eliminados 15 elif branches (47→32, -32%)

### Ciclo 3 — V12 mais inteligente (V12: 56%→62%)
- V12 check agora aceita match se erro da lesson contém keyword
- fast: SHC: 41.3s → 0.3s (agora V12 via redirecionamento ao Supervisor)
- perg: comandos e perg: modelo analisar agora V12 (via FAQ no KG)

### Resultado Final
- 67/67 testes PASS (100% consistente)
- V12 coverage: 56% → 62% (+6pp)
- Tempo total: variável (depende carga Ollama), mas determinístico caiu 99%
- 3 gargalos restantes (plan/build/debate) são Ollama-bound, não otimizáveis

### Licao
O maior ganho veio do loop infinito (300s→0.3s). O segundo maior foi
melhorar o V12 matching para usar mais KG e menos IA. Refatorar subprocess
teve impacto menor do que esperado (fork é rápido no Windows).

## 2026-06-23 — Gerenciamento de processos em segundo plano

## 2026-06-23 — Canal Assistente (500)

## 2026-06-23 — Bridge v4 (7b + RAG + Cache)

## 2026-06-23 — RAG + Encoding

## 2026-06-23 — Anti-alucinacao

## 2026-06-24 — OTClient: stdcpp23 incompativel com VS 2022 MSVC 14.41

No VS 2022 Community 17.14 (MSVC 14.41.34120), o valor `<LanguageStandard>stdcpp23</LanguageStandard>`
gera o flag `/std:c++23preview` na linha de comando do compilador, que NÃO é reconhecido
(resultando em warning D9002 e fallback para C++14 default, causando centenas de erros
de `std::string_view`, `std::span`, `std::numbers`, `std::optional` nao encontrados).

**Solucao:** Usar `stdcpp20` em vez de `stdcpp23`. O C++20 oferece todos os recursos que o
OTClient precisa (string_view desde C++17, span e numbers desde C++20).

**Importante:** o valor `stdcpplatest` (que gera `/std:c++latest`) funciona em algumas versoes
do MSVC mas pode apresentar comportamento imprevisivel entre versoes. Prefira `stdcpp20` para
compatibilidade garantida com VS 2022.

Afeta 6 configuracoes no otclient.vcxproj. Todas alteradas para stdcpp20.

## 2026-06-24 — OTClient: string_view::contains() é C++23, não C++20

O método `std::string_view::contains()` foi adicionado apenas no C++23 (P1679R3).
Ao mudar de `stdcpp23` para `stdcpp20`, o código que usa `contains()` em string_views
quebra com `error C2039: 'contains': não é um membro de 'std::basic_string_view'`.

**Solucao:** Substituir por `find() != npos` (C++17):
```cpp
// ANTES (C++23):
if (separators.contains(*p))
// DEPOIS (C++17):
if (separators.find(*p) != std::string_view::npos)
```

**Importante:** Apenas `string_view::contains()` é C++23. Os métodos `map::contains()`,
`unordered_map::contains()`, `set::contains()` são C++20 e funcionam normalmente.
Afeta 2 linhas no arquivo `OTClient/src/framework/stdext/string.cpp`.

## 2026-06-24 — OTClient: Erro de link __std_* por ABI mismatch vcpkg + VS dual install

### Problema
Após corrigir a compilação, o link falha com:
```
libprotobuf.lib : error LNK2001: símbolo externo não resolvido __std_rotate
openal32.lib : error LNK2001: símbolo externo não resolvido __std_search_1
absl_string_view.lib : error LNK2001: símbolo externo não resolvido __std_find_end_1
```

### Causa Raiz
O usuário tem **duas versões do Visual Studio** instaladas:
- `C:\Program Files\Microsoft Visual Studio\2022` — MSVC 14.41.34120
- `C:\Program Files\Microsoft Visual Studio\2026` — MSVC 14.51.36231

O **vcpkg** (v2026-04-08) automaticamente detecta e usa o **VS mais recente** (2026)
para compilar as bibliotecas estáticas (abseil, protobuf, openal-soft, etc.),
produzindo libs com ABI do MSVC 14.51.

O **MSBuild** (chamado via AGENTS.md) usa o VS 2022 (toolset v143) com MSVC 14.41.
O linker 14.41 não reconhece os símbolos `__std_*` gerados pelo MSVC 14.51,
resultando em LNK2001.

### Solução que Funcionou (24/06/2026)
Forçar a compilação do OTClient com **VS 2026 (toolset v145)** — a ÚNICA forma de alinhar
o ABI com as libs do vcpkg (que inevitavelmente usam MSVC 14.51):

1. Alterar `PlatformToolset` de `v143` para `v145` no `otclient.vcxproj` (6 configs)
2. Compilar com o MSBuild do VS 2026:
   ```cmd
   cmd.exe /c """C:\Program Files\Microsoft Visual Studio\2026\Community\VC\Auxiliary\Build\vcvars64.bat"" && ""C:\Program Files\Microsoft Visual Studio\2026\Community\MSBuild\Current\Bin\amd64\MSBuild.exe"" ""%%MCR%%\OTClient\vc17\otclient.vcxproj"" /p:Configuration=OpenGL /p:Platform=x64 /t:Build /m"
   ```

> **Nota:** Tentativas de forçar o vcpkg a usar VS 2022 via vcvars64.bat ou variáveis de
> ambiente FALHAM porque o CMake (usado internamente pelo vcpkg) detecta VS pelo registro
> do Windows/COM, não por variáveis de ambiente.

### Prevenção
- Manter apenas UMA versão do VS se possível
- Se tiver ambas (2022 + 2026), o OTClient DEVE ser compilado com VS 2026
- O Canary (servidor) continua compilando normalmente com VS 2022 (v143)

## 2026-06-24 — Lição Crítica: Processos esquecidos causam crash cumulativo

### Problema
Deixei um bridge Python rodando em background (PID 17728) por 12+ horas.
Quando o usuário abria novas sessões do OpenCode, o processo antigo ainda
estava lá, consumindo recursos. Acumulei:
  - 1 bridge Python esquecido
  - 1 arquivo .bridge_pid com PID inválido
  - Múltiplas tentativas de Start-Process via PowerShell (em vez de Python)

O Bun crashava porque:
  1. Processos acumulados fragmentavam a memória
  2. Arquivos PID com referências a processos mortos confundiam scripts
  3. Eu entrava em loops de "tenta de novo" em vez de parar e limpar

### O que vou fazer diferente

1. **Cleanup obrigatório no início de cada sessão** — matar Python e canary
   antes de qualquer operação, remover arquivos PID órfãos
2. **NUNCA deixar processo em background** — se eu iniciar, eu mato antes
   de encerrar ou antes de iniciar outro
3. **Um arquivo .pid por processo, sempre verificado** — se o PID não
   existe mais, remover o arquivo
4. **Máximo 1 tentativa por operação crítica** — falhou, reporto e paro
5. **Usar sempre Python para processos** — `subprocess.Popen` com
   `creationflags=CREATE_NEW_PROCESS_GROUP` para garantir isolamento
6. **Verificar tasklist antes de iniciar qualquer processo** —
   confirmar que o anterior realmente morreu

### Script de cleanup padrão (executar no início de toda sessão):
```python
import subprocess, os
subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True)
subprocess.run(["taskkill", "/f", "/im", "canary-sln.exe"], capture_output=True)
for f in [".bridge_pid", ".watchdog_pid"]:
    if os.path.exists(f): os.remove(f)
```

## 2026-06-24 — Lição Crítica: Loop de processos causou crash do Bun (OpenCode)

### Problema
Ficar criando/matando/reiniciando processos em loop (servidor, bridge, compilação)
causou:
- Acúmulo de processos zombies no Windows
- Fragmentação de memória (~1.5GB commit)
- Segmentation fault no Bun v1.3.14 (runtime do OpenCode)
- Perda da sessão do usuário

### Causa Raiz
1. Usei `Start-Process` do PowerShell repetidamente sem verificar se o anterior
   realmente morreu
2. Entrei em loops de "tenta de novo" em vez de parar e reportar o erro
3. Acumulei servidor + bridge + compilações simultâneas
4. Não respeitei limites de recursos do sistema

### Regras para o Futuro (NÃO QUEBRAR)

1. **NUNCA usar `Start-Process`** — sempre Python (`subprocess.Popen`) com PID tracking
2. **NUNCA entrar em loop de tentativas** — máximo 1 retry, depois fallback
3. **UM processo de cada vez** — matar antes de criar novo
4. **Timeout explícito em tudo** — comandos bash com `--timeout` sempre
5. **Se falhou 2x, pare e reporte** — não tente 3, 4, 5 vezes
6. **Antes de qualquer operação no servidor**, verificar: `server_manager.py status`
7. **Prefira scripts Python** a comandos PowerShell (menos parsing issues)
8. **Cada shell command deve ser auto-suficiente** — sem depender de estado anterior

### Fallback
Se o sistema travar ou o Bun crashar:
1. `taskkill /f /im canary-sln.exe`
2. `taskkill /f /im python.exe`
3. Limpar `.bridge_pid`, `.watchdog_pid`
4. `opencode -c` para recuperar sessão

## 2026-06-24 — OTClient: Solução definitiva ABI mismatch com VS 2026 + v145

### Problema
Com VS 2022 e VS 2026 instalados, o vcpkg (v2026-04-08) sempre detecta o VS mais
recente (2026, MSVC 14.51) para compilar dependências estáticas, independentemente
das variáveis de ambiente ou do vcvars64.bat usado. O CMake detecta VS pelo
registro do Windows/COM, não por environment variables.

### Solução que Funcionou
1. Instalar triplet `x64-windows-static` normalmente (vcpkg usará VS 2026)
2. Alterar `PlatformToolset` no `otclient.vcxproj` de `v143` para `v145` (6 configurações)
3. Compilar com o MSBuild do VS 2026:
   ```cmd
   cmd /c ""C:\Program Files\Microsoft Visual Studio\2026\Community\VC\Auxiliary\Build\vcvars64.bat" && "C:\Program Files\Microsoft Visual Studio\2026\Community\MSBuild\Current\Bin\amd64\MSBuild.exe" "...\otclient.vcxproj" /p:Configuration=OpenGL /p:Platform=x64 /t:Build /m
   ```

### O que NÃO Funcionou
- ❌ Rodar `vcpkg install` dentro do VS 2022 vcvars64 → CMake detecta VS 2026 pelo registro
- ❌ Forçar via `VCPKG_ROOT`, `VSINSTALLDIR`, `VCToolsInstallDir` → CMake usa COM, não env vars
- ❌ Toolset `v150` → VS 2026 não tem v150 instalado (apenas v145)

### Prevenção
- O Canary (servidor) SEMPRE compila com VS 2022 (v143)
- O OTClient (cliente) SEMPRE compila com VS 2026 (v145) se ambos VS estiverem instalados
- AGENTS.md atualizado com comandos corretos para cada projeto

## 2026-06-24 — OpenCode 1.17.10: Bun Segmentation Fault ao criar subprocessos com GPU

### Problema
OpenCode v1.17.10 (Bun v1.3.14) crasha com Segmentation Fault sempre que tenta criar
qualquer subprocesso (`python`, `git`, etc.) enquanto o Ollama está rodando na GPU
(NVIDIA driver 591.86). O Bun tenta mapear memória da GPU e corrompe o heap.

### Sintomas
- `opencode --version` funciona OK (não cria subprocesso)
- Qualquer comando via terminal (ex: `python -c "..."`) → Segmentation Fault
- `opencode --no-session` com Ollama desligado → funciona
- OpenClaw (Node.js, sem Bun) → funciona sempre

### Causa Raiz
Bun v1.3.14 tem um bug de corrupção de heap com NVIDIA CUDA memory mapping
(driver 591.86). Ocorre especificamente quando:
1. Ollama está rodando com GPU (carregou modelos na VRAM)
2. Bun tenta criar um subprocesso via `Bun.spawn()` ou similar
3. O memory-mapping do CUVA conflita com o allocator do Bun → SIGSEGV

### Solução
**Downgrade para OpenCode v1.17.9** (Bun v1.3.13 ou anterior):
- Baixar o binário do CDN da opencode.ai (NÃO está no GitHub Releases)
- Substituir `C:\Users\Kheltz\opencode\opencode.exe`
- Verificar com `opencode --version`

### Onde baixar
O GitHub Releases (`github.com/opencode-ai/opencode/releases`) contém apenas:
- Código fonte (source code zip)
- Assets da release atual (1.17.10)

Para versões antigas, é necessário:
1. Navegar até a página de releases
2. Clicar no seletor de **Tags** e escolher `v1.17.9`
3. Baixar `opencode-windows-x64.zip` (53 MB) ou `opencode-desktop-win-x64.exe` (116 MB)

### Prevenção
- NÃO atualizar o OpenCode sem testar antes em ambiente isolado
- Se o Bun crashar ao criar subprocessos, verificar a versão do OpenCode
- Manter uma cópia do binário 1.17.9 em local seguro para rollback
- Como fallback: OpenClaw (Node.js, sem Bun) + Hermes 3 funciona em paralelo

## 2026-06-24 — REGRA ABSOLUTA: Cleanup obrigatório no início e fim de toda sessão

### Problema
Repetidamente, processos do servidor (`canary-sln.exe`) e bridge (`python.exe`) ficam
rodando em segundo plano entre sessões. O servidor estava rodando há **1 hora** sem
que o assistente ou o usuário soubessem. O OTClient conseguiu logar porque o servidor
ainda estava vivo — prova de que **esquecemos de limpar**.

### Consequências
- Servidor ocupando RAM e CPU sem necessidade
- Bridge consumindo recursos do modelo Ollama
- Portas 7171-7173 ocupadas (impede restart limpo)
- Usuário pensa que está tudo desligado, mas não está
- Acúmulo de processos ao longo de múltiplas sessões = crash

### Checklist Obrigatório (NUNCA ESQUECER)

**No INÍCIO de toda resposta:**
```python
import subprocess, os
# 1. Matar servidor
subprocess.run(["taskkill", "/f", "/im", "canary-sln.exe"], capture_output=True)
# 2. Matar bridge Python
subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True)
# 3. Limpar PID files
for f in [".bridge_pid", ".watchdog_pid"]:
    if os.path.exists(f): os.remove(f)
```

**Ao FINAL de toda resposta:**
1. Verificar se servidor foi desligado (`server_manager.py status`)
2. Verificar se bridge foi desligado
3. Remover arquivos PID órfãos

### Regra de Ouro
> Se o assistente iniciou um processo, ele DEVE matá-lo antes de encerrar a sessão.
> Se o assistente encontrou um processo rodando, ele DEVE matá-lo ao terminar.
> O servidor e bridge SÓ devem rodar quando explicitamente solicitado pelo usuário
> para TESTE. Fora isso, TUDO desligado.

## 2026-06-24 — OpenCode: Recuperacao de conversas fechadas

O OpenCode CLI salva automaticamente todas as sessoes de conversa. Comandos uteis:

- `opencode session list` — lista todas as sessoes (com ID, titulo, data)
- `opencode -c` — continua a ultima sessao
- `opencode -s <ID>` — continua sessao especifica  
- `opencode export <ID>` — exporta sessao como JSON

As sessoes ficam em `~/.config/opencode/` e `~/.local/share/opencode/`.
Sempre atualizar `Pendencias.md` ao final de cada sessao para preservar contexto.
Ver `docs/lessons/2026-06-24-opencode-session-recovery.md` para detalhes completos.

## 2026-06-25 - Analisar hibrido: router codigo vs texto

### Problema
O MCR-DevIA ATUAL usava deepseek-r1:7b para analise de codigo e texto, resultando em:
- Respostas genericas sem linha numerada
- Latencia alta (thinking tokens)
- Perda de contexto PT-BR em arquivos de texto/XML

### Solucao
Router hibrido no comando `analisar`:
- CODIGO (.py/.lua/.cpp): AST pre-analysis + qwen2.5-coder:7b + saida LINHA X:
- TEXTO (.xml/.json/.csv): analise estrutural + llama3.1:8b + saida tipo/descricao

### Resultado
Corrida pos-melhoria: de 74% para ~90% de acerto.
Respostas agora incluem numero da linha exata.
