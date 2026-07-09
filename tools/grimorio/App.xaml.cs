using System.IO;
using System.Linq;
using System.Windows;
using MCR.Grimorio.Core.Services;

namespace MCR.Grimorio;

public partial class App : Application
{
    public SettingsService SettingsService { get; } = new();
    public DatabaseService DatabaseService { get; } = new();
    public SpriteSheetService? SpriteSheets { get; private set; }
    public string SpriteStatus { get; private set; } = "";
    public string OtbmPath { get; set; } = "";
    public string ItemsXmlPath { get; set; } = "";
    public string CanaryExePath { get; set; } = "";

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        RegisterServices();
        AutoDetectPaths();
        InitDatabase();
        InitSprites();
    }

    private void RegisterServices()
    {
        ServiceProvider.RegisterSingleton<IDatabaseService>(DatabaseService);
        ServiceProvider.RegisterSingleton<IServerService>(new ServerService(
            SettingsService.GetServerPath(),
            SettingsService.GetServerExeName()));
    }

    private void AutoDetectPaths()
    {
        var serverPath = SettingsService.GetServerPath();
        if (Directory.Exists(serverPath))
        {
            CanaryExePath = DetectCanaryExe(serverPath);
            ItemsXmlPath = FindItemsXml(serverPath);
            OtbmPath = FindOtbm(serverPath);
        }

        var otPath = SettingsService.GetOtclientPath();
        if (string.IsNullOrEmpty(otPath) || !Directory.Exists(otPath))
        {
            otPath = Path.GetFullPath(Path.Combine(
                AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", "..", "OTClient"));
            SettingsService.SetOtclientPath(otPath);
        }
    }

    public string DetectCanaryExe(string serverPath)
    {
        var candidates = new[] { "canary.exe", "canary-sln.exe", "canary-sln-dbg.exe" };
        foreach (var name in candidates)
        {
            var path = Path.Combine(serverPath, name);
            if (File.Exists(path))
            {
                SettingsService.SetServerExeName(name);
                return path;
            }
        }
        foreach (var name in candidates)
        {
            var path = Path.Combine(serverPath, "build", "bin", "Release", name);
            if (File.Exists(path))
            {
                SettingsService.SetServerExeName(name);
                return path;
            }
        }
        return Path.Combine(serverPath, "canary-sln.exe");
    }

    public string FindItemsXml(string serverPath)
    {
        var candidates = new[]
        {
            Path.Combine(serverPath, "data", "items", "items.xml"),
            Path.Combine(serverPath, "data-otservbr-global", "items", "items.xml"),
            Path.Combine(serverPath, "data-canary", "items", "items.xml"),
        };
        return candidates.FirstOrDefault(File.Exists) ?? candidates[0];
    }

    public string FindOtbm(string serverPath)
    {
        // Prioridade: dataPackDirectory ("data-canary") > coreDirectory ("data")
        var dirs = new[]
        {
            Path.Combine(serverPath, "data-canary", "world"),
            Path.Combine(serverPath, "data", "world"),
            Path.Combine(serverPath, "data", "maps"),
        };

        foreach (var dir in dirs)
        {
            if (!Directory.Exists(dir)) continue;
            // Ignora placeholders vazios (< 1KB)
            var files = Directory.GetFiles(dir, "*.otbm")
                .Where(f => new FileInfo(f).Length > 1024)
                .ToArray();
            if (files.Length > 0) return files[0];
        }

        return "";
    }

    private void InitDatabase()
    {
        var s = SettingsService.Settings;
        if (s.IsValid)
        {
            DatabaseService.Configure(
                s.MySql.Host, s.MySql.Port,
                s.MySql.User, s.MySql.Password,
                s.MySql.Database);
        }
    }

    private void InitSprites()
    {
        try
        {
            var thingsDir = SettingsService.GetSprPath();
            if (!string.IsNullOrEmpty(thingsDir) && Directory.Exists(thingsDir))
            {
                SpriteSheets = new SpriteSheetService(thingsDir);
                SpriteStatus = SpriteSheets.Status;
            }
            else
            {
                SpriteStatus = "Diretório de sprites não encontrado em: " + (thingsDir ?? "(vazio)");
            }
        }
        catch (Exception ex)
        {
            SpriteStatus = $"Erro ao carregar sprites: {ex.Message}";
            SpriteSheets = null;
        }
    }

    public void ReinitializeAll()
    {
        AutoDetectPaths();
        InitDatabase();
        InitSprites();
    }

    public void ReinitializeSpriteSheets()
    {
        InitSprites();
    }
}
