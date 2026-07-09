using System.Windows.Controls;
using System.Windows.Threading;

namespace MCR.Grimorio.Modules.MundoMCR;

public partial class MundoMCRView : UserControl
{
    private readonly MundoMCRViewModel _viewModel;
    private readonly DispatcherTimer _refreshTimer;

    public MundoMCRView()
    {
        InitializeComponent();

        _viewModel = new MundoMCRViewModel();
        DataContext = _viewModel;

        _refreshTimer = new DispatcherTimer
        {
            Interval = TimeSpan.FromSeconds(5)
        };
        _refreshTimer.Tick += async (s, e) => await _viewModel.RefreshAllAsync();

        Loaded += async (s, e) =>
        {
            _refreshTimer.Start();
            await _viewModel.RefreshAllAsync();
        };

        Unloaded += (s, e) =>
        {
            _refreshTimer.Stop();
        };
    }
}
