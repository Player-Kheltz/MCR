using System.Xml.Linq;

namespace MCR.Grimorio.Data;

public class ItemData
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public string Article { get; set; } = "";
    public string Plural { get; set; } = "";
    public string Type { get; set; } = "";
    public string Description { get; set; } = "";
    public int Weight { get; set; }
    public int ContainerSize { get; set; }
    public int Armor { get; set; }
    public int Attack { get; set; }
    public int Defense { get; set; }
    public int SpriteId { get; set; }

    public string DisplayName => $"{Article} {Name}".Trim();

    public static ItemData FromXml(XElement element)
    {
        var item = new ItemData();
        item.Id = (int)element.Attribute("id")!;
        item.SpriteId = item.Id;
        item.Name = (string)element.Attribute("name") ?? "";
        item.Article = (string)element.Attribute("article") ?? "";
        item.Plural = (string)element.Attribute("plural") ?? "";

        foreach (var attr in element.Elements("attribute"))
        {
            var key = (string)attr.Attribute("key") ?? "";
            var val = (string)attr.Attribute("value") ?? "";
            switch (key)
            {
                case "type": item.Type = val; break;
                case "description": item.Description = val; break;
                case "weight": int.TryParse(val, out var w); item.Weight = w; break;
                case "containersize": int.TryParse(val, out var cs); item.ContainerSize = cs; break;
                case "armor": int.TryParse(val, out var a); item.Armor = a; break;
                case "attack": int.TryParse(val, out var at); item.Attack = at; break;
                case "defense": int.TryParse(val, out var d); item.Defense = d; break;
            }
        }

        return item;
    }
}
