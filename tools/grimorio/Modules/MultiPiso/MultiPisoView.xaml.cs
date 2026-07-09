using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using MCR.Grimorio.Core.Detection;
using MCR.Grimorio.Core.Services;

namespace MCR.Grimorio.Modules.MultiPiso;

public partial class MultiPisoView : UserControl
{
    private readonly SettingsService _settings;

    public MultiPisoView()
    {
        InitializeComponent();
        _settings = (Application.Current as App)?.SettingsService ?? new SettingsService();
        DetectionText.Text = new MCRDetector().Detect().HasMultiPiso ? "✓ Detectado" : "Não detectado";
    }

    private void ScanButton_Click(object sender, RoutedEventArgs e)
    {
        var serverPath = _settings.GetServerPath();
        if (string.IsNullOrEmpty(serverPath)) return;

        var results = new System.Text.StringBuilder();
        results.AppendLine(">>> Arquivos encontrados:");
        results.AppendLine();

        var srcDirs = new[] {
            Path.Combine(serverPath, "src", "mcr", "core"),
            Path.Combine(serverPath, "src"),
        };

        foreach (var dir in srcDirs)
        {
            if (!Directory.Exists(dir)) continue;
            var files = Directory.GetFiles(dir, "*monster*", SearchOption.AllDirectories)
                .Concat(Directory.GetFiles(dir, "*multi*", SearchOption.AllDirectories))
                .Concat(Directory.GetFiles(dir, "*pursuit*", SearchOption.AllDirectories))
                .Distinct().ToArray();

            foreach (var f in files.Take(20))
                results.AppendLine($"  {Path.GetFileName(f)} ({(new FileInfo(f).Length / 1024)} KB)");
        }

        results.AppendLine();
        results.AppendLine($"Config: pursuitLimit={PursuitBox.Text}, congestion={CongestBox.Text}, jitter={JitterBox.Text}ms");
        OutputBox.Text = results.ToString();
    }
}
