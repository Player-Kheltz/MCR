using System.Collections.ObjectModel;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using System.Windows.Input;
using MCR.Grimorio.Core;
using MCR.Grimorio.Models;
using MCR.Grimorio.Services;

namespace MCR.Grimorio.Modules.PainelMCR;

public class PainelMCRViewModel : ViewModelBase
{
    private readonly HttpClient _http;
    private readonly WorldStatusService _worldStatus;
    private readonly System.Timers.Timer _pollTimer;

    private bool _serverOnline;
    private string _serverStatusText = "Verificando...";
    private bool _isBusy;
    private string _perturbType = "death";
    private string _perturbTarget = "";
    private string _perturbKiller = "";
    private string _resultadoPerturb = "";

    public bool ServerOnline { get => _serverOnline; set => SetProperty(ref _serverOnline, value); }
    public string ServerStatusText { get => _serverStatusText; set => SetProperty(ref _serverStatusText, value); }
    public bool IsBusy { get => _isBusy; set => SetProperty(ref _isBusy, value); }
    public string PerturbType { get => _perturbType; set => SetProperty(ref _perturbType, value); }
    public string PerturbTarget { get => _perturbTarget; set => SetProperty(ref _perturbTarget, value); }
    public string PerturbKiller { get => _perturbKiller; set => SetProperty(ref _perturbKiller, value); }
    public string ResultadoPerturb { get => _resultadoPerturb; set => SetProperty(ref _resultadoPerturb, value); }

    public ObservableCollection<WorldEvent> Eventos { get; } = new();

    public ICommand RefreshCommand { get; }
    public ICommand PerturbarCommand { get; }

    public PainelMCRViewModel()
    {
        _http = new HttpClient { BaseAddress = new Uri("http://127.0.0.1:7778"), Timeout = TimeSpan.FromSeconds(5) };
        _worldStatus = new WorldStatusService();

        RefreshCommand = new RelayCommand(async () => await RefreshAsync(), () => !IsBusy);
        PerturbarCommand = new RelayCommand(async () => await SendPerturbAsync(), () => !IsBusy);

        _pollTimer = new System.Timers.Timer(5000);
        _pollTimer.Elapsed += async (s, e) => await RefreshAsync();
        _pollTimer.AutoReset = true;
        _pollTimer.Start();
    }

    public async Task RefreshAsync()
    {
        IsBusy = true;
        try
        {
            // Server status
            try
            {
                var resp = await _http.GetStringAsync("/status");
                ServerOnline = resp.Contains("online");
                ServerStatusText = ServerOnline ? "Online" : "Offline";
            }
            catch
            {
                ServerOnline = false;
                ServerStatusText = "Offline";
            }

            // Events
            try
            {
                var eventsResp = await _http.GetFromJsonAsync<WorldEventsResponse>("/world/events");
                if (eventsResp?.Eventos is not null)
                {
                    Eventos.Clear();
                    foreach (var e in eventsResp.Eventos)
                        Eventos.Add(e);
                }
            }
            catch { }
        }
        finally
        {
            IsBusy = false;
        }
    }

    private async Task SendPerturbAsync()
    {
        IsBusy = true;
        ResultadoPerturb = "";
        try
        {
            var request = new PerturbRequest
            {
                Evento = new PerturbEvent
                {
                    Type = PerturbType,
                    Target = PerturbTarget,
                    Killer = PerturbKiller,
                },
                DeltaH = PerturbType == "death" ? -0.3 : 0.1,
            };
            var json = JsonSerializer.Serialize(request, new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower
            });
            var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");
            var response = await _http.PostAsync("/world/perturb", content);
            ResultadoPerturb = response.IsSuccessStatusCode
                ? "✔ Perturbação enviada"
                : "✘ Falha ao enviar";
        }
        catch (Exception ex)
        {
            ResultadoPerturb = $"✘ Erro: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
            await RefreshAsync();
        }
    }

    protected override void DisposeManaged()
    {
        _pollTimer.Stop();
        _pollTimer.Dispose();
        _worldStatus.Dispose();
        _http.Dispose();
    }
}
