using System.Windows.Controls;

namespace MCR.Grimorio.Modules.Npcs;

public partial class NpcsView : UserControl
{
    private readonly NpcsViewModel _viewModel;

    public NpcsView()
    {
        InitializeComponent();
        _viewModel = new NpcsViewModel();
        DataContext = _viewModel;
    }

    private void NpcList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (e.AddedItems.Count > 0 && e.AddedItems[0] is string nome)
            _viewModel.SelecionarNpc(nome);
    }
}
