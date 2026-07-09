using System.IO;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using MCR.Grimorio.Core.Services;
using System.Text.RegularExpressions;

namespace MCR.Grimorio.Modules.Tools;

public partial class ToolsView : UserControl
{
    private readonly MonsterService _monsterService;

    public ToolsView()
    {
        InitializeComponent();
        _monsterService = new MonsterService();
    }

    private void RunBalanceButton_Click(object sender, RoutedEventArgs e)
    {
        var result = _monsterService.AnalyzeBalance();

        AvgExpText.Text = $"{result.AvgExperience:N0}";
        StdExpText.Text = $"{result.StdDevExperience:N0}";
        AvgHpText.Text = $"{result.AvgHealth:N0}";
        StdHpText.Text = $"{result.StdDevHealth:N0}";

        OutlierList.ItemsSource = result.Outliers;
    }

    private void ValidateButton_Click(object sender, RoutedEventArgs e)
    {
        var output = new StringBuilder();
        var baseDir = Path.GetFullPath(Path.Combine(
            AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", "..", "Canary"));
        var scriptDirs = new[] {
            Path.Combine(baseDir, "data", "scripts"),
            Path.Combine(baseDir, "data-canary", "scripts"),
            Path.Combine(baseDir, "data-otservbr-global", "scripts")
        };

        var totalFiles = 0;
        var errors = 0;

        foreach (var dir in scriptDirs)
        {
            if (!Directory.Exists(dir)) continue;

            foreach (var file in Directory.GetFiles(dir, "*.lua", SearchOption.AllDirectories))
            {
                totalFiles++;
                try
                {
                    var content = File.ReadAllText(file);
                    var validationErrors = ValidateLua(content);
                    if (validationErrors.Count > 0)
                    {
                        errors++;
                        output.AppendLine($"[{Path.GetFileName(file)}] {string.Join("; ", validationErrors)}");
                    }
                }
                catch (Exception ex)
                {
                    errors++;
                    output.AppendLine($"[{Path.GetFileName(file)}] ERRO: {ex.Message}");
                }
            }
        }

        if (output.Length == 0)
            output.AppendLine($"✅ {totalFiles} arquivos validados — nenhum erro encontrado");
        else
            output.Insert(0, $"⚠️ {errors} arquivos com problemas de {totalFiles}:\n\n");

        ValidationOutput.Text = output.ToString();
    }

    private List<string> ValidateLua(string content)
    {
        var errors = new List<string>();

        var lines = content.Split('\n');
        var parenStack = new Stack<(char, int)>();
        var bracketStack = new Stack<(string, int)>();

        for (int i = 0; i < lines.Length; i++)
        {
            var line = lines[i];
            if (string.IsNullOrWhiteSpace(line) || line.TrimStart().StartsWith("--")) continue;

            for (int j = 0; j < line.Length; j++)
            {
                var c = line[j];
                if (c == '(' || c == '{' || c == '[') parenStack.Push((c, i + 1));
                else if (c == ')' || c == '}' || c == ']')
                {
                    if (parenStack.Count == 0) errors.Add($"Linha {i + 1}: '{c}' sem abertura");
                }
            }
        }

        if (parenStack.Count > 0)
        {
            var remaining = string.Join("", parenStack.Select(x => x.Item1));
            errors.Add($"{parenStack.Count} delimitadores não fechados: {remaining}");
        }

        return errors;
    }
}
