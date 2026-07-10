using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using MCR.Grimorio.Core.Services;

namespace MCR.Grimorio.Modules.Config;

public partial class ConfigView : UserControl
{
    private readonly ConfigService _configService;
    private List<ConfigEntry> _allEntries = new();
    private ConfigEntry? _selectedEntry;

    public ConfigView()
    {
        InitializeComponent();
        _configService = new ConfigService();
        Loaded += (s, e) => LoadConfig();
    }

    private void LoadConfig()
    {
        try
        {
            if (!_configService.Exists)
            {
                StatusText.Text = "config.lua não encontrado";
                return;
            }

            _allEntries = _configService.ReadAll();
            ConfigList.ItemsSource = _allEntries;
            StatusText.Text = $"{_allEntries.Count} configurações";
        }
        catch (Exception ex)
        {
            StatusText.Text = $"Erro ao carregar configurações: {ex.Message}";
            System.Diagnostics.Debug.WriteLine($"[ConfigView] {ex}");
        }
    }

    private void SearchBox_TextChanged(object sender, TextChangedEventArgs e)
    {
        var q = SearchBox.Text?.Trim().ToLower() ?? "";
        ConfigList.ItemsSource = string.IsNullOrEmpty(q)
            ? _allEntries
            : _allEntries.Where(e =>
                e.Key.ToLower().Contains(q) ||
                (e.Description?.ToLower().Contains(q) ?? false) ||
                e.Value.ToLower().Contains(q)).ToList();
    }

    private void ConfigList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (ConfigList.SelectedItem is not ConfigEntry entry)
        {
            DetailPanel.Visibility = Visibility.Collapsed;
            return;
        }

        _selectedEntry = entry;
        DetailPanel.Visibility = Visibility.Visible;
        DetailKey.Text = entry.Key;
        DetailType.Text = entry.Type;
        ValueBox.Text = entry.Value;
        DetailDesc.Text = entry.Description ?? "Sem descrição";
        SaveButton.IsEnabled = true;
        SaveStatus.Visibility = Visibility.Collapsed;
    }

    private async void SaveButton_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedEntry == null) return;

        var newValue = ValueBox.Text?.Trim();
        if (string.IsNullOrEmpty(newValue)) return;

        var success = await _configService.SetValueAsync(_selectedEntry.Key, newValue);

        SaveStatus.Visibility = Visibility.Visible;
        SaveStatus.Foreground = new SolidColorBrush(success
            ? Color.FromRgb(0x4E, 0xC9, 0xB0)
            : Color.FromRgb(0xF4, 0x47, 0x47));
        SaveStatus.Text = success ? "✓ Salvo!" : "✗ Erro ao salvar";

        if (success)
        {
            _selectedEntry.Value = newValue;
            ConfigList.Items.Refresh();
        }
    }
}
