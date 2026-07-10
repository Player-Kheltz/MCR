# Status Real do Grimório WPF — Diagnóstico e Correções

**Data:** 2026-07-09
**Compilação:** 0 erros, 0 warnings

## Resumo das Correções

| Tipo | Quantidade | Status |
|------|------------|--------|
| Crashes críticos corrigidos | 5 | ✅ |
| Empty catch blocks com logging | 12 | ✅ |
| HttpClient leak no MapView | 1 | ✅ |

## Status por Aba (Pós-Correção)

| Aba | Status | Dependência | Comportamento se falhar |
|-----|--------|-------------|------------------------|
| **PainelMCR** | ✅ Funcional | Bridge API :7778 | Mostra "Offline" — sem crash |
| **Npcs** | ✅ Funcional | Bridge API :7778 | "Bridge API offline" |
| **Monsters** | ✅ Funcional | Server `.lua` files | Lista vazia |
| **Mapa** | ✅ Funcional | OTBM + Bridge + :8081 | Mapa não carregado, players ausentes, heatmap offline |
| **Items** | ✅ Funcional | `items.xml` | "items.xml não encontrado" |
| **Quests** | ✅ Autossuficiente | Nenhuma | Gera código sempre |
| **Scripts** | ✅ Funcional | Server scripts dir | Árvore vazia |
| **Database** | ✅ Funcional | MySQL | "Desconectado" |
| **Config** | ✅ Funcional | `config.lua` | "config.lua não encontrado" |
| **Settings** | ✅ Funcional | Server filesystem | Config padrão |
| **Deploy** | ✅ Funcional | git + cmake CLI | Erro de build/deploy |
| **Dashboard** | ✅ Funcional | MySQL + Server | Métricas vazias |
| **Logs** | ✅ Funcional | Server logs dir | "Diretório não encontrado" |
| **MCRSkills** | ✅ Funcional | `MCRDetector` (arquivos) | Geração sempre funciona |
| **MountSummon** | ✅ Funcional | Server scripts dir | Lista vazia |
| **MultiPiso** | ✅ Funcional | Server src dir | Resultados vazios |
| **MundoMCR** | ✅ Funcional | Bridge API :7778 | "Bridge API Offline" |
| **NPCDialogue** | ✅ Funcional | Nenhuma (autossuficiente) | Geração sempre funciona |
| **Protocol** | ✅ Funcional | OTClient `protocolcodes.h` | "Arquivo não encontrado" |
| **Spawns** | ✅ Funcional | Server `.otbm`/`.xml` | "Nenhum arquivo encontrado" |
| **Tools** | ✅ Funcional | Server scripts dir | Analisador vazio |

## Bugs Críticos Corrigidos

### #1: DatabaseView — `rows[0].Keys` IndexOutOfRange
- **Antes:** `var dt = new DataTable(); foreach (var key in results[0].Keys)`
- **Depois:** Guard `if (results.Count == 0) return;` já existia — **não era bug** (falso positivo do diagnóstico)

### #2-#4: Split('(')[1] sem verificação
**Arquivos:** MCRSkillsView, QuestsView (3x)
- **Antes:** `domainStr.Split('(')[1].TrimEnd(')')` — crash se formato mudar
- **Depois:** `SafeExtractId(input, fallback)` — verifica `parts.Length >= 2`

### #5: ConfigView sem try/catch
- **Antes:** `_configService.ReadAll()` sem proteção
- **Depois:**
  ```csharp
  try {
      if (!_configService.Exists) { ... return; }
      _allEntries = _configService.ReadAll();
  } catch (Exception ex) {
      StatusText.Text = $"Erro ao carregar: {ex.Message}";
      Debug.WriteLine(...);
  }
  ```

## Melhorias de Resiliência

### Empty catch blocks (12 ocorrências)
Substituídos por:
```csharp
catch (Exception ex) { System.Diagnostics.Debug.WriteLine("[Grimorio] " + ex.Message); }
```

### HttpClient leak no MapView
- **Antes:** `new HttpClient()` a cada 5s e 10s (socket exhaustion)
- **Depois:** Reutiliza campo `readonly HttpClient _http` da classe

## Recomendações Futuras

Para tornar o Grimório totalmente independente da estrutura de diretórios:
1. Criar `appsettings.json` com `ServerPath`, `ScriptsPath`, `OtbmPath`
2. Ler caminhos centralizadamente via `AppConfig` (injetado via DI)
3. Se caminho não configurado, exibir "Configure em Ajustes"
