using System;
using System.Text;
using System.Windows;
using System.Windows.Controls;

namespace MCR.Grimorio.Modules.Quests;

public partial class QuestsView : UserControl
{
    public QuestsView()
    {
        InitializeComponent();
        SetupTypeParams(); // Render initial kill params
    }

    private void QuestTypeBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        SetupTypeParams();
    }

    private void SetupTypeParams()
    {
        try
        {
            TypeParamsGrid.Children.Clear();
            TypeParamsGrid.RowDefinitions.Clear();
            TypeParamsGrid.ColumnDefinitions.Clear();

            for (int i = 0; i < 4; i++)
                TypeParamsGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

            var typeIndex = QuestTypeBox.SelectedIndex;
            if (typeIndex < 0) typeIndex = 0;

        // Row 1: type-specific params
        TypeParamsGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

        var desc = new TextBlock { FontSize = 11, Foreground = FindResource("FgMutedBrush") as System.Windows.Media.Brush };
        Grid.SetRow(desc, 0);
        Grid.SetColumnSpan(desc, 4);

        switch (typeIndex)
        {
            case 0: // Kill
                desc.Text = "Alvo: monstro · Quantidade";
                TypeParamsGrid.Children.Add(desc);
                AddParam(0, 1, "Monstro", "MonsterNameBox", "Orc");
                AddParam(0, 2, "Quantidade", "KillQtyBox", "10");
                AddParam(0, 3, "Monster ID (opcional)", "MonsterIdBox", "");
                break;
            case 1: // Collect
                desc.Text = "Item a coletar · Quantidade";
                TypeParamsGrid.Children.Add(desc);
                AddParam(0, 1, "Item ID", "CollectItemIdBox", "235");
                AddParam(0, 2, "Quantidade", "CollectQtyBox", "5");
                AddParam(0, 3, "Nome do Item", "CollectItemNameBox", "item misterioso");
                break;
            case 2: // Deliver
                desc.Text = "Item a entregar · Quantidade · NPC destino";
                TypeParamsGrid.Children.Add(desc);
                AddParam(0, 1, "Item ID", "DeliverItemIdBox", "235");
                AddParam(0, 2, "Quantidade", "DeliverQtyBox", "1");
                AddParam(0, 3, "NPC Destino", "DeliverNpcBox", "");
                break;
            case 3: // Explore
                desc.Text = "Coordenadas do local · Raio";
                TypeParamsGrid.Children.Add(desc);
                AddParam(0, 1, "X", "ExploreXBox", "32000");
                AddParam(0, 2, "Y", "ExploreYBox", "32000");
                AddParam(0, 3, "Z", "ExploreZBox", "7");
                break;
            case 4: // Talk
                desc.Text = "NPC alvo · Palavra-chave para falar";
                TypeParamsGrid.Children.Add(desc);
                AddParam(0, 1, "NPC Alvo", "TalkNpcBox", "Aldeão");
                AddParam(0, 2, "Palavra-chave", "TalkKeywordBox", "recado");
                AddParam(0, 3, "Storage (opcional)", "TalkStorageBox", "");
                break;
            case 5: // Escort
                desc.Text = "NPC a escoltar · Distância máxima · Storage de chegada";
                TypeParamsGrid.Children.Add(desc);
                AddParam(0, 1, "NPC", "EscortNpcBox", "Viajante");
                AddParam(0, 2, "Distância Máx", "EscortDistBox", "10");
                AddParam(0, 3, "Destino X", "EscortDestXBox", "32100");
                break;
            case 6: // Craft
                desc.Text = "Item a craftar · Quantidade · Skill necessária";
                TypeParamsGrid.Children.Add(desc);
                AddParam(0, 1, "Item ID", "CraftItemIdBox", "3456");
                AddParam(0, 2, "Quantidade", "CraftQtyBox", "3");
                AddParam(0, 3, "Skill Lv. Mín", "CraftSkillBox", "10");
                break;
            case 7: // Timed
                desc.Text = "Tempo limite (minutos) · Ação esperada";
                TypeParamsGrid.Children.Add(desc);
                AddParam(0, 1, "Minutos", "TimedMinBox", "30");
                AddParam(0, 2, "Descrição", "TimedDescBox", "volte em 30 min");
                AddParam(0, 3, "Storage Timer", "TimedStorageBox", "50100");
                break;
        }
        }
        catch (Exception ex) { System.Diagnostics.Debug.WriteLine("[QuestsView] " + ex.Message); }
    }

    private void AddParam(int row, int col, string label, string name, string defaultValue)
    {
        var stack = new StackPanel { Margin = new Thickness(col > 1 ? 6 : 0, 0, 0, 0) };
        stack.Children.Add(new TextBlock
        {
            Text = label,
            FontSize = 11,
            Foreground = FindResource("FgMutedBrush") as System.Windows.Media.Brush
        });
        var tb = new TextBox
        {
            Name = name,
            Text = defaultValue,
            Margin = new Thickness(0, 2, 0, 0),
            Background = FindResource("BgDarkestBrush") as System.Windows.Media.Brush,
            Foreground = FindResource("FgPrimaryBrush") as System.Windows.Media.Brush,
            BorderThickness = new Thickness(0)
        };
        stack.Children.Add(tb);
        Grid.SetRow(stack, row);
        Grid.SetColumn(stack, col);
        TypeParamsGrid.Children.Add(stack);
    }

    private string GetTypeParamValue(string name)
    {
        foreach (var child in TypeParamsGrid.Children)
        {
            if (child is StackPanel sp)
                foreach (var c in sp.Children)
                    if (c is TextBox tb && tb.Name == name)
                        return tb.Text;
        }
        return "";
    }

    private string GetQuestTypeLua()
    {
        return QuestTypeBox.SelectedIndex switch
        {
            0 => "MISSAO_MATAR",   // Kill
            1 => "MISSAO_COLETAR",  // Collect
            2 => "MISSAO_ENTREGAR", // Deliver
            3 => "MISSAO_EXPLORAR", // Explore
            4 => "MISSAO_FALAR",    // Talk
            5 => "MISSAO_ESCORTAR", // Escort
            6 => "MISSAO_CRAFT",    // Craft
            7 => "MISSAO_TEMPO",    // Timed
            _ => "MISSAO_MATAR"
        };
    }

    private string BuildQuestTypeCheck()
    {
        var typeIdx = QuestTypeBox.SelectedIndex;
        return typeIdx switch
        {
            0 => BuildKillCheck(),
            1 => BuildCollectCheck(),
            2 => BuildDeliverCheck(),
            3 => BuildExploreCheck(),
            4 => BuildTalkCheck(),
            5 => BuildEscortCheck(),
            6 => BuildCraftCheck(),
            7 => BuildTimedCheck(),
            _ => ""
        };
    }

    private string BuildKillCheck()
    {
        var monster = GetTypeParamValue("MonsterNameBox");
        var qty = GetTypeParamValue("KillQtyBox");
        var mid = GetTypeParamValue("MonsterIdBox");
        if (string.IsNullOrWhiteSpace(monster)) monster = "Orc";
        if (string.IsNullOrWhiteSpace(qty)) qty = "10";
        var sb = new StringBuilder();
        sb.AppendLine($"    local questType = \"{GetQuestTypeLua()}\"");
        sb.AppendLine($"    local targetMonster = \"{monster}\"");
        sb.AppendLine($"    local killTarget = {qty}");
        if (!string.IsNullOrWhiteSpace(mid))
            sb.AppendLine($"    local targetMonsterId = {mid}");
        sb.AppendLine();
        sb.AppendLine("    -- Verifica mortes via storage de contagem");
        sb.AppendLine("    local killCount = player:getStorageValue(storage + 1) or 0");
        sb.AppendLine("    if killCount < killTarget then");
        sb.AppendLine("        npcHandler:say(string.format(\"Você já matou %d de %d \" .. c(\"{" + monster + "}\", COR.INIMIGO_MONSTRO) .. \".\", killCount, killTarget), npc, creature)");
        sb.AppendLine("    else");
        sb.AppendLine("        -- Concluiu");
        sb.AppendLine("        concluirQuest(player, npc, creature)");
        sb.AppendLine("    end");
        return sb.ToString();
    }

    private string BuildCollectCheck()
    {
        var itemId = GetTypeParamValue("CollectItemIdBox");
        var qty = GetTypeParamValue("CollectQtyBox");
        var name = GetTypeParamValue("CollectItemNameBox");
        if (string.IsNullOrWhiteSpace(itemId)) itemId = "235";
        if (string.IsNullOrWhiteSpace(qty)) qty = "5";
        if (string.IsNullOrWhiteSpace(name)) name = "item";
        var sb = new StringBuilder();
        sb.AppendLine($"    local questType = \"{GetQuestTypeLua()}\"");
        sb.AppendLine($"    local collectItemId = {itemId}");
        sb.AppendLine($"    local collectQty = {qty}");
        sb.AppendLine();
        sb.AppendLine("    local count = player:getItemCount(collectItemId)");
        sb.AppendLine("    if count >= collectQty then");
        sb.AppendLine("        concluirQuest(player, npc, creature)");
        sb.AppendLine("    else");
        sb.AppendLine("        npcHandler:say(string.format(\"Você tem %d de %d \" .. c(\"{<" + name + ">}\", COR.NPC_ITEM) .. \".\", count, collectQty), npc, creature)");
        sb.AppendLine("    end");
        return sb.ToString();
    }

    private string BuildDeliverCheck()
    {
        var itemId = GetTypeParamValue("DeliverItemIdBox");
        var qty = GetTypeParamValue("DeliverQtyBox");
        var destNpc = GetTypeParamValue("DeliverNpcBox");
        if (string.IsNullOrWhiteSpace(itemId)) itemId = "235";
        if (string.IsNullOrWhiteSpace(qty)) qty = "1";
        var sb = new StringBuilder();
        sb.AppendLine($"    local questType = \"{GetQuestTypeLua()}\"");
        sb.AppendLine($"    local deliverItemId = {itemId}");
        sb.AppendLine($"    local deliverQty = {qty}");
        if (!string.IsNullOrWhiteSpace(destNpc))
            sb.AppendLine($"    local deliverTargetNpc = \"{destNpc}\"");
        sb.AppendLine();
        sb.AppendLine("    local count = player:getItemCount(deliverItemId)");
        sb.AppendLine("    if count >= deliverQty then");
        sb.AppendLine("        if player:removeItem(deliverItemId, deliverQty) then");
        sb.AppendLine("            concluirQuest(player, npc, creature)");
        sb.AppendLine("        end");
        sb.AppendLine("    else");
        sb.AppendLine("        npcHandler:say(string.format(\"Você tem %d de %d itens.\", count, deliverQty), npc, creature)");
        sb.AppendLine("    end");
        return sb.ToString();
    }

    private string BuildExploreCheck()
    {
        var x = GetTypeParamValue("ExploreXBox");
        var y = GetTypeParamValue("ExploreYBox");
        var z = GetTypeParamValue("ExploreZBox");
        if (string.IsNullOrWhiteSpace(x)) x = "32000";
        if (string.IsNullOrWhiteSpace(y)) y = "32000";
        if (string.IsNullOrWhiteSpace(z)) z = "7";
        var sb = new StringBuilder();
        sb.AppendLine($"    local questType = \"{GetQuestTypeLua()}\"");
        sb.AppendLine($"    local targetPos = Position({x}, {y}, {z})");
        sb.AppendLine();
        sb.AppendLine("    local playerPos = player:getPosition()");
        sb.AppendLine("    if playerPos.x == targetPos.x and playerPos.y == targetPos.y and playerPos.z == targetPos.z then");
        sb.AppendLine("        concluirQuest(player, npc, creature)");
        sb.AppendLine("    else");
        sb.AppendLine("        npcHandler:say(\"Você ainda não chegou ao destino. Vá para \" .. c(\"{{" + x + ", " + y + ", " + z + "}}\", COR.MISSAO_EXPLORAR) .. \".\", npc, creature)");
        sb.AppendLine("    end");
        return sb.ToString();
    }

    private string BuildTalkCheck()
    {
        var npc = GetTypeParamValue("TalkNpcBox");
        var keyword = GetTypeParamValue("TalkKeywordBox");
        if (string.IsNullOrWhiteSpace(npc)) npc = "Aldeão";
        if (string.IsNullOrWhiteSpace(keyword)) keyword = "recado";
        var sb = new StringBuilder();
        sb.AppendLine($"    local questType = \"{GetQuestTypeLua()}\"");
        sb.AppendLine($"    local talkTargetNpc = \"{npc}\"");
        sb.AppendLine($"    local talkKeyword = \"{keyword}\"");
        sb.AppendLine();
        sb.AppendLine("    -- Storage de progresso setado pelo NPC alvo");
        sb.AppendLine("    local talked = player:getStorageValue(storage + 2) or 0");
        sb.AppendLine("    if talked >= 1 then");
        sb.AppendLine("        concluirQuest(player, npc, creature)");
        sb.AppendLine("    else");
        sb.AppendLine("        npcHandler:say(\"Vá falar com \" .. c(\"{" + npc + "}\", COR.NPC_NOME) .. \" e diga \" .. c(\"{" + keyword + "}\", COR.NPC_COMANDO) .. \".\", npc, creature)");
        sb.AppendLine("    end");
        return sb.ToString();
    }

    private string BuildEscortCheck()
    {
        var npc = GetTypeParamValue("EscortNpcBox");
        var dist = GetTypeParamValue("EscortDistBox");
        var destX = GetTypeParamValue("EscortDestXBox");
        if (string.IsNullOrWhiteSpace(npc)) npc = "Viajante";
        if (string.IsNullOrWhiteSpace(dist)) dist = "10";
        if (string.IsNullOrWhiteSpace(destX)) destX = "32100";
        var sb = new StringBuilder();
        sb.AppendLine($"    local questType = \"{GetQuestTypeLua()}\"");
        sb.AppendLine($"    local escortNpcName = \"{npc}\"");
        sb.AppendLine($"    local escortDestX = {destX}");
        sb.AppendLine();
        sb.AppendLine("    -- Verifica storage setado quando o NPC chega ao destino");
        sb.AppendLine("    local arrived = player:getStorageValue(storage + 3) or 0");
        sb.AppendLine("    if arrived >= 1 then");
        sb.AppendLine("        concluirQuest(player, npc, creature)");
        sb.AppendLine("    else");
        sb.AppendLine("        npcHandler:say(\"Escorte \" .. c(\"{" + npc + "}\", COR.NPC_NOME) .. \" até o destino.\", npc, creature)");
        sb.AppendLine("    end");
        return sb.ToString();
    }

    private string BuildCraftCheck()
    {
        var itemId = GetTypeParamValue("CraftItemIdBox");
        var qty = GetTypeParamValue("CraftQtyBox");
        var skill = GetTypeParamValue("CraftSkillBox");
        if (string.IsNullOrWhiteSpace(itemId)) itemId = "3456";
        if (string.IsNullOrWhiteSpace(qty)) qty = "3";
        if (string.IsNullOrWhiteSpace(skill)) skill = "10";
        var sb = new StringBuilder();
        sb.AppendLine($"    local questType = \"{GetQuestTypeLua()}\"");
        sb.AppendLine($"    local craftItemId = {itemId}");
        sb.AppendLine($"    local craftQty = {qty}");
        sb.AppendLine($"    local craftSkillMin = {skill}");
        sb.AppendLine();
        sb.AppendLine("    local count = player:getItemCount(craftItemId)");
        sb.AppendLine("    if count >= craftQty then");
        sb.AppendLine("        concluirQuest(player, npc, creature)");
        sb.AppendLine("    else");
        sb.AppendLine("        npcHandler:say(string.format(\"Você criou %d de %d itens.\", count, craftQty), npc, creature)");
        sb.AppendLine("    end");
        return sb.ToString();
    }

    private string BuildTimedCheck()
    {
        var mins = GetTypeParamValue("TimedMinBox");
        var desc = GetTypeParamValue("TimedDescBox");
        var timerStorage = GetTypeParamValue("TimedStorageBox");
        if (string.IsNullOrWhiteSpace(mins)) mins = "30";
        if (string.IsNullOrWhiteSpace(timerStorage)) timerStorage = "50100";
        var sb = new StringBuilder();
        sb.AppendLine($"    local questType = \"{GetQuestTypeLua()}\"");
        sb.AppendLine($"    local timedMinutes = {mins}");
        sb.AppendLine($"    local timerStorage = {timerStorage}");
        sb.AppendLine();
        sb.AppendLine("    local startTime = player:getStorageValue(timerStorage) or 0");
        sb.AppendLine("    if startTime == 0 then");
        sb.AppendLine("        player:setStorageValue(timerStorage, os.time())");
        sb.AppendLine("        npcHandler:say(string.format(\"Você tem %d minutos. \" .. c(\"{"
            + (string.IsNullOrEmpty(desc) ? "volte quando terminar" : desc) + "}\", COR.MISSAO_TEMPO) .. \".\", timedMinutes), npc, creature)");
        sb.AppendLine("    elseif os.time() - startTime >= timedMinutes * 60 then");
        sb.AppendLine("        concluirQuest(player, npc, creature)");
        sb.AppendLine("    else");
        sb.AppendLine("        local remaining = timedMinutes - math.floor((os.time() - startTime) / 60)");
        sb.AppendLine("        npcHandler:say(string.format(\"Restam %d minutos.\", remaining), npc, creature)");
        sb.AppendLine("    end");
        return sb.ToString();
    }

    private void GenerateQuestButton_Click(object sender, RoutedEventArgs e)
    {
        var questName = QuestNameBox.Text.Trim();
        var npcName = QuestNpcBox.Text.Trim();
        var storageStr = QuestStorageBox.Text.Trim();
        var levelStr = QuestLevelBox.Text.Trim();

        if (string.IsNullOrWhiteSpace(questName)) questName = "Nova Missão";
        if (string.IsNullOrWhiteSpace(npcName)) npcName = "MestreNPC";
        if (string.IsNullOrWhiteSpace(storageStr)) storageStr = "50000";
        if (string.IsNullOrWhiteSpace(levelStr)) levelStr = "1";

        int.TryParse(storageStr, out var storageId);
        int.TryParse(levelStr, out var minLevel);

        var sanitized = questName.ToLower().Replace(" ", "_").Replace("'", "").Replace("\"", "");
        var npcSanitized = npcName.ToLower().Replace(" ", "_").Replace("'", "").Replace("\"", "");

        var offer = OfferText.Text?.Trim() ?? "Preciso de sua ajuda, aventureiro! Aceita?";
        var progress = ProgressText.Text?.Trim() ?? "Já conseguiu o que pedi?";
        var complete = CompleteText.Text?.Trim() ?? "Excelente trabalho! Aqui está sua recompensa.";

        var xp = RewardXpBox.Text?.Trim();
        var money = RewardMoneyBox.Text?.Trim();
        var itemId = RewardItemIdBox.Text?.Trim();
        var itemQty = RewardItemQtyBox.Text?.Trim();
        var domainReward = ((ComboBoxItem)RewardDomainBox.SelectedItem)?.Content?.ToString() ?? "Nenhum";

        var reqDomain = ((ComboBoxItem)ReqDomainBox.SelectedItem)?.Content?.ToString() ?? "Nenhum";
        var reqDomainLevel = ReqDomainLevelBox.Text?.Trim() ?? "5";

        var sb = new StringBuilder();
        sb.AppendLine("-- Quest: " + questName + " | Gerado pelo MCR Grimório");
        sb.AppendLine("-- Tipo: " + ((ComboBoxItem)QuestTypeBox.SelectedItem)?.Content);
        sb.AppendLine("-- Salvar como UTF-8");
        sb.AppendLine();
        sb.AppendLine("local questName = \"" + questName + "\"");
        sb.AppendLine("local npcName = \"" + npcName + "\"");
        sb.AppendLine("local storage = " + storageId);
        sb.AppendLine("local minLevel = " + minLevel);
        sb.AppendLine();

        // Domain requirement
        if (reqDomain != "Nenhum")
        {
            var reqDomId = SafeExtractId(reqDomain, "1");
            sb.AppendLine("local reqDominioId = " + reqDomId);
            sb.AppendLine("local reqDominioNivel = " + reqDomainLevel);
            sb.AppendLine();
        }

        // Rewards
        int.TryParse(xp, out var xpVal);
        int.TryParse(money, out var moneyVal);
        int.TryParse(itemId, out var itemIdVal);
        int.TryParse(itemQty, out var itemQtyVal);

        // Domain reward parsing
        string? domId = null;
        if (domainReward != "Nenhum")
            domId = SafeExtractId(domainReward, "1");

        sb.AppendLine("-- Recompensas");
        if (xpVal > 0) sb.AppendLine("local rewardXp = " + xpVal);
        if (moneyVal > 0) sb.AppendLine("local rewardMoney = " + moneyVal);
        if (itemIdVal > 0) sb.AppendLine("local rewardItemId = " + itemIdVal);
        if (itemQtyVal > 0) sb.AppendLine("local rewardItemQty = " + itemQtyVal);
        if (domId != null) sb.AppendLine("local rewardDominioId = " + domId);
        sb.AppendLine();

        // NPC Type
        sb.AppendLine("local npcType = Game.createNpcType(\"" + npcSanitized + "\")");
        sb.AppendLine("local npcConfig = {");
        sb.AppendLine("    name = \"" + npcName + "\",");
        sb.AppendLine("    description = \"NPC da quest " + questName + "\",");
        sb.AppendLine("    health = 100, maxHealth = 100,");
        sb.AppendLine("    outfit = { lookType = 130, lookHead = 0, lookBody = 0, lookLegs = 0, lookFeet = 0, lookAddons = 0 },");
        sb.AppendLine("    canPrintMessages = true,");
        sb.AppendLine("    canListen = true,");
        sb.AppendLine("}");
        sb.AppendLine();
        sb.AppendLine("local keywordHandler = KeywordHandler:new()");
        sb.AppendLine("local npcHandler = NpcHandler:new(keywordHandler)");
        sb.AppendLine();

        // Concluir quest function
        sb.AppendLine("local function concluirQuest(player, npc, creature)");
        sb.AppendLine("    local tr = NpcUtils.getTratamento(player)");
        sb.AppendLine("    player:setStorageValue(storage, 2)");
        sb.AppendLine("    npcHandler:say(\"" + complete + "\", npc, creature)");
        if (xpVal > 0)
        {
            sb.AppendLine("    player:addExperience(rewardXp, true)");
            sb.AppendLine("    player:sendTextMessage(MESSAGE_EXPERIENCE, \"+ \" .. rewardXp .. \" XP\")");
        }
        if (moneyVal > 0)
        {
            sb.AppendLine("    player:addMoney(rewardMoney)");
            sb.AppendLine("    player:sendTextMessage(MESSAGE_TRADE, \"+ \" .. rewardMoney .. \" gold\")");
        }
        if (itemIdVal > 0 && itemQtyVal > 0)
        {
            sb.AppendLine("    player:addItem(rewardItemId, rewardItemQty)");
        }
        if (domId != null)
        {
            sb.AppendLine("    adicionarAfinidade(player, rewardDominioId, 50)");
            sb.AppendLine("    player:sendTextMessage(MESSAGE_EVENT_ADVANCE, \"Você sente uma nova conexão com o domínio!\")");
        }
        sb.AppendLine("    -- Atualiza HUD da quest");
        sb.AppendLine("    player:sendExtendedOpcode(180, \"quest_complete|\" .. storage)");
        sb.AppendLine("end");
        sb.AppendLine();

        // creatureSayCallback
        sb.AppendLine("local function creatureSayCallback(npc, creature, type, message)");
        sb.AppendLine("    local player = Player(creature)");
        sb.AppendLine("    local playerId = player:getId()");
        sb.AppendLine("    if not npcHandler:checkInteraction(npc, creature) then return false end");
        sb.AppendLine();
        sb.AppendLine("    local tr = NpcUtils.getTratamento(player)");
        sb.AppendLine();

        // Level check
        sb.AppendLine("    if player:getLevel() < minLevel then");
        sb.AppendLine("        npcHandler:say(string.format(\"Você precisa ser nível %d para esta missão, %s.\", minLevel, tr.vocativo), npc, creature)");
        sb.AppendLine("        return true");
        sb.AppendLine("    end");
        sb.AppendLine();

        // Domain requirement check
        if (reqDomain != "Nenhum")
        {
            var reqDomId = SafeExtractId(reqDomain, "1");
            sb.AppendLine("    -- Verifica requisito de domínio");
            sb.AppendLine("    local afinidade = player:getDominioAfinidade(reqDominioId)");
            sb.AppendLine("    local nivel = getNivelPorAfinidade(afinidade)");
            sb.AppendLine("    if nivel < reqDominioNivel then");
            sb.AppendLine("        npcHandler:say(\"Você ainda não tem experiência suficiente neste domínio. Treine mais e volte.\", npc, creature)");
            sb.AppendLine("        return true");
            sb.AppendLine("    end");
            sb.AppendLine();
        }

        // Quest flow
        sb.AppendLine("    -- Fluxo da quest");
        sb.AppendLine("    local progress = player:getStorageValue(storage) or 0");
        sb.AppendLine();
        sb.AppendLine("    if MsgContains(message, 'missao') or MsgContains(message, 'quest') or MsgContains(message, 'missão') or MsgContains(message, 'ajuda') then");
        sb.AppendLine("        if progress < 1 or progress == -1 then");
        sb.AppendLine("            -- Oferecer quest");
        sb.AppendLine("            npcHandler:say(c(\"{" + offer + "}\", COR.NPC_INTENCAO), npc, creature)");
        sb.AppendLine("            npcHandler:setTopic(playerId, 1)");
        sb.AppendLine("        elseif progress == 1 then");
        sb.AppendLine("            -- Verificar progresso");
        sb.AppendLine("            npcHandler:say(c(\"{" + progress + "}\", COR.MISSAO_COLETAR), npc, creature)");

        // Type-specific progress check
        sb.AppendLine(BuildQuestTypeCheck());

        sb.AppendLine("        elseif progress >= 2 then");
        sb.AppendLine("            -- Quest concluída");
        sb.AppendLine("            npcHandler:say(\"Obrigado pela ajuda! Volte sempre que tiver novas missões.\", npc, creature)");
        sb.AppendLine("        end");
        sb.AppendLine();
        sb.AppendLine("    elseif MsgContains(message, 'yes') or MsgContains(message, 'sim') then");
        sb.AppendLine("        if npcHandler:getTopic(playerId) == 1 then");
        sb.AppendLine("            player:setStorageValue(storage, 1)");

        // Setup kill count tracking
        if (QuestTypeBox.SelectedIndex == 0)
        {
            var qty = GetTypeParamValue("KillQtyBox");
            if (string.IsNullOrWhiteSpace(qty)) qty = "10";
            sb.AppendLine("            player:setStorageValue(storage + 1, 0) -- contador de mortes");
        }

        sb.AppendLine("            player:sendExtendedOpcode(180, \"quest_start|\" .. storage)");
        sb.AppendLine("            npcHandler:say(c(\"Excelente! Vá e complete sua missão.\", COR.SUCESSO_CURA), npc, creature)");
        sb.AppendLine("            npcHandler:setTopic(playerId, 0)");
        sb.AppendLine("        end");
        sb.AppendLine("    end");
        sb.AppendLine();
        sb.AppendLine("    return true");
        sb.AppendLine("end");
        sb.AppendLine();

        // Callbacks
        sb.AppendLine("npcHandler:setCallback(CALLBACK_MESSAGE_DEFAULT, creatureSayCallback)");
        sb.AppendLine();
        sb.AppendLine("npcType.onThink = function(npc, interval) npcHandler:onThink(npc, interval) end");
        sb.AppendLine("npcType.onAppear = function(npc, creature) npcHandler:onAppear(npc, creature) end");
        sb.AppendLine("npcType.onDisappear = function(npc, creature) npcHandler:onDisappear(npc, creature) end");
        sb.AppendLine("npcType.onMove = function(npc, creature, fromPosition, toPosition) npcHandler:onMove(npc, creature, fromPosition, toPosition) end");
        sb.AppendLine("npcType.onSay = function(npc, creature, type, message) npcHandler:onSay(npc, creature, type, message) end");
        sb.AppendLine("npcType.onCloseChannel = function(npc, creature) npcHandler:onCloseChannel(npc, creature) end");
        sb.AppendLine();
        sb.AppendLine("npcHandler:addModule(FocusModule:new(), npcConfig.name, true, true, true)");
        sb.AppendLine("npcType:register(npcConfig)");

        QuestOutput.Text = sb.ToString();
    }

    private void CopyQuestBtn_Click(object sender, RoutedEventArgs e)
    {
        if (!string.IsNullOrEmpty(QuestOutput.Text))
            Clipboard.SetText(QuestOutput.Text);
    }

    private static string SafeExtractId(string input, string fallback)
    {
        var parts = input.Split('(');
        if (parts.Length < 2) return fallback;
        return parts[1].TrimEnd(')');
    }
}
