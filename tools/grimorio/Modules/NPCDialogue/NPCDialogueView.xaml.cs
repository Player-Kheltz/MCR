using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using MCR.Grimorio.Core.Detection;

namespace MCR.Grimorio.Modules.NPCDialogue;

public partial class NPCDialogueView : UserControl
{
    public NPCDialogueView()
    {
        InitializeComponent();
        DetectionText.Text = new MCRDetector().Detect().HasNpcDialogue
            ? "✓ Sistema de diálogo MCR detectado"
            : "Não detectado";
        ShopItemsBox.Text =
            "backpack,2854,10,0\n" +
            "rope,3003,50,8\n" +
            "shovel,3457,20,5\n" +
            "fishing rod,3483,150,30";
    }

    private static string GetPersonality(string p)
    {
        return p switch
        {
            "Sábio" => "estudioso",
            "Misterioso" => "enigmático",
            "Rude" => "ranzinza",
            "Alegre" => "festivo",
            "Guerreiro" => "veterano",
            "Místico" => "espiritual",
            "Comerciante" => "negociante",
            "Ferreiro" => "artesão",
            "Herbalista" => "naturalista",
            "Arcanista" => "arcano",
            "Eremita" => "solitário",
            _ => "amigável"
        };
    }

    private static string GetGreeting(string personality, string schedule)
    {
        var greetings = personality switch
        {
            "Misterioso" => new[] {
                "Ah, vejo que os ventos o trouxeram até mim...",
                "O destino cruza nossos caminhos novamente.",
                "Sinto sua presença antes mesmo de vê-lo." },
            "Rude" => new[] {
                "O que você quer? Não tenho o dia todo.",
                "Já vou avisando: não estou de bom humor.",
                "Fale logo e vá embora." },
            "Sábio" => new[] {
                "Saudações, jovem. Busca conhecimento?",
                "Ah, um visitante! Sempre bom ver mentes curiosas.",
                "O saber flui como água. O que deseja aprender?" },
            "Alegre" => new[] {
                "Opa! Que bom te ver por aqui!",
                "Eba! Visitas! Senta aí e conta as novidades!",
                "O dia já está melhor com sua presença!" },
            "Guerreiro" => new[] {
                "Pronto para mais uma batalha?",
                "Endireite a postura. Um guerreiro não se curva.",
                "O campo de batalha nos espera. O que precisa?" },
            "Místico" => new[] {
                "Sinto uma energia diferente em você hoje...",
                "Os espíritos sussurram seu nome. Aproxime-se.",
                "O véu entre os mundos está fino. Você sente?" },
            "Comerciante" => new[] {
                "Ofertas imperdíveis hoje! O que vai levar?",
                "Para você, preço especial! Só hoje!",
                "Mercadorias frescas, direto do porto!" },
            "Ferreiro" => new[] {
                "Tsc, tsc. Essa armadura precisa de reparos?",
                "O fogo está aceso e a bigorna espera.",
                "Mais uma lâmina para forjar? Vamos nessa." },
            "Herbalista" => new[] {
                "Sinto cheiro de ervas em você. Interessante...",
                "A natureza nos abençoa com sua presença.",
                "As plantas me contaram que você viria." },
            "Arcanista" => new[] {
                "Ah, um buscador do arcano! Entre, entre.",
                "Os runas estão dispostas. O que procura?",
                "O mana flui ao seu redor. Posso sentir." },
            "Eremita" => new[] {
                "Poucos encontram minha humilde morada.",
                "O silêncio é meu companheiro. Por que me procura?",
                "O mundo lá fora é barulhento demais." },
            _ => new[] {
                "Olá, aventureiro! Em que posso ajudar?",
                "Bem-vindo! Como posso ser útil hoje?",
                "Prazer em vê-lo! Precisa de algo?" }
        };
        var rng = new Random();
        var greet = greetings[rng.Next(greetings.Length)];
        if (schedule == "Nenhum") return greet;
        return greet + " " + (schedule switch
        {
            "Dia/Noite" => "( {#turno} )",
            _ => "( {#turno} )"
        });
    }

