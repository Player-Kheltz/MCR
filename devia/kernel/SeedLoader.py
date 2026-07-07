"""SeedLoader — converte PERSONALIDADE.md em seeds para MarkovDecider + ContextCrew.

Três cargas:
1. carregar_analises() → seeds de classificação (12 seções → MarkovDecider)
2. carregar_contexto() → fragmentos de contexto (Sistemas MCR → ContextCrew)
3. carregar_regras() → regras de validação (14 regras → AutorevisaoTracker)
"""
import os

# ─── SEEDS DAS 12 SEÇÕES DE ANÁLISE (PERSONALIDADE.md linhas 228-420) ─────

SEEDS_ANALISE = {
    "analisar_bug": [
        "crash no servidor",
        "null pointer exception",
        "dangling pointer",
        "double free detectado",
        "memory leak em",
        "buffer overflow",
        "integer overflow",
        "signed unsigned bug",
        "race condition",
        "deadlock no spawn",
        "uso incorreto de mutex",
        "concorrencia insegura",
        "callback invalido",
        "recurso nao liberado",
        "codigo morto",
        "comportamento inesperado",
        "serializacao incorreta",
        "inconsistencia entre cliente e servidor",
        "incompatibilidade de protocolo",
        "sql injection",
        "credentials hardcoded",
        "coredump",
        "segfault",
        "stack overflow",
        "heap corruption",
        "use after free",
        "uninitialized variable",
        "divisao por zero",
        "loop infinito",
        "vazamento de memoria",
    ],
    "analisar_performance": [
        "loop critico",
        "pathfinding lento",
        "consulta sql sem indice",
        "carregamento repetido",
        "alocacao frequente",
        "fragmentacao de memoria",
        "uso excessivo de string",
        "copia desnecessaria",
        "container stl inadequado",
        "object pool necessario",
        "cache de dados faltando",
        "renderizacao lenta",
        "draw call excessivo",
        "leitura integral de log",
        "parsing lento com regex",
    ],
    "analisar_arquitetura": [
        "organizacao de modulos",
        "separacao de responsabilidades",
        "acoplamento alto",
        "baixa coesao",
        "dependencia ciclica",
        "falta de injecao de dependencia",
        "mvvm ausente",
        "singleton sem interface",
        "caminhos relativos ageis",
        "arquitetura de eventos",
        "integracao cpp lua",
        "api interna mal definida",
    ],
    "revisar_codigo": [
        "funcao muito grande",
        "classe muito grande",
        "arquivo muito grande",
        "codigo duplicado",
        "macros excessivas",
        "numero magico",
        "switch gigante",
        "ifs excessivos",
        "responsabilidades misturadas",
        "heranca desnecessaria",
        "baixo encapsulamento",
        "comentario incorreto",
        "nome pouco descritivo",
        "violacao de solid",
        "violacao de raii",
        "const correctness",
    ],
    "analisar_seguranca": [
        "validacao insuficiente",
        "pacote malformado",
        "packet injection",
        "packet spoofing",
        "flood de pacotes",
        "abuso de protocolo",
        "opcode invalido",
        "lua injection",
        "corrupcao de memoria",
        "acesso fora dos limites",
        "serializacao insegura",
        "carregamento inseguro",
        "exploit grafico",
        "interpolacao de sql",
    ],
    "modernizar_codigo": [
        "std optional",
        "std span",
        "std expected",
        "constexpr",
        "enum class",
        "ranges",
        "concepts",
        "smart pointers",
        "async await",
        "cancellation token",
        "di container",
        "view model",
    ],
    "revisar_lua": [
        "organizacao de script lua",
        "reutilizacao de codigo lua",
        "callback lua",
        "evento lua",
        "api lua incorreta",
        "modularizacao lua",
        "dependencia lua",
        "logging mcr",
        "encoding utf8 lua",
        "tolatina1 antes do protocolo",
    ],
    "analisar_gameplay": [
        "combate desbalanceado",
        "criatura desbalanceada",
        "npc sem personalidade",
        "quest mal projetada",
        "progressao quebrada",
        "crafting desbalanceado",
        "loot excessivo",
        "economia inflacionada",
        "mercado quebrado",
        "guilda sem funcionalidade",
        "party desbalanceado",
        "raid mal feita",
        "evento sem graca",
        "achievement impossivel",
        "sistema de progressao",
        "encantamento",
    ],
    "verificar_compatibilidade": [
        "compatibilidade canary otclient",
        "compatibilidade canary rme",
        "compatibilidade canary grimorio",
        "protocolo incompativel",
        "opcode desatualizado",
        "asset faltando",
        "sprite incorreto",
        "mapa corrompido",
        "otb desatualizado",
        "otbm incompativel",
        "xml malformado",
        "versao de protocolo",
        "compatibilidade retroativa",
    ],
    "avaliar_ferramentas": [
        "build system",
        "cmake mal configurado",
        "organizacao do projeto",
        "dependencia externa",
        "ci cd quebrado",
        "teste automatizado faltando",
        "documentacao desatualizada",
        "script utilitario quebrado",
        "deploy manual",
    ],
    "sugerir_feature": [
        "melhoria de desempenho",
        "sistema de metricas",
        "monitoramento",
        "profiling",
        "log estruturado",
        "sistema de eventos",
        "hot reload",
        "ferramenta de admin",
        "anti cheat",
        "auditoria",
        "melhoria de ui",
        "hud",
        "notificacao",
        "efeito grafico",
        "qualidade de vida",
        "ferramenta de produtividade",
        "validacao automatica",
        "edicao em lote",
        "login seguro",
        "cache de dados",
    ],
    "gerar_relatorio": [
        "crie um relatorio",
        "analise o projeto",
        "resumo executivo",
        "analysis report",
        "levantamento de bugs",
        "diagnostico completo",
        "auditoria de codigo",
    ],
}

