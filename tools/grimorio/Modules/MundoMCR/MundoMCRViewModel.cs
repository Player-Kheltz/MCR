using System.Collections.ObjectModel;
using System.Windows.Input;
using MCR.Grimorio.Core;
using MCR.Grimorio.Models;

namespace MCR.Grimorio.Modules.MundoMCR;

public class MundoMCRViewModel : ViewModelBase
{
    private readonly Services.MCRWorldService _service;

    private double _entropia;
    private int _npcsVivos;
    private int _npcsMortos;
    private int _totalMonstros;
    private int _totalQuests;
    private double _thresholdMetacog;
    private string _ultimaAcao = "—";
    private string _statusConexao = "Conectando...";
    private bool _isConnected;
    private bool _isBusy;
    private string _perturbType = "death";
    private string _perturbTarget = "";
    private string _perturbKiller = "";
    private string _resultadoPerturb = "";

    public double Entropia { get => _entropia; set => SetProperty(ref _entropia, value); }
    public int NpcsVivos { get => _npcsVivos; set => SetProperty(ref _npcsVivos, value); }
    public int NpcsMortos { get => _npcsMortos; set => SetProperty(ref _npcsMortos, value); }
    public int TotalMonstros { get => _totalMonstros; set => SetProperty(ref _totalMonstros, value); }
    public int TotalQuests { get => _totalQuests; set => SetProperty(ref _totalQuests, value); }
    public double ThresholdMetacog { get => _thresholdMetacog; set => SetProperty(ref _thresholdMetacog, value); }
    public string UltimaAcao { get => _ultimaAcao; set => SetProperty(ref _ultimaAcao, value); }
    public string StatusConexao { get => _statusConexao; set => SetProperty(ref _statusConexao, value); }
    public bool IsConnected { get => _isConnected; set => SetProperty(ref _isConnected, value); }
    public bool IsBusy { get => _isBusy; set => SetProperty(ref _isBusy, value); }
    public string PerturbType { get => _perturbType; set => SetProperty(ref _perturbType, value); }
    public string PerturbTarget { get => _perturbTarget; set => SetProperty(ref _perturbTarget, value); }
    public string PerturbKiller { get => _perturbKiller; set => SetProperty(ref _perturbKiller, value); }
    public string ResultadoPerturb { get => _resultadoPerturb; set => SetProperty(ref _resultadoPerturb, value); }

    public string EntropiaBarWidth => $"{Entropia * 100:F0}%";
    public string EntropiaCor => Entropia switch
    {
        < 0.2 => "#F44747",
        < 0.7 => "#4EC9B0",
        _ => "#FFA500",
    };
    public string NpcsDisplay => $"{NpcsVivos} vivos / {NpcsMortos} mortos";

    public ObservableCollection<WorldEvent> Eventos { get; } = new();
    public ObservableCollection<WorldEvent> Decisoes { get; } = new();

    public ICommand RefreshCommand { get; }
    public ICommand PerturbarCommand { get; }

    public MundoMCRViewModel()
    {
        _service = new Services.MCRWorldService();
        RefreshCommand = new RelayCommand(async () => await RefreshAllAsync(), () => !IsBusy);
        PerturbarCommand = new RelayCommand(async () => await SendPerturbationAsync(), () => !IsBusy && IsConnected);
    }

    public async Task RefreshAllAsync()
    {
        IsBusy = true;
        try
        {
            var status = await _service.GetStatusAsync();
            if (status is null)
            {
                StatusConexao = "Bridge API Offline";
                IsConnected = false;
                return;
            }

            IsConnected = true;
            StatusConexao = "Online";

            // Zona 1: Telemetria
            NpcsVivos = status.State?.TotalNpcs ?? 0;
            NpcsMortos = 0; // TODO: ler do world_state quando tiver contagem
            TotalMonstros = status.State?.TotalNpcs ?? 0; // placeholder
            TotalQuests = status.Observer?.TotalEventos ?? 0;
            ThresholdMetacog = 0.75; // placeholder — MCRMeta retorna
            UltimaAcao = status.Observer?.CooldownRestante > 0 ? "COMPENSAR" : "AGUARDANDO";
            Entropia = 0.5; // placeholder — MCRMeta retorna

            OnPropertyChanged(nameof(EntropiaBarWidth));
            OnPropertyChanged(nameof(EntropiaCor));
            OnPropertyChanged(nameof(NpcsDisplay));

            // Zona 2: Eventos
            var eventsResp = await _service.GetEventsAsync();
            if (eventsResp?.Eventos is not null)
            {
                Eventos.Clear();
                foreach (var e in eventsResp.Eventos)
                    Eventos.Add(e);
            }
        }
        finally
        {
            IsBusy = false;
        }
    }

    private async Task SendPerturbationAsync()
    {
        IsBusy = true;
        ResultadoPerturb = "";
        try
        {
            var request = new Models.PerturbRequest
            {
                Evento = new Models.PerturbEvent
                {
                    Type = PerturbType,
                    Target = PerturbTarget,
                    Killer = PerturbKiller,
                },
                DeltaH = PerturbType == "death" ? -0.3 : 0.1,
            };
            var success = await _service.SendPerturbationAsync(request);
            ResultadoPerturb = success
                ? "✔ Perturbação enviada com sucesso"
                : "✘ Falha ao enviar perturbação";
        }
        catch (Exception ex)
        {
            ResultadoPerturb = $"✘ Erro: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
            await RefreshAllAsync();
        }
    }
}
