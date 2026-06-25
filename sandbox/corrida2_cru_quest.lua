-- CRU: Quest — O Despertar de Eridanus
local quest = Quest("O Despertar de Eridanus")
quest:setDescricao("Uma antiga profecia esta se cumprindo. Os tres pilares de Eridanus foram abalados e alguem tenta despertar um poder antigo. Voce deve encontrar o Guardiao das Profecias e impedir o despertar.")
quest:setNivelMinimo(15)
quest:setNpcIniciador("Guardiao das Profecias")

quest:addEtapa({
    nome = "O Selo do Guardiao",
    descricao = "Derrote o Espectro da Torre e obtenha o Selo do Guardiao.",
    objetivos = {
        { tipo = "matar", monster = "Espectro da Torre", quantidade = 1 },
        { tipo = "coletar", item = 41001, quantidade = 1 },
    },
    recompensa = { xp = 500, gold = 200 },
})

quest:addEtapa({
    nome = "A Chama da Sabedoria",
    descricao = "Derrote o Golem de Pedra na biblioteca e obtenha a Chama da Sabedoria.",
    objetivos = {
        { tipo = "matar", monster = "Golem de Pedra", quantidade = 1 },
        { tipo = "coletar", item = 41002, quantidade = 1 },
    },
    recompensa = { xp = 750, gold = 400 },
})

quest:addEtapa({
    nome = "O Coracao da Terra",
    descricao = "Nas profundezas, derrote o Guardiao Subterraneo e obtenha o Coracao da Terra.",
    objetivos = {
        { tipo = "matar", monster = "Guardiao Subterraneo", quantidade = 1 },
        { tipo = "coletar", item = 41003, quantidade = 1 },
    },
    recompensa = { xp = 1500, gold = 800 },
})

quest:addEtapa({
    nome = "O Selamento",
    descricao = "Retorne ao Guardiao das Profecias com os tres artefatos para selar o poder antigo.",
    objetivos = {
        { tipo = "falar", npc = "Guardiao das Profecias", quantidade = 1 },
        { tipo = "entregar", item = 41001, quantidade = 1 },
        { tipo = "entregar", item = 41002, quantidade = 1 },
        { tipo = "entregar", item = 41003, quantidade = 1 },
    },
    recompensa = { xp = 3000, gold = 1500 },
})

quest:setRecompensaFinal({
    xp = 5000,
    gold = 2000,
    itens = {
        { id = 41004, quantidade = 1 }, -- Amuleto do Heroi
        { id = 40003, quantidade = 5 }, -- Pocoes de experiencia
    },
})

print("Quest O Despertar de Eridanus carregada.")