    private static string GetFarewell(string personality)
    {
        return personality switch
        {
            "Misterioso" => "Os ventos o levarão aonde precisar...",
            "Rude" => "Finalmente. Vá logo.",
            "Sábio" => "Que o conhecimento o acompanhe.",
            "Alegre" => "Volte sempre, amigo!",
            "Guerreiro" => "Que seus golpes sejam precisos.",
            "Místico" => "Que os espíritos o guiem.",
            "Comerciante" => "Volte quando tiver mais moedas!",
            "Ferreiro" => "Se suas armas quebrarem, já sabe onde me encontrar.",
            "Herbalista" => "Que as plantas floresçam em seu caminho.",
            "Arcanista" => "Que os runas estejam a seu favor.",
            "Eremita" => "Vá em paz. O silêncio me espera.",
            _ => "Até logo, e boa sorte!"
        };
    }

    private static string GetScheduleBlock(string schedule)
    {
        if (schedule == "Nenhum") return "";
        var sb = new StringBuilder();
        if (schedule == "Dia/Noite")
        {
            sb.AppendLine();
            sb.AppendLine("-- Schedule: Dia / Noite");
            sb.AppendLine("local function getTurnoSaudacao()");
            sb.AppendLine("    if getWorldLight() == LIGHT_DAYLIGHT then");
            sb.AppendLine("        return c(\"bom dia!\", COR.NPC_INTENCAO)");
            sb.AppendLine("    else");
            sb.AppendLine("        return c(\"boa noite!\", COR.NPC_INTENCAO)");
            sb.AppendLine("    end");
            sb.AppendLine("end");
        }
        else
        {
            sb.AppendLine();
            sb.AppendLine("-- Schedule: Manhã / Tarde / Noite");
            sb.AppendLine("local function getTurnoSaudacao()");
            sb.AppendLine("    local hour = tonumber(os.date(\"%H\"))");
            sb.AppendLine("    if hour >= 6 and hour < 12 then");
            sb.AppendLine("        return c(\"bom dia!\", COR.NPC_INTENCAO)");
            sb.AppendLine("    elseif hour >= 12 and hour < 18 then");
            sb.AppendLine("        return c(\"boa tarde!\", COR.NPC_INTENCAO)");
            sb.AppendLine("    else");
            sb.AppendLine("        return c(\"boa noite!\", COR.NPC_INTENCAO)");
            sb.AppendLine("    end");
            sb.AppendLine("end");
        }
        return sb.ToString();
    }

