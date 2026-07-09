using System.Text.Json.Serialization;

namespace MCR.Grimorio.Models;

public class WorldEvent
{
    [JsonPropertyName("ts")]
    public string? Timestamp { get; set; }

    [JsonPropertyName("type")]
    public string? Type { get; set; }

    [JsonPropertyName("target")]
    public string? Target { get; set; }

    [JsonPropertyName("killer")]
    public string? Killer { get; set; }

    [JsonPropertyName("pos")]
    public WorldPosition? Position { get; set; }

    public string Display => $"{Timestamp?[11..16] ?? "--:--"}  {Type?.PadRight(8)}  {Target}";
    public string Details => $"Tipo: {Type}\nAlvo: {Target}\nAssassino: {Killer}\nLocal: ({Position?.x}, {Position?.y}, {Position?.z})";
}

public class WorldPosition
{
    public int x { get; set; }
    public int y { get; set; }
    public int z { get; set; }
}

public class WorldEventsResponse
{
    [JsonPropertyName("eventos")]
    public List<WorldEvent>? Eventos { get; set; }

    [JsonPropertyName("total")]
    public int Total { get; set; }
}
