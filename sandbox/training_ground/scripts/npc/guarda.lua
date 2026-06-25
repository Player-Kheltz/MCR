-- NPC: Guarda
local npc = NPC("Guarda")
npc:setSaudacao("Pare! Identifique-se.")

npc:addDialog("quest", {
    {"O que faz aqui?", "Patrulho a cidade."},
    {"Posso passar?", "So se tiver permissao."},
    {"Tenho permissao", "Entao pode passar."},
})

npc:closeDialog()  -- Adicione esta linha para fechar a tabela de diálogo

print("NPC Guarda carregado.")