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

        // Auto-load se já houver caminho configurado
        var itemsPath = app?.ItemsXmlPath;
        if (!string.IsNullOrEmpty(itemsPath) && File.Exists(itemsPath))
        {
            Loaded += async (s, e) => await LoadItemsAsync();
        }
        else
        {
            StatusText.Text = "items.xml não encontrado. Configure o caminho do servidor em Ajustes.";
        }
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
            var path = (Application.Current as App)?.ItemsXmlPath ?? _settings.GetItemsXmlPath();
            if (string.IsNullOrEmpty(path) || !File.Exists(path))
            {
                StatusText.Text = "items.xml não encontrado. Configure o caminho em Ajustes.";
                return;
            }

            var doc = XDocument.Load(path);
            _allItems = doc.Root!.Elements("item")
                .Select(ItemData.FromXml)
                .Where(i => i.Id > 0)
                .ToList();

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

            ApplyFilter();
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

    private async void LoadButton_Click(object sender, RoutedEventArgs e) => await LoadItemsAsync();

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
                try { sprite = _sheets?.GetSprite(i.SpriteId); } catch { }
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
