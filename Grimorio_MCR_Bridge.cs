// Grimorio_MCR_Bridge.cs
// Classe C# para conectar o MCR Grimorio ao MCR-DevIA Python via HTTP REST.
// .NET 8, WPF, System.Net.Http.Json
// Modos: Rapido (template, 0ms) e Criativo (LLM, ~5-10s)

using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using System.Collections.Generic;

public class MCRBridge
{
    private readonly HttpClient _http;
    private readonly string _baseUrl;

    public MCRBridge(string baseUrl = "http://127.0.0.1:7778")
    {
        _baseUrl = baseUrl;
        _http = new HttpClient();
        _http.Timeout = System.TimeSpan.FromSeconds(120);
    }

    // ─── Models ─────────────────────────────────────────────

    public class ToolRequest
    {
        [JsonPropertyName("prompt")]
        public string? Prompt { get; set; }

        [JsonPropertyName("params")]
        public NpcParams? Params { get; set; }
    }

    public class NpcParams
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = "NPC";

        [JsonPropertyName("health")]
        public int Health { get; set; } = 100;

        [JsonPropertyName("looktype")]
        public int Looktype { get; set; } = 128;

        [JsonPropertyName("shop_items")]
        public List<ShopItem>? ShopItems { get; set; }
    }

    public class ShopItem
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = "item";

        [JsonPropertyName("clientId")]
        public int ClientId { get; set; } = 100;

        [JsonPropertyName("buy")]
        public int Buy { get; set; }

        [JsonPropertyName("sell")]
        public int Sell { get; set; }
    }

    public class ToolResponse
    {
        [JsonPropertyName("status")]
        public string Status { get; set; } = "";

        [JsonPropertyName("tipo")]
        public string Tipo { get; set; } = "";

        [JsonPropertyName("modo")]
        public string? Modo { get; set; }

        [JsonPropertyName("mensagem")]
        public string Mensagem { get; set; } = "";
    }

    public class StatusResponse
    {
        [JsonPropertyName("status")]
        public string Status { get; set; } = "";

        [JsonPropertyName("porta")]
        public int Porta { get; set; }

        [JsonPropertyName("models")]
        public string[] Models { get; set; } = [];
    }

    // ─── Metodos Publicos ───────────────────────────────────

    /// <summary>Gera NPC via template (Sistema 1, 0ms, zero LLM).</summary>
    public async Task<string> GerarNpcRapidoAsync(string nome, int health = 100, int looktype = 128)
    {
        var request = new ToolRequest
        {
            Params = new NpcParams
            {
                Name = nome,
                Health = health,
                Looktype = looktype,
            }
        };
        return await PostAsync("/tool/npc/custom", request);
    }

    /// <summary>Gera NPC via LLM (Sistema 2, ~5-10s, Qwen Coder).</summary>
    public async Task<string> GerarNpcAsync(string prompt)
    {
        var request = new ToolRequest { Prompt = prompt };
        return await PostAsync("/tool/npc/custom", request);
    }

    /// <summary>Gera Monstro via LLM.</summary>
    public async Task<string> GerarMonstroAsync(string prompt)
    {
        var request = new ToolRequest { Prompt = prompt };
        return await PostAsync("/tool/monster", request);
    }

    /// <summary>Verifica se o servidor esta online.</summary>
    public async Task<bool> PingAsync()
    {
        try
        {
            var response = await _http.GetAsync($"{_baseUrl}/status");
            return response.IsSuccessStatusCode;
        }
        catch { return false; }
    }

    // ─── Privado ─────────────────────────────────────────────

    private async Task<string> PostAsync(string endpoint, ToolRequest request)
    {
        var response = await _http.PostAsJsonAsync($"{_baseUrl}{endpoint}", request);
        response.EnsureSuccessStatusCode();
        var result = await response.Content.ReadFromJsonAsync<ToolResponse>();
        return result?.Mensagem ?? "[Erro] Resposta vazia do MCR-DevIA";
    }
}

// Exemplo de uso no WPF ViewModel:
//
// var mcr = new MCRBridge();
//
// // Botao "Criar NPC Rapido" (template, 0ms)
// string resultado = await mcr.GerarNpcRapidoAsync("Arqueiro Real", 150, 129);
//
// // Botao "Criar NPC Personalizado" (LLM, ~8s)
// string resultado = await mcr.GerarNpcAsync("Crie um mago sombrio com poderes de fogo");
