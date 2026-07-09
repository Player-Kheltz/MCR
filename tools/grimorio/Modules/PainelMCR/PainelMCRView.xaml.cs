using System.Windows;
using System.Windows.Controls;

namespace MCR.Grimorio.Modules.PainelMCR;

public partial class PainelMCRView : UserControl
{
    private readonly PainelMCRViewModel _viewModel;

    public PainelMCRView()
    {
        InitializeComponent();
        _viewModel = new PainelMCRViewModel();
        DataContext = _viewModel;
        Loaded += async (s, e) => await _viewModel.RefreshAsync();
    }

    private void ToggleTestPanel(object sender, RoutedEventArgs e)
    {
        TestExpander.IsExpanded = !TestExpander.IsExpanded;
    }
}
