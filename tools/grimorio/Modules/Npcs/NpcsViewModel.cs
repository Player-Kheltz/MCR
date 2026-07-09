using System.Collections.ObjectModel;
using System.Net.Http;
using System.Net.Http.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using MCR.Grimorio.Core;
using MCR.Grimorio.Models;
using MCR.Grimorio.Services;

namespace MCR.Grimorio.Modules.Npcs;

public class NpcsViewModel : ViewModelBase
{
    private readonly HttpClient _http;
    private readonly MCRGenerationService _mcr;

    private string _searchText = "";
    private string _npcName = "";
    private string _npcDescription = "";
    private string _npcHealth = "100";
    private string _npcLookType = "128";
    private string _dialogText = "";
    private string _luaPreview = "";
    private bool _isBusy;
    private string _statusText = "";
    private string _selectedNpc = "";

    public string SearchText { get => _searchText; set { SetProperty(ref _searchText, value); _ = SearchNpcsAsync(); } }
    public string NpcName { get => _npcName; set { SetProperty(ref _npcName, value); UpdatePreview(); } }
    public string NpcDescription { get => _npcDescription; set { SetProperty(ref _npcDescription, value); UpdatePreview(); } }
    public string NpcHealth { get => _npcHealth; set { SetProperty(ref _npcHealth, value); UpdatePreview(); } }
    public string NpcLookType { get => _npcLookType; set { SetProperty(ref _npcLookType, value); UpdatePreview(); } }
    public string DialogText { get => _dialogText; set { SetProperty(ref _dialogText, value); UpdatePreview(); } }
    public string LuaPreview { get => _luaPreview; set => SetProperty(ref _luaPreview, value); }
    public bool IsBusy { get => _isBusy; set => SetProperty(ref _isBusy, value); }
    public string StatusText { get => _statusText; set => SetProperty(ref _statusText, value); }
    public string SelectedNpc { get => _selectedNpc; set => SetProperty(ref _selectedNpc, value); }

    public ObservableCollection<string> NpcList { get; } = new();
    public ObservableCollection<string> FilteredNpcs { get; } = new();

    public ICommand GerarMcrCommand { get; }
    public ICommand SalvarCommand { get; }
    public ICommand RefreshListCommand { get; }

    public NpcsViewModel()
    {
        _http = new HttpClient { BaseAddress = new Uri("http://127.0.0.1:7778"), Timeout = TimeSpan.FromSeconds(10) };
        _mcr = new MCRGenerationService();

        GerarMcrCommand = new RelayCommand(async () => await GerarViaMcrAsync(), () => !IsBusy);
        SalvarCommand = new RelayCommand(async () => await SalvarNpcAsync(), () => !IsBusy && !string.IsNullOrEmpty(NpcName));
        RefreshListCommand = new RelayCommand(async () => await CarregarListaAsync(), () => !IsBusy);

        _ = CarregarListaAsync();
    }

    public async Task CarregarListaAsync()
    {
        try
        {
            var ws = await _http.GetFromJsonAsync<WorldStatus>("/world/status");
            NpcList.Clear();
            if (ws?.State?.Npcs is not null)
            {
                foreach (var n in ws.State.Npcs)
                    NpcList.Add(n);
            }
            FilterList();
        }
        catch
        {
            StatusText = "Bridge API offline";
        }
    }

    private void FilterList()
    {
        FilteredNpcs.Clear();
        var filtro = SearchText?.ToLower() ?? "";
        foreach (var n in NpcList)
        {
            if (string.IsNullOrEmpty(filtro) || n.ToLower().Contains(filtro))
                FilteredNpcs.Add(n);
        }
    }

    private async Task SearchNpcsAsync()
    {
        if (string.IsNullOrEmpty(SearchText))
            await CarregarListaAsync();
        else
            FilterList();
        await Task.CompletedTask;
    }

    public void SelecionarNpc(string nome)
    {
        SelectedNpc = nome;
        NpcName = nome;
        NpcDescription = $"NPC {nome} do servidor Canary";
        NpcHealth = "100";
        NpcLookType = "128";
        DialogText = $"-- Dialogo para {nome}\nkeywordHandler:addKeyword({{\"oi\"}}, StdModule.say, {{npc = npcType, text = \"Ola!\"}})\n";
        UpdatePreview();
    }

