using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using MCR.Grimorio.Core.Detection;
using MCR.Grimorio.Core.Services;

namespace MCR.Grimorio.Modules.MountSummon;

public partial class MountSummonView : UserControl
{
    private readonly SettingsService _settings;

    public MountSummonView()
    {
        InitializeComponent();
        _settings = (Application.Current as App)?.SettingsService ?? new SettingsService();
        DetectionText.Text = new MCRDetector().Detect().HasMountSummon ? "✓ Detectado" : "Não detectado";
    }

    private void ScanButton_Click(object sender, RoutedEventArgs e)
    {
        var serverPath = _settings.GetServerPath();
        if (string.IsNullOrEmpty(serverPath)) return;

        var dirs = new[] {
            Path.Combine(serverPath, "data", "scripts", "MCR", "MountSummon"),
            Path.Combine(serverPath, "data-canary", "scripts", "MCR", "MountSummon"),
            Path.Combine(serverPath, "data", "scripts", "MCR"),
        };

        var items = new List<object>();
        foreach (var dir in dirs)
        {
            if (!Directory.Exists(dir)) continue;
            foreach (var file in Directory.GetFiles(dir, "*.lua"))
            {
                try
                {
                    var content = File.ReadAllText(file);
                    var tags = new List<string>();
                    if (content.Contains("mount", StringComparison.OrdinalIgnoreCase)) tags.Add("mount");
                    if (content.Contains("summon", StringComparison.OrdinalIgnoreCase)) tags.Add("summon");
                    if (content.Contains("pet", StringComparison.OrdinalIgnoreCase)) tags.Add("pet");

                    items.Add(new
                    {
                        Name = Path.GetFileName(file),
                        Type = tags.Count > 0 ? string.Join(", ", tags) : "outro",
                        Size = $"{new FileInfo(file).Length / 1024} KB"
                    });
                }
                catch { }
            }
        }

        FileList.ItemsSource = items;
        if (items.Count == 0)
            FileList.ItemsSource = new[] { new { Name = "Nenhum arquivo encontrado", Type = "", Size = "" } };
    }
}
