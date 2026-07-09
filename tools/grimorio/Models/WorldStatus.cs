using System.Text.Json.Serialization;

namespace MCR.Grimorio.Models;

public class WorldStatus
{
    [JsonPropertyName("world_observer")]
    public WorldObserverStats? Observer { get; set; }

    [JsonPropertyName("world_state")]
    public WorldStateData? State { get; set; }
}

public class WorldObserverStats
{
    [JsonPropertyName("total_eventos")]
    public int TotalEventos { get; set; }

    [JsonPropertyName("eventos_por_tipo")]
    public Dictionary<string, int>? EventosPorTipo { get; set; }

    [JsonPropertyName("fila_atual")]
    public int FilaAtual { get; set; }

    [JsonPropertyName("ultima_reacao")]
    public double UltimaReacao { get; set; }

    [JsonPropertyName("cooldown_restante")]
    public double CooldownRestante { get; set; }
}

public class WorldStateData
{
    [JsonPropertyName("total_npcs")]
    public int TotalNpcs { get; set; }

    [JsonPropertyName("npcs")]
    public List<string>? Npcs { get; set; }

    [JsonPropertyName("tem_foundation")]
    public bool TemFoundation { get; set; }
}
