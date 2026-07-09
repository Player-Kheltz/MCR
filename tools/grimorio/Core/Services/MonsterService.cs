using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using MCR.Grimorio.Data;

namespace MCR.Grimorio.Core.Services;

public class MonsterService
{
    private readonly string _monsterPath;
    private List<MonsterData>? _cache;
    private Dictionary<string, DateTime> _fileTimestamps = new();
    private DateTime _lastCacheBuild;

    public MonsterService() : this(null) { }

    public MonsterService(string? customPath)
    {
        if (!string.IsNullOrEmpty(customPath) && Directory.Exists(customPath))
        {
            _monsterPath = customPath;
            return;
        }

        var settings = ((App)System.Windows.Application.Current)?.SettingsService;
        if (settings != null)
        {
            _monsterPath = settings.GetMonsterPath();
            if (Directory.Exists(_monsterPath)) return;
        }

        var baseDir = Path.GetFullPath(Path.Combine(
            AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", "..", "Canary"));
        _monsterPath = Path.Combine(baseDir, "data-otservbr-global", "monster");
        if (!Directory.Exists(_monsterPath))
            _monsterPath = Path.Combine(baseDir, "data-canary", "monster");
    }

    public string MonsterPath => _monsterPath;

    public void InvalidateCache()
    {
        _cache = null;
        _fileTimestamps.Clear();
    }

    private bool CacheIsValid()
    {
        if (_cache == null) return false;
        foreach (var kvp in _fileTimestamps)
        {
            var file = new FileInfo(kvp.Key);
            if (!file.Exists || file.LastWriteTime != kvp.Value)
                return false;
        }
        return true;
    }

    public List<MonsterData> GetAll()
    {
        if (CacheIsValid()) return _cache!;

        _cache = new List<MonsterData>();
        _fileTimestamps.Clear();

        if (!Directory.Exists(_monsterPath)) return _cache;

        foreach (var categoryDir in Directory.GetDirectories(_monsterPath))
        {
            var category = Path.GetFileName(categoryDir);
            foreach (var file in Directory.GetFiles(categoryDir, "*.lua"))
            {
                try
                {
                    var monster = ParseMonsterFile(file, category);
                    if (monster != null)
                    {
                        _cache.Add(monster);
                        _fileTimestamps[file] = new FileInfo(file).LastWriteTime;
                    }
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"ParseMonsterFile Error ({file}): {ex.Message}");
                }
            }
        }

        _lastCacheBuild = DateTime.UtcNow;
        return _cache;
    }

    public List<string> GetCategories()
    {
        if (!Directory.Exists(_monsterPath)) return new();
        return Directory.GetDirectories(_monsterPath)
            .Select(Path.GetFileName)
            .OrderBy(x => x)
            .ToList()!;
    }

    public List<MonsterData> GetByCategory(string category)
    {
        return GetAll().Where(m =>
            m.Category.Equals(category, StringComparison.OrdinalIgnoreCase)).ToList();
    }

    public MonsterData? GetByName(string name)
    {
        return GetAll().FirstOrDefault(m =>
            m.Name.Equals(name, StringComparison.OrdinalIgnoreCase));
    }

    public List<MonsterData> Search(string query)
    {
        var q = query.ToLower();
        return GetAll().Where(m =>
            m.Name.ToLower().Contains(q) ||
            m.Category.ToLower().Contains(q)).ToList();
    }

    public BalanceResult AnalyzeBalance()
    {
        var monsters = GetAll().Where(m => m.Hostile && m.Health > 0).ToList();
        if (monsters.Count == 0) return new BalanceResult();

        var result = new BalanceResult();
        result.TotalMonsters = monsters.Count;

        var xpValues = monsters.Select(m => (double)m.Experience).ToList();
        var hpValues = monsters.Select(m => (double)m.Health).ToList();
        var xpPerHp = monsters.Select(m => m.GetXpPerHp()).ToList();
        var maxDmg = monsters.Select(m => (double)m.GetMaxDamage()).ToList();

        result.AvgExperience = xpValues.Average();
        result.StdDevExperience = StdDev(xpValues);
        result.AvgHealth = hpValues.Average();
        result.StdDevHealth = StdDev(hpValues);
        result.AvgXpPerHp = xpPerHp.Average();
        result.StdDevXpPerHp = StdDev(xpPerHp);

        result.Outliers = new List<MonsterOutlier>();

        foreach (var m in monsters)
        {
            var xpZ = (m.Experience - result.AvgExperience) / (result.StdDevExperience > 0 ? result.StdDevExperience : 1);
            var hpZ = (m.Health - result.AvgHealth) / (result.StdDevHealth > 0 ? result.StdDevHealth : 1);
            var xphZ = (m.GetXpPerHp() - result.AvgXpPerHp) / (result.StdDevXpPerHp > 0 ? result.StdDevXpPerHp : 1);

            if (Math.Abs(xpZ) > 2 || Math.Abs(hpZ) > 2 || Math.Abs(xphZ) > 2)
            {
                result.Outliers.Add(new MonsterOutlier
                {
                    Name = m.Name,
                    Category = m.Category,
                    Experience = m.Experience,
                    Health = m.Health,
                    XpPerHp = m.GetXpPerHp(),
                    ZScoreExperience = xpZ,
                    ZScoreHealth = hpZ,
                    ZScoreXpPerHp = xphZ,
                    Reason = GetOutlierReason(xpZ, hpZ, xphZ)
                });
            }
        }

        return result;
    }

    private static string GetOutlierReason(double xpZ, double hpZ, double xphZ)
    {
        var reasons = new List<string>();
        if (xpZ > 2) reasons.Add($"EXP {xpZ:F1}σ acima da média");
        if (xpZ < -2) reasons.Add($"EXP {Math.Abs(xpZ):F1}σ abaixo da média");
        if (hpZ > 2) reasons.Add($"HP {hpZ:F1}σ acima da média");
        if (hpZ < -2) reasons.Add($"HP {Math.Abs(hpZ):F1}σ abaixo da média");
        if (xphZ > 2) reasons.Add($"XP/HP {xphZ:F1}σ acima");
        if (xphZ < -2) reasons.Add($"XP/HP {Math.Abs(xphZ):F1}σ abaixo");
        return string.Join(", ", reasons);
    }

    private static double StdDev(List<double> values)
    {
        var avg = values.Average();
        var sumSq = values.Sum(v => Math.Pow(v - avg, 2));
        return Math.Sqrt(sumSq / values.Count);
    }

    private static MonsterData? ParseMonsterFile(string filePath, string category)
    {
        var content = File.ReadAllText(filePath, Encoding.UTF8);
        var monster = new MonsterData
        {
            FilePath = filePath,
            Category = category
        };

        var nameMatch = Regex.Match(content,
            @"Game\.createMonsterType\(""([^""]+)""\)");
        if (!nameMatch.Success) return null;
        monster.Name = nameMatch.Groups[1].Value;

        monster.Description = ExtractStringField(content, "description");
        monster.Experience = ExtractIntField(content, "experience");
        monster.Health = ExtractIntField(content, "health");
        monster.MaxHealth = ExtractIntField(content, "maxHealth");
        monster.Speed = ExtractIntField(content, "speed");
        monster.ManaCost = ExtractIntField(content, "manaCost");
        monster.LookType = ExtractIntField(content, "lookType");
        monster.RaceId = ExtractIntField(content, "raceId");
        monster.Corpse = ExtractIntField(content, "corpse");
        monster.TargetDistance = ExtractIntField(content, "targetDistance");

        monster.Armor = ExtractNestedIntField(content, "defenses", "armor");
        monster.Defense = ExtractNestedIntField(content, "defenses", "defense");

        monster.Race = ExtractRace(content);
        monster.Summonable = ExtractFlag(content, "summonable");
        monster.Attackable = ExtractFlag(content, "attackable");
        monster.Hostile = ExtractFlag(content, "hostile");
        monster.Convinceable = ExtractFlag(content, "convinceable");
        monster.Pushable = ExtractFlag(content, "pushable");

        monster.Loot = ParseLoot(content);
        monster.Attacks = ParseAttacks(content);
        monster.Defenses = ParseDefense(content);
        monster.Elements = ParseElements(content);

        if (monster.MaxHealth == 0) monster.MaxHealth = monster.Health;

        return monster;
    }

    private static int ExtractIntField(string content, string field)
    {
        var match = Regex.Match(content, $@"{field}\s*=\s*(\d+)");
        return match.Success && int.TryParse(match.Groups[1].Value, out var val) ? val : 0;
    }

    private static string ExtractStringField(string content, string field)
    {
        var match = Regex.Match(content, $@"{field}\s*=\s*""([^""]*)""");
        return match.Success ? match.Groups[1].Value : "";
    }

    private static int ExtractNestedIntField(string content, string section, string field)
    {
        var sectionMatch = Regex.Match(content, $@"monster\.{section}\s*=\s*\{{([^}}]+)\}}", RegexOptions.Singleline);
        if (!sectionMatch.Success) return 0;
        var match = Regex.Match(sectionMatch.Groups[1].Value, $@"{field}\s*=\s*(\d+)");
        return match.Success && int.TryParse(match.Groups[1].Value, out var val) ? val : 0;
    }

    private static string ExtractRace(string content)
    {
        var match = Regex.Match(content, @"race\s*=\s*""([^""]+)""");
        return match.Success ? match.Groups[1].Value : "blood";
    }

    private static bool ExtractFlag(string content, string flag)
    {
        var match = Regex.Match(content, $@"{flag}\s*=\s*(true|false)");
        return match.Success && match.Groups[1].Value == "true";
    }

    private static List<MonsterLoot> ParseLoot(string content)
    {
        var loot = new List<MonsterLoot>();
        var lootMatch = Regex.Match(content,
            @"monster\.loot\s*=\s*\{([^}]+)\}", RegexOptions.Singleline);
        if (!lootMatch.Success) return loot;

        var entries = Regex.Matches(lootMatch.Groups[1].Value,
            @"\{\s*id\s*=\s*(\d+)\s*,\s*chance\s*=\s*(\d+)(?:\s*,\s*maxCount\s*=\s*(\d+))?\s*\}");
        foreach (Match entry in entries)
        {
            loot.Add(new MonsterLoot
            {
                Id = int.Parse(entry.Groups[1].Value),
                Chance = int.Parse(entry.Groups[2].Value),
                MaxCount = entry.Groups[3].Success ? int.Parse(entry.Groups[3].Value) : 1
            });
        }
        return loot;
    }

    private static List<MonsterAttack> ParseAttacks(string content)
    {
        var attacks = new List<MonsterAttack>();
        var attacksMatch = Regex.Match(content,
            @"monster\.attacks\s*=\s*\{(.*?)\}", RegexOptions.Singleline);
        if (!attacksMatch.Success) return attacks;

        var entries = Regex.Matches(attacksMatch.Groups[1].Value,
            @"\{\s*name\s*=\s*""([^""]+)""\s*,\s*interval\s*=\s*(\d+)\s*,\s*chance\s*=\s*(\d+)[^}]*minDamage\s*=\s*(-?\d+)[^}]*maxDamage\s*=\s*(-?\d+)[^}]*effect\s*=\s*(\w+)[^}]*\}");
        foreach (Match entry in entries)
        {
            attacks.Add(new MonsterAttack
            {
                Name = entry.Groups[1].Value,
                Interval = int.Parse(entry.Groups[2].Value),
                Chance = int.Parse(entry.Groups[3].Value),
                MinDamage = int.Parse(entry.Groups[4].Value),
                MaxDamage = int.Parse(entry.Groups[5].Value),
                Effect = entry.Groups[6].Value
            });
        }
        return attacks;
    }

    private static MonsterDefense ParseDefense(string content)
    {
        var def = new MonsterDefense();
        var defMatch = Regex.Match(content,
            @"monster\.defenses\s*=\s*\{([^}]+)\}", RegexOptions.Singleline);
        if (!defMatch.Success) return def;

        var dMatch = Regex.Match(defMatch.Groups[1].Value,
            @"defense\s*=\s*(\d+)");
        if (dMatch.Success) def.Defense = int.Parse(dMatch.Groups[1].Value);

        var aMatch = Regex.Match(defMatch.Groups[1].Value,
            @"armor\s*=\s*(\d+)");
        if (aMatch.Success) def.Armor = int.Parse(aMatch.Groups[1].Value);

        return def;
    }

    private static MonsterElements ParseElements(string content)
    {
        var elems = new MonsterElements();
        var elemsMatch = Regex.Match(content,
            @"monster\.elements\s*=\s*\{(.*?)\}", RegexOptions.Singleline);
        if (!elemsMatch.Success) return elems;

        var entries = Regex.Matches(elemsMatch.Groups[1].Value,
            @"\{\s*type\s*=\s*(\w+)\s*,\s*percent\s*=\s*(-?\d+)\s*\}");
        foreach (Match entry in entries)
        {
            var type = entry.Groups[1].Value;
            var percent = int.Parse(entry.Groups[2].Value);
            switch (type)
            {
                case "COMBAT_PHYSICALDAMAGE": elems.Physical = percent; break;
                case "COMBAT_ENERGYDAMAGE": elems.Energy = percent; break;
                case "COMBAT_EARTHDAMAGE": elems.Earth = percent; break;
                case "COMBAT_FIREDAMAGE": elems.Fire = percent; break;
                case "COMBAT_ICEDAMAGE": elems.Ice = percent; break;
                case "COMBAT_HOLYDAMAGE": elems.Holy = percent; break;
                case "COMBAT_DEATHDAMAGE": elems.Death = percent; break;
            }
        }
        return elems;
    }

    public string GenerateMonsterLua(MonsterData m)
    {
        var sb = new System.Text.StringBuilder();
        sb.AppendLine($"local mType = Game.createMonsterType(\"{m.Name}\")");
        sb.AppendLine("local monster = {}");
        sb.AppendLine();
        sb.AppendLine($"monster.description = \"{m.Description}\"");
        sb.AppendLine($"monster.experience = {m.Experience}");
        sb.AppendLine($"monster.outfit = {{ lookType = {m.LookType}, lookHead = 0, lookBody = 0, lookLegs = 0, lookFeet = 0, lookAddons = 0, lookMount = 0 }}");
        sb.AppendLine($"monster.raceId = {m.RaceId}");
        sb.AppendLine($"monster.health = {m.Health}");
        sb.AppendLine($"monster.maxHealth = {m.MaxHealth}");
        sb.AppendLine($"monster.race = \"{m.Race}\"");
        sb.AppendLine($"monster.corpse = {m.Corpse}");
        sb.AppendLine($"monster.speed = {m.Speed}");
        sb.AppendLine($"monster.manaCost = {m.ManaCost}");
        sb.AppendLine();
        sb.AppendLine("monster.flags = {");
        sb.AppendLine($"    summonable = {(m.Summonable ? "true" : "false")},");
        sb.AppendLine($"    attackable = {(m.Attackable ? "true" : "false")},");
        sb.AppendLine($"    hostile = {(m.Hostile ? "true" : "false")},");
        sb.AppendLine($"    convinceable = {(m.Convinceable ? "true" : "false")},");
        sb.AppendLine($"    pushable = {(m.Pushable ? "true" : "false")},");
        sb.AppendLine($"    targetDistance = {m.TargetDistance},");
        sb.AppendLine("}");
        sb.AppendLine();
        sb.AppendLine($"mType:register(monster)");
        return sb.ToString();
    }
}

public class BalanceResult
{
    public int TotalMonsters { get; set; }
    public double AvgExperience { get; set; }
    public double StdDevExperience { get; set; }
    public double AvgHealth { get; set; }
    public double StdDevHealth { get; set; }
    public double AvgXpPerHp { get; set; }
    public double StdDevXpPerHp { get; set; }
    public List<MonsterOutlier> Outliers { get; set; } = new();
}

public class MonsterOutlier
{
    public string Name { get; set; } = "";
    public string Category { get; set; } = "";
    public int Experience { get; set; }
    public int Health { get; set; }
    public double XpPerHp { get; set; }
    public double ZScoreExperience { get; set; }
    public double ZScoreHealth { get; set; }
    public double ZScoreXpPerHp { get; set; }
    public string Reason { get; set; } = "";
}
