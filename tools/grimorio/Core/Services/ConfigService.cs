using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace MCR.Grimorio.Core.Services;

public class ConfigEntry
{
    public string Key { get; set; } = "";
    public string Value { get; set; } = "";
    public string Type { get; set; } = "string";
    public string? Description { get; set; }
    public int LineNumber { get; set; }
    public string Category { get; set; } = "";
    public override string ToString() => $"{Key} = {Value}";
}

public class ConfigService
{
    private readonly string _configPath;

    public ConfigService(string? customPath = null)
    {
        if (!string.IsNullOrEmpty(customPath))
        {
            _configPath = customPath;
            return;
        }

        var settings = ((App)System.Windows.Application.Current)?.SettingsService;
        if (settings != null)
        {
            _configPath = settings.GetConfigPath();
            if (File.Exists(_configPath)) return;
        }

        var baseDir = Path.GetFullPath(Path.Combine(
            AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", "..", "Canary"));
        _configPath = Path.Combine(baseDir, "config.lua");
    }

    public string ConfigPath => _configPath;
    public bool Exists => File.Exists(_configPath);

    public List<ConfigEntry> ReadAll()
    {
        var entries = new List<ConfigEntry>();
        if (!Exists) return entries;

        var lines = File.ReadAllLines(_configPath, Encoding.UTF8);

        for (int i = 0; i < lines.Length; i++)
        {
            var line = lines[i];

            var commentMatch = Regex.Match(line, @"^\s*--\s*(.+)$");
            if (commentMatch.Success)
            {
                if (entries.Count > 0 && entries[^1].Description == null)
                    entries[^1].Description = commentMatch.Groups[1].Value.Trim();
                continue;
            }

            var configMatch = Regex.Match(line,
                @"^\s*(\w+)\s*=\s*(.+?)\s*(?:--.*)?$");
            if (configMatch.Success)
            {
                var key = configMatch.Groups[1].Value;
                var rawValue = configMatch.Groups[2].Value.Trim();

                var entry = new ConfigEntry
                {
                    Key = key,
                    LineNumber = i + 1,
                    Description = ExtractComment(line)
                };

                if (rawValue.StartsWith("\"") && rawValue.EndsWith("\""))
                {
                    entry.Type = "string";
                    entry.Value = rawValue[1..^1];
                }
                else if (rawValue == "true" || rawValue == "false")
                {
                    entry.Type = "boolean";
                    entry.Value = rawValue;
                }
                else if (int.TryParse(rawValue, out _))
                {
                    entry.Type = "integer";
                    entry.Value = rawValue;
                }
                else if (double.TryParse(rawValue,
                    System.Globalization.NumberStyles.Any,
                    System.Globalization.CultureInfo.InvariantCulture, out _))
                {
                    entry.Type = "float";
                    entry.Value = rawValue;
                }
                else
                {
                    entry.Type = "other";
                    entry.Value = rawValue;
                }

                entries.Add(entry);
            }
        }

        return entries;
    }

    public string? GetValue(string key)
    {
        var entries = ReadAll();
        return entries.FirstOrDefault(e =>
            e.Key.Equals(key, StringComparison.OrdinalIgnoreCase))?.Value;
    }

    public async Task<bool> SetValueAsync(string key, string newValue)
    {
        if (!Exists) return false;

        var lines = File.ReadAllLines(_configPath, Encoding.UTF8);
        var found = false;

        for (int i = 0; i < lines.Length; i++)
        {
            var match = Regex.Match(lines[i],
                @"^(\s*)(" + Regex.Escape(key) + @")\s*=\s*(.+?)(\s*--.*)?$");
            if (match.Success)
            {
                var trailingComment = match.Groups[4].Success ? match.Groups[4].Value : "";
                lines[i] = $"{match.Groups[1].Value}{key} = {FormatValue(newValue)}{trailingComment}";
                found = true;
                break;
            }
        }

        if (!found) return false;

        await File.WriteAllLinesAsync(_configPath, lines);
        return true;
    }

    private static string FormatValue(string value)
    {
        if (value == "true" || value == "false")
            return value;
        if (int.TryParse(value, out _) || double.TryParse(value,
            System.Globalization.NumberStyles.Any,
            System.Globalization.CultureInfo.InvariantCulture, out _))
            return value;

        return $"\"{value.Replace("\\", "\\\\").Replace("\"", "\\\"")}\"";
    }

    private static string? ExtractComment(string line)
    {
        var match = Regex.Match(line, @"--\s*(.+)$");
        return match.Success ? match.Groups[1].Value.Trim() : null;
    }

    public List<string> GetCategories()
    {
        return new List<string>
        {
            "Geral", "Rede", "SQL", "Mundo", "Gameplay",
            "PvP", "Loot", "Cidades", "VIP", "MCR"
        };
    }
}
