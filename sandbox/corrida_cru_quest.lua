-- Quest: O Legado Perdido de Eridanus
-- Criado pelo MCR CRU (factory default)

local quest = Quest("O Legado Perdido de Eridanus")

quest:setDescricao("Ajude o Velho Sabio a recuperar os tres artefatos perdidos que protegem Eridanus.")
quest:setNivelMinimo(10)
quest:setNpcIniciador("Velho Sabio")

-- Etapa 1: Encontrar o Olho de Eridanus
quest:addEtapa({
    nome = "O Olho de Eridanus",
    descricao = "Explore a Mina Abandonada ao norte de Eridanus e encontre o Olho de Eridanus.",
    objetivos = {
        { tipo = "coletar", item = 30010, quantidade = 1, descricao = "Encontrar o Olho de Eridanus" },
    },
    recompensa = {
        xp = 500,
        gold = 200,
    },
})

-- Etapa 2: Encontrar a Chama Eterna
quest:addEtapa({
    nome = "A Chama Eterna",
    descricao = "Nas Ruinas do Templo a leste, encontre a Chama Eterna que nunca se apaga.",
    objetivos = {
        { tipo = "coletar", item = 30011, quantidade = 1, descricao = "Coletar a Chama Eterna" },
    },
    recompensa = {
        xp = 750,
        gold = 300,
    },
})

-- Etapa 3: Encontrar o Selo do Fundador
quest:addEtapa({
    nome = "O Selo do Fundador",
    descricao = "Na Biblioteca Antiga sob a cidade, decifre o enigma e obtenha o Selo do Fundador.",
    objetivos = {
        { tipo = "coletar", item = 30012, quantidade = 1, descricao = "Obter o Selo do Fundador" },
    },
    recompensa = {
        xp = 1000,
        gold = 500,
    },
})

-- Recompensa final
quest:setRecompensaFinal({
    xp = 2500,
    gold = 1000,
    itens = {
        { id = 30020, quantidade = 1 }, -- Amuleto do Fundador
        { id = 30021, quantidade = 3 }, -- Pocoes de Experiencia
    },
})

print("Quest O Legado Perdido de Eridanus carregada.")
