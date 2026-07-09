using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using MCR.Grimorio.Data;

namespace MCR.Grimorio.Core.Services;

public class NpcService
{
    private readonly string _npcPath;
    private readonly string _npcMcrPath;
    private List<NpcData>? _cache;

    public NpcService()
    {
        var settings = ((App)System.Windows.Application.Current)?.SettingsService;
        if (settings != null)
        {
            _npcPath = settings.GetNpcPath();
            _npcMcrPath = Path.Combine(settings.GetServerPath(), "data-canary", "scripts", "MCR");
            if (Directory.Exists(_npcPath) || Directory.Exists(_npcMcrPath)) return;
        }

        var baseDir = Path.GetFullPath(Path.Combine(
            AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", "..", "Canary"));
        _npcPath = Path.Combine(baseDir, "data-otservbr-global", "npc");
        _npcMcrPath = Path.Combine(baseDir, "data-canary", "scripts", "MCR");
    }

    public List<NpcData> GetAll()
    {
        if (_cache != null) return _cache;
        _cache = new List<NpcData>();

        if (Directory.Exists(_npcPath))
        {
            foreach (var file in Directory.GetFiles(_npcPath, "*.lua"))
            {
                try
                {
                    var npc = ParseNpcFile(file);
                    if (npc != null) _cache.Add(npc);
                }
                catch { }
            }
        }

        if (Directory.Exists(_npcMcrPath))
        {
            foreach (var file in Directory.GetFiles(_npcMcrPath, "*.lua"))
            {
                try
                {
                    var npc = ParseNpcFile(file);
                    if (npc != null) _cache.Add(npc);
                }
                catch { }
            }
        }

        return _cache;
    }

    public NpcData? GetByName(string name)
    {
        return GetAll().FirstOrDefault(n =>
            n.Name.Equals(name, StringComparison.OrdinalIgnoreCase));
    }

    public List<NpcData> Search(string query)
    {
        var q = query.ToLower();
        return GetAll().Where(n =>
            n.Name.ToLower().Contains(q)).ToList();
    }

    private NpcData? ParseNpcFile(string filePath)
    {
        var content = File.ReadAllText(filePath, Encoding.UTF8);

        // Try UTF-8 if Latin-1 has replacement chars
        if (content.Contains("�"))
            content = File.ReadAllText(filePath, Encoding.UTF8);

        var npc = new NpcData { FilePath = filePath };

        var nameMatch = Regex.Match(content,
            @"""?internalNpcName""?\s*=\s*""([^""]+)""",
            RegexOptions.Singleline);
        if (!nameMatch.Success)
        {
            nameMatch = Regex.Match(content,
                @"Game\.createNpcType\(""([^""]+)""\)");
        }
        if (!nameMatch.Success) return null;
        npc.Name = nameMatch.Groups[1].Value;

        var descMatch = Regex.Match(content,
            @"description\s*=\s*""([^""]*)""");
        if (descMatch.Success) npc.Description = descMatch.Groups[1].Value;

        var lookMatch = Regex.Match(content,
            @"lookType\s*=\s*(\d+)");
        if (lookMatch.Success) npc.LookType = int.Parse(lookMatch.Groups[1].Value);

        npc.HasShop = content.Contains("npcConfig.shop") || content.Contains("npcConfig.shop =");

        var shopItems = Regex.Matches(content,
            @"\{\s*itemName\s*=\s*""([^""]+)""\s*,\s*clientId\s*=\s*(\d+)[^}]*\}");
        foreach (Match item in shopItems)
        {
            npc.ShopItems.Add(new NpcShopItem
            {
                Name = item.Groups[1].Value,
                ClientId = int.Parse(item.Groups[2].Value)
            });
        }

        if (content.Contains("buy") || content.Contains("sell")) npc.HasShop = true;

        if (content.Contains("Storage") || content.Contains("storage") ||
            content.Contains("quest") || content.Contains("mission"))
            npc.Type = "quest";
        else if (npc.HasShop) npc.Type = "shop";
        else if (content.Contains("balance") || content.Contains("bank"))
            npc.Type = "bank";
        else
            npc.Type = "dialogue";

        return npc;
    }

    public string GenerateNpcLua(NpcData npc, List<NpcScheduleEntry>? schedule = null)
    {
        var sb = new System.Text.StringBuilder();
        sb.AppendLine($"local internalNpcName = \"{npc.Name}\"");
        sb.AppendLine($"local npcType = Game.createNpcType(internalNpcName)");
        sb.AppendLine("local npcConfig = {}");
        sb.AppendLine();
        sb.AppendLine($"npcConfig.name = internalNpcName");
        sb.AppendLine($"npcConfig.description = \"{npc.Description}\"");
        sb.AppendLine($"npcConfig.health = 100");
        sb.AppendLine($"npcConfig.maxHealth = npcConfig.health");
        sb.AppendLine($"npcConfig.walkInterval = 2000");
        sb.AppendLine($"npcConfig.walkRadius = 2");
        sb.AppendLine();
        sb.AppendLine("npcConfig.outfit = {");
        sb.AppendLine($"    lookType = {npc.LookType},");
        sb.AppendLine("    lookHead = 0, lookBody = 0, lookLegs = 0, lookFeet = 0, lookAddons = 0");
        sb.AppendLine("}");
        sb.AppendLine();
        sb.AppendLine("npcConfig.flags = { floorchange = false }");
        sb.AppendLine();

        if (npc.HasShop && npc.ShopItems.Count > 0)
        {
            sb.AppendLine("npcConfig.shop = {");
            foreach (var item in npc.ShopItems.Take(10))
            {
                sb.AppendLine($"    {{ itemName = \"{item.Name}\", clientId = {item.ClientId}, buy = {(item.BuyPrice > 0 ? item.BuyPrice : 50)} }},");
            }
            sb.AppendLine("}");
            sb.AppendLine();
        }

        if (schedule != null && schedule.Count > 0)
        {
            sb.AppendLine("-- Schedule Engine");
            sb.AppendLine("npcConfig.schedule = {");
            foreach (var entry in schedule)
            {
                sb.AppendLine($"    {{ time = \"{entry.Time}\", activity = \"{entry.Activity}\", target = \"{entry.TargetArea}\", duration = {entry.DurationMinutes} }},");
            }
            sb.AppendLine("}");
            sb.AppendLine();
        }

        sb.AppendLine("local keywordHandler = KeywordHandler:new()");
        sb.AppendLine("local npcHandler = NpcHandler:new(keywordHandler)");
        sb.AppendLine();
        sb.AppendLine("npcType.onThink = function(npc, interval)");
        sb.AppendLine("    npcHandler:onThink(npc, interval)");
        sb.AppendLine("end");
        sb.AppendLine("npcType.onAppear = function(npc, creature) npcHandler:onAppear(npc, creature) end");
        sb.AppendLine("npcType.onDisappear = function(npc, creature) npcHandler:onDisappear(npc, creature) end");
        sb.AppendLine("npcType.onMove = function(npc, creature, fromPosition, toPosition) npcHandler:onMove(npc, creature, fromPosition, toPosition) end");
        sb.AppendLine("npcType.onSay = function(npc, creature, type, message) npcHandler:onSay(npc, creature, type, message) end");
        sb.AppendLine("npcType.onCloseChannel = function(npc, creature) npcHandler:onCloseChannel(npc, creature) end");
        sb.AppendLine();
        sb.AppendLine("npcHandler:addModule(FocusModule:new(), npcConfig.name, true, true, true)");
        sb.AppendLine("npcType:register(npcConfig)");

        return sb.ToString();
    }
}