    private static string GetDomainReaction(string domain)
    {
        return domain switch
        {
            "Fogo (23)" =>
                "    if nivel >= 10 then\n" +
                "        npcHandler:say(\"Sinto um \" .. c(\"calor\", COR.ELEM_FOGO) .. \" emanando de ti... O fogo reconhece sua alma.\", npc, creature)\n" +
                "    elseif nivel >= 5 then\n" +
                "        npcHandler:say(\"Há uma centelha em você... Já treina com o \" .. c(\"fogo\", COR.ELEM_FOGO) .. \"?\", npc, creature)\n" +
                "    end\n",
            "Gelo (24)" =>
                "    if nivel >= 10 then\n" +
                "        npcHandler:say(\"O ar ao seu redor \" .. c(\"esfria\", COR.ELEM_GELO) .. \" quando você se aproxima. Impressionante.\", npc, creature)\n" +
                "    elseif nivel >= 5 then\n" +
                "        npcHandler:say(\"Seu toque é \" .. c(\"frio\", COR.ELEM_GELO) .. \". Anda treinando com o gelo?\", npc, creature)\n" +
                "    end\n",
            "Terra (25)" =>
                "    if nivel >= 10 then\n" +
                "        npcHandler:say(\"A \" .. c(\"terra\", COR.ELEM_TERRA) .. \" parece responder a seus comandos. Você é um amigo do solo.\", npc, creature)\n" +
                "    elseif nivel >= 5 then\n" +
                "        npcHandler:say(\"Suas mãos têm uma \" .. c(\"conexão\", COR.NPC_INTENCAO) .. \" com a natureza. Interessante.\", npc, creature)\n" +
                "    end\n",
            "Energia (26)" =>
                "    if nivel >= 10 then\n" +
                "        npcHandler:say(\"Faíscas \" .. c(\"dançam\", COR.ELEM_RAIO) .. \" ao seu redor. Domina bem a energia.\", npc, creature)\n" +
                "    elseif nivel >= 5 then\n" +
                "        npcHandler:say(\"Sinto \" .. c(\"estática\", COR.NPC_INTENCAO) .. \" no ar perto de você. Mexe com energia?\", npc, creature)\n" +
                "    end\n",
            "Espadas Leves (100)" =>
                "    if nivel >= 10 then\n" +
                "        npcHandler:say(\"Sua \" .. c(\"elegância\", COR.DOM_COMBATE_PRECISAO) .. \" com a lâmina é notável. Quase uma dança.\", npc, creature)\n" +
                "    elseif nivel >= 5 then\n" +
                "        npcHandler:say(\"O aço \" .. c(\"leve\", COR.DOM_COMBATE_PRECISAO) .. \" parece chamar por você. Tem treinado?\", npc, creature)\n" +
                "    end\n",
            "Espadas Pesadas (101)" =>
                "    if nivel >= 10 then\n" +
                "        npcHandler:say(\"Nossa, que \" .. c(\"força\", COR.DOM_COMBATE_IMPACTO) .. \"! Essa espada pesada parece um brinquedo em suas mãos.\", npc, creature)\n" +
                "    elseif nivel >= 5 then\n" +
                "        npcHandler:say(\"Você tem \" .. c(\"porte\", COR.DOM_COMBATE_IMPACTO) .. \" para brandir armas pesadas. Impressionante.\", npc, creature)\n" +
                "    end\n",
            "Combate (1)" =>
                "    if nivel >= 15 then\n" +
                "        npcHandler:say(\"Você é um verdadeiro \" .. c(\"Mestre da Guerra\", COR.RARIDADE_LENDARIO) .. \". Sua aura intimida.\", npc, creature)\n" +
                "    elseif nivel >= 10 then\n" +
                "        npcHandler:say(\"Sinto o \" .. c(\"espírito\", COR.NPC_INTENCAO) .. \" de um guerreiro em você. Já viu muitas batalhas.\", npc, creature)\n" +
                "    elseif nivel >= 5 then\n" +
                "        npcHandler:say(\"Você tem \" .. c(\"potencial\", COR.NPC_INTENCAO) .. \" marcial. Continue treinando.\", npc, creature)\n" +
                "    end\n",
            "Summon (28)" =>
                "    if nivel >= 10 then\n" +
                "        npcHandler:say(\"Você \" .. c(\"não está só\", COR.NPC_MISTERIOSO) .. \". Sinto almas vinculadas à sua.\", npc, creature)\n" +
                "    elseif nivel >= 5 then\n" +
                "        npcHandler:say(\"Há \" .. c(\"ecos\", COR.NPC_MISTERIOSO) .. \" de outras criaturas ao seu redor. Invocador?\", npc, creature)\n" +
                "    end\n",
            "Sobrevivência (400)" =>
                "    if nivel >= 10 then\n" +
                "        npcHandler:say(\"Suas \" .. c(\"cicatrizes\", COR.NPC_DIALOGO) .. \" contam histórias. Você é difícil de derrubar.\", npc, creature)\n" +
                "    elseif nivel >= 5 then\n" +
                "        npcHandler:say(\"Você tem \" .. c(\"olhar\", COR.NPC_DIALOGO) .. \" de quem já passou por tempestades.\", npc, creature)\n" +
                "    end\n",
            _ => ""
        };
    }

    private static string GetShopCode(string itemsText)
    {
        if (string.IsNullOrWhiteSpace(itemsText)) return "";
        var sb = new StringBuilder();
        sb.AppendLine();
        sb.AppendLine("    -- Configuração da Loja");
        sb.AppendLine("    shop = {");
        foreach (var line in itemsText.Split('\n', StringSplitOptions.RemoveEmptyEntries))
        {
            var trimmed = line.Trim();
            if (string.IsNullOrEmpty(trimmed)) continue;
            var parts = trimmed.Split(',');
            if (parts.Length < 2) continue;
            var name = parts[0].Trim();
            var clientId = parts[1].Trim();
            var buy = parts.Length > 2 ? parts[2].Trim() : "0";
            var sell = parts.Length > 3 ? parts[3].Trim() : "0";
            sb.AppendLine($"        {{ itemName = \"{name}\", clientId = {clientId}, buy = {buy}, sell = {sell} }},");
        }
        sb.AppendLine("    },");
        sb.AppendLine();
        sb.AppendLine("    -- Callbacks da Loja");
        sb.AppendLine("    onBuyItem = function(npc, player, itemId, subType, amount, ignore, inBackpacks, totalCost)");
        sb.AppendLine("        npc:sellItem(player, itemId, amount, subType, 0, ignore, inBackpacks)");
        sb.AppendLine("    end,");
        sb.AppendLine("    onSellItem = function(npc, player, itemId, subtype, amount, ignore, name, totalCost)");
        sb.AppendLine("        player:sendTextMessage(MESSAGE_TRADE, string.format(\"Vendido %ix %s por %i gold.\", amount, name, totalCost))");
        sb.AppendLine("    end,");
        sb.AppendLine("    onCheckItem = function(npc, player, clientId, subType) end,");
        return sb.ToString();
    }

