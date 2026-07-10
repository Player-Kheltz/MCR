using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Threading;
using MCR.Grimorio.Core.Services;

namespace MCR.Grimorio.Modules.Dashboard;

public partial class DashboardView : UserControl
{
    private readonly IServerService _serverService;
    private readonly IDatabaseService _databaseService;
    private readonly DashboardViewModel _viewModel;
    private readonly DispatcherTimer _refreshTimer;

    public DashboardView()
    {
        InitializeComponent();

        _serverService = ServiceProvider.Resolve<IServerService>();
        _databaseService = ServiceProvider.Resolve<IDatabaseService>();
        _viewModel = new DashboardViewModel(_serverService, _databaseService);
        DataContext = _viewModel;

        _refreshTimer = new DispatcherTimer
        {
            Interval = TimeSpan.FromSeconds(3)
        };
        _refreshTimer.Tick += async (s, e) => await RefreshStatusAsync();

        StartButton.Click += async (s, e) => await _serverService.StartAsync();
        StopButton.Click += async (s, e) => await _serverService.StopAsync();
        RestartButton.Click += async (s, e) => await _serverService.RestartAsync();
        RefreshButton.Click += async (s, e) => await RefreshStatusAsync();
        ClearLogButton.Click += (s, e) => LogList.Items.Clear();
        DbConnectButton.Click += async (s, e) => await ConnectDatabaseAsync();
        OpenFolderButton.Click += (s, e) =>
        {
            if (Directory.Exists(_serverService.ServerPath))
                Process.Start("explorer.exe", _serverService.ServerPath);
        };

        var app = Application.Current as App;
        SpriteStatus.Text = app?.SpriteStatus ?? "—";

        _serverService.OnLogLine += line =>
        {
            Dispatcher.Invoke(() =>
            {
                LogList.Items.Add(line);
                if (LogList.Items.Count > 500)
                    LogList.Items.RemoveAt(0);
                LogScrollViewer.ScrollToEnd();
            });
        };

        PathText.Text = _serverService.ServerPath;

        Loaded += async (s, e) =>
        {
            _refreshTimer.Start();
            await RefreshStatusAsync();
        };
    }

    private async Task RefreshStatusAsync()
    {
        try
        {
            await _viewModel.RefreshStatus();

            var status = _serverService.GetStatus();

            StatusIndicator.Fill = new SolidColorBrush(
                status.IsRunning
                    ? Color.FromRgb(0x4E, 0xC9, 0xB0)
                    : Color.FromRgb(0xF4, 0x47, 0x47));
            StatusText.Text = status.IsRunning ? "Online" : "Parado";
            StatusText.Foreground = new SolidColorBrush(
                status.IsRunning
                    ? Color.FromRgb(0x4E, 0xC9, 0xB0)
                    : Color.FromRgb(0xF4, 0x47, 0x47));
            PidText.Text = status.IsRunning
                ? $"PID: {status.Pid}"
                : "PID: ---";
            PlayersText.Text = status.PlayersOnline.ToString();

            if (status.IsRunning && status.StartedAt != default)
            {
                var uptime = DateTime.Now - status.StartedAt;
                if (uptime.TotalHours >= 1)
                    UptimeText.Text = $"{(int)uptime.TotalHours}h {uptime.Minutes}m";
                else if (uptime.TotalMinutes >= 1)
                    UptimeText.Text = $"{(int)uptime.TotalMinutes}m {uptime.Seconds}s";
                else
                    UptimeText.Text = $"{uptime.TotalSeconds:F0}s";
            }
            else
            {
                UptimeText.Text = "---";
            }

            UpdateDbIndicator();
        }
        catch (Exception ex) { System.Diagnostics.Debug.WriteLine("[Grimorio] " + ex.Message); }
    }

    private async Task ConnectDatabaseAsync()
    {
        if (_databaseService.IsConnected)
        {
            _databaseService.Disconnect();
            UpdateDbIndicator();
            return;
        }

        DbConnectButton.IsEnabled = false;
        DbConnectButton.Content = "Conectando...";

        var success = await _databaseService.ConnectAsync();
        UpdateDbIndicator();

        DbConnectButton.Content = success ? "Desconectar" : "Conectar";
        DbConnectButton.IsEnabled = true;

        if (!success)
        {
            MessageBox.Show(
                "Não foi possível conectar ao banco de dados.\n" +
                "Verifique se o MySQL está rodando em localhost:3306\n" +
                "e se as credenciais estão corretas.",
                "Erro de Conexão",
                MessageBoxButton.OK,
                MessageBoxImage.Warning);
        }
    }

    private void UpdateDbIndicator()
    {
        var connected = _databaseService.IsConnected;
        DbIndicator.Fill = new SolidColorBrush(connected
            ? Color.FromRgb(0x4E, 0xC9, 0xB0)
            : Color.FromRgb(0xF4, 0x47, 0x47));
        DbStatusText.Text = connected ? "Conectado" : "Desconectado";
        DbStatusText.Foreground = new SolidColorBrush(connected
            ? Color.FromRgb(0x4E, 0xC9, 0xB0)
            : Color.FromRgb(0x85, 0x85, 0x85));
    }
}
