using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Windows.Media;
using MCR.Grimorio.Data;

namespace MCR.Grimorio.Modules.Items;

public class ItemDetailViewModel : INotifyPropertyChanged
{
    private ItemData? _item;
    private ImageSource? _sprite;

    public event PropertyChangedEventHandler? PropertyChanged;

    public ItemData? Item
    {
        get => _item;
        set
        {
            if (_item == value) return;
            _item = value;
            NotifyAll();
        }
    }

    public ImageSource? Sprite
    {
        get => _sprite;
        set
        {
            if (_sprite == value) return;
            _sprite = value;
            Notify(nameof(Sprite));
        }
    }

    public bool HasItem => _item != null;
    public string DisplayName => _item?.DisplayName ?? "";
    public int Id => _item?.Id ?? 0;
    public string Type => _item?.Type ?? "";
    public string Description => _item?.Description ?? "";
    public int Weight => _item?.Weight ?? 0;
    public int Attack => _item?.Attack ?? 0;
    public int Defense => _item?.Defense ?? 0;
    public int Armor => _item?.Armor ?? 0;
    public int ContainerSize => _item?.ContainerSize ?? 0;
    public bool HasAttack => _item?.Attack > 0;
    public bool HasDefense => _item?.Defense > 0;
    public bool HasArmor => _item?.Armor > 0;
    public bool HasContainerSize => _item?.ContainerSize > 0;
    public bool HasWeight => _item?.Weight > 0;
    public bool HasDescription => !string.IsNullOrEmpty(_item?.Description);
    public bool HasType => !string.IsNullOrEmpty(_item?.Type);

    private void NotifyAll()
    {
        Notify(nameof(HasItem));
        Notify(nameof(DisplayName));
        Notify(nameof(Id));
        Notify(nameof(Type));
        Notify(nameof(Description));
        Notify(nameof(Weight));
        Notify(nameof(Attack));
        Notify(nameof(Defense));
        Notify(nameof(Armor));
        Notify(nameof(ContainerSize));
        Notify(nameof(HasAttack));
        Notify(nameof(HasDefense));
        Notify(nameof(HasArmor));
        Notify(nameof(HasContainerSize));
        Notify(nameof(HasWeight));
        Notify(nameof(HasDescription));
        Notify(nameof(HasType));
    }

    private void Notify(string propertyName)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }
}
