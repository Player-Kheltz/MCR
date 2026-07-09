using System.IO;
using System.Windows.Controls;

namespace MCR.Grimorio.Modules.Spawns;

public partial class SpawnsView : UserControl
{
    public SpawnsView()
    {
        InitializeComponent();

        Loaded += (s, e) => ScanOtbmFiles();
    }

    private void ScanOtbmFiles()
    {
        var baseDir = Path.GetFullPath(Path.Combine(
            AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", "..", "Canary"));

        var candidates = new[] {
            Path.Combine(baseDir, "data", "world"),
            Path.Combine(baseDir, "data", "maps"),
            Path.Combine(baseDir, "data-canary", "world"),
        };

        OtbmFilesList.Items.Clear();

        foreach (var dir in candidates)
        {
            if (!Directory.Exists(dir)) continue;
            foreach (var file in Directory.GetFiles(dir, "*.otbm"))
            {
                var info = new System.IO.FileInfo(file);
                OtbmFilesList.Items.Add($"{file} ({info.Length / 1024 / 1024:N1} MB)");
            }
            foreach (var file in Directory.GetFiles(dir, "*.xml"))
            {
                if (file.Contains("spawn", StringComparison.OrdinalIgnoreCase))
                {
                    OtbmFilesList.Items.Add($"{file} (spawn XML)");
                }
            }
        }

        if (OtbmFilesList.Items.Count == 0)
            OtbmFilesList.Items.Add("Nenhum arquivo OTBM ou spawn XML encontrado.");
    }
}
