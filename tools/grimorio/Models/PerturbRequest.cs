using System.Text.Json.Serialization;

namespace MCR.Grimorio.Models;

public class PerturbRequest
{
    [JsonPropertyName("evento")]
    public PerturbEvent? Evento { get; set; }

    [JsonPropertyName("delta_h")]
    public double DeltaH { get; set; } = -0.3;
}

public class PerturbEvent
{
    [JsonPropertyName("type")]
    public string? Type { get; set; }

    [JsonPropertyName("target")]
    public string? Target { get; set; }

    [JsonPropertyName("killer")]
    public string? Killer { get; set; }
}