    private static string GetQuestBlock()
    {
        var sb = new StringBuilder();
        sb.AppendLine();
        sb.AppendLine("    -- Tópicos da Quest (storages 50000+)");
        sb.AppendLine("    local questStorage = 50000");
        sb.AppendLine("    local questItemId = 235 -- Ajuste para o item da quest");
        sb.AppendLine("    local questRewardMoney = 100");
        sb.AppendLine("    local questRewardItem = 3725");
        sb.AppendLine("    local questRewardQty = 5");
        sb.AppendLine();
        sb.AppendLine("    if MsgContains(message, 'missao') or MsgContains(message, 'quest') or MsgContains(message, 'missão') then");
        sb.AppendLine("        local progress = player:getStorageValue(questStorage)");
        sb.AppendLine("        if progress < 0 or progress == nil then");
        sb.AppendLine("            npcHandler:say(\"Preciso de sua ajuda! Uma \" .. c(\"missão\", COR.MISSAO_COLETAR) .. \" importante.\", npc, creature)");
        sb.AppendLine("            npcHandler:setTopic(playerId, 10)");
        sb.AppendLine("        elseif progress == 1 then");
        sb.AppendLine("            npcHandler:say(\"Já conseguiu o que pedi?\", npc, creature)");
        sb.AppendLine("            npcHandler:setTopic(playerId, 11)");
        sb.AppendLine("        elseif progress == 2 then");
        sb.AppendLine("            npcHandler:say(\"Obrigado pela ajuda! Não tenho mais nada no momento.\", npc, creature)");
        sb.AppendLine("        end");
        sb.AppendLine("    elseif MsgContains(message, 'yes') or MsgContains(message, 'sim') then");
        sb.AppendLine("        local topic = npcHandler:getTopic(playerId)");
        sb.AppendLine("        if topic == 10 then");
        sb.AppendLine("            player:setStorageValue(questStorage, 1)");
        sb.AppendLine("            npcHandler:say(\"Preciso que colete \" .. c(\"{1 item misterioso}\", COR.NPC_ITEM) .. \". Volte quando conseguir.\", npc, creature)");
        sb.AppendLine("        elseif topic == 11 then");
        sb.AppendLine("            if player:removeItem(questItemId, 1) then");
        sb.AppendLine("                player:setStorageValue(questStorage, 2)");
        sb.AppendLine("                player:addMoney(questRewardMoney)");
        sb.AppendLine("                player:addItem(questRewardItem, questRewardQty)");
        sb.AppendLine("                npcHandler:say(c(\"Excelente!\", COR.SUCESSO_CURA) .. \" Aqui está sua recompensa.\", npc, creature)");
        sb.AppendLine("            else");
        sb.AppendLine("                npcHandler:say(\"Você ainda não tem o item. Volte quando conseguir.\", npc, creature)");
        sb.AppendLine("            end");
        sb.AppendLine("        end");
        sb.AppendLine("    elseif topic == 10 or topic == 11 then");
        sb.AppendLine("        npcHandler:say(\"Volte quando estiver pronto.\", npc, creature)");
        sb.AppendLine("    end");
        return sb.ToString();
    }

