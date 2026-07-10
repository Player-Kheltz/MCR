using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Threading;
using ICSharpCode.AvalonEdit;
using ICSharpCode.AvalonEdit.Highlighting;
using ICSharpCode.AvalonEdit.Highlighting.Xshd;

namespace MCR.Grimorio.Modules.Scripts;

public partial class ScriptsView : UserControl
{
    private readonly string _baseDir;
    private int _totalFiles;
    private string? _currentFilePath;
    private string? _originalContent;
    private TextEditor? _editor;
    private DispatcherTimer? _debounce;
    private int _findIndex = -1;

    public ScriptsView()
    {
        InitializeComponent();
        IniciarEditor();
        _baseDir = ObterBaseDir();
        CarregarTree();
    }

    private static string ObterBaseDir()
    {
        var app = Application.Current as App;
        var svc = app?.SettingsService;
        if (svc != null && !string.IsNullOrEmpty(svc.GetServerPath()))
            return svc.GetServerPath();
        return System.IO.Path.GetFullPath(System.IO.Path.Combine(
            AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", "..", "Canary"));
    }

    // ─── Editor ───────────────────────────────────────────

    private void IniciarEditor()
    {
        _editor = new TextEditor();
        _editor.FontFamily = new System.Windows.Media.FontFamily("Consolas");
        _editor.FontSize = 11;
        _editor.Background = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(0x1E, 0x1E, 0x1E));
        _editor.Foreground = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(0xCC, 0xCC, 0xCC));
        _editor.ShowLineNumbers = true;
        _editor.WordWrap = false;
        _editor.HorizontalScrollBarVisibility = ScrollBarVisibility.Auto;
        _editor.VerticalScrollBarVisibility = ScrollBarVisibility.Auto;

        // Carrega syntax highlighting Lua do arquivo .xshd
        try
        {
            var path = System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Resources", "Lua.xshd");
            if (System.IO.File.Exists(path))
            {
                using var reader = new System.Xml.XmlTextReader(path);
                _editor.SyntaxHighlighting = HighlightingLoader.Load(reader, HighlightingManager.Instance);
            }
        }
        catch { }

        EditorContainer.Child = _editor;

        _editor.TextChanged += (s, e) =>
        {
            if (_currentFilePath == null) return;
            var mod = _editor.Text != _originalContent;
            EditStatusText.Text = mod ? "✏️ Não salvo" : "";
            EditStatusText.Visibility = mod ? Visibility.Visible : Visibility.Collapsed;
            EditStatusText.Foreground = mod ? System.Windows.Media.Brushes.LightYellow : System.Windows.Media.Brushes.Transparent;
        };
    }

    // ─── ─── Toolbar ──────────────────────────────────────

    private void ToggleFerramentas_Checked(object s, RoutedEventArgs e)
    {
        if (ToolbarPanel == null) return;
        ToolbarPanel.Visibility = Visibility.Visible;
    }
    private void ToggleFerramentas_Unchecked(object s, RoutedEventArgs e)
    {
        if (ToolbarPanel == null) return;
        ToolbarPanel.Visibility = Visibility.Collapsed;
    }

    private void MostrarBotoes(bool visivel)
    {
        var v = visivel ? Visibility.Visible : Visibility.Collapsed;
        SaveBtn.Visibility = v;
        RevertBtn.Visibility = v;
        OpenFolderBtn.Visibility = v;
        FindBox.Visibility = v;
        FindCountText.Visibility = v;
        FindPrevBtn.Visibility = v;
        FindNextBtn.Visibility = v;
        SubstituirLabel.Visibility = v;
        ReplaceBox.Visibility = v;
        ReplaceBtn.Visibility = v;
        GotoBox.Visibility = v;
        GotoBtn.Visibility = v;
        WordWrapBtn.Visibility = v;
    }

    // ─── Tree ─────────────────────────────────────────────

