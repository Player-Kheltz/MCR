using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using MCR.Grimorio.Models;

namespace MCR.Grimorio.Services;

public class MCRGenerationService : IDisposable
{
    private readonly HttpClient _http;
    private const string BaseUrl = "http://127.0.0.1:7778";

    public MCRGenerationService()
    {
        _http = new HttpClient
        {
            BaseAddress = new Uri(BaseUrl),
            Timeout = TimeSpan.FromSeconds(120)
        };
    }

    public async Task<MCRNpcResponse?> GerarNpcAsync(string tema)
    {
        try
        {
            var request = new MCRNpcRequest { Tema = tema };
            var response = await _http.PostAsJsonAsync("/mcr/gerar_npc", request,
                new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower });
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<MCRNpcResponse>();
        }
        catch (Exception ex)
        {
            return new MCRNpcResponse
            {
                Status = "erro",
                Mensagem = ex.Message
            };
        }
    }

    public void Dispose()
    {
        _http.Dispose();
    }
}
