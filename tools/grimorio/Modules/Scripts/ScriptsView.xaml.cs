using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Threading;

namespace MCR.Grimorio.Modules.Scripts;

public class ScriptTreeNode
{
    public string Name { get; set; } = "";
    public string? FullPath { get; set; }
    public List<ScriptTreeNode> Children { get; set; } = new();
    public bool IsDirectory => Children.Count > 0;
}

public partial class ScriptsView : UserControl
{
    private readonly string _baseDir;
    private int _totalFiles;
    private DispatcherTimer? _debounceTimer;

    public ScriptsView()
    {
        InitializeComponent();
        _baseDir = GetBaseDir();
        Loaded += (s, e) => LoadScriptTree();
    }

    private static string GetBaseDir()
    {
        var app = Application.Current as App;
        var svc = app?.SettingsService;
        if (svc != null && !string.IsNullOrEmpty(svc.GetServerPath()))
            return svc.GetServerPath();

        return Path.GetFullPath(Path.Combine(
            AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", "..", "Canary"));
    }

    private void LoadScriptTree()
    {
        ScriptTree.Items.Clear();
        _totalFiles = 0;

        var dirs = new[] {
            Path.Combine(_baseDir, "data", "scripts"),
            Path.Combine(_baseDir, "data-canary", "scripts"),
            Path.Combine(_baseDir, "data-otservbr-global", "scripts"),
        };

        foreach (var dir in dirs)
        {
            if (!Directory.Exists(dir)) continue;
            var node = new ScriptTreeNode
            {
                Name = Path.GetFileName(dir),
                FullPath = dir
            };
            foreach (var sub in Directory.GetDirectories(dir))
                node.Children.Add(BuildTreeNode(sub));
            foreach (var file in Directory.GetFiles(dir, "*.lua"))
            {
                _totalFiles++;
                node.Children.Add(new ScriptTreeNode { Name = Path.GetFileName(file), FullPath = file });
            }
            ScriptTree.Items.Add(node);
        }

        ScriptCountText.Text = $"{_totalFiles} scripts Lua";
    }

    private ScriptTreeNode BuildTreeNode(string path)
    {
        var node = new ScriptTreeNode { Name = Path.GetFileName(path), FullPath = path };
        try
        {
            foreach (var dir in Directory.GetDirectories(path))
                node.Children.Add(BuildTreeNode(dir));
            foreach (var file in Directory.GetFiles(path, "*.lua"))
            {
                _totalFiles++;
                node.Children.Add(new ScriptTreeNode { Name = Path.GetFileName(file), FullPath = file });
            }
        }
        catch { }
        return node;
    }

    private void ScriptSearchBox_TextChanged(object sender, TextChangedEventArgs e)
    {
        _debounceTimer?.Stop();
        _debounceTimer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(300) };
        _debounceTimer.Tick += (s, args) =>
        {
            _debounceTimer.Stop();
            DoSearch();
        };
        _debounceTimer.Start();
    }

    private async void DoSearch()
    {
        var search = ScriptSearchBox.Text?.Trim().ToLower();
        if (string.IsNullOrEmpty(search))
        {
            LoadScriptTree();
            return;
        }

        ScriptTree.Items.Clear();

        var allDirs = new[] {
            Path.Combine(_baseDir, "data"),
            Path.Combine(_baseDir, "data-canary"),
            Path.Combine(_baseDir, "data-otservbr-global"),
        };

        var results = await Task.Run(() =>
        {
            var found = new List<string>();
            foreach (var dir in allDirs)
            {
                if (!Directory.Exists(dir)) continue;
                try
                {
                    found.AddRange(Directory.GetFiles(dir, "*.lua", SearchOption.AllDirectories)
                        .Where(f => Path.GetFileName(f).ToLower().Contains(search)));
                }
                catch { }
            }
            return found;
        });

        ScriptCountText.Text = $"{results.Count} resultados para \"{search}\"";

        foreach (var file in results.Take(200))
        {
            ScriptTree.Items.Add(new ScriptTreeNode
            {
                Name = Path.GetFileName(file),
                FullPath = file
            });
        }
    }

    private async void ScriptTree_SelectedItemChanged(object sender, RoutedPropertyChangedEventArgs<object> e)
    {
        if (e.NewValue is not ScriptTreeNode node || node.IsDirectory || node.FullPath == null) return;

        try
        {
            var content = await File.ReadAllTextAsync(node.FullPath);
            ScriptTitle.Text = node.FullPath;
            ScriptContent.Text = content;
        }
        catch (Exception ex)
        {
            ScriptTitle.Text = $"Erro: {ex.Message}";
            ScriptContent.Text = "";
        }
    }
}
