using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Text.RegularExpressions;

namespace MCR.Grimorio.Modules.Protocol;

public partial class ProtocolView : UserControl
{
    public ProtocolView()
    {
        InitializeComponent();
    }

    private void LoadOpcodesButton_Click(object sender, RoutedEventArgs e)
    {
        var otclientDir = Path.GetFullPath(Path.Combine(
            AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", "..", "OTClient"));

        var protocolFiles = new[] {
            Path.Combine(otclientDir, "src", "client", "protocolcodes.h"),
            Path.Combine(otclientDir, "src", "protocol", "protocolcodes.h"),
            Path.Combine(otclientDir, "modules", "game_protocol", "protocolcodes.h"),
        };

        foreach (var file in protocolFiles)
        {
            if (File.Exists(file))
            {
                try
                {
                    var content = File.ReadAllText(file);
                    var lines = content.Split('\n');

                    var opcodes = new List<string>();
                    foreach (var line in lines)
                    {
                        var match = Regex.Match(line,
                            @"^\s*(\w+)\s*=\s*(\d+)\s*,?\s*(?://\s*(.*))?$");
                        if (match.Success)
                        {
                            var name = match.Groups[1].Value;
                            var value = match.Groups[2].Value;
                            var comment = match.Groups[3].Success ? $" — {match.Groups[3].Value}" : "";
                            opcodes.Add($"{name} = {value}{comment}");
                        }
                    }

                    OpcodesBox.Text = $">>> {Path.GetFileName(file)}\n{new string('-', 40)}\n" +
                        string.Join(Environment.NewLine, opcodes.Take(200));
                    return;
                }
                catch (Exception ex)
                {
                    OpcodesBox.Text = $"Erro: {ex.Message}";
                    return;
                }
            }
        }

        OpcodesBox.Text = "Arquivo protocolcodes.h não encontrado.\n" +
            "Caminhos procurados:\n" + string.Join(Environment.NewLine, protocolFiles);
    }

    private void LoadServerInfoButton_Click(object sender, RoutedEventArgs e)
    {
        var canaryDir = Path.GetFullPath(Path.Combine(
            AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", "..", "Canary"));

        var configFiles = new[] {
            Path.Combine(canaryDir, "config.lua"),
            Path.Combine(canaryDir, "data", "config.lua"),
        };

        foreach (var file in configFiles)
        {
            if (File.Exists(file))
            {
                try
                {
                    var content = File.ReadAllText(file);
                    var lines = content.Split('\n');

                    var info = new List<string>
                    {
                        $">>> {Path.GetFileName(file)}",
                        new string('-', 40)
                    };

                    foreach (var line in lines)
                    {
                        var match = Regex.Match(line,
                            @"^\s*(\w+)\s*=\s*(.+?)\s*(?:--.*)?$");
                        if (match.Success)
                        {
                            var key = match.Groups[1].Value;
                            var val = match.Groups[2].Value.Trim();
                            if (key.Contains("ip") || key.Contains("port") ||
                                key.Contains("name") || key.Contains("world") ||
                                key.Contains("protocol") || key.Contains("version") ||
                                key.Contains("status") || key.Contains("motd"))
                            {
                                info.Add($"{key} = {val}");
                            }
                        }
                    }

                    ServerInfoBox.Text = string.Join(Environment.NewLine, info);
                    return;
                }
                catch (Exception ex) { System.Diagnostics.Debug.WriteLine("[Grimorio] " + ex.Message); }
            }
        }

        ServerInfoBox.Text = "Nenhum arquivo config.lua encontrado.";
    }
}
