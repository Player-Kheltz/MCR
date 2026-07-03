# Compilacao.md — Compilação MCR

> Parte do sistema modular `docs/rules/`. Consulte `../AGENTS.md` para visão geral.

## Stack

Ambos os projetos compilam com **Visual Studio**.

### Canary Server (VS 2022)

```cmd
cmd.exe /c """C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"" && ""C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\amd64\MSBuild.exe"" ""%MCR%\Canary\vcproj\canary.vcxproj"" /p:Configuration=Release /p:Platform=x64 /t:Build /m"
```

### OTClient (VS 2026)

> **Motivo:** O vcpkg (v2026-04-08) detecta automaticamente o VS mais recente (2026) e compila as dependências com MSVC 14.51. Para alinhar ABI, o OTClient deve ser compilado com VS 2026 (toolset v145).

```cmd
cmd.exe /c """C:\Program Files\Microsoft Visual Studio\2026\Community\VC\Auxiliary\Build\vcvars64.bat"" && ""C:\Program Files\Microsoft Visual Studio\2026\Community\MSBuild\Current\Bin\amd64\MSBuild.exe"" ""%MCR%\OTClient\vc17\otclient.vcxproj"" /p:Configuration=OpenGL /p:Platform=x64 /t:Build /m"
```

### Alternativa: Compilar pelo Visual Studio

Abra o `.vcxproj` diretamente no **VS 2026** e clique em Build → Build Solution. A primeira compilação do OTClient pode demorar (vcpkg compila dependências estáticas). Depois da primeira vez, as compilações são rápidas (1-2 min).

> **Nota:** Se tiver VS 2022 e VS 2026 instalados, o OTClient DEVE ser compilado com VS 2026. O Canary (servidor) continua compilando com VS 2022.
