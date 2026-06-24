# Licoes Recentes

## 2026-06-23 — Teste Bridge: alucinacoes Qwen 7B

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

## 2026-06-24 — OpenCode: Recuperacao de conversas fechadas

O OpenCode CLI salva automaticamente todas as sessoes de conversa. Comandos uteis:

- `opencode session list` — lista todas as sessoes (com ID, titulo, data)
- `opencode -c` — continua a ultima sessao
- `opencode -s <ID>` — continua sessao especifica  
- `opencode export <ID>` — exporta sessao como JSON

As sessoes ficam em `~/.config/opencode/` e `~/.local/share/opencode/`.
Sempre atualizar `Pendencias.md` ao final de cada sessao para preservar contexto.
Ver `docs/lessons/2026-06-24-opencode-session-recovery.md` para detalhes completos.
