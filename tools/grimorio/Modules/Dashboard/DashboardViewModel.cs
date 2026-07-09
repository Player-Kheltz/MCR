using System.Windows.Input;
using MCR.Grimorio.Core;
using MCR.Grimorio.Core.Services;

namespace MCR.Grimorio.Modules.Dashboard;

public class DashboardViewModel : ViewModelBase
{
    private readonly IServerService _serverService;
    private readonly IDatabaseService _databaseService;
    private readonly ServerMetricsService _metricsService;

    private string _serverStatus = "Desconectado";
    private string _uptime = "0s";
    private int _playersOnline;
    private bool _isDbConnected;
    private string _lastLogLine = "";
    private bool _isBusy;

    private double _cpuPercent;
    private long _memoryMb;
    private string _tickTime = "—";
    private int _slowQueries;
    private int _activeThreads;

    public string ServerStatus { get => _serverStatus; set => SetProperty(ref _serverStatus, value); }
    public string Uptime { get => _uptime; set => SetProperty(ref _uptime, value); }
    public int PlayersOnline { get => _playersOnline; set => SetProperty(ref _playersOnline, value); }
    public bool IsDbConnected { get => _isDbConnected; set => SetProperty(ref _isDbConnected, value); }
    public string LastLogLine { get => _lastLogLine; set => SetProperty(ref _lastLogLine, value); }
    public bool IsBusy { get => _isBusy; set => SetProperty(ref _isBusy, value); }

    public double CpuPercent { get => _cpuPercent; set => SetProperty(ref _cpuPercent, value); }
    public long MemoryMb { get => _memoryMb; set => SetProperty(ref _memoryMb, value); }
    public string TickTime { get => _tickTime; set => SetProperty(ref _tickTime, value); }
    public int SlowQueries { get => _slowQueries; set => SetProperty(ref _slowQueries, value); }
    public int ActiveThreads { get => _activeThreads; set => SetProperty(ref _activeThreads, value); }

    public string CpuDisplay => $"{CpuPercent:F1}%";
    public string MemoryDisplay => $"{MemoryMb} MB";
    public string SlowQueriesDisplay => $"{SlowQueries}";

    public ICommand StartServerCommand { get; }
    public ICommand StopServerCommand { get; }
    public ICommand RestartServerCommand { get; }
    public ICommand RefreshStatusCommand { get; }

    public DashboardViewModel() : this(
        ServiceProvider.Resolve<IServerService>(),
        ServiceProvider.Resolve<IDatabaseService>())
    {
    }

    public DashboardViewModel(IServerService serverService, IDatabaseService databaseService)
    {
        _serverService = serverService;
        _databaseService = databaseService;
        _metricsService = new ServerMetricsService(serverService);

        StartServerCommand = new RelayCommand(async () => await StartServer(), () => !IsBusy);
        StopServerCommand = new RelayCommand(async () => await StopServer(), () => !IsBusy);
        RestartServerCommand = new RelayCommand(async () => await RestartServer(), () => !IsBusy);
        RefreshStatusCommand = new RelayCommand(async () => await RefreshStatus(), () => !IsBusy);

        _serverService.OnLogLine += line => LastLogLine = line;
        _serverService.OnStatusChanged += OnServerStatusChanged;
    }

    private void OnServerStatusChanged(ServerStatus status)
    {
        ServerStatus = status.IsRunning ? "Online" : "Offline";
        PlayersOnline = status.PlayersOnline;
        if (status.IsRunning)
        {
            var ts = TimeSpan.FromMilliseconds(status.UptimeMs);
            Uptime = ts.TotalHours >= 1
                ? $"{ts.Hours}h {ts.Minutes}m"
                : $"{ts.Minutes}m {ts.Seconds}s";
        }
        else
        {
            Uptime = "0s";
        }
    }

    private async Task StartServer()
    {
        IsBusy = true;
        try
        {
            await _serverService.StartAsync();
        }
        finally
        {
            IsBusy = false;
        }
    }

    private async Task StopServer()
    {
        IsBusy = true;
        try
        {
            await _serverService.StopAsync();
        }
        finally
        {
            IsBusy = false;
        }
    }

    private async Task RestartServer()
    {
        IsBusy = true;
        try
        {
            await _serverService.RestartAsync();
        }
        finally
        {
            IsBusy = false;
        }
    }

    public async Task RefreshStatus()
    {
        IsBusy = true;
        try
        {
            var status = _serverService.GetStatus();
            OnServerStatusChanged(status);
            IsDbConnected = _databaseService.IsConnected;

            var metrics = _metricsService.GetMetrics();
            CpuPercent = metrics.CpuPercent;
            MemoryMb = metrics.MemoryMb;
            TickTime = metrics.TickTimeMs > 0 ? $"{metrics.TickTimeMs} ms" : "—";
            SlowQueries = metrics.SlowQueries;
            ActiveThreads = metrics.ActiveThreads;

            OnPropertyChanged(nameof(CpuDisplay));
            OnPropertyChanged(nameof(MemoryDisplay));
            OnPropertyChanged(nameof(SlowQueriesDisplay));
        }
        finally
        {
            IsBusy = false;
        }
    }
}
