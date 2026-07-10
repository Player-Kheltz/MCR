using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Xml.Linq;
using MCR.Grimorio.Core.Services;
using MCR.Grimorio.Data;

namespace MCR.Grimorio.Modules.Items;

public partial class ItemsView : UserControl
{
    private readonly SettingsService _settings;
    private readonly SpriteSheetService? _sheets;
    private List<ItemData> _allItems = new();
    private bool _loading;

    public ItemsView()
    {
        InitializeComponent();
        var app = Application.Current as App;
        _settings = app?.SettingsService ?? new SettingsService();
        _sheets = app?.SpriteSheets;

        // Tenta carregar automaticamente (usa timer para garantir UI pronta)
        var timer = new System.Windows.Threading.DispatcherTimer { Interval = TimeSpan.FromMilliseconds(100) };
        timer.Tick += async (s, e) =>
        {
            timer.Stop();
            await LoadItemsAsync();
        };
        timer.Start();
    }

    private async System.Threading.Tasks.Task LoadItemsAsync()
    {
        if (_loading) return;
        _loading = true;
        LoadButton.IsEnabled = false;
        StatusText.Text = "Carregando itens...";

        await System.Threading.Tasks.Task.Delay(30);

        try
        {
            // Tenta varios caminhos ate achar o arquivo
            var path = (Application.Current as App)?.ItemsXmlPath;
            if (string.IsNullOrEmpty(path) || !File.Exists(path))
                path = _settings.GetItemsXmlPath();
            if (!File.Exists(path))
                path = @"E:\MCR\server\data\items\items.xml";
            if (!File.Exists(path))
            {
                StatusText.Text = "items.xml não encontrado. Clique em 📂 para selecionar.";
                return;
            }

            var doc = XDocument.Load(path);
            _allItems = doc.Root!.Elements("item")
                .Select(ItemData.FromXml)
                .Where(i => i.Id > 0)
                .ToList();

            System.Diagnostics.Debug.WriteLine($"[Items] Carregados {_allItems.Count} itens do XML");

            // Se nao carregou nada, tenta com fallback
            if (_allItems.Count == 0)
            {
                StatusText.Text = "Nenhum item encontrado no arquivo XML";
                return;
            }

            var types = _allItems
                .Where(i => !string.IsNullOrEmpty(i.Type))
                .Select(i => i.Type)
                .Distinct()
                .OrderBy(t => t)
                .ToList();

            TypeFilter.Items.Clear();
            TypeFilter.Items.Add(new ComboBoxItem { Content = "Todos", IsSelected = true });
            foreach (var t in types)
                TypeFilter.Items.Add(new ComboBoxItem { Content = t });

            Dispatcher.Invoke(() => ApplyFilter());
            StatusText.Text = $"{_allItems.Count} itens carregados";
        }
        catch (Exception ex)
        {
            StatusText.Text = $"Erro: {ex.Message}";
        }
        finally
        {
            _loading = false;
            LoadButton.IsEnabled = true;
        }
    }

    private async void LoadButton_Click(object sender, RoutedEventArgs e)
    {
        await LoadItemsAsync();
    }

    private void SearchBox_TextChanged(object sender, TextChangedEventArgs e) => ApplyFilter();

    private void TypeFilter_SelectionChanged(object sender, SelectionChangedEventArgs e) => ApplyFilter();

    private void ApplyFilter()
    {
        try
        {
            if (_loading || _allItems.Count == 0) return;

            var search = SearchBox.Text?.Trim().ToLower() ?? "";
            var typeFilter = (TypeFilter.SelectedItem as ComboBoxItem)?.Content?.ToString();

            var filtered = _allItems.AsEnumerable();

            if (!string.IsNullOrEmpty(search))
                filtered = filtered.Where(i =>
                    i.Name.ToLower().Contains(search) ||
                    i.Id.ToString().Contains(search));

            if (!string.IsNullOrEmpty(typeFilter) && typeFilter != "Todos")
                filtered = filtered.Where(i =>
                    i.Type.Equals(typeFilter, StringComparison.OrdinalIgnoreCase));

            var list = filtered.Select(i =>
            {
                ImageSource? sprite = null;
                try
                {
                    sprite = _sheets?.GetSprite(i.SpriteId);
                    if (sprite == null)
                    {
                        // Placeholder: retangulo com o ID do sprite
                        var placeholder = new System.Windows.Media.DrawingGroup();
                        placeholder.Children.Add(new System.Windows.Media.GeometryDrawing
                        {
                            Geometry = new System.Windows.Media.RectangleGeometry(new System.Windows.Rect(0, 0, 32, 32)),
                            Brush = System.Windows.Media.Brushes.Transparent,
                            Pen = new System.Windows.Media.Pen(System.Windows.Media.Brushes.Gray, 1)
                        });
                        var dib = new System.Windows.Media.Imaging.RenderTargetBitmap(32, 32, 96, 96, System.Windows.Media.PixelFormats.Default);
                        var drawingVisual = new System.Windows.Media.DrawingVisual();
                        using (var dc = drawingVisual.RenderOpen())
                            dc.DrawDrawing(placeholder);
                        dib.Render(drawingVisual);
                        sprite = dib;
                    }
                }
                catch { }
                return new ItemListItem
                {
                    Id = i.Id,
                    Name = i.DisplayName,
                    Type = i.Type,
                    Sprite = sprite,
                    Data = i
                };
            }).ToList();

            ItemList.ItemsSource = list;

            // Auto-select first item
            if (list.Count > 0 && ItemList.SelectedItem == null)
                ItemList.SelectedItem = list[0];

            StatusText.Text = $"{_allItems.Count} itens | exibindo {list.Count}";
        }
        catch (Exception ex)
        {
            StatusText.Text = $"Erro: {ex.Message}";
        }
    }

    private void ItemList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (ItemList.SelectedItem is ItemListItem item)
        {
            var i = item.Data;

            // Detail panel
            DetailScroll.Visibility = Visibility.Visible;
            EmptyPanel.Visibility = Visibility.Collapsed;

            var sprite = _sheets?.GetSpriteScaled(i.SpriteId, 64);
            DetailSprite.Source = sprite;

            DetailName.Text = i.DisplayName;
            DetailId.Text = $"ID: {i.Id}";
            DetailTypeWeight.Text = $"{i.Type ?? "Desconhecido"} | {i.Weight:F1} oz";

            if (!string.IsNullOrEmpty(i.Description))
            {
                DetailDescPanel.Visibility = Visibility.Visible;
                DetailDescription.Text = i.Description;
            }
            else
            {
                DetailDescPanel.Visibility = Visibility.Collapsed;
            }

            StatsPanel.Visibility = Visibility.Visible;
            DetailAttack.Text = i.Attack > 0 ? i.Attack.ToString() : "—";
            DetailDefense.Text = i.Defense > 0 ? i.Defense.ToString() : "—";
            DetailArmor.Text = i.Armor > 0 ? i.Armor.ToString() : "—";

            if (i.ContainerSize > 0)
            {
                ContainerPanel.Visibility = Visibility.Visible;
                DetailContainerSize.Text = i.ContainerSize.ToString();
            }
            else
            {
                ContainerPanel.Visibility = Visibility.Collapsed;
            }

            // Scroll to top
            DetailScroll.ScrollToTop();
        }
        else
        {
            DetailScroll.Visibility = Visibility.Collapsed;
            EmptyPanel.Visibility = Visibility.Visible;
        }
    }
}

public class ItemListItem
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public string Type { get; set; } = "";
    public ImageSource? Sprite { get; set; }
    public ItemData Data { get; set; } = null!;
}