    private void GenerateButton_Click(object sender, RoutedEventArgs e)
    {
        var name = NpcNameBox.Text.Trim();
        if (string.IsNullOrWhiteSpace(name)) name = "NPC";
        var rawName = name;
        name = name.ToLower().Replace(" ", "_").Replace("-", "_");

        var personality = ((ComboBoxItem)PersonalityBox.SelectedItem)?.Content?.ToString() ?? "Amigável";
        var schedule = ((ComboBoxItem)ScheduleBox.SelectedItem)?.Content?.ToString() ?? "Nenhum";
        var domain = ((ComboBoxItem)DomainBox.SelectedItem)?.Content?.ToString() ?? "Nenhum";
        var dialogType = ((ComboBoxItem)DialogTypeBox.SelectedItem)?.Content?.ToString() ?? "Básico (saudações)";
        var outfit = OutfitBox.Text.Trim();
        if (string.IsNullOrWhiteSpace(outfit)) outfit = "130";
        var desc = DescBox.Text.Trim();
        if (string.IsNullOrWhiteSpace(desc)) desc = $"Um NPC {GetPersonality(personality)}.";

        var hasShop = dialogType.Contains("Shop");
        var hasQuest = dialogType.Contains("Quest");
        var greet = GetGreeting(personality, schedule);
        var farewell = GetFarewell(personality);
        var domainReaction = GetDomainReaction(domain);

        var sb = new StringBuilder();

        sb.AppendLine("-- NPC: " + rawName + " | Personalidade: " + personality);
        sb.AppendLine("-- Gerado pelo MCR Grimório — NPC Dialogue Rico");
        sb.AppendLine("-- Encodado como UTF-8 conforme padrão MCR");
        sb.AppendLine();
        sb.AppendLine("local internalNpcName = \"" + name + "\"");
        sb.AppendLine("local npcType = Game.createNpcType(internalNpcName)");
        sb.AppendLine("local npcConfig = {");
        sb.AppendLine("    name = internalNpcName,");
        sb.AppendLine("    description = \"" + desc + "\",");
        sb.AppendLine("    health = 100, maxHealth = 100,");
        sb.AppendLine("    outfit = { lookType = " + outfit + ", lookHead = 0, lookBody = 0, lookLegs = 0, lookFeet = 0, lookAddons = 0 },");
        sb.AppendLine("    walkInterval = 2000,");
        sb.AppendLine("    walkSpeed = 100,");
        sb.AppendLine("    walkable = false,");
        sb.AppendLine("    canPrintMessages = true,");
        sb.AppendLine("    canListen = true,");
        sb.AppendLine("    canWalk = true,");

        if (hasShop) sb.Append(GetShopCode(ShopItemsBox.Text));

        sb.AppendLine("}");
        sb.AppendLine();
        sb.AppendLine("-- KeywordHandler");
        sb.AppendLine("local keywordHandler = KeywordHandler:new()");
        sb.AppendLine("local npcHandler = NpcHandler:new(keywordHandler)");
        sb.AppendLine();
        sb.AppendLine("-- Palavras-chave");
        sb.AppendLine("keywordHandler:addKeywordSpecific({'job', 'trabalho'}, StdModule.say, {npcHandler = npcHandler, text = \"" + desc + "\"})");

        if (hasShop)
        {
            sb.AppendLine("keywordHandler:addKeywordSpecific({'trade', 'shop', 'loja', 'trocar'}, StdModule.say, {npcHandler = npcHandler, text = \"Claro! Dê uma olhada.\"})");
        }

        sb.AppendLine();

        // Schedule code
        var scheduleBlock = GetScheduleBlock(schedule);
        if (!string.IsNullOrEmpty(scheduleBlock))
        {
            sb.AppendLine(scheduleBlock);
            sb.AppendLine();
        }

        // Domain reaction helper
        if (!string.IsNullOrEmpty(domainReaction))
        {
            var domainId = domain.Split('(')[1].TrimEnd(')');
            sb.AppendLine("-- Reação ao Domínio " + domain);
            sb.AppendLine("local function checkDominio(player, npc, creature)");
            sb.AppendLine("    local afinidade = player:getDominioAfinidade(" + domainId + ")");
            sb.AppendLine("    local nivel = getNivelPorAfinidade(afinidade)");
            sb.AppendLine(domainReaction);
            sb.AppendLine("end");
            sb.AppendLine();
        }

        // CreatureSay callback
        sb.AppendLine("local function creatureSayCallback(npc, creature, type, message)");
        sb.AppendLine("    local player = Player(creature)");
        sb.AppendLine("    local playerId = player:getId()");
        sb.AppendLine("    if not npcHandler:checkInteraction(npc, creature) then return false end");
        sb.AppendLine();
        sb.AppendLine("    -- Tratamento por pronome");
        sb.AppendLine("    local tr = NpcUtils.getTratamento(player)");
        sb.AppendLine();

        if (!string.IsNullOrEmpty(scheduleBlock))
        {
            sb.AppendLine("    local turno = getTurnoSaudacao()");
        }

        sb.AppendLine("    if MsgContains(message, 'bye') or MsgContains(message, 'tchau') or MsgContains(message, 'tchau') then");
        sb.AppendLine("        npcHandler:say(\"" + farewell + "\", npc, creature)");
        sb.AppendLine();
        sb.AppendLine("    elseif MsgContains(message, 'hello') or MsgContains(message, 'oi') or MsgContains(message, 'ola') or MsgContains(message, 'olá') then");

        if (!string.IsNullOrEmpty(scheduleBlock))
        {
            sb.AppendLine("        local saudacao = string.format(\"" + greet.Replace("{#turno}", "%s") + "\", turno)");
            sb.AppendLine("        npcHandler:say(saudacao, npc, creature)");
        }
        else
        {
            sb.AppendLine("        npcHandler:say(\"" + greet + "\", npc, creature)");
        }

        if (!string.IsNullOrEmpty(domainReaction))
        {
            sb.AppendLine("        checkDominio(player, npc, creature)");
        }

        sb.AppendLine();
        sb.AppendLine("    elseif MsgContains(message, 'pronome') or MsgContains(message, 'genero') or MsgContains(message, 'gênero') or MsgContains(message, 'tratamento') then");
        sb.AppendLine("        npcHandler:say(string.format(\"Então você prefere ser chamado de %s. Perfeito, %s!\", tr.pronome, tr.tratamento), npc, creature)");

        if (hasQuest)
        {
            sb.AppendLine();
            sb.Append(GetQuestBlock());
        }

        sb.AppendLine("    end");
        sb.AppendLine("    return true");
        sb.AppendLine("end");
        sb.AppendLine("npcHandler:setCallback(CALLBACK_MESSAGE_DEFAULT, creatureSayCallback)");
        sb.AppendLine();

        // Greet callback with pronoun
        sb.AppendLine("local function greetCallback(npc, creature)");
        sb.AppendLine("    local player = Player(creature)");
        sb.AppendLine("    local tr = NpcUtils.getTratamento(player)");
        sb.AppendLine("    npcHandler:setMessage(MESSAGE_GREET, string.format(\"Saudações, \" .. c(\"%%s\", COR.NPC_INTENCAO) .. \"! Eu sou \" .. c(\"" + rawName + "\", COR.NPC_COMANDO) .. \".\", tr.vocativo))");

        if (!string.IsNullOrEmpty(domainReaction))
        {
            sb.AppendLine("    checkDominio(player, npc, creature)");
        }

        sb.AppendLine("    return true");
        sb.AppendLine("end");
        sb.AppendLine("npcHandler:setCallback(CALLBACK_GREET, greetCallback)");
        sb.AppendLine();
        sb.AppendLine("-- Callbacks da engine");
        sb.AppendLine("npcType.onThink = function(npc, interval) npcHandler:onThink(npc, interval) end");
        sb.AppendLine("npcType.onAppear = function(npc, creature) npcHandler:onAppear(npc, creature) end");
        sb.AppendLine("npcType.onDisappear = function(npc, creature) npcHandler:onDisappear(npc, creature) end");
        sb.AppendLine("npcType.onMove = function(npc, creature, fromPosition, toPosition) npcHandler:onMove(npc, creature, fromPosition, toPosition) end");
        sb.AppendLine("npcType.onSay = function(npc, creature, type, message) npcHandler:onSay(npc, creature, type, message) end");
        sb.AppendLine("npcType.onCloseChannel = function(npc, creature) npcHandler:onCloseChannel(npc, creature) end");
        sb.AppendLine();
        sb.AppendLine("npcHandler:addModule(FocusModule:new(), npcConfig.name, true, true, true)");
        sb.AppendLine("npcType:register(npcConfig)");

        OutputBox.Text = sb.ToString();
    }