    private void CarregarTree()
    {
        ScriptTree.Items.Clear();
        _totalFiles = 0;

        var roots = new[] {
            ("Servidor (data/scripts)", System.IO.Path.Combine(_baseDir, "data", "scripts")),
            ("Canary (data-canary/scripts)", System.IO.Path.Combine(_baseDir, "data-canary", "scripts")),
            ("Global (data-otservbr-global/scripts)", System.IO.Path.Combine(_baseDir, "data-otservbr-global", "scripts")),
        };

        foreach (var (label, dir) in roots)
        {
            if (!System.IO.Directory.Exists(dir)) continue;
            var root = new TreeViewItem { Header = "📁 " + label, IsExpanded = false };
            foreach (var sub in System.IO.Directory.GetDirectories(dir))
            {
                var si = new TreeViewItem { Header = "   " + System.IO.Path.GetFileName(sub) };
                foreach (var f in System.IO.Directory.GetFiles(sub, "*.lua"))
                { _totalFiles++; si.Items.Add(new TreeViewItem { Header = "      " + System.IO.Path.GetFileName(f), Tag = f }); }
                if (si.Items.Count > 0) root.Items.Add(si);
            }
            foreach (var f in System.IO.Directory.GetFiles(dir, "*.lua"))
            { _totalFiles++; root.Items.Add(new TreeViewItem { Header = "   " + System.IO.Path.GetFileName(f), Tag = f }); }
            ScriptTree.Items.Add(root);
        }
        ScriptCountText.Text = $"Total: {_totalFiles} scripts Lua";
    }

