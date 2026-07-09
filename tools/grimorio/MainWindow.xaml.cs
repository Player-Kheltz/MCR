using System.Windows;
using System.Windows.Media;
using MCR.Grimorio.Controls;
using MCR.Grimorio.Services;

namespace MCR.Grimorio;

public partial class MainWindow : Window
{
    private readonly SolidColorBrush _activeBrush = new(Color.FromRgb(0x00, 0x7A, 0xCC));
    private NavButton? _activeNav;
    private readonly WorldStatusService _worldStatus;

    public MainWindow()
    {
        InitializeComponent();

        _worldStatus = new WorldStatusService();
        _worldStatus.OnStatusChanged += UpdateEntropyBar;

        NavigateToPainelMCR(null, null!);
    }

    private void UpdateEntropyBar()
    {
        Dispatcher.Invoke(() =>
        {
            var pct = _worldStatus.EntropiaPercent;
            EntropyBarInner.Width = EntropyBarOuter.ActualWidth * pct / 100.0;
            var color = _worldStatus.EntropiaCor;
            EntropyBarInner.Background = new SolidColorBrush(
                (Color)ColorConverter.ConvertFromString(color));
        });
    }

    private void SetActiveNav(NavButton button)
    {
        if (_activeNav != null)
            _activeNav.Background = Brushes.Transparent;
        _activeNav = button;
        _activeNav.Background = _activeBrush;
    }

    private void NavigateToPainelMCR(object sender, RoutedEventArgs e)
    { SetActiveNav(NavPainelMCR); MainContent.Content = new Modules.PainelMCR.PainelMCRView(); }
    private void NavigateToDatabase(object sender, RoutedEventArgs e)
    { SetActiveNav(NavDatabase); MainContent.Content = new Modules.Database.DatabaseView(); }
    private void NavigateToMonsters(object sender, RoutedEventArgs e)
    { SetActiveNav(NavMonsters); MainContent.Content = new Modules.Monsters.MonstersView(); }
    private void NavigateToNpcs(object sender, RoutedEventArgs e)
    { SetActiveNav(NavNpcs); MainContent.Content = new Modules.Npcs.NpcsView(); }
    private void NavigateToScripts(object sender, RoutedEventArgs e)
    { SetActiveNav(NavScripts); MainContent.Content = new Modules.Scripts.ScriptsView(); }
    private void NavigateToConfig(object sender, RoutedEventArgs e)
    { SetActiveNav(NavConfig); MainContent.Content = new Modules.Config.ConfigView(); }
    private void NavigateToMapa(object sender, RoutedEventArgs e)
    { SetActiveNav(NavMap); MainContent.Content = new Modules.Map.MapView(); }
    private void NavigateToItems(object sender, RoutedEventArgs e)
    { SetActiveNav(NavItems); MainContent.Content = new Modules.Items.ItemsView(); }
    private void NavigateToMCRSkills(object sender, RoutedEventArgs e)
    { SetActiveNav(NavMCRSkills); MainContent.Content = new Modules.MCRSkills.MCRSkillsView(); }
    private void NavigateToQuests(object sender, RoutedEventArgs e)
    { SetActiveNav(NavQuests); MainContent.Content = new Modules.Quests.QuestsView(); }
    private void NavigateToNPCDialogue(object sender, RoutedEventArgs e)
    { SetActiveNav(NavNPCDialogue); MainContent.Content = new Modules.NPCDialogue.NPCDialogueView(); }
    private void NavigateToSettings(object sender, RoutedEventArgs e)
    { SetActiveNav(NavSettings); MainContent.Content = new Modules.Settings.SettingsView(); }
}
