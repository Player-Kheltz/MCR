using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Microsoft.Win32;
using MCR.Grimorio.Core.Services;
using MCR.Grimorio.Data;

namespace MCR.Grimorio.Modules.Settings;

public partial class SettingsView : UserControl
{
    private readonly SettingsService _settingsService;
    private readonly DatabaseService _dbService;

    public SettingsView()
    {
        InitializeComponent();
        var app = Application.Current as App;
        _settingsService = app?.SettingsService ?? new SettingsService();
        _dbService = app?.DatabaseService ?? new DatabaseService();
        LoadSettings();

        if (app != null)
        {
            SpriteStatusText.Text = app.SpriteStatus;
        }
    }

    private void LoadSettings()
    {
        var s = _settingsService.Settings;
        ServerPathBox.Text = s.ServerPath;
        ServerExeBox.Text = string.IsNullOrEmpty(s.ServerExeName)
            ? "canary-sln.exe"
            : s.ServerExeName;
        OtclientPathBox.Text = s.OtclientPath;
        OtbmPathBox.Text = s.OtbmPath;
        DbHostBox.Text = s.MySql.Host;
        DbPortBox.Text = s.MySql.Port.ToString();
        DbNameBox.Text = s.MySql.Database;
        DbUserBox.Text = s.MySql.User;
        DbPassBox.Password = s.MySql.Password;
    }

    private void BrowseServerButton_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new Ookii.Dialogs.Wpf.VistaFolderBrowserDialog();
        if (dialog.ShowDialog() == true)
        {
            ServerPathBox.Text = dialog.SelectedPath;
            _settingsService.SetServerPath(dialog.SelectedPath);

            // Auto-detect executable
            var app = Application.Current as App;
            if (app != null)
            {
                var exePath = app.DetectCanaryExe(dialog.SelectedPath);
                if (!string.IsNullOrEmpty(exePath))
                    ServerExeBox.Text = Path.GetFileName(exePath);

                app.ItemsXmlPath = app.FindItemsXml(dialog.SelectedPath);
                app.OtbmPath = app.FindOtbm(dialog.SelectedPath);
                OtbmPathBox.Text = app.OtbmPath;
            }
        }
    }

    private void BrowseExeButton_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFileDialog
        {
            Filter = "Executáveis (*.exe)|*.exe",
            InitialDirectory = ServerPathBox.Text
        };
        if (dialog.ShowDialog() == true)
        {
            ServerExeBox.Text = Path.GetFileName(dialog.FileName);
        }
    }

    private void BrowseOtclientButton_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new Ookii.Dialogs.Wpf.VistaFolderBrowserDialog();
        if (dialog.ShowDialog() == true)
        {
            OtclientPathBox.Text = dialog.SelectedPath;
            _settingsService.SetOtclientPath(dialog.SelectedPath);

            // Reload sprites
            var app = Application.Current as App;
            if (app != null)
            {
                app.ReinitializeSpriteSheets();
                SpriteStatusText.Text = app.SpriteStatus;
            }
        }
    }

    private void BrowseOtbmButton_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFileDialog
        {
            Filter = "Mapa OTBM (*.otbm)|*.otbm",
            InitialDirectory = ServerPathBox.Text
        };
        if (dialog.ShowDialog() == true)
        {
            OtbmPathBox.Text = dialog.FileName;
            _settingsService.SetOtbmPath(dialog.FileName);
            var app = Application.Current as App;
            if (app != null) app.OtbmPath = dialog.FileName;
        }
    }

    private async void TestConnectionButton_Click(object sender, RoutedEventArgs e)
    {
        _dbService.Configure(
            DbHostBox.Text,
            int.TryParse(DbPortBox.Text, out var p) ? p : 3306,
            DbUserBox.Text,
            DbPassBox.Password,
            DbNameBox.Text);

        var ok = await _dbService.ConnectAsync();
        StatusBar.Visibility = Visibility.Visible;
        StatusText.Text = ok ? "✅ Conexão estabelecida com sucesso!" : "❌ Falha na conexão — verifique as credenciais.";
        StatusText.Foreground = new SolidColorBrush(ok
            ? Color.FromRgb(0x4E, 0xC9, 0xB0)
            : Color.FromRgb(0xF4, 0x47, 0x47));

        if (ok) _dbService.Disconnect();
    }

    private void SaveButton_Click(object sender, RoutedEventArgs e)
    {
        var settings = new AppSettings
        {
            ServerPath = ServerPathBox.Text,
            ServerExeName = ServerExeBox.Text,
            OtclientPath = OtclientPathBox.Text,
            OtbmPath = OtbmPathBox.Text,
            MySql = new MySqlSettings
            {
                Host = DbHostBox.Text,
                Port = int.TryParse(DbPortBox.Text, out var p) ? p : 3306,
                Database = DbNameBox.Text,
                User = DbUserBox.Text,
                Password = DbPassBox.Password,
            }
        };

        _settingsService.Save(settings);

        // Reinitialize everything
        var app = Application.Current as App;
        if (app != null)
        {
            app.ReinitializeAll();
            SpriteStatusText.Text = app.SpriteStatus;
            OtbmPathBox.Text = app.OtbmPath;
        }

        StatusBar.Visibility = Visibility.Visible;
        StatusText.Text = "✅ Configuração salva. Sprites e caminhos recarregados!";
        StatusText.Foreground = new SolidColorBrush(Color.FromRgb(0x4E, 0xC9, 0xB0));
    }
}
