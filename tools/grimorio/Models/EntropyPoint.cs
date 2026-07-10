using System.Text.Json.Serialization;

namespace MCR.Grimorio.Models;

public class EntropyPoint
{
    [JsonPropertyName("x")]
    public int X { get; set; }

    [JsonPropertyName("y")]
    public int Y { get; set; }

    [JsonPropertyName("z")]
    public int Z { get; set; }

    [JsonPropertyName("entropy")]
    public double Entropy { get; set; }

    [JsonPropertyName("event_count")]
    public int EventCount { get; set; }
}

public class EntropyGridResponse
{
    [JsonPropertyName("status")]
    public string? Status { get; set; }

    [JsonPropertyName("grid")]
    public List<EntropyPoint>? Grid { get; set; }

    [JsonPropertyName("max_entropy")]
    public double MaxEntropy { get; set; }

    [JsonPropertyName("min_entropy")]
    public double MinEntropy { get; set; }

    [JsonPropertyName("total_events")]
    public int TotalEvents { get; set; }
}
