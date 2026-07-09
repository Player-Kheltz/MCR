using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using MCR.Grimorio.Models;

namespace MCR.Grimorio.Services;

public class MCRWorldService
{
    private readonly HttpClient _http;
    private const string BaseUrl = "http://127.0.0.1:7778";

    public MCRWorldService()
    {
        _http = new HttpClient
        {
            BaseAddress = new Uri(BaseUrl),
            Timeout = TimeSpan.FromSeconds(5)
        };
    }

    public async Task<WorldStatus?> GetStatusAsync()
    {
        try
        {
            return await _http.GetFromJsonAsync<WorldStatus>("/world/status");
        }
        catch
        {
            return null;
        }
    }

    public async Task<WorldEventsResponse?> GetEventsAsync()
    {
        try
        {
            return await _http.GetFromJsonAsync<WorldEventsResponse>("/world/events");
        }
        catch
        {
            return null;
        }
    }

    public async Task<bool> SendPerturbationAsync(PerturbRequest request)
    {
        try
        {
            var json = JsonSerializer.Serialize(request, new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower
            });
            var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");
            var response = await _http.PostAsync("/world/perturb", content);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    public void Dispose()
    {
        _http.Dispose();
    }
}