    private void ScriptSearchBox_TextChanged(object s, TextChangedEventArgs e)
    {
        _debounce?.Stop();
        _debounce = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(300) };
        _debounce.Tick += (_, _) => { _debounce.Stop(); FiltrarTree(); };
        _debounce.Start();
    }

    private void FiltrarTree()
    {
        var q = ScriptSearchBox.Text?.Trim().ToLower();
        ScriptTree.Items.Clear();
        if (string.IsNullOrEmpty(q)) { CarregarTree(); return; }

        foreach (var d in new[] { "data", "data-canary", "data-otservbr-global" })
        {
            var dir = System.IO.Path.Combine(_baseDir, d);
            if (!System.IO.Directory.Exists(dir)) continue;
            try
            {
                foreach (var f in System.IO.Directory.GetFiles(dir, "*.lua", System.IO.SearchOption.AllDirectories)
                    .Where(f => System.IO.Path.GetFileName(f).ToLower().Contains(q)))
                    ScriptTree.Items.Add(new TreeViewItem { Header = "   " + System.IO.Path.GetFileName(f), Tag = f });
            }
            catch { }
        }
        ScriptCountText.Text = $"{ScriptTree.Items.Count} resultados";
    }

    // ─── Seleção de arquivo ───────────────────────────────

    private async void ScriptTree_SelectedItemChanged(object s, RoutedPropertyChangedEventArgs<object> e)
    {
        if (e.NewValue is not TreeViewItem item || item.Tag is not string path || !System.IO.File.Exists(path))
        { LimparEditor(); return; }

        try
        {
            var text = await System.IO.File.ReadAllTextAsync(path);
            var fi = new System.IO.FileInfo(path);

            _editor.Text = text;
            _originalContent = text;
            _currentFilePath = path;
            _findIndex = -1;
            FindBox.Text = "";
            ReplaceBox.Text = "";
            GotoBox.Text = "";

            FileInfoText.Text = $"{System.IO.Path.GetFileName(path)} | {text.Split('\n').Length} linhas | {System.Math.Round(fi.Length / 1024.0, 1)} KB";
            MostrarBotoes(true);
            EditStatusText.Visibility = Visibility.Collapsed;
            FindBox.Focus();
        }
        catch (System.Exception ex) { FileInfoText.Text = $"Erro: {ex.Message}"; }
    }

    private void LimparEditor()
    {
        if (_editor != null) _editor.Text = "";
        FileInfoText.Text = "Nenhum arquivo selecionado";
        MostrarBotoes(false);
        _currentFilePath = null;
        _originalContent = null;
    }

    // ─── Arquivo ──────────────────────────────────────────

    private void SaveBtn_Click(object s, RoutedEventArgs e)
    {
        if (_currentFilePath == null || _editor == null) return;
        try
        {
            System.IO.File.WriteAllText(_currentFilePath, _editor.Text);
            _originalContent = _editor.Text;
            StatusVerde("✓ Salvo!");
        }
        catch (System.Exception ex) { StatusVermelho($"✗ {ex.Message}"); }
    }

    private void RevertBtn_Click(object s, RoutedEventArgs e)
    {
        if (_currentFilePath == null || _editor == null) return;
        try
        {
            if (System.IO.File.Exists(_currentFilePath))
                _originalContent = System.IO.File.ReadAllText(_currentFilePath);
            _editor.Text = _originalContent;
            StatusAmarelo("↩ Restaurado");
        }
        catch (System.Exception ex) { StatusVermelho($"✗ {ex.Message}"); }
    }

    private void OpenFolderBtn_Click(object s, RoutedEventArgs e)
    {
        if (_currentFilePath == null) return;
        try { System.Diagnostics.Process.Start("explorer.exe", "/select,\"" + _currentFilePath + "\""); }
        catch { }
    }

    private void StatusVerde(string m) { EditStatusText.Text = m; EditStatusText.Foreground = System.Windows.Media.Brushes.LightGreen; EditStatusText.Visibility = Visibility.Visible; }
    private void StatusAmarelo(string m) { EditStatusText.Text = m; EditStatusText.Foreground = System.Windows.Media.Brushes.LightYellow; EditStatusText.Visibility = Visibility.Visible; }
    private void StatusVermelho(string m) { EditStatusText.Text = m; EditStatusText.Foreground = System.Windows.Media.Brushes.OrangeRed; EditStatusText.Visibility = Visibility.Visible; }

    // ─── Busca inline ─────────────────────────────────────

    private void FindBox_TextChanged(object s, TextChangedEventArgs e)
    {
        _findIndex = -1;
        var term = FindBox.Text;
        if (string.IsNullOrEmpty(term) || _editor == null)
        { FindCountText.Text = ""; return; }

        int c = 0, p = 0;
        var txt = _editor.Text;
        while ((p = txt.IndexOf(term, p, System.StringComparison.OrdinalIgnoreCase)) >= 0)
        { c++; p += term.Length; }
        FindCountText.Text = c > 0 ? $"{c}" : "0";

        var idx = txt.IndexOf(term, System.StringComparison.OrdinalIgnoreCase);
        if (idx >= 0) { _findIndex = idx; _editor.Select(idx, term.Length); _editor.ScrollTo(_editor.Document.GetLocation(idx).Line, 0); }
    }

    private void FindNextBtn_Click(object s, RoutedEventArgs e) => NavegarBusca(1);
    private void FindPrevBtn_Click(object s, RoutedEventArgs e) => NavegarBusca(-1);

    private void NavegarBusca(int dir)
    {
        var term = FindBox.Text;
        if (string.IsNullOrEmpty(term) || _editor == null) return;
        var txt = _editor.Text;
        var idx = dir > 0
            ? txt.IndexOf(term, _findIndex < 0 ? 0 : _findIndex + term.Length, System.StringComparison.OrdinalIgnoreCase)
            : txt.LastIndexOf(term, _findIndex > 0 ? _findIndex - 1 : txt.Length - 1, System.StringComparison.OrdinalIgnoreCase);
        if (idx < 0)
            idx = dir > 0
                ? txt.IndexOf(term, System.StringComparison.OrdinalIgnoreCase)
                : txt.LastIndexOf(term, txt.Length - 1, System.StringComparison.OrdinalIgnoreCase);
        if (idx >= 0) { _findIndex = idx; _editor.Select(idx, term.Length); _editor.ScrollTo(_editor.Document.GetLocation(idx).Line, 0); _editor.Focus(); }
    }

    private void ReplaceBtn_Click(object s, RoutedEventArgs e)
    {
        var term = FindBox.Text;
        var subs = ReplaceBox.Text;
        if (string.IsNullOrEmpty(term) || _editor == null) return;
        var sel = _editor.SelectionStart;
        var len = _editor.SelectionLength;
        if (len > 0 && _editor.Text.Substring(sel, len).Equals(term, System.StringComparison.OrdinalIgnoreCase))
        {
            _editor.Document.Replace(sel, len, subs);
            _findIndex = sel + subs.Length;
        }
        NavegarBusca(1);
    }

    // ─── Ir para linha ────────────────────────────────────

    private void GotoBox_TextChanged(object s, TextChangedEventArgs e)
    {
        if (_editor == null) return;
        if (int.TryParse(GotoBox.Text?.Trim(), out var line) && line > 0)
        {
            _editor.ScrollTo(line, 0);
        }
    }

    private void GotoBtn_Click(object s, RoutedEventArgs e)
    {
        if (_editor == null) return;
        if (int.TryParse(GotoBox.Text?.Trim(), out var line) && line > 0)
        {
            _editor.ScrollTo(line, 0);
            _editor.Focus();
        }
    }

    // ─── Wrap ─────────────────────────────────────────────

    private void WordWrapBtn_Click(object s, RoutedEventArgs e)
    {
        if (_editor == null) return;
        _editor.WordWrap = !_editor.WordWrap;
        WordWrapBtn.Content = _editor.WordWrap ? "Wrap: ON" : "Wrap: OFF";
    }
}