    private void CopyButton_Click(object sender, RoutedEventArgs e)
    {
        if (string.IsNullOrEmpty(OutputBox.Text)) return;
        Clipboard.SetText(OutputBox.Text);
        CopyButton.Content = "✓ Copiado!";
        var t = new System.Timers.Timer(2000) { AutoReset = false };
        t.Elapsed += (_, _) => Dispatcher.Invoke(() => CopyButton.Content = "📋 Copiar");
        t.Start();
    }

    private void SaveFileButton_Click(object sender, RoutedEventArgs e)
    {
        if (string.IsNullOrEmpty(OutputBox.Text)) return;
        var name = (string.IsNullOrWhiteSpace(NpcNameBox.Text) ? "npc" : NpcNameBox.Text)
            .ToLower().Replace(" ", "_").Replace("-", "_");
        var path = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Desktop), $"{name}.lua");
        try
        {
            File.WriteAllText(path, OutputBox.Text, Encoding.UTF8);
            SaveFileButton.Content = "✓ Salvo!";
            var t = new System.Timers.Timer(2000) { AutoReset = false };
            t.Elapsed += (_, _) => Dispatcher.Invoke(() => SaveFileButton.Content = "💾 Salvar (.lua)");
            t.Start();
        }
        catch (Exception ex) { System.Diagnostics.Debug.WriteLine("[Grimorio] " + ex.Message); }
    }
}
