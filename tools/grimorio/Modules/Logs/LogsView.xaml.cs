using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using MCR.Grimorio.Core.Services;

namespace MCR.Grimorio.Modules.Logs;

public partial class LogsView : UserControl
{
    private readonly SettingsService _settings;
    private string _currentFilter = "all";
    private string _currentFile = "";
    private List<string> _lastLines = new();
    private const int MaxLines = 500;

    public LogsView()
    {
        InitializeComponent();
        _settings = (Application.Current as App)?.SettingsService ?? new SettingsService();
        Loaded += (s, e) => RefreshLogs();
    }

    private void RefreshLogs()
    {
        var logDir = _settings.GetLogsPath();
        if (!Directory.Exists(logDir))
        {
            LogContent.Text = $"Diretório de logs não encontrado: {logDir}";
            return;
        }

        var logFiles = Directory.GetFiles(logDir, "*.log")
            .OrderByDescending(f => new FileInfo(f).LastWriteTime)
            .ToArray();

        if (logFiles.Length == 0)
        {
            LogContent.Text = "Nenhum arquivo .log encontrado.";
            return;
        }

        try
        {
            var latestLog = logFiles[0];
            _currentFile = Path.GetFileName(latestLog);
            _lastLines = ReadTailLines(latestLog, MaxLines);
            ApplyFilter(_lastLines);
        }
        catch (Exception ex)
        {
            LogContent.Text = $"Erro ao ler log: {ex.Message}";
        }
    }

    private static List<string> ReadTailLines(string path, int count)
    {
        var lines = new List<string>(count);
        try
        {
            using var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
            using var reader = new StreamReader(fs);
            var buffer = new Queue<string>(count);
            string? line;
            while ((line = reader.ReadLine()) != null)
            {
                buffer.Enqueue(line);
                if (buffer.Count > count)
                    buffer.Dequeue();
            }
            lines.AddRange(buffer);
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"ReadTailLines Error: {ex.Message}");
        }
        return lines;
    }

    private void ApplyFilter(List<string> allLines)
    {
        IEnumerable<string> filtered = allLines;

        if (_currentFilter == "error")
            filtered = allLines.Where(l =>
                l.Contains("ERROR", StringComparison.OrdinalIgnoreCase) ||
                l.Contains("FATAL", StringComparison.OrdinalIgnoreCase));
        else if (_currentFilter == "warning")
            filtered = allLines.Where(l =>
                l.Contains("WARNING", StringComparison.OrdinalIgnoreCase) ||
                l.Contains("WARN", StringComparison.OrdinalIgnoreCase));

        var header = $">>> {_currentFile} ({allLines.Count} linhas, filtrando: {_currentFilter})\n{new string('-', 50)}\n";
        LogContent.Text = header + string.Join(Environment.NewLine, filtered.TakeLast(MaxLines));
    }

    private void ShowAllButton_Click(object sender, RoutedEventArgs e) { _currentFilter = "all"; ApplyFilter(_lastLines); }
    private void ShowErrorsButton_Click(object sender, RoutedEventArgs e) { _currentFilter = "error"; ApplyFilter(_lastLines); }
    private void ShowWarningsButton_Click(object sender, RoutedEventArgs e) { _currentFilter = "warning"; ApplyFilter(_lastLines); }
    private void RefreshLogsButton_Click(object sender, RoutedEventArgs e) { RefreshLogs(); }
    private void ClearLogsButton_Click(object sender, RoutedEventArgs e) { LogContent.Text = ""; }
}
