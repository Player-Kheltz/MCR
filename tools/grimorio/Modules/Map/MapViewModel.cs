using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Windows.Input;
using MCR.Grimorio.Core;
using MCR.Grimorio.Data;
using MCR.Grimorio.Models;

namespace MCR.Grimorio.Modules.Map;

public class MapViewModel : ViewModelBase
{
    private OtbmMapData? _mapData;
    private int _selectedFloor = 7;
    private int _zoomLevel = 2;
    private bool _showGridLines;
    private string _mouseCoords = "";
    private string _statusText = "Nenhum mapa carregado";
    private bool _isLoading;
    private bool _heatmapVisible;
    private readonly MinimapRenderer _renderer = new();
    public List<EntropyPoint> EntropyGrid { get; set; } = new();
    public double EntropyMax { get; set; } = 1.0;
    public double EntropyMin { get; set; } = 0.0;
    public int EntropyTotalEvents { get; set; }

    public OtbmMapData? MapData
    {
        get => _mapData;
        set
        {
            if (SetProperty(ref _mapData, value))
            {
                _renderer.InvalidateCache();
                StatusText = value != null
                    ? $"Mapa: {value.Name} ({value.Width}x{value.Height})"
                    : "Nenhum mapa carregado";
                if (value != null && value.Floors.Count > 0)
                    SelectedFloor = value.Floors.Keys.Min();
                RequestRender?.Invoke();
            }
        }
    }

    public int SelectedFloor
    {
        get => _selectedFloor;
        set
        {
            var clamped = Math.Clamp(value, 0, 15);
            if (SetProperty(ref _selectedFloor, clamped))
            {
                _renderer.InvalidateCache();
                RequestRender?.Invoke();
            }
        }
    }

    public int ZoomLevel
    {
        get => _zoomLevel;
        set
        {
            var clamped = Math.Clamp(value, 1, 16);
            if (SetProperty(ref _zoomLevel, clamped))
            {
                _renderer.InvalidateCache();
                RequestRender?.Invoke();
            }
        }
    }

    public bool ShowGridLines
    {
        get => _showGridLines;
        set
        {
            if (SetProperty(ref _showGridLines, value))
            {
                _renderer.InvalidateCache();
                RequestRender?.Invoke();
            }
        }
    }

    public string MouseCoords
    {
        get => _mouseCoords;
        set => SetProperty(ref _mouseCoords, value);
    }

    public string StatusText
    {
        get => _statusText;
        set => SetProperty(ref _statusText, value);
    }

    public bool IsLoading
    {
        get => _isLoading;
        set => SetProperty(ref _isLoading, value);
    }

    public bool HeatmapVisible
    {
        get => _heatmapVisible;
        set
        {
            if (SetProperty(ref _heatmapVisible, value))
            {
                if (!value) EntropyGrid.Clear();
                RequestRender?.Invoke();
            }
        }
    }

    public bool HasMap => _mapData != null;
    public string ZoomLabel => $"{ZoomLevel}x";
    public string FloorLabel => $"Piso {SelectedFloor}";

    public ObservableCollection<PlayerPosition> Players { get; } = new();
    public MinimapRenderer Renderer => _renderer;

    public Action? RequestRender { get; set; }

    public ICommand LoadMapCommand { get; }
    public ICommand FloorUpCommand { get; }
    public ICommand FloorDownCommand { get; }
    public ICommand ZoomInCommand { get; }
    public ICommand ZoomOutCommand { get; }
    public ICommand ToggleGridCommand { get; }

    public MapViewModel()
    {
        LoadMapCommand = new RelayCommand(async () => await LoadMap());
        FloorUpCommand = new RelayCommand(() => { SelectedFloor++; return Task.CompletedTask; });
        FloorDownCommand = new RelayCommand(() => { SelectedFloor--; return Task.CompletedTask; });
        ZoomInCommand = new RelayCommand(() => { ZoomLevel++; return Task.CompletedTask; });
        ZoomOutCommand = new RelayCommand(() => { ZoomLevel--; return Task.CompletedTask; });
        ToggleGridCommand = new RelayCommand(() => { ShowGridLines = !ShowGridLines; return Task.CompletedTask; });
    }

    public bool LoadMapFromPath(string path)
    {
        if (!File.Exists(path)) return false;
        var data = OtbmReader.Load(path);
        if (data != null)
        {
            MapData = data;
            return true;
        }
        StatusText = "Falha ao carregar: " + path;
        return false;
    }

    private async Task LoadMap()
    {
        var dlg = new Microsoft.Win32.OpenFileDialog
        {
            Filter = "OTBM (*.otbm)|*.otbm",
            Title = "Abrir mapa OTBM"
        };
        if (dlg.ShowDialog() != true) return;
        IsLoading = true;
        try
        {
            var data = OtbmReader.Load(dlg.FileName);
            if (data != null)
                MapData = data;
            else
                StatusText = "Falha ao carregar mapa";
        }
        catch (Exception ex)
        {
            StatusText = $"Erro: {ex.Message}";
            System.Diagnostics.Debug.WriteLine($"[MapView] {ex}");
        }
        finally
        {
            IsLoading = false;
        }
    }

    public void SetMouseCoords(int tileX, int tileY)
    {
        MouseCoords = $"Tile: {tileX}, {tileY}, {SelectedFloor}";
    }

    public void ZoomIn()
    {
        ZoomLevel = Math.Min(ZoomLevel + 1, 16);
    }

    public void ZoomOut()
    {
        ZoomLevel = Math.Max(ZoomLevel - 1, 1);
    }
}