# ─── SEEDS DOS 15 CRITÉRIOS DE ANÁLISE (PERSONALIDADE.md linhas 204-222) ───

SEEDS_CRITERIOS = {
    "verificar_dominio_identidade": [
        "sentimento central do dominio",
        "3 adjetivos do dominio",
        "frase de assinatura",
        "cor do dominio",
        "identidade do dominio",
    ],
    "verificar_hierarquia_pai_filho": [
        "getNivelEfetivo",
        "dominio pai nao verifica filho",
        "hierarquia de dominio",
        "propagacao 4 2 1",
    ],
    "verificar_feedback_narrativo": [
        "padrao limpo v3 3",
        "feedback narrativo",
        "cor cond acao sucesso",
        "3 4 palavras coloridas",
        "travessao longo",
    ],
    "verificar_rastreabilidade": [
        "mcr stair",
        "mcr cogni",
        "mcr engage",
        "mcr return",
        "mcr player",
        "mcr walk",
        "mcr route",
        "mcr explore",
        "mcr debug",
        "prefixo de log",
    ],
    "verificar_pilares": [
        "jornada 100 no cliente",
        "escopo maximo de customizacao",
        "idioma oficial pt br",
        "imersao narrativa",
        "experiencia moderna",
        "rastreabilidade por logs",
        "progressao organica",
    ],
    "verificar_categoria_gatilho": [
        "categoria aoe",
        "categoria single",
        "categoria debuff",
        "categoria buff",
        "categoria finisher",
        "categoria sinergia",
        "categoria defense",
        "campo categoria obrigatorio",
    ],
    "verificar_passivas_vida_mana": [
        "passiva de vida",
        "passiva de mana",
        "passiva de velocidade",
        "campo efeito vazio",
        "recalcularVidaMana",
        "recalcularVelocidade",
    ],
    "verificar_magic_effect": [
        "magicEffect opcional",
        "efeito visual coerente",
        "conditionMagicEffect",
        "fallback EFEITOS_ELEMENTAIS",
    ],
    "verificar_condicao_foco": [
        "condicaoFocoMin",
        "foco minimo 0",
        "foco minimo 25",
        "foco minimo 50",
        "foco minimo 75",
        "foco minimo 90",
    ],
    "verificar_distribuicao_categorias": [
        "limite de categoria",
        "aoe max 2",
        "single max 3",
        "debuff max 2",
        "buff max 2",
        "finisher max 1",
        "sinergia max 2",
        "defense max 2",
        "distribuicao equilibrada",
    ],
    "verificar_efeito_config": [
        "efeitoConfig em vez de efeito",
        "efeito manual",
        "gatilho modular",
    ],
    "verificar_cooldowns": [
        "cooldown desbalanceado",
        "prioridade desbalanceada",
        "tempo de recarga",
    ],
    "verificar_sinergia_escalonada": [
        "sinergia_escalonada",
        "efeitosSecundarios manual",
        "efeitoBase",
        "efeitosPorDominio",
        "efeitoEpico",
    ],
    "verificar_encoding": [
        "utf8 literal no cpp",
        "utf8 no msvc",
        "tolatina1 antes do protocolo",
        "lua como latin1",
        "encoding utf8 xml",
    ],
}

