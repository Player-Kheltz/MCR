using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace MCR.Grimorio.Controls;

public class NavButton : Button
{
    public static readonly DependencyProperty IconProperty =
        DependencyProperty.Register(nameof(Icon), typeof(string), typeof(NavButton));

    public static readonly DependencyProperty LabelProperty =
        DependencyProperty.Register(nameof(Label), typeof(string), typeof(NavButton));

    public string Icon
    {
        get => (string)GetValue(IconProperty);
        set => SetValue(IconProperty, value);
    }

    public string Label
    {
        get => (string)GetValue(LabelProperty);
        set => SetValue(LabelProperty, value);
    }

    static NavButton()
    {
        DefaultStyleKeyProperty.OverrideMetadata(
            typeof(NavButton),
            new FrameworkPropertyMetadata(typeof(NavButton)));
    }
}
