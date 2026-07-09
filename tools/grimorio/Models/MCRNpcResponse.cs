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

    [JsonPropertyName("acao")]
    public string? Acao { get; set; }

    [JsonPropertyName("estado")]
    public string? Estado { get; set; }

    [JsonPropertyName("nota")]
    public double Nota { get; set; }

    [JsonPropertyName("n_tokens")]
    public int NTokens { get; set; }

    [JsonPropertyName("tamanho_gerado")]
    public int TamanhoGerado { get; set; }

    public bool IsSuccess => Status == "ok";
}