    private void UpdatePreview()
    {
        var name = string.IsNullOrEmpty(NpcName) ? "NPC" : NpcName;
        var health = int.TryParse(NpcHealth, out var h) ? h : 100;
        var look = int.TryParse(NpcLookType, out var l) ? l : 128;

        LuaPreview =
            $"-- {name}.lua\n" +
            $"local internalNpcName = \"{name}\"\n" +
            $"local npcType = Game.createNpcType(internalNpcName)\n" +
            $"local npcConfig = {{}}\n" +
            $"\n" +
            $"npcConfig.name = internalNpcName\n" +
            $"npcConfig.description = \"{NpcDescription}\"\n" +
            $"npcConfig.health = {health}\n" +
            $"npcConfig.maxHealth = {health}\n" +
            $"npcConfig.walkInterval = 2000\n" +
            $"npcConfig.walkRadius = 2\n" +
            $"npcConfig.outfit = {{lookType = {look}}}\n" +
            $"npcConfig.flags = {{floorchange = false}}\n" +
            $"\n" +
            $"local keywordHandler = KeywordHandler:new()\n" +
            $"{DialogText}\n" +
            $"npcType:register(npcConfig)\n";
    }

    private async Task GerarViaMcrAsync()
    {
        IsBusy = true;
        StatusText = "Gerando NPC via MCR...";
        try
        {
            var tema = await ShowInputDialogAsync();
            if (string.IsNullOrEmpty(tema)) return;

            var resultado = await _mcr.GerarNpcAsync(tema);
            if (resultado is not null && resultado.IsSuccess)
            {
                NpcName = resultado.Nome ?? tema;
                NpcDescription = $"Gerado via MCR: {tema}";
                StatusText = $"NPC {resultado.Nome} gerado via {resultado.Modo}";
                await CarregarListaAsync();
            }
            else
            {
                StatusText = $"Erro: {resultado?.Mensagem ?? "Falha desconhecida"}";
            }
        }
        catch (Exception ex)
        {
            StatusText = $"Erro: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }

    private static async Task<string?> ShowInputDialogAsync()
    {
        var tcs = new TaskCompletionSource<string?>();
        var input = new System.Windows.Controls.TextBox
        {
            FontSize = 14,
            Padding = new System.Windows.Thickness(6, 4, 6, 4),
            Text = ""
        };

        var dialog = new Window
        {
            Title = "Gerar NPC via MCR",
            Width = 400,
            Height = 200,
            WindowStartupLocation = WindowStartupLocation.CenterOwner,
            Owner = Application.Current.MainWindow,
            Background = new SolidColorBrush(Color.FromRgb(0x1E, 0x1E, 0x1E)),
            Foreground = Brushes.White,
        };

        var stack = new StackPanel { Margin = new System.Windows.Thickness(16) };
        stack.Children.Add(new System.Windows.Controls.TextBlock
        {
            Text = "Digite um tema/conceito para o NPC:",
            FontSize = 14,
            Foreground = Brushes.White,
            Margin = new System.Windows.Thickness(0, 0, 0, 12)
        });
        stack.Children.Add(input);

        var btnPanel = new StackPanel
        {
            Orientation = System.Windows.Controls.Orientation.Horizontal,
            HorizontalAlignment = System.Windows.HorizontalAlignment.Right,
            Margin = new System.Windows.Thickness(0, 12, 0, 0)
        };
        var cancelBtn = new System.Windows.Controls.Button
        {
            Content = "Cancelar",
            Width = 80,
            Height = 30,
            Margin = new System.Windows.Thickness(0, 0, 8, 0),
            IsCancel = true,
            Cursor = System.Windows.Input.Cursors.Hand,
        };
        var okBtn = new System.Windows.Controls.Button
        {
            Content = "Gerar",
            Width = 80,
            Height = 30,
            IsDefault = true,
            Cursor = System.Windows.Input.Cursors.Hand,
        };
        btnPanel.Children.Add(cancelBtn);
        btnPanel.Children.Add(okBtn);
        stack.Children.Add(btnPanel);
        dialog.Content = stack;

        okBtn.Click += (s, e) => { tcs.TrySetResult(input.Text); dialog.Close(); };
        cancelBtn.Click += (s, e) => { tcs.TrySetResult(null); dialog.Close(); };

        dialog.ShowDialog();
        return await tcs.Task;
    }

    private async Task SalvarNpcAsync()
    {
        StatusText = "Salvamento direto em breve.";
        await Task.CompletedTask;
    }

    protected override void DisposeManaged()
    {
        _http.Dispose();
        _mcr.Dispose();
    }
}
