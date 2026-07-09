using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;

namespace MCR.Grimorio.Modules.Database;

public partial class DatabaseView : UserControl
{
    private readonly Core.Services.DatabaseService _db;
    private List<string> _allTables = new();
    private bool _loading;

    public DatabaseView()
    {
        InitializeComponent();
        _db = ((App)Application.Current).DatabaseService;
        _db.OnConnectionChanged += connected =>
        {
            if (connected) Dispatcher.Invoke(async () => await LoadTablesAsync());
        };

        Loaded += async (s, e) =>
        {
            if (_db.IsConnected) await LoadTablesAsync();
        };
    }

    private async Task LoadTablesAsync()
    {
        if (_loading) return;
        _loading = true;

        try
        {
            _allTables = await _db.GetTablesAsync();
            _allTables.Sort();
            ApplyTableFilter();
        }
        finally
        {
            _loading = false;
        }
    }

    private void ApplyTableFilter()
    {
        var filter = TableSearchBox.Text?.Trim().ToLower() ?? "";
        TableList.Items.Clear();

        foreach (var table in _allTables)
        {
            if (string.IsNullOrEmpty(filter) ||
                table.Contains(filter))
            {
                TableList.Items.Add(table);
            }
        }
    }

    private void TableSearchBox_TextChanged(object sender, TextChangedEventArgs e)
    {
        ApplyTableFilter();
    }

    private async void TableList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (TableList.SelectedItem is not string table) return;

        TableTitle.Text = $"Tabela: {table}";
        DataGrid.ItemsSource = null;

        try
        {
            var rows = await _db.GetRowsAsync(table, 200);
            if (rows.Count == 0) return;

            var dt = new System.Data.DataTable();
            foreach (var key in rows[0].Keys)
                dt.Columns.Add(key);

            foreach (var row in rows)
            {
                var dr = dt.NewRow();
                foreach (var kv in row)
                    dr[kv.Key] = kv.Value;
                dt.Rows.Add(dr);
            }

            DataGrid.ItemsSource = dt.DefaultView;
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Erro ao carregar tabela: {ex.Message}");
        }
    }

    private async void SearchButton_Click(object sender, RoutedEventArgs e)
    {
        var search = SearchBox.Text?.Trim();
        if (string.IsNullOrEmpty(search)) return;

        TableTitle.Text = $"Busca: \"{search}\"";
        DataGrid.ItemsSource = null;

        try
        {
            var results = await _db.SearchPlayersAsync(search);
            if (results.Count == 0)
            {
                MessageBox.Show("Nenhum jogador encontrado.");
                return;
            }

            var dt = new System.Data.DataTable();
            foreach (var key in results[0].Keys)
                dt.Columns.Add(key);

            foreach (var row in results)
            {
                var dr = dt.NewRow();
                foreach (var kv in row)
                    dr[kv.Key] = kv.Value;
                dt.Rows.Add(dr);
            }

            DataGrid.ItemsSource = dt.DefaultView;
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Erro na busca: {ex.Message}");
        }
    }
}
