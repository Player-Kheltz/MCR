"""
STOP WORDS CENTRALIZADAS — Usado por mcr_devia.py, context_crew.py, crew_pattern.py
Evita duplicacao de listas entre arquivos.
"""

# Stop words para busca V12 (keyword matching no KG)
STOP_V12 = {
    'como','para','que','com','mais','mas','por','dos','das','era','sao',
    'isso','entre','sobre','antes','depois','tem','ser','seu','sua','todo',
    'pode','muito','pouco','quando','onde','assim','apos','ate','sem','sob',
    'fazer','ter','estar','ficar','ainda','bem','ja','nao','sim','vai','foi',
    'em','e','o','a','de','da','do','no','na','um','uma','leia','arquivo',
    'voce','ele','ela','nos','vos','eles','elas','meu','seu','esta','esse',
    'aquele','mesmo','forma','parte','cada','maior','menor','melhor','outro',
    'novo','grande','pequeno','durante','atraves','todos','entao','tambem',
    'apenas','agora','sempre','nunca','talvez','quase','dentro','fora','cima',
    'baixo','sobre','tudo','vai','foi','era','sao','estao','foram','serao',
    'seja','sejam','sido','tido','feito','dito','visto','lido','vindo','tendo',
    'sendo','estando','feita','dita','vista','lida','vinda','feitos','ditos',
    'vistos','lidos','vindos','feitas','ditas','vistas','lidas','vindas',
    'sou','e','ou','mas','se','ate','por','com','sem','sob','ate','desde',
}

# Stop words especificas para pipeline de busca (grep)
STOP_BUSCA = {
    'como','para','que','com','mais','mas','por','dos','das','era','sao',
    'isso','aquele','entre','sobre','antes','depois','durante','atraves',
    'todos','voce','esta','esse','mesmo','forma','parte','ser','tem','seu',
    'sua','todo','toda','tudo','cada','maior','menor','melhor','pode','muito',
    'pouco','outro','novo','grande','pequeno','quando','onde','assim','apos',
    'ate','sem','sob','fazer','dizer','ter','estar','ficar','saber','poder',
    'querer','achar','ainda','bem','ja','nao','sim','vai','era','foi','sao',
    'estao','foram','serao','seja','sejam','sido','tido','feito','dito',
    'visto','lido','vindo','tendo','sendo','estando','feita','dita','vista',
    'lida','vinda','feitos','ditos','vistos','lidos','vindos','feitas','ditas',
    'vistas','lidas','vindas','em','e','o','a','de','da','do','no','na','um','uma',
}

# Palavras-chave comuns do projeto MCR (para V12 dar match mais facil)
KEYWORDS_MCR = {
    'mcr', 'shc', 'spa', 'canary', 'otclient', 'tfs', 'eridanus',
    'dominio', 'dominios', 'kg', 'v12', 'crew', 'contextcrew',
    'tibia', 'otserv', 'npc', 'monster', 'quest', 'item', 'spell',
    'lore', 'runa', 'runas', 'artigo', 'genero', 'validador',
    'compilar', 'compilacao', 'vs2022', 'vs2026', 'vcpkg',
    'bridge', 'ollama', 'qwen', 'llama', 'deepseek',
    'aprender', 'ensinar', 'perguntar', 'analisar', 'extrair',
    'knowledge', 'graph', 'licao', 'licoes', 'pipeline',
}
