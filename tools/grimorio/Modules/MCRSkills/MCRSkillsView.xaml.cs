using System;
using System.Collections.Generic;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using MCR.Grimorio.Core.Detection;

namespace MCR.Grimorio.Modules.MCRSkills;

public partial class MCRSkillsView : UserControl
{
    public MCRSkillsView()
    {
        InitializeComponent();
        DetectionText.Text = new MCRDetector().GetDetectionSummary();
        SetupEffectParams();
    }

    private void EffectTypeBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        SetupEffectParams();
    }

    private void SetupEffectParams()
    {
        try
        {
            EffectParamsGrid.Children.Clear();
            EffectParamsGrid.RowDefinitions.Clear();
            EffectParamsGrid.ColumnDefinitions.Clear();

            for (int i = 0; i < 4; i++)
                EffectParamsGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

            EffectParamsGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            EffectParamsGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            var label = new TextBlock
        {
            Text = "Parâmetros do Efeito:",
            FontSize = 11,
            Foreground = FindResource("FgMutedBrush") as Brush
        };
        Grid.SetRow(label, 0);
        Grid.SetColumnSpan(label, 4);
        EffectParamsGrid.Children.Add(label);

        var effectType = ((ComboBoxItem)EffectTypeBox.SelectedItem)?.Content?.ToString() ?? "dano_extra";
        var fields = GetEffectFields(effectType);
        int col = 0, row = 1;
        foreach (var (fieldName, defaultValue) in fields)
        {
            var sp = new StackPanel
            {
                Margin = new Thickness(col > 0 ? 6 : 0, 4, 0, 0)
            };
            sp.Children.Add(new TextBlock
            {
                Text = fieldName,
                FontSize = 10,
                Foreground = FindResource("FgMutedBrush") as Brush
            });
            var tb = new TextBox
            {
                Name = "EP_" + fieldName.Replace(" ", "_").Replace("%", "pct"),
                Text = defaultValue,
                Margin = new Thickness(0, 2, 0, 0),
                Background = FindResource("BgDarkestBrush") as Brush,
                Foreground = FindResource("FgPrimaryBrush") as Brush,
                BorderThickness = new Thickness(0)
            };
            sp.Children.Add(tb);
            Grid.SetRow(sp, row);
            Grid.SetColumn(sp, col);
            EffectParamsGrid.Children.Add(sp);
            col++;
            if (col >= 4) { col = 0; row++; EffectParamsGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto }); }
        }
        }
        catch (Exception ex) { System.Diagnostics.Debug.WriteLine("[MCRSkills] " + ex.Message); }
    }

    private static List<(string, string)> GetEffectFields(string type)
    {
        return type switch
        {
            "dano_extra" => new() { ("percentual", "0.25"), ("multiplicador", "1.0") },
            "area_ground" => new() { ("centro", "jogador"), ("raio", "2"), ("percentual", "0.40"), ("magicEffect", "") },
            "area_target" => new() { ("raio", "2"), ("percentual", "0.50"), ("areaPercentual", "0.30") },
            "ricochete" => new() { ("percentual", "0.35"), ("raio", "3"), ("saltos", "2") },
            "knockback" => new() { ("comDano", "true"), ("percentual", "0.25"), ("distancia", "2") },
            "rajada" => new() { ("percentual", "0.18"), ("numProjeteis", "4"), ("intervaloMs", "200") },
            "corrente" => new() { ("percentual", "0.35"), ("raio", "2") },
            "finisher" => new() { ("percentual", "1.00"), ("sangramentoArea", "false") },
            "condicao" => new() { ("conditionType", "CONDITION_BLEEDING"), ("duration", "6000"), ("periodicDamage", "10"), ("comDano", "false") },
            "buff_speed" => new() { ("multiplier", "0.40"), ("durationMs", "700") },
            "buff_damage" => new() { ("percentExtra", "15"), ("buffHits", "3") },
            "life_leech" => new() { ("leechPercent", "8"), ("durationSec", "1") },
            "defesa_cura" => new() { ("percentual", "0"), ("reflect", "true"), ("reflectPercentual", "0.30") },
            "defesa_barreira" => new() { ("factor", "0.40"), ("durationMs", "2000") },
            "defesa_contra_ataque" => new() { ("percentual", "0.50") },
            "field" => new() { ("elemento", "COMBAT_FIREDAMAGE"), ("duration", "10000"), ("damagePerTick", "20") },
            "sinergia" => new() { ("dominioFilho", "23"), ("percentual", "0.30") },
            "storm" => new() { ("raio", "3"), ("dano", "0.8"), ("durationMs", "5000"), ("intervaloMs", "1000") },
            "orbit" => new() { ("raio", "2"), ("dano", "0.5"), ("numEsferas", "3"), ("durationMs", "6000") },
            "rain" => new() { ("raio", "4"), ("dano", "0.6"), ("numProjeteis", "8"), ("durationMs", "4000") },
            "pulse" => new() { ("raio", "3"), ("dano", "0.7"), ("intervaloMs", "800"), ("numPulsos", "3") },
            "trap" => new() { ("centro", "alvo"), ("raio", "2"), ("dano", "1.2"), ("markEffect", "CONST_ME_MAGIC_RED") },
            "summon" => new() { ("criatura", "demon"), ("quantidade", "1"), ("duracaoBaseMs", "15000") },
            "melee" => new() { ("dano", "1.0"), ("angulo", "0") },
            "projectile" => new() { ("dano", "1.5"), ("acertos", "3") },
            "beam" => new() { ("dano", "2.0"), ("range", "5") },
            "explosion_ring" => new() { ("raio", "3"), ("dano", "1.0"), ("knockback", "0") },
            _ => new() { ("percentual", "0.25") }
        };
    }

    private string GetEpValue(string name)
    {
        foreach (var child in EffectParamsGrid.Children)
        {
            if (child is StackPanel sp)
                foreach (var c in sp.Children)
                    if (c is TextBox tb && tb.Name == "EP_" + name.Replace(" ", "_").Replace("%", "pct"))
                        return tb.Text;
        }
        return "";
    }

    private void GenerateSkillBtn_Click(object sender, RoutedEventArgs e)
    {
        var name = SkillNameBox.Text.Trim();
        if (string.IsNullOrWhiteSpace(name)) name = "Nova Habilidade";

        var domainStr = ((ComboBoxItem)DomainIdBox.SelectedItem)?.Content?.ToString() ?? "1";
        var domainId = SafeExtractId(domainStr, "1");

        var skillType = ((ComboBoxItem)SkillTypeBox.SelectedItem)?.Content?.ToString() ?? "gatilho";
        var category = ((ComboBoxItem)CategoryBox.SelectedItem)?.Content?.ToString() ?? "single";
        var effectType = ((ComboBoxItem)EffectTypeBox.SelectedItem)?.Content?.ToString() ?? "dano_extra";
        var element = ((ComboBoxItem)ElementBox.SelectedItem)?.Content?.ToString() ?? "COMBAT_PHYSICALDAMAGE";
        var cor = ((ComboBoxItem)CorBox.SelectedItem)?.Content?.ToString() ?? "COR.DOM_COMBATE_LAMINAS";

        var cooldown = CooldownBox.Text.Trim();
        if (string.IsNullOrWhiteSpace(cooldown)) cooldown = "5";
        var minLevel = MinLevelBox.Text.Trim();
        if (string.IsNullOrWhiteSpace(minLevel)) minLevel = "5";
        var focoMin = FocoMinBox.Text.Trim();
        if (string.IsNullOrWhiteSpace(focoMin)) focoMin = "25";
        var desc = DescBox.Text.Trim();
        if (string.IsNullOrWhiteSpace(desc)) desc = "Uma habilidade poderosa.";

        var impeto = ImpetoBox.Text.Trim();
        if (string.IsNullOrWhiteSpace(impeto)) impeto = "1.2";
        var guarda = GuardaBox.Text.Trim();
        if (string.IsNullOrWhiteSpace(guarda)) guarda = "0.7";

        // Build efeitoConfig
        var efeitoConfigSb = new StringBuilder();
        efeitoConfigSb.Append($"        tipo = \"{effectType}\"");

        var isCastType = skillType == "gatilho";
        if (isCastType && effectType != "sinergia_escalonada")
        {
            foreach (var (field, _) in GetEffectFields(effectType))
            {
                if (field == "tipo") continue;
                var val = GetEpValue(field);
                if (string.IsNullOrEmpty(val)) continue;

                // Determine if the value is numeric or needs quotes
                if (field == "centro" || field == "conditionType" || field == "magicEffect" || field == "markEffect")
                    efeitoConfigSb.Append($",\n        {field} = \"{val}\"");
                else if (field == "comDano" || field == "reflect" || field == "sangramentoArea")
                    efeitoConfigSb.Append($",\n        {field} = {val.ToLower()}");
                else if (double.TryParse(val, out _) || int.TryParse(val, out _))
                    efeitoConfigSb.Append($",\n        {field} = {val}");
                else
                    efeitoConfigSb.Append($",\n        {field} = \"{val}\"");
            }

            // Only add element for damage-dealing effects
            if (effectType is "dano_extra" or "area_ground" or "area_target" or "ricochete"
                or "rajada" or "corrente" or "finisher" or "melee" or "projectile" or "beam"
                or "explosion_ring" or "storm" or "orbit" or "rain" or "pulse")
            {
                efeitoConfigSb.Append($",\n        elemento = {element}");
            }
        }

        var sb = new StringBuilder();
        sb.AppendLine("-- Habilidade: " + name + " | Gerado pelo MCR Grimório");
        sb.AppendLine("-- Salvar como UTF-8");
        sb.AppendLine();
        sb.AppendLine("HABILIDADES[ID] = {");
        sb.AppendLine("    nome = \"" + name + "\",");
        sb.AppendLine("    tipo = \"" + skillType + "\",");
        sb.AppendLine("    dominio = {" + domainId + "},");
        sb.AppendLine("    cooldown = " + cooldown + ",");
        sb.AppendLine("    categoria = \"" + category + "\",");
        sb.AppendLine("    nivelMin = " + minLevel + ",");
        sb.AppendLine("    condicaoFocoMin = " + focoMin + ",");
        sb.AppendLine("    descricao = \"" + desc + "\",");
        sb.AppendLine("    descricaoEfeito = \"" + desc + "\",");
        sb.AppendLine("    cor = " + cor + ",");
        sb.AppendLine();

        if (isCastType)
        {
            sb.AppendLine("    efeitoConfig = {");
            sb.Append(efeitoConfigSb);
            sb.AppendLine();
            sb.AppendLine("    },");
            sb.AppendLine();
            sb.AppendLine("    postura = {");
            sb.AppendLine("        [1] = { efeitoConfig = { dano = " + impeto + " } },");
            sb.AppendLine("        [3] = { efeitoConfig = { dano = " + guarda + " } },");
            sb.AppendLine("    },");
        }
        else
        {
            sb.AppendLine("    efeito = \"...\",");
        }

        sb.AppendLine("}");

        OutputBox.Text = sb.ToString();
    }

    private void CopyBtn_Click(object sender, RoutedEventArgs e)
    {
        if (!string.IsNullOrEmpty(OutputBox.Text))
            Clipboard.SetText(OutputBox.Text);
    }

    private static string SafeExtractId(string input, string fallback)
    {
        var parts = input.Split('(');
        if (parts.Length < 2) return fallback;
        return parts[1].TrimEnd(')');
    }
}
