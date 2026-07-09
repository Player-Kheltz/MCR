using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using MCR.Grimorio.Core.Services;
using MCR.Grimorio.Data;

namespace MCR.Grimorio.Modules.Monsters;

public class MonsterListItem
{
    public string Name { get; set; } = "";
    public int Exp { get; set; }
    public int Hp { get; set; }
    public ImageSource? Sprite { get; set; }
    public MonsterData? Data { get; set; }
}

public partial class MonstersView : UserControl
{
    private readonly MonsterService _monsterService;
    private readonly SpriteSheetService? _sheets;
    private List<MonsterData> _currentMonsters = new();

    public MonstersView()
    {
        InitializeComponent();
        _monsterService = new MonsterService();
        _sheets = (Application.Current as App)?.SpriteSheets;
        Loaded += (s, e) => LoadCategories();
    }

    private void LoadCategories()
    {
        var cats = _monsterService.GetCategories();
        CategoryList.Items.Clear();
        foreach (var c in cats) CategoryList.Items.Add(c);

        var total = _monsterService.GetAll().Count;
        StatusText.Text = $"{total} monstros em {cats.Count} categorias";
        if (cats.Count > 0) CategoryList.SelectedIndex = 0;
    }

    private void CategoryList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (CategoryList.SelectedItem is string cat)
        {
            _currentMonsters = _monsterService.GetByCategory(cat);
            ListTitle.Text = $"{cat} ({_currentMonsters.Count})";
            MonsterList.ItemsSource = _currentMonsters.Select(m => new MonsterListItem
            {
                Name = m.Name,
                Exp = m.Experience,
                Hp = m.Health,
                Sprite = _sheets?.GetSprite(m.LookType),
                Data = m
            }).ToList();
            DetailPanel.Visibility = Visibility.Collapsed;
        }
    }

    private void SearchBox_TextChanged(object sender, TextChangedEventArgs e)
    {
        var q = SearchBox.Text?.Trim();
        if (string.IsNullOrEmpty(q))
        {
            if (CategoryList.SelectedItem is string cat)
            {
                _currentMonsters = _monsterService.GetByCategory(cat);
                ListTitle.Text = $"{cat} ({_currentMonsters.Count})";
                MonsterList.ItemsSource = _currentMonsters.Select(m => new MonsterListItem
                {
                    Name = m.Name,
                    Exp = m.Experience,
                    Hp = m.Health,
                    Sprite = _sheets?.GetSprite(m.LookType),
                    Data = m
                }).ToList();
            }
            return;
        }

        var results = _monsterService.Search(q);
        ListTitle.Text = $"Busca: \"{q}\" ({results.Count})";
        MonsterList.ItemsSource = results.Select(m => new MonsterListItem
        {
            Name = m.Name,
            Exp = m.Experience,
            Hp = m.Health,
            Sprite = _sheets?.GetSprite(m.LookType),
            Data = m
        }).ToList();
    }

    private void MonsterList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (MonsterList.SelectedItem is not MonsterListItem item || item.Data == null)
        {
            DetailPanel.Visibility = Visibility.Collapsed;
            return;
        }

        DetailPanel.Visibility = Visibility.Visible;
        var m = item.Data;

        DetailSprite.Source = _sheets?.GetSprite(m.LookType);
        DetailName.Text = m.Name;
        DetailDesc.Text = string.IsNullOrEmpty(m.Description) ? "Sem descrição" : m.Description;

        DHP.Text = m.Health.ToString("N0");
        DExp.Text = m.Experience.ToString("N0");
        DSpeed.Text = m.Speed.ToString("N0");

        DArmor.Text = m.Defenses.Armor.ToString();
        DDefense.Text = m.Defenses.Defense.ToString();
        DMana.Text = m.ManaCost > 0 ? m.ManaCost.ToString() : "—";

        LootList.ItemsSource = m.Loot.Select(l => new
        {
            l.Id,
            Name = $"Item {l.Id}",
            ChancePct = l.Chance / 10000.0,
            l.MaxCount
        }).ToList();

        AttackList.ItemsSource = m.Attacks.Select(a => new
        {
            a.Name,
            Damage = $"{a.MinDamage} a {a.MaxDamage}",
            Interval = $"{a.Interval}ms"
        }).ToList();

        var elements = new List<object>();
        AddElement(elements, "Físico", m.Elements.Physical);
        AddElement(elements, "Fogo", m.Elements.Fire);
        AddElement(elements, "Gelo", m.Elements.Ice);
        AddElement(elements, "Terra", m.Elements.Earth);
        AddElement(elements, "Energia", m.Elements.Energy);
        AddElement(elements, "Sagrado", m.Elements.Holy);
        AddElement(elements, "Morte", m.Elements.Death);

        ElementsPanel.ItemsSource = elements;
    }

    private static void AddElement(List<object> list, string name, int value)
    {
        if (value == 0) return;
        var isResist = value > 0;
        list.Add(new
        {
            Text = $"{name} {(value > 0 ? "+" : "")}{value}%",
            Bg = isResist ? new SolidColorBrush(Color.FromArgb(40, 78, 201, 176))
                          : new SolidColorBrush(Color.FromArgb(40, 244, 71, 71)),
            Fg = isResist ? new SolidColorBrush(Color.FromRgb(78, 201, 176))
                          : new SolidColorBrush(Color.FromRgb(244, 71, 71))
        });
    }
}
