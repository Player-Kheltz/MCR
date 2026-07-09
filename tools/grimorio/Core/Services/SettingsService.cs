using System.IO;
using System.Security.Cryptography;
using System.Text.Json;
using MCR.Grimorio.Data;

namespace MCR.Grimorio.Core.Services;

public class SettingsService
{
    private static readonly byte[] _entropy = 
        System.Text.Encoding.UTF8.GetBytes("MCR.Grimorio.v1");

    private readonly string _settingsPath;
    private AppSettings _settings;
    private readonly Lazy<string> _resolvedBaseDir;

    private static string ResolveRepoRoot()
    {
        var dir = AppDomain.CurrentDomain.BaseDirectory;
        for (int i = 0; i < 6; i++)
        {
            var parent = Path.GetDirectoryName(dir);
            if (parent == null) break;
            if (File.Exists(Path.Combine(parent, "PERSONALIDADE.md")))
                return parent;
            if (File.Exists(Path.Combine(parent, ".gitignore")))
                return parent;
            dir = parent;
        }
        return Path.GetFullPath(Path.Combine(
            AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", ".."));
    }

    public SettingsService()
    {
        _settingsPath = Path.Combine(
            AppDomain.CurrentDomain.BaseDirectory, "settings.json");
        _resolvedBaseDir = new Lazy<string>(ResolveRepoRoot);
        _settings = Load();
    }

    public AppSettings Settings => _settings;
    public event Action? OnSettingsChanged;

    public AppSettings Load()
    {
        try
        {
            if (File.Exists(_settingsPath))
            {
                var json = File.ReadAllText(_settingsPath);
                var s = JsonSerializer.Deserialize<AppSettings>(json) ?? new AppSettings();
                if (!string.IsNullOrEmpty(s.MySql.Password))
                    s.MySql.Password = UnprotectPassword(s.MySql.Password);
                return s;
            }
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"Settings Load Error: {ex.Message}");
        }
        return new AppSettings();
    }

    public void Save(AppSettings settings)
    {
        _settings = settings;
        var encryptedPassword = ProtectPassword(settings.MySql.Password);
        settings.MySql.Password = encryptedPassword;
        var json = JsonSerializer.Serialize(settings, new JsonSerializerOptions
        {
            WriteIndented = true
        });
        settings.MySql.Password = UnprotectPassword(encryptedPassword);
        File.WriteAllText(_settingsPath, json);
        OnSettingsChanged?.Invoke();
    }

    private static string ProtectPassword(string plainText)
    {
        if (string.IsNullOrEmpty(plainText)) return "";
        try
        {
            var data = System.Text.Encoding.UTF8.GetBytes(plainText);
            var encrypted = ProtectedData.Protect(data, _entropy, DataProtectionScope.CurrentUser);
            return Convert.ToBase64String(encrypted);
        }
        catch
        {
            return plainText;
        }
    }

    private static string UnprotectPassword(string encryptedBase64)
    {
        if (string.IsNullOrEmpty(encryptedBase64)) return "";
        try
        {
            var encrypted = Convert.FromBase64String(encryptedBase64);
            var data = ProtectedData.Unprotect(encrypted, _entropy, DataProtectionScope.CurrentUser);
            return System.Text.Encoding.UTF8.GetString(data);
        }
        catch
        {
            return encryptedBase64;
        }
    }

    public string GetServerPath()
    {
        if (!string.IsNullOrEmpty(_settings.ServerPath))
            return _settings.ServerPath;

        return Path.Combine(_resolvedBaseDir.Value, "Canary");
    }

    public string GetServerExeName()
    {
        if (!string.IsNullOrEmpty(_settings.ServerExeName))
            return _settings.ServerExeName;
        return "canary-sln.exe";
    }

    public void SetServerPath(string path)
    {
        _settings.ServerPath = path;
    }

    public void SetServerExeName(string name)
    {
        _settings.ServerExeName = name;
    }

    public string GetOtclientPath()
    {
        if (!string.IsNullOrEmpty(_settings.OtclientPath))
            return _settings.OtclientPath;
        return Path.Combine(_resolvedBaseDir.Value, "OTClient");
    }

    public void SetOtclientPath(string path)
    {
        _settings.OtclientPath = path;
    }

    public string GetMonsterPath()
    {
        var dirs = new[]
        {
            Path.Combine(GetServerPath(), "data-otservbr-global", "monster"),
            Path.Combine(GetServerPath(), "data-canary", "monster"),
        };
        return dirs.FirstOrDefault(Directory.Exists) ?? dirs[0];
    }

    public string GetNpcPath()
    {
        return Path.Combine(GetServerPath(), "data-otservbr-global", "npc");
    }

    public string GetConfigPath()
    {
        return Path.Combine(GetServerPath(), "config.lua");
    }

    public string GetItemsXmlPath()
    {
        var dirs = new[]
        {
            Path.Combine(GetServerPath(), "data-otservbr-global", "items", "items.xml"),
            Path.Combine(GetServerPath(), "data", "items", "items.xml"),
            Path.Combine(GetServerPath(), "data-canary", "items", "items.xml"),
        };
        return dirs.FirstOrDefault(File.Exists) ?? dirs[0];
    }

    public string GetSprPath()
    {
        if (!string.IsNullOrEmpty(_settings.OtclientPath))
        {
            var thingsDir = Path.Combine(_settings.OtclientPath, "data", "things");
            if (Directory.Exists(thingsDir))
            {
                var versions = Directory.GetDirectories(thingsDir)
                    .OrderByDescending(d => d).ToArray();
                if (versions.Length > 0)
                    return versions[0];
            }
        }

        var fallback = Path.Combine(_resolvedBaseDir.Value, "OTClient", "data", "things");
        if (Directory.Exists(fallback))
        {
            var versions = Directory.GetDirectories(fallback)
                .OrderByDescending(d => d).ToArray();
            if (versions.Length > 0)
                return versions[0];
        }

        return "";
    }

    public string GetLogsPath()
    {
        var dirs = new[]
        {
            Path.Combine(GetServerPath(), "data", "logs"),
            Path.Combine(GetServerPath(), "logs"),
            Path.Combine(GetServerPath(), "log"),
        };
        return dirs.FirstOrDefault(Directory.Exists) ?? dirs[0];
    }

    public string GetScriptsPath(int index = 0)
    {
        var dirs = new[]
        {
            Path.Combine(GetServerPath(), "data", "scripts"),
            Path.Combine(GetServerPath(), "data-canary", "scripts"),
            Path.Combine(GetServerPath(), "data-otservbr-global", "scripts"),
        };
        return index < dirs.Length ? dirs[index] : dirs[0];
    }

    public string GetWorldPath()
    {
        var dirs = new[]
        {
            Path.Combine(GetServerPath(), "data", "world"),
            Path.Combine(GetServerPath(), "data", "maps"),
            Path.Combine(GetServerPath(), "data-canary", "world"),
        };
        return dirs.FirstOrDefault(Directory.Exists) ?? dirs[0];
    }

    public string GetOtbmPath()
    {
        if (!string.IsNullOrEmpty(_settings.OtbmPath) && File.Exists(_settings.OtbmPath))
            return _settings.OtbmPath;

        var worldPath = GetWorldPath();
        if (Directory.Exists(worldPath))
        {
            var files = Directory.GetFiles(worldPath, "*.otbm");
            if (files.Length > 0) return files[0];
        }
        return "";
    }

    public void SetOtbmPath(string path)
    {
        _settings.OtbmPath = path;
    }
}
