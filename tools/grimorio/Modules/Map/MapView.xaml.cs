using System.IO;
using System.Net.Http;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Text.Json;
using MCR.Grimorio.Data;
using MCR.Grimorio.Models;

namespace MCR.Grimorio.Modules.Map;

public partial class MapView : UserControl
{
    private readonly MapViewModel _viewModel;
    private readonly HttpClient _http = new();
    private bool _heatmapActive;

    public MapView()
    {
        InitializeComponent();
        _viewModel = new MapViewModel();
        DataContext = _viewModel;

        _viewModel.RequestRender += OnRequestRender;

        // Auto-load do .otbm se configurado
        var app = Application.Current as App;
        var otbmPath = app?.OtbmPath;
        if (!string.IsNullOrEmpty(otbmPath) && File.Exists(otbmPath))
        {
            _viewModel.LoadMapFromPath(otbmPath);
        }
        else
        {
            StatusText.Text = "Mapa não encontrado. Configure em Ajustes.";
        }

        // Polling de jogadores online via API
        _ = RefreshPlayersLoop();
    }

    private void OnRequestRender()
    {
        Dispatcher.Invoke(() =>
        {
            try
            {
                var map = _viewModel.MapData;
                if (map == null) return;

                var bmp = _viewModel.Renderer.Render(
                    map, _viewModel.SelectedFloor,
                    _viewModel.ZoomLevel, _viewModel.ShowGridLines);
                if (bmp != null)
                {
                    _viewModel.Renderer.DrawPlayers(
                        bmp, map, _viewModel.SelectedFloor,
                        _viewModel.ZoomLevel, _viewModel.Players.ToList());

                    if (_viewModel.HeatmapVisible && _viewModel.EntropyGrid.Count > 0)
                    {
                        _viewModel.Renderer.DrawEntropyGrid(
                            bmp, map, _viewModel.SelectedFloor,
                            _viewModel.ZoomLevel, _viewModel.EntropyGrid,
                            _viewModel.EntropyMin, _viewModel.EntropyMax);
                    }

                    MapImage.Source = bmp;
                    MapImage.Width = bmp.PixelWidth;
                    MapImage.Height = bmp.PixelHeight;
                    var heatInfo = _viewModel.HeatmapVisible
                        ? $" | Heatmap: {_viewModel.EntropyTotalEvents} eventos"
                        : "";
                    CoordText.Text =
                        $"Mapa: {map.Width}x{map.Height} | " +
                        $"Floor {_viewModel.SelectedFloor} | " +
                        $"Zoom {_viewModel.ZoomLevel}x | " +
                        $"{_viewModel.Players.Count} players" + heatInfo;
                }
            }
            catch (Exception ex)
            {
                StatusText.Text = $"Render erro: {ex.Message}";
                System.Diagnostics.Debug.WriteLine($"[MapView] Render: {ex}");
            }
        });
    }

    private async Task RefreshPlayersLoop()
    {
        while (true)
        {
            try
            {
                _http.Timeout = TimeSpan.FromSeconds(3);
                var json = await _http.GetStringAsync("http://127.0.0.1:8081/api/players");
                var players = JsonSerializer.Deserialize<List<PlayerPosition>>(json);
                if (players != null)
                {
                    Dispatcher.Invoke(() =>
                    {
                        _viewModel.Players.Clear();
                        foreach (var p in players) _viewModel.Players.Add(p);
                    });
                }
            }
            catch (Exception ex) { System.Diagnostics.Debug.WriteLine("[Grimorio] " + ex.Message); }
            await Task.Delay(5000);
            _viewModel.Renderer.InvalidateCache();
            _viewModel.RequestRender?.Invoke();
        }
    }

    private async Task RefreshHeatmapLoop()
    {
        while (_heatmapActive)
        {
            try
            {
                _http.Timeout = TimeSpan.FromSeconds(5);
                var json = await _http.GetStringAsync("http://127.0.0.1:7778/world/entropy_grid?minutes=10");
                var response = JsonSerializer.Deserialize<EntropyGridResponse>(json,
                    new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower });
                if (response != null && response.Grid != null)
                {
                    Dispatcher.Invoke(() =>
                    {
                        _viewModel.EntropyGrid = response.Grid;
                        _viewModel.EntropyMax = response.MaxEntropy;
                        _viewModel.EntropyMin = response.MinEntropy;
                        _viewModel.EntropyTotalEvents = response.TotalEvents;
                        _viewModel.Renderer.InvalidateCache();
                        _viewModel.RequestRender?.Invoke();
                    });
                }
            }
            catch
            {
                StatusText.Text = _viewModel.HeatmapVisible
                    ? "Heatmap: Bridge API indisponivel"
                    : StatusText.Text;
            }
            await Task.Delay(10000);
        }
    }

    private void ScrollViewer_PreviewMouseWheel(object sender, MouseWheelEventArgs e)
    {
        if (Keyboard.Modifiers == ModifierKeys.Control)
        {
            if (e.Delta > 0) _viewModel.ZoomIn();
            else _viewModel.ZoomOut();
            e.Handled = true;
        }
    }

    private void MapImage_MouseMove(object sender, MouseEventArgs e)
    {
        var pos = e.GetPosition(MapImage);
        _viewModel.SetMouseCoords((int)(pos.X / _viewModel.ZoomLevel), (int)(pos.Y / _viewModel.ZoomLevel));
    }

    private void FloorUp_Click(object sender, RoutedEventArgs e) => _viewModel.SelectedFloor++;
    private void FloorDown_Click(object sender, RoutedEventArgs e) => _viewModel.SelectedFloor--;
    private void ZoomIn_Click(object sender, RoutedEventArgs e) => _viewModel.ZoomIn();
    private void ZoomOut_Click(object sender, RoutedEventArgs e) => _viewModel.ZoomOut();
    private void ToggleGrid_Click(object sender, RoutedEventArgs e) => _viewModel.ShowGridLines = !_viewModel.ShowGridLines;

    private void ToggleHeatmap_Click(object sender, RoutedEventArgs e)
    {
        _heatmapActive = _viewModel.HeatmapVisible;
        if (_heatmapActive)
        {
            _ = RefreshHeatmapLoop();
        }
        else
        {
            _viewModel.EntropyGrid.Clear();
            _viewModel.Renderer.InvalidateCache();
            _viewModel.RequestRender?.Invoke();
        }
    }

    private void LoadMap_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new Microsoft.Win32.OpenFileDialog { Filter = "OTBM (*.otbm)|*.otbm" };
        if (dialog.ShowDialog() == true)
        {
            _viewModel.LoadMapFromPath(dialog.FileName);
            var app = Application.Current as App;
            if (app != null) app.OtbmPath = dialog.FileName;
        }
    }
}
