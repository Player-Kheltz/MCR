using System.Text.Json.Serialization;

namespace MCR.Grimorio.Models;

public class MCRNpcRequest
{
    [JsonPropertyName("tema")]
    public string? Tema { get; set; }
}

public class MCRNpcResponse
{
    [JsonPropertyName("status")]
    public string? Status { get; set; }

    [JsonPropertyName("tipo")]
    public string? Tipo { get; set; }

    [JsonPropertyName("nome")]
    public string? Nome { get; set; }

    [JsonPropertyName("arquivo")]
    public string? Arquivo { get; set; }

    [JsonPropertyName("modo")]
    public string? Modo { get; set; }

    [JsonPropertyName("mensagem")]
    public string? Mensagem { get; set; }

    public bool IsSuccess => Status == "ok";
}
