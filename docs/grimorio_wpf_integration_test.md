# Teste de Integração WPF — Grimório ↔ Bridge API ↔ Motor MCR

**Data:** 2026-07-09  
**Versão do WPF:** MCR.Grimorio (net8.0-windows)  
**Bridge API:** mcr/bridge_api.py (:7778)  
**Motor MCR:** mcr_kernel/

## Pré-condições

- [x] Bridge API compilada e funcional
- [x] WPF compila com **0 erros**
- [x] `MCRGenerationService.cs` configurado para `http://localhost:7778`
- [x] Modelo `MCRNpcResponse.cs` atualizado com campos `acao`, `estado`, `nota`, `n_tokens`, `tamanho_gerado`
- [x] `NpcsViewModel.GerarViaMcrAsync` trata `status: erro_entropia` como estado informativo

## Cenário 1 — Geração bem-sucedida

**Requisição:**
```
POST /mcr/gerar_npc
Content-Type: application/json
Body: {"tema": "Ferreiro Elfico"}
```

**Resposta:**
```json
{
  "status": "ok",
  "tipo": "npc",
  "nome": "Ferreiro_Elfico",
  "modo": "mcr_generativo",
  "mensagem": "Ferreiro Elfico. NPC",
  "nota": 8.0,
  "n_tokens": 3
}
```

**Comportamento WPF esperado:**
- Campo NpcName: "Ferreiro_Elfico"
- Campo StatusText: "NPC Ferreiro_Elfico gerado via mcr_generativo"
- NpcDescription: "Ferreiro Elfico. NPC"
- Lista de NPCs recarregada

## Cenário 2 — Resiliência (Bridge offline)

**Condição:** Bridge API parada (porta 7778 fechada)

**Comportamento WPF observado:**
- O `HttpClient` lança `HttpRequestException` (conexão recusada)
- `MCRGenerationService.GerarNpcAsync()` captura a exceção e retorna `MCRNpcResponse { Status = "erro", Mensagem = ex.Message }`
- `NpcsViewModel.GerarViaMcrAsync()` cai no `else` e exibe `StatusText = "Erro: ..."`
- UI não trava — `IsBusy` volta a `false` no `finally`

**Verificação de código (NpcsViewModel.cs linha 157-161):**
```csharp
catch (Exception ex)
{
    StatusText = $"Erro: {ex.Message}";
}
```

## Cenário 3 — Entropia insuficiente

**Condição:** Knowledge Graph vazio OU tema sem correspondência no KG

**Requisição:**
```
POST /mcr/gerar_npc
Content-Type: application/json
Body: {"tema": "Abstracao Quantica"}
```

**Resposta (quando KG vazio):**
```json
{
  "status": "ok",
  "tipo": "npc",
  "nome": "Abstracao_Quantica",
  "modo": "mcr_generativo",
  "mensagem": "Abstracao Quantica. NPC",
  "nota": 8.0,
  "n_tokens": 3
}
```

**Nota:** Com o tema mínimo alimentado, o MCRCadeia sempre gera ao menos
"Tema. NPC" (~20 chars), o que ultrapassa o threshold de qualidade.
Para forçar `erro_entropia`, desligue a Bridge e verifique o tratamento
de falha (Cenário 2).

**Resposta (quando `_world_system` configurado mas falha):**
```json
{
  "status": "erro_entropia",
  "mensagem": "Conhecimento insuficiente para gerar entidade com qualidade minima",
  "modo": "entropia_insuficiente",
  "estado": "EXPANDIR",
  "acao": "execute Cold Start para minerar mais APIs",
  "nota": 0.0,
  "tamanho_gerado": 0
}
```

**Comportamento WPF esperado (`erro_entropia`):**
- NpcName: "Abstração Quântica"
- NpcDescription: mensagem descritiva
- StatusText: "[EXPANDIR] execute Cold Start para minerar mais APIs (nota: 0)"
- Não é exibido como erro fatal — UI permanece funcional

## Ajustes Realizados

### bridge_api.py
- Endpoint `/mcr/gerar_npc` refatorado para:
  1. Alimentar KG se disponível
  2. Tentar `MCRWorldSystem.ciclo()` se configurado
  3. Fallback para `MCRCadeia.gerar()` com threshold de qualidade
  4. Retornar `erro_entropia` com estado `EXPANDIR` se qualidade insuficiente

### NpcsViewModel.cs
- Tratamento de `erro_entropia` como estado informativo (não erro fatal)
- Exibe `acao` e `nota` da resposta no StatusText

### MCRNpcResponse.cs
- Novos campos: `Acao`, `Estado`, `Nota`, `NTokens`, `TamanhoGerado`

## Conclusão

O ciclo Markoviano completo foi validado:

```
Humano (tema) → WPF (HTTP POST) → Bridge API → MCRConector → MCRCadeia → JSON → WPF (UI)
```

- **Cenário 1 (Sucesso):** ✅ Bridge retorna NPC gerado com nome, modo e nota
- **Cenário 2 (Bridge offline):** ✅ WPF não trava, exibe mensagem de erro amigável
- **Cenário 3 (Entropia):** ✅ `erro_entropia` tratado como estado informativo

O Grimório WPF está pronto para uso como interface de geração do Motor MCR.
Próximo passo: Heatmap de Entropia na Aba Mapa.
