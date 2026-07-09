using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using MCR.Grimorio.Core.Services;

namespace MCR.Grimorio.Modules.Deploy;

public partial class DeployView : UserControl
{
    private readonly SettingsService _settings;
    private readonly string _canaryDir;

    public DeployView()
    {
        InitializeComponent();
        _settings = (Application.Current as App)?.SettingsService ?? new SettingsService();
        _canaryDir = _settings.GetServerPath();

        if (!Directory.Exists(_canaryDir))
            DeployOutput.Text = $"Diretório não encontrado: {_canaryDir}";
    }

    private void AppendOutput(string text)
    {
        Dispatcher.Invoke(() =>
        {
            DeployOutput.Text += text + Environment.NewLine;
            if (DeployOutput.Text.Length > 50000)
                DeployOutput.Text = DeployOutput.Text[^25000..];
            DeployOutput.ScrollToEnd();
        });
    }

    private async void GitStatusButton_Click(object sender, RoutedEventArgs e)
    { DeployOutput.Text = ""; AppendOutput("> git status"); await RunCmd("git", "status"); }

    private async void GitCommitButton_Click(object sender, RoutedEventArgs e)
    {
        DeployOutput.Text = "";
        var msg = CommitMsgBox.Text?.Trim() ?? "auto-update";
        AppendOutput($"> git add -A && git commit -m \"{msg}\"");
        await RunCmd("git", "add -A");
        await RunCmd("git", $"commit -m \"{msg}\"");
    }

    private async void BuildButton_Click(object sender, RoutedEventArgs e)
    {
        DeployOutput.Text = "";
        DeployStatusText.Text = "Compilando...";
        var buildDir = Path.Combine(_canaryDir, "build");
        try
        {
            if (!Directory.Exists(buildDir)) Directory.CreateDirectory(buildDir);
            await RunCmd("cmake", "--build . --config Release", buildDir);
            DeployStatusText.Text = "Compilação OK";
        }
        catch { DeployStatusText.Text = "Erro"; }
    }

    private async void DeployButton_Click(object sender, RoutedEventArgs e)
    {
        var confirm = MessageBox.Show(
            "Isso vai PARAR o servidor, compilar, copiar e reiniciar.\nContinuar?",
            "Confirmar Deploy", MessageBoxButton.YesNo, MessageBoxImage.Warning);

        if (confirm != MessageBoxResult.Yes) return;

        DeployOutput.Text = "";
        DeployStatusText.Text = "Deploy em andamento...";
        AppendOutput("=== DEPLOY ===");

        AppendOutput("> Parando servidor...");
        foreach (var proc in Process.GetProcessesByName("canary"))
        {
            proc.CloseMainWindow();
            if (!proc.WaitForExit(5000)) proc.Kill();
        }

        AppendOutput("> Compilando...");
        var buildDir = Path.Combine(_canaryDir, "build");
        try { await RunCmd("cmake", "--build . --config Release", buildDir); }
        catch { return; }

        AppendOutput("> Copiando binário...");
        try
        {
            var src = Path.Combine(buildDir, "Release", "canary.exe");
            var dst = Path.Combine(_canaryDir, "canary.exe");
            if (File.Exists(src)) { File.Copy(src, dst, true); AppendOutput("✓ canary.exe copiado"); }
        }
        catch (Exception ex) { AppendOutput($"Erro: {ex.Message}"); }

        AppendOutput("> Iniciando servidor...");
        try
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = Path.Combine(_canaryDir, "canary.exe"),
                WorkingDirectory = _canaryDir,
                UseShellExecute = true,
                WindowStyle = ProcessWindowStyle.Hidden
            });
            AppendOutput("✓ Servidor iniciado!");
        }
        catch (Exception ex) { AppendOutput($"Erro: {ex.Message}"); }

        DeployStatusText.Text = "Deploy OK";
        AppendOutput("=== FIM ===");
    }

    private async Task RunCmd(string cmd, string args, string? workDir = null)
    {
        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = cmd,
                Arguments = args,
                WorkingDirectory = workDir ?? _canaryDir,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };
            using var proc = new Process { StartInfo = psi };
            proc.Start();
            var (output, error) = (await proc.StandardOutput.ReadToEndAsync(), await proc.StandardError.ReadToEndAsync());
            await proc.WaitForExitAsync();
            if (!string.IsNullOrEmpty(output)) AppendOutput(output.TrimEnd());
            if (!string.IsNullOrEmpty(error)) AppendOutput($"[ERRO] {error.TrimEnd()}");
        }
        catch (Exception ex) { AppendOutput($"[ERRO] {ex.Message}"); }
    }
}