# ─── CONTEXTO DOS SISTEMAS MCR (PERSONALIDADE.md linhas 54-146) ────────────

CONTEXTO_SISTEMAS = [
    {
        "tag": "spa",
        "conteudo": "SPA - Sistema de Progressao do Aventureiro. Fim das vocacoes, todo personagem vocation=0. Hierarquia: Primarios (Combate 1, Magia 2, Oficios 3, Natureza 4) -> Secundarios (Laminas 10, ...) -> Especialidades (Espadas Leves 100, ...). Propagacao 4:2:1. Curva de nivel getNivelEfetivo. Estados de Alma: Lampejo, Vinculo, Maestria. Posturas: Impeto, Equilibrio, Guarda. Traco Inerente nos niveis 5/10/15/20.",
        "docs": ["MCR - Filosofia do SPA.txt", "MCR - Documentacao Tecnica do Motor SPA.txt"],
    },
    {
        "tag": "habilidades",
        "conteudo": "Habilidades SPA - Arquitetura modular em 3 camadas: Motor (motor_habilidades.lua v2.0) com 27 tipos de efeito, Definicoes (habilidades_*.lua) com apenas parametros em efeitoConfig, Narrativa (narrativa_habilidades.lua) com feedback automatico. Tipos de efeito: classico, modular, temporal, estrategico, invocacao. Campos obrigatorios: nome, tipo, dominio, nivelMin, descricaoEfeito, cor, efeitoConfig. Categoria obrigatoria para gatilhos.",
        "docs": ["13 - MCR - Guia de Criacao de Habilidades.txt", "Gabarito Habilidade Gabarito.txt"],
    },
    {
        "tag": "shc",
        "conteudo": "SHC - Sistema de Habilidades Contextuais. 5 camadas de resolucao: Postura, Nivel (5/10/15/20), Sinergias (outros dominios), Estados (Vinculo/Lampejo), Condicoes (cercado, vida baixa). Arquivos: contexto.lua, executor.lua v10.0, motor_habilidades.lua v2.0.",
        "docs": ["Sistema de Habilidades Contextuais/00 - INDICE.txt"],
    },
    {
        "tag": "multipiso",
        "conteudo": "Perseguicao Multi-Piso v3.2.0. Maquina de 5 estados: COMBATE > PERSEGUICAO MULTI-PISO > PLANEAMENTO DE ESCADA > RETORNO AO SPAWN > IDLE. Estruturas: GlobalMonsterMap, StairTransition, SurfaceWaypoint. Algoritmos: A* segmentado com escadas, atalho multi-piso, rota alternativa. Anti-ping-pong com penalizacao +10000. Diferenca entre summons (nunca desistem) e hostis (retornam ao spawn).",
        "docs": ["MCR - Sistema de Perseguicao Multi-Piso.txt"],
    },
    {
        "tag": "mountsummon",
        "conteudo": "MountSummon - Sistema de Montarias. Desmontar cria CriaturaSPA em tile adjacente livre. force=true faz summon nascer no tile do jogador ignorando colisao. Persistencia KV: mount-state, mount-hp, pet-id, mount-id, mount-client-id. Velocidade: playerSpeed * 1.1. Inventario de 20 slots.",
        "docs": ["MCR - Sistema de Montaria como Summon (MountSummon).txt"],
    },
    {
        "tag": "pets",
        "conteudo": "Pets e Invocacao (Summon 28). SUMMON_CONFIGS define criaturas invocaveis. Duracao escala com barra de foco. IA modular (summon_ai.lua). PetSystem (pet_system.lua): getPets(), addPet(), removePet(), getPetMax(). SPAManager C++: m_playerPets, m_petMaster, m_petData.",
        "docs": [],
    },
    {
        "tag": "sqh",
        "conteudo": "SQH - Sistema de Quests Hibrido. Combina profundidade narrativa do chat com feedback visual (HUD, notificacoes toast). Sem janelas modais para progresso. Palavras destacadas com {chaves} e cores c(). Progresso em storages 50000-50999. Recompensas diretas no inventario. Uso de pronouns.lua para pronomes.",
        "docs": ["7 - MCR - Guia de Quests (Sistema Hibrido SQH).txt"],
    },
    {
        "tag": "npc",
        "conteudo": "NPCs MCR com personalidade definida. 4 niveis de intimidade: 0 Desconhecido, 1 Conhecido, 2 Amigo, 3 Confidente. Personalidades: Sábio caloroso, Guerreiro rude, Mistico enigmatico, Comerciante astuto. Uso de pronouns.lua para tratamento. Sistema de cores COR v10.0 com c() e enviarMsgColorida. NUNCA usar }? junto, sempre } ?.",
        "docs": ["6 - MCR - Guia de Narrativa e Dialogos.txt"],
    },
    {
        "tag": "encoding",
        "conteudo": "Encoding: .lua salvo como ISO-8859-1 (Latin-1). .cpp com /utf-8 no MSVC. Strings que saem pelo protocolo DEVEM passar por toLatin1() antes de msg.addString(). XML com encoding=UTF-8. Python e Go usam UTF-8 natural.",
        "docs": ["DevLog/Sistema de Codificacao.md"],
    },
    {
        "tag": "cor",
        "conteudo": "Sistema de cores COR v10.0. Tabela com ~70 cores: COND_*, ACAO_*, DANO_*, ELEM_*, DOM_*, NPC_*, MISSAO_*, POSTURA_*. Funcao c(texto, cor) formata {texto, #Cor}. enviarMsgColorida(player, texto) no canal 24. Padrao limpo v3.3: max 3-4 palavras coloridas por frase.",
        "docs": [],
    },
]

