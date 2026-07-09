namespace MCR.Grimorio.Data;

public class NpcData
{
    public string Name { get; set; } = "";
    public string FilePath { get; set; } = "";
    public string Description { get; set; } = "";
    public int LookType { get; set; } = 130;
    public bool HasShop { get; set; }
    public List<NpcShopItem> ShopItems { get; set; } = new();
    public string Type { get; set; } = "dialogue";

    public override string ToString() => Name;
}

public class NpcShopItem
{
    public string Name { get; set; } = "";
    public int ClientId { get; set; }
    public int BuyPrice { get; set; }
    public int SellPrice { get; set; }
}

public class NpcScheduleEntry
{
    public string Time { get; set; } = "00:00";
    public string Activity { get; set; } = "idle";
    public string TargetArea { get; set; } = "";
    public string DialogueText { get; set; } = "";
    public int DurationMinutes { get; set; } = 60;
}

public enum NpcActivityType
{
    Dormindo,
    Andando,
    Trabalhando,
    Pausa
}
