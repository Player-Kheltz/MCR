using System.ComponentModel;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using System.Timers;
using MCR.Grimorio.Models;
using Timer = System.Timers.Timer;

namespace MCR.Grimorio.Services;

public class WorldStatusService : IDisposable
{
    private readonly HttpClient _http;
    private readonly Timer _timer;
    private const string BaseUrl = "http://127.0.0.1:7778";

    private bool _serverOnline;
    private double _entropia;
    private int _npcsVivos;
    private int _totalEventos;
    private bool _isBridgeOnline;

    public event Action? OnStatusChanged;

    public bool ServerOnline { get => _serverOnline; private set => SetField(ref _serverOnline, value); }
    public double Entropia { get => _entropia; private set => SetField(ref _entropia, value); }
    public int NpcsVivos { get => _npcsVivos; private set => SetField(ref _npcsVivos, value); }
    public int TotalEventos { get => _totalEventos; private set => SetField(ref _totalEventos, value); }
    public bool IsBridgeOnline { get => _isBridgeOnline; private set => SetField(ref _isBridgeOnline, value); }

    public string EntropiaCor => !IsBridgeOnline ? "#555555" :
        Entropia < 0.2 ? "#F44747" :
        Entropia < 0.7 ? "#4EC9B0" :
        Entropia < 0.9 ? "#FFA500" :
        "#F44747";

    public double EntropiaPercent => Entropia * 100;

    public WorldStatusService()
    {
        _http = new HttpClient { BaseAddress = new Uri(BaseUrl), Timeout = TimeSpan.FromSeconds(5) };
        _timer = new Timer(5000);
        _timer.Elapsed += OnTimerElapsed;
        _timer.AutoReset = true;
        _timer.Start();
        _ = PollAsync();
    }

    private async void OnTimerElapsed(object? sender, ElapsedEventArgs e) => await PollAsync();

    private async Task PollAsync()
    {
        try
        {
            var status = await _http.GetFromJsonAsync<WorldStatus>("/world/status");
            if (status is null)
            {
                IsBridgeOnline = false;
                NotifyChanged();
                return;
            }

            IsBridgeOnline = true;
            ServerOnline = true;
            Entropia = 0.5; // placeholder ate MCRMeta expor
            NpcsVivos = status.State?.TotalNpcs ?? 0;
            TotalEventos = status.Observer?.TotalEventos ?? 0;
            NotifyChanged();
        }
        catch
        {
            IsBridgeOnline = false;
            NotifyChanged();
        }
    }

    private void NotifyChanged() => OnStatusChanged?.Invoke();

    private event PropertyChangedEventHandler? _propertyChanged;
    public event PropertyChangedEventHandler? PropertyChanged
    {
        add => _propertyChanged += value;
        remove => _propertyChanged -= value;
    }

    private void SetField<T>(ref T field, T value)
    {
        if (EqualityComparer<T>.Default.Equals(field, value)) return;
        field = value;
        _propertyChanged?.Invoke(this, new PropertyChangedEventArgs(null));
    }

    public void Dispose()
    {
        _timer.Stop();
        _timer.Dispose();
        _http.Dispose();
    }
}