# ─── REGRAS DE CONDUTA (PERSONALIDADE.md linhas 489-502) ───────────────────

REGRAS_CONDUTA = [
    "Nao invente problemas. Baseie todas as conclusoes exclusivamente no codigo.",
    "Sempre informe o arquivo, classe e funcao envolvidos.",
    "Quando nao houver certeza, marque como 'Hipotese'.",
    "Priorize estabilidade, desempenho e compatibilidade.",
    "Considere o impacto sobre servidor, cliente, editor e Grimorio antes de sugerir alteracoes.",
    "Sempre que possivel, proponha mudancas pequenas, incrementais e adequadas para Pull Requests independentes.",
    "Evite sugestoes genericas; prefira melhorias especificas, justificadas e tecnicamente viaveis.",
    "Sempre considere a interacao entre C++, Lua, C#, banco de dados e protocolo de rede.",
    "Respeite a compatibilidade com versoes existentes.",
    "Siga os Pilares Permanentes do MCR e as regras de encoding.",
    "Inclua uma secao 'Autorevisao do Assistente' na resposta sempre que criar ou modificar um arquivo, listando quais documentos foram consultados e como cada pilar/regra foi respeitado.",
]

# ─── PILARES PERMANENTES (PERSONALIDADE.md linhas 36-46) ───────────────────

PILARES = [
    ("1", "Jornada 100% no Cliente - nenhuma experiencia essencial fora do OTClient"),
    ("2", "Escopo Maximo de Customizacao - qualquer componente pode ser modificado em nivel de codigo-fonte"),
    ("3", "Idioma Oficial PT-BR - strings visiveis, comentarios, logs e documentacao em portugues com acentuacao"),
    ("4", "Imersao Narrativa - mundo de fantasia original, NPCs com personalidade e reacao ao contexto"),
    ("5", "Experiencia Moderna - {chaves} destacadas, cores c(), HUD, notificacoes toast"),
    ("6", "Rastreabilidade por Logs - prefixos [MCR-*] em todo script condicional"),
    ("7", "Progressao Organica e Modular - SPA substitui vocacoes, afinidade 4:2:1, Estados de Alma"),
]


def carregar_analises(markov_decider):
    """Carrega as 12 secoes de analise como seeds no MarkovDecider."""
    count = 0
    for classe, exemplos in SEEDS_ANALISE.items():
        for exemplo in exemplos:
            markov_decider.aprender(exemplo, classe)
            count += 1
    return count


def carregar_criterios(markov_decider):
    """Carrega os 15 criterios de analise como seeds no MarkovDecider."""
    count = 0
    for classe, exemplos in SEEDS_CRITERIOS.items():
        for exemplo in exemplos:
            markov_decider.aprender(exemplo, classe)
            count += 1
    return count


def carregar_contexto(context_crew):
    """Carrega contexto dos sistemas MCR no ContextCrew."""
    for ctx in CONTEXTO_SISTEMAS:
        if hasattr(context_crew, 'adicionar'):
            context_crew.adicionar(ctx["tag"], ctx["conteudo"])
    return len(CONTEXTO_SISTEMAS)


def carregar_tudo(markov_decider=None, context_crew=None):
    """Carrega todas as seeds de uma vez."""
    stats = {}
    if markov_decider:
        stats["analises"] = carregar_analises(markov_decider)
        stats["criterios"] = carregar_criterios(markov_decider)
    if context_crew:
        stats["contexto"] = carregar_contexto(context_crew)
    return stats
