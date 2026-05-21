--[[
    Projeto MCR ? SPA v4.0 ? Inicializador
    Regista os domínios base e prepara o ambiente.
    Os domínios específicos (Desarmado, etc.) são registados nos seus próprios ficheiros.
--]]

-- Garantir que as tabelas globais existem
SPA = SPA or {}
HABILIDADES = HABILIDADES or {}

-- Domínios Primários
SPA.registerDomain(1, "Combate")
SPA.registerDomain(2, "Magia")
SPA.registerDomain(3, "Ofícios")
SPA.registerDomain(4, "Natureza")

-- Secundários de Combate
SPA.registerDomain(10, "Lâminas", 1)
SPA.registerDomain(11, "Machados", 1)
SPA.registerDomain(12, "Clavas", 1)
SPA.registerDomain(13, "Precisão", 1)
SPA.registerDomain(14, "Desarmado", 1)
SPA.registerDomain(15, "Escudo", 1)

-- Secundários de Magia
SPA.registerDomain(20, "Elementos", 2)
SPA.registerDomain(21, "Espectro", 2)
SPA.registerDomain(22, "Runologia", 2)

-- Especialidades de Combate
SPA.registerDomain(100, "Espadas Leves", 10)
SPA.registerDomain(101, "Espadas Pesadas", 10)
SPA.registerDomain(110, "Machados Leves", 11)
SPA.registerDomain(111, "Machados Pesados", 11)
SPA.registerDomain(112, "Clavas Leves", 12)
SPA.registerDomain(113, "Clavas Pesadas", 12)
SPA.registerDomain(120, "Arcos", 13)
SPA.registerDomain(121, "Arremesso", 13)

-- Especialidades de Desarmado (novo)
SPA.registerDomain(130, "Desarmado Puro", 14)
SPA.registerDomain(131, "Desarmado com Escudo", 14)
SPA.registerDomain(132, "Armas de Punho", 14)
SPA.registerDomain(133, "Bastões Arcanos", 14)

-- Especialidades Mágicas
SPA.registerDomain(23, "Fogo e Ar", 20)
SPA.registerDomain(24, "Água e Gelo", 20)
SPA.registerDomain(25, "Terra e Veneno", 20)
SPA.registerDomain(200, "Sagrado e Morte", 21)
SPA.registerDomain(210, "Wands", 22)
SPA.registerDomain(211, "Rods", 22)
SPA.registerDomain(212, "Runas", 22)

-- Outros
SPA.registerDomain(400, "Sobrevivência", 4)

-- Preencher ALL_DOMINIOS com os IDs registados
for _, id in ipairs(SPA.getAllDomainIds()) do
    table.insert(ALL_DOMINIOS, id)
end

print("DEBUG: SPA v4.0 inicializado com sucesso.")