#!/usr/bin/env python3
"""mcr.mcr_world_builder — Pipeline de Mundo (Etapas 1-4).
Etapa 1: gerar_lore_com_feedback — LLM + loop de entropia por gap de conceitos.
Etapa 2: extrair_entidades — extrai nomes proprios + LLM estruturado.
Etapa 3: arquitetar_mundo — entidades -> ordens de servico (Build Orders).
Etapa 4: planejar_contexto — tarefa + lore -> dossier focado para o codificador."""
import json
import os
import re
import sys
import time
import urllib.request
from typing import Dict, List, Optional

OLLAMA_CHAT = "http://localhost:11434/api/generate"
from mcr.config_llm import MODELO_LORE, MODELO_CODIGO

MODELO = MODELO_CODIGO
MODELO_CHAT = MODELO_LORE

# Conceitos essenciais que a lore deve conter
_CONCEITOS_OBRIGATORIOS = {
    'conflito': ['conflito', 'guerra', 'batalha', 'disputa', 'conflito', 'revolta', 'invasao'],
    'personagem': ['rei', 'heroi', 'mago', 'guerreiro', 'lider', 'sacerdote', 'mestre'],
    'lugar': ['cidade', 'reino', 'floresta', 'montanha', 'vale', 'torre', 'templo', 'castelo'],
    'monstro': ['monstro', 'dragao', 'feras', 'criatura', 'bestas', 'demonio', 'espectro'],
    'magia': ['magia', 'feitico', 'encantamento', 'poder', 'energia', 'elemento', 'arcano'],
}

# Modelos de resposta para extrair entidades
_PROMPT_EXTRACAO = (
    "Leia o texto abaixo e extraia as entidades.\n"
    "Retorne APENAS um JSON valido no formato:\n"
    '{"personagens": [], "monstros": [], "lugares": [], "conflito": "string"}\n'
    "Nada mais. Nenhum texto antes ou depois do JSON.\n\n"
    "TEXTO:\n"
)


def _chamar_llm(prompt: str, max_tokens: int = 600) -> Optional[str]:
    """Chama o Mistral 7B via Ollama."""
    try:
        payload = json.dumps({
            "model": MODELO_LORE, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.8, "max_tokens": max_tokens}
        }).encode()
        req = urllib.request.Request(OLLAMA_CHAT, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read())
        return resp.get('response', '').strip()
    except Exception as e:
        print('[WorldBuilder] Erro LLM: %s' % e)
        return None


def _avaliar_gap(texto: str) -> List[str]:
    """Avalia quais conceitos estao faltando no texto usando contagem de keywords."""
    texto_lower = texto.lower()
    faltando = []
    for conceito, keywords in _CONCEITOS_OBRIGATORIOS.items():
        count = sum(1 for kw in keywords if kw in texto_lower)
        if count == 0:
            faltando.append(conceito)
    return faltando


def gerar_lore_com_feedback(tema: str) -> str:
    """Gera lore com loop de feedback por entropia de conceitos.
    
    1. Gera lore inicial via LLM.
    2. Avalia gaps de conceitos.
    3. Se houver gap, chama LLM novamente pedindo para incluir o conceito faltante.
    4. Maximo 2 iteracoes.
    """
    print('[WorldBuilder] Gerando lore sobre: %s' % tema)

    prompt_inicial = (
        "Crie uma lore de 3 paragrafos para o seguinte tema:\n%s\n\n"
        "Inclua: personagens, lugares, um conflito central, e elementos de magia.\n"
        "Seja descritivo e imersivo.\n\nLore:" % tema
    )

    lore = _chamar_llm(prompt_inicial, max_tokens=800)
    if not lore:
        return '[Erro] Falha ao gerar lore.'

    print('[WorldBuilder] Lore inicial gerada (%d chars)' % len(lore))

    # Loop de feedback
    for tentativa in range(2):
        gaps = _avaliar_gap(lore)
        if not gaps:
            print('[WorldBuilder] Nenhum gap detectado.')
            break

        print('[WorldBuilder] Conceitos faltantes detectados: %s. Reescrevendo...' % ', '.join(gaps))
        prompt_refinamento = (
            "A lore abaixo nao detalha suficientemente os seguintes conceitos: %s.\n"
            "Reescreva a lore INTEIRA incluindo estes elementos de forma natural.\n\n"
            "=== LORE ATUAL ===\n%s\n\n=== NOVA LORE (reescrita completa):" % (', '.join(gaps), lore)
        )

        nova_lore = _chamar_llm(prompt_refinamento, max_tokens=800)
        if nova_lore:
            lore = nova_lore
            print('[WorldBuilder] Lore reescrita (%d chars)' % len(lore))
        else:
            break

    print('[WorldBuilder] Lore final: %d chars, %d iteracoes' % (len(lore), tentativa + 1))
    return lore


def extrair_entidades(lore: str) -> Dict:
    """Extrai entidades da lore usando regex + LLM.
    
    Returns:
        dict com personagens, monstros, lugares, conflito.
    """
    if not lore:
        return {'personagens': [], 'monstros': [], 'lugares': [], 'conflito': ''}

    # 1. Regex: extrai nomes proprios (palavras com maiuscula no meio do texto)
    # Palavras com > 3 chars que comecam com maiuscula e nao estao no inicio da frase
    nomes_proprios = re.findall(r'(?<![.!?]\s)[A-Z][a-zà-ú]{3,}', lore)
    # Remove duplicatas mantendo ordem
    vistos = set()
    nomes_unicos = []
    for n in nomes_proprios:
        if n.lower() not in vistos:
            vistos.add(n.lower())
            nomes_unicos.append(n)

    # 2. LLM: extrai estruturado
    prompt = _PROMPT_EXTRACAO + lore
    resposta_llm = _chamar_llm(prompt, max_tokens=400)

    entidades = {'personagens': [], 'monstros': [], 'lugares': [], 'conflito': ''}

    if resposta_llm:
        # Tenta limpar marcacoes markdown
        texto = resposta_llm.strip()
        if '```json' in texto:
            texto = texto.split('```json')[1].split('```')[0].strip()
        elif '```' in texto:
            texto = texto.split('```')[1].split('```')[0].strip()

        try:
            parsed = json.loads(texto)
            if isinstance(parsed, dict):
                entidades = {
                    'personagens': parsed.get('personagens', []),
                    'monstros': parsed.get('monstros', []),
                    'lugares': parsed.get('lugares', []),
                    'conflito': parsed.get('conflito', ''),
                }
        except json.JSONDecodeError:
            # Fallback: usa os nomes proprios extraidos por regex
            entidades['personagens'] = nomes_unicos[:5]
            entidades['conflito'] = 'Nao foi possivel extrair. Verificar LLM.'

    # Preenche lugares com regex se o LLM nao retornou
    if not entidades['lugares']:
        lugares_regex = re.findall(r'(?:em |na |no |para |de )([A-Z][a-zà-ú]{3,})', lore)
        entidades['lugares'] = list(set(lugares_regex))[:5]

    return entidades


# ─── Etapa 3: Arquiteto Geral ────────────────────────────────

# Palavras do tema que indicam comercio para gerar papeis semanticos
_TERMOS_COMERCIO = {
    'feira', 'mercador', 'mercadores', 'comercio', 'comerciante', 'comerciantes',
    'venda', 'vendedor', 'vendedores', 'loja', 'lojas', 'shop', 'shopping',
    'mercado', 'bazar', 'leilao', 'troca', 'escambo', 'negocio', 'negocios',
    'item', 'itens', 'pocao', 'pocoes', 'arma', 'armas', 'armadura', 'ferreiro',
}

# Papel gerado para NPCs conforme o tema detectado
_PAPEIS_COMERCIO = [
    'Mercador na feira',
    'Vendedor de pocoes e itens magicos',
    'Comerciante de armas e armaduras',
    'Mestre de negocios',
    'Vendedor de itens exoticos',
    'Guarda da feira',
    'Leiloeiro do bazar',
    'Alquimista vendendo pocoes',
    'Ferreiro negociando equipamentos',
    'Banqueiro da feira',
]


def _detectar_contexto_tema(tema: str) -> str:
    """Detecta se o tema e de comercio e retorna palavras-chave semanticas."""
    if not tema:
        return ''
    tema_lower = tema.lower()
    palavras = set(re.findall(r'\b[a-z]{3,}\b', tema_lower))
    match = palavras & _TERMOS_COMERCIO
    if match:
        print('[Arquiteto] Tema comercial detectado: %s' % ', '.join(sorted(match)))
        return 'comercio'
    return ''


def _gerar_papel_npc(nome: str, conflito: str, contexto_tema: str) -> str:
    """Gera papel contextual para NPC baseado no tema e no conflito."""
    import random
    if contexto_tema == 'comercio':
        idx = random.randint(0, len(_PAPEIS_COMERCIO) - 1)
        papel = _PAPEIS_COMERCIO[idx]
        if conflito:
            return '%s durante: %s' % (papel, conflito)
        return '%s' % papel
    # Fallback: papel generico baseado no conflito
    if conflito:
        return 'Personagem da historia: %s' % conflito
    return 'Figura central do mundo'


def arquitetar_mundo(entidades: dict, tema: str = '') -> list:
    """Recebe entidades + tema e retorna ordens de servico (Build Orders).

    Analisa o tema para detectar contexto (comercio, combate, magia, etc.)
    e gera papeis semanticos apropriados que disparam a busca nivel 1
    no _carregar_padroes.

    Para cada personagem -> ordem npc.
    Para cada monstro -> ordem monster.
    Para cada lugar -> ordem lugar (armazenamento de contexto).
    """
    contexto_tema = _detectar_contexto_tema(tema)
    ordens = []
    conflito = entidades.get('conflito', '')

    for nome in entidades.get('personagens', []):
        papel = _gerar_papel_npc(nome, conflito, contexto_tema)
        ordens.append({
            'tipo': 'npc',
            'nome': nome,
            'papel': papel,
        })

    for nome in entidades.get('monstros', []):
        ordens.append({
            'tipo': 'monster',
            'nome': nome,
            'papel': 'Ameaca na historia: %s' % (conflito if conflito else 'criatura do mundo'),
        })

    for nome in entidades.get('lugares', []):
        ordens.append({
            'tipo': 'place',
            'nome': nome,
            'papel': 'Cenario da historia: %s' % (conflito if conflito else 'localizacao'),
        })

    return ordens


# ─── Etapa 4: Planejador de Contexto ─────────────────────────

def _extrair_frases_contexto(lore: str, termos: list) -> str:
    """Extrai frases da lore que mencionam qualquer um dos termos."""
    frases = re.split(r'(?<=[.!?])\s+', lore)
    selecionadas = []
    for frase in frases:
        frase_lower = frase.lower()
        for termo in termos:
            if termo.lower() in frase_lower:
                selecionadas.append(frase.strip())
                break
    return '\n'.join(selecionadas[:10]) if selecionadas else lore[:500]


def planejar_contexto(tarefa: dict, lore: str) -> str:
    """Gera um Dossie de Construcao focado na tarefa.
    
    Filtra a lore para apenas as frases que mencionam a entidade da tarefa,
    e monta um prompt direto para o codificador Lua.
    """
    nome = tarefa.get('nome', '')
    papel = tarefa.get('papel', '')
    tipo = tarefa.get('tipo', 'generic')

    # Termos de busca: nome da entidade + conflito
    termos_busca = [nome] if nome else []
    if papel:
        # Extrai palavras-chave do papel
        for palavra in re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', papel):
            termos_busca.append(palavra)

    contexto_filtrado = _extrair_frases_contexto(lore, termos_busca)

    dossie = (
        "[CONTEXTO DO MUNDO]\n"
        "%s\n\n" % contexto_filtrado +
        "[SUA TAREFA]\n"
        "Voce e %s. Papel: %s.\n" % (nome, papel) +
        "Escreva um script Lua para o servidor Canary.\n"
        "Use as APIs corretas do Canary (%s).\n" % (
            'Game.createNpcType, npcConfig, KeywordHandler' if tipo == 'npc' else
            'Game.createMonsterType, monsterConfig' if tipo == 'monster' else
            'Game.createNpcType'
        ) +
        "Nao invente APIs. Seja criativo, mas use apenas as APIs reais."
    )

    return dossie


# ─── Etapa 5: Codificador Universal ───────────────────────────

def _filtrar_estrutura_exemplo(codigo: str, tipo: str) -> str:
    """Extrai apenas a estrutura essencial do golden example, ignorando
    callbacks complexos (onBuyItem, creatureSayCallback, etc.) que fazem
    o LLM alucinar APIs similares."""
    if tipo != 'npc':
        return codigo[:800]

    linhas = codigo.split('\n')
    estrutura = []
    dentro_callback = 0  # profundidade de escopo de callback

    for linha in linhas:
        # Detecta inicio de callback
        if any(pat in linha for pat in ['npcType.onBuyItem', 'npcType.onSellItem',
                'npcType.onCheckItem', 'npcType.onAppear', 'npcType.onDisappear',
                'npcType.onSay', 'npcType.onThink', 'npcType.onCloseChannel',
                'npcHandler:setCallback', 'npcHandler:addModule',
                'local function creatureSay', 'function creatureSay']):
            dentro_callback = 1
            if '{' in linha:
                dentro_callback += linha.count('{') - linha.count('}')
            continue

        # Rastreia profundidade de escopo
        if dentro_callback > 0:
            dentro_callback += linha.count('{') - linha.count('}')
            dentro_callback += linha.count('function(')  # funcoes aninhadas
            # end diminui escopo
            if linha.strip().startswith('end') or linha.strip() == 'end':
                dentro_callback -= 1
            if dentro_callback <= 0:
                dentro_callback = 0
            continue

        # Linhas de Cabeçalho de callback que escaparam (ex: "local function getTable()")
        if linha.strip().startswith('local function') or linha.strip().startswith('function('):
            continue

        estrutura.append(linha)

    codigo_filtrado = '\n'.join(estrutura)
    return codigo_filtrado[:800]


def _carregar_padroes(tipo: str, max_exemplos: int = 2, papel: str = '') -> str:
    """Busca Golden Examples reais do Canary com 3 niveis:
    1. Semantica no KG (api_calls + variables keywords)
    2. MCRRadar fingerprint
    3. Fallback aleatorio

    Filtra exemplos para incluir apenas codigo Canary (Game.createNpcType / Game.createMonsterType).
    """
    from mcr.paths import KG_DIR
    from mcr.mcr_radar import RadarMCR
    from mcr.encoding import read_file

    # Padroes Canary esperados em cada tipo
    _API_CANARY_NPC = 'Game.createNpcType'
    _API_CANARY_MONSTER = 'Game.createMonsterType'

    # Carrega padroes do KG filtrando por tipo
    padroes = []
    for fpath in sorted(KG_DIR.glob('patterns_*.json')):
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            for p in dados.get('padroes', dados if isinstance(dados, list) else []):
                if p.get('tipo') != tipo:
                    continue
                arquivo = p.get('arquivo', '')
                if not arquivo or not os.path.exists(arquivo):
                    continue
                # Filtro Canary: verifica se o arquivo usa a API correta
                try:
                    with open(arquivo, 'r', encoding='latin-1') as f_check:
                        primeiras = f_check.read(500)
                    api_canary = _API_CANARY_NPC if tipo == 'npc' else _API_CANARY_MONSTER
                    if api_canary not in primeiras:
                        continue  # pula exemplos de servidores antigos (TFS)
                except Exception:
                    continue
                padroes.append(p)
        except Exception:
            continue
    if not padroes:
        return ''

    # Fallback aleatorio se nao tem papel
    if not papel or len(papel) < 5:
        import random
        amostra = random.sample(padroes, min(max_exemplos, len(padroes)))
        blocos = []
        for p in amostra:
            try:
                codigo = read_file(p['arquivo'])
            except Exception:
                continue
            codigo = _filtrar_estrutura_exemplo(codigo, tipo)
            blocos.append('-- %s\n%s' % (os.path.basename(p['arquivo']), codigo))
        return '\n\n'.join(blocos)

    # NIVEL 1: Busca semantica no KG (api_calls + variables)
    palavras_chave = re.findall(r'\b[a-zA-Z]{3,}\b', papel.lower())
    mapa_semantico = {
        'vende': ['shop', 'buy', 'sell', 'trade', 'npcconfig.shop', 'onbuyitem', 'onsellitem'],
        'compra': ['shop', 'buy', 'trade', 'npcconfig.shop'],
        'vendedor': ['shop', 'buy', 'sell', 'npcconfig.shop'],
        'shop': ['shop', 'buy', 'sell', 'npcconfig.shop'],
        'mercador': ['shop', 'buy', 'sell', 'trade', 'npcconfig.shop', 'onbuyitem', 'onsellitem'],
        'mercadores': ['shop', 'buy', 'sell', 'trade', 'npcconfig.shop', 'onbuyitem', 'onsellitem'],
        'comerciante': ['shop', 'buy', 'sell', 'trade', 'npcconfig.shop', 'onbuyitem', 'onsellitem'],
        'feira': ['shop', 'buy', 'sell', 'trade', 'npcconfig.shop', 'onbuyitem', 'onsellitem', 'bazar'],
        'loja': ['shop', 'buy', 'sell', 'trade', 'npcconfig.shop'],
        'leiloeiro': ['shop', 'buy', 'sell', 'trade', 'bazar'],
        'banqueiro': ['bank', 'deposit', 'withdraw'],
        'alquimista': ['potion', 'item', 'clientid'],
        'item': ['item', 'itemname', 'clientid'],
        'missao': ['quest', 'storage', 'mission', 'reward', 'topic'],
        'quest': ['quest', 'storage', 'mission', 'reward', 'topic'],
        'guilda': ['guild'],
        'guarda': ['guard'],
        'magia': ['spell', 'magic', 'rune'],
        'treinador': ['train', 'skill'],
        'banco': ['bank', 'deposit', 'withdraw'],
        'ferreiro': ['smith', 'weapon', 'armor'],
        'pocao': ['potion'],
        'arma': ['weapon', 'sword'],
    }
    termos_busca = set()
    for palavra in palavras_chave:
        if palavra in mapa_semantico:
            termos_busca.update(mapa_semantico[palavra])
        termos_busca.add(palavra)
    if termos_busca:
        selecionados = []
        for p in padroes:
            vars_str = '|'.join(p.get('variaveis', []))
            api_str = '|'.join(p.get('api_calls', []))
            score = 0
            for termo in termos_busca:
                if termo in vars_str.lower() or termo in api_str.lower():
                    score += 1
            if score > 0:
                selecionados.append((score, p))
        if selecionados:
            selecionados.sort(key=lambda x: -x[0])
            print('[WorldBuilder] Busca semantica no KG: %d matches' % len(selecionados))
            # Re-ordena por PONTE_OTIMA (equacao MCR) para priorizar
            # exemplos com maior divergencia, especificidade e profundidade
            try:
                from mcr.mcr_meta import MCRMeta
                selecionados_com_ponte = []
                for score_sem, p in selecionados[:10]:  # top 10 semanticos
                    ponte = MCRMeta._calcular_ponte_otima(
                        p.get('api_calls', []),
                        p.get('variaveis', []),
                        p.get('tamanho_linhas', 50))
                    selecionados_com_ponte.append((score_sem, ponte, p))
                # Ordena por PONTE_OTIMA decrescente, desempate pelo score semantico
                selecionados_com_ponte.sort(key=lambda x: (-x[1], -x[0]))
                selecionados = [(s, p) for s, pt, p in selecionados_com_ponte]
                for s, p in selecionados[:max_exemplos]:
                    print('  [score=%d ponte=%.1f] %s' % (
                        s, MCRMeta._calcular_ponte_otima(
                            p.get('api_calls', []), p.get('variaveis', []),
                            p.get('tamanho_linhas', 50)),
                        os.path.basename(p.get('arquivo', ''))))
            except Exception:
                pass
            amostra = [p for _, p in selecionados[:max_exemplos]]
            blocos = []
            for p in amostra:
                try:
                    codigo = read_file(p['arquivo'])
                except Exception:
                    continue
                codigo = _filtrar_estrutura_exemplo(codigo, tipo)
                blocos.append('-- %s\n%s' % (os.path.basename(p['arquivo']), codigo))
            return '\n\n'.join(blocos)

    # NIVEL 2: MCRRadar fingerprint
    print('[WorldBuilder] Radar (fingerprint) para: %s' % papel)
    candidatos = []
    for p in padroes:
        arquivo = p.get('arquivo', '')
        if not arquivo or not os.path.exists(arquivo):
            continue
        try:
            conteudo = read_file(arquivo)
        except Exception:
            continue
        texto_busca = os.path.basename(arquivo) + ' ' + ' '.join(p.get('variaveis', []))
        texto_busca += ' ' + ' '.join(p.get('api_calls', [])) + ' ' + conteudo[:800]
        candidatos.append({'id': arquivo, 'texto': texto_busca, 'conteudo': conteudo})
    if candidatos:
        radar = RadarMCR()
        resultados = radar.buscar(papel, candidatos, funcao_similaridade=RadarMCR.fingerprint_sim)
        selecionados = resultados[:max_exemplos]
        if selecionados:
            print('[WorldBuilder] Radar encontrou %d exemplos' % len(selecionados))
            blocos = []
            for cand in selecionados:
                arquivo = cand['id']
                conteudo_raw = cand.get('conteudo', '') or read_file(arquivo)
                conteudo = _filtrar_estrutura_exemplo(conteudo_raw, tipo)
                blocos.append('-- %s\n%s' % (os.path.basename(arquivo), conteudo))
            return '\n\n'.join(blocos)

    # NIVEL 3: Fallback aleatorio
    print('[WorldBuilder] Fallback aleatorio para golden examples.')
    import random
    amostra = random.sample(padroes, min(max_exemplos, len(padroes)))
    blocos = []
    for p in amostra:
        try:
            codigo = read_file(p['arquivo'])
        except Exception:
            continue
        codigo = _filtrar_estrutura_exemplo(codigo, tipo)
        blocos.append('-- %s\n%s' % (os.path.basename(p['arquivo']), codigo))
    return '\n\n'.join(blocos)


def codificar(tarefa: dict, dossie: str) -> dict:
    """Gera codigo Lua para uma tarefa (NPC ou Monster).
    
    Busca Golden Examples reais no KG via MCRRadar.
    Validacao em 2 camadas: LuaValidator (sintaxe) + SanityValidator (semantica).
    """
    tipo = tarefa.get('tipo', '')
    nome = tarefa.get('nome', 'Entidade')
    papel = tarefa.get('papel', '')

    if tipo not in ('npc', 'monster'):
        return {'sucesso': False, 'erro': 'Tipo nao suportado: %s' % tipo}

    # Busca Golden Examples reais no KG via MCRRadar (busca semantica ativa)
    padroes = _carregar_padroes(tipo, papel=papel)
    if not padroes:
        return {'sucesso': False, 'erro': 'Nenhum padrao de %s no KG' % tipo}

    # Detecta se comercio para instrucao extra de shop
    e_comercio = any(t in papel.lower() for t in ['mercador', 'vendedor', 'comerciante',
                                                       'feira', 'shop', 'vende', 'compra'])
    instrucao_shop = (
        "Se o NPC vende/itens, use npcConfig.shop = { {itemName = ..., clientId = ..., buy = ..., sell = ...} }.\n"
        "NAO use onBuyItem, onSellItem, onSellCallback ou qualquer callback de venda. "
        "Essas funcoes NAO existem no Canary.\n"
        "Apenas a tabela npcConfig.shop com a lista de itens.\n"
    ) if e_comercio else ''

    # Prompt com Golden Examples reais + guia estrutural explicito
    padrao_canary = (
        "PADRAO ESTRUTURAL CANARY (use exatamente esta estrutura):\n"
        "-- 1. Crie o tipo\n"
        "local npcType = Game.createNpcType(nome)\n"
        "-- 2. Tabela de configuracao (NAO use npcType:metodos)\n"
        "local npcConfig = {}\n"
        "npcConfig.name = nome\n"
        "npcConfig.description = nome\n"
        "npcConfig.health = 100\n"
        "npcConfig.maxHealth = 100\n"
        "npcConfig.walkInterval = 2000\n"
        "npcConfig.walkRadius = 2\n"
        "npcConfig.outfit = {lookType = 136}\n"
        "npcConfig.flags = {floorchange = false}\n"
    )
    if e_comercio:
        padrao_canary += (
            "-- 3. Shop (se vende itens) — NAO use metodos, apenas a tabela:\n"
            "npcConfig.shop = {\n"
            '    {itemName = "mana potion", clientId = 238, buy = 50, sell = 20},\n'
            "}\n"
        )
    padrao_canary += (
        "-- 4. Dialogo\n"
        "local keywordHandler = KeywordHandler:new()\n"
        'keywordHandler:addKeyword({"oi"}, StdModule.say, {npc = npcType, text = "Ola!"})\n'
        "-- 5. Registro (NAO use metodos como :register sem config):\n"
        "npcType:register(npcConfig)\n\n"
    )

    prompt = (
        "%s\n\n" % dossie +
        "GOLDEN EXAMPLES REAIS DO CODIGO FONTE DO CANARY (use como referencia):\n"
        "%s\n\n" % padroes +
        padrao_canary +
        "Escreva um arquivo Lua completo para %s '%s'.\n" % (tipo, nome) +
        "Papel: %s\n" % papel +
        "Siga o PADRAO ESTRUTURAL CANARY acima. Nao invente APIs.\n"
        "Responda APENAS com o codigo Lua."
    )

    print('[WorldBuilder] Codificando %s "%s"...' % (tipo, nome))
    t0 = time.time()
    codigo = _gerar_codigo_llm(prompt)

    if not codigo:
        return {'sucesso': False, 'erro': 'Codigo vazio'}

    # -- Validacao em 2 camadas (sintaxe + semantica) --
    valido, erro_sintaxe = _validar_sintaxe(codigo)
    if not valido:
        print('[WorldBuilder] Sintaxe invalida. Tentando correcao...')
        prompt_corrigido = prompt + '\n\nCORRIGA O ERRO DE SINTAXE: %s' % erro_sintaxe
        codigo2 = _gerar_codigo_llm(prompt_corrigido)
        if codigo2:
            valido, erro_sintaxe = _validar_sintaxe(codigo2)
            if valido:
                codigo = codigo2

    if not valido:
        return {'sucesso': False, 'erro': 'Codigo invalido apos 2 tentativas'}

    # SanityValidator: detecta APIs alucinadas
    apis_desconhecidas = _validar_semantica(codigo, tipo)
    if apis_desconhecidas:
        print('[WorldBuilder] API alucinada detectada: %s. Rejeitado. Reescrevendo...' % ', '.join(apis_desconhecidas[:3]))
        apis_proibidas = '\n'.join('- %s' % a for a in apis_desconhecidas[:5])
        prompt_corrigido_base = (
            "CODIGO ANTERIOR (INVALIDO):\n%s\n\n" % codigo +
            "ERRO: As APIs abaixo NAO existem no Canary:\n%s\n\n" % apis_proibidas
        )
        if tipo == 'npc':
            prompt_corrigido_base += (
                "CORRECAO: No Canary, NPCs usam o padrao:\n"
                "  local npcType = Game.createNpcType(nome)\n"
                "  local npcConfig = {}\n"
                "  npcConfig.name = nome\n"
                "  npcConfig.shop = {{itemName = ..., clientId = ..., buy = ..., sell = ...}}\n"
                "  npcConfig.flags = {floorchange = false}\n"
                "  local keywordHandler = KeywordHandler:new()\n"
                "  keywordHandler:addKeyword({...}, StdModule.say, {npc = npcType, text = ...})\n"
                "  npcType:register(npcConfig)\n"
                "NAO use npcType:metodo() ou Game.createNpc. Use npcConfig.campo = valor.\n\n"
            )
        else:
            prompt_corrigido_base += (
                "CORRECAO: No Canary, Monsters usam o padrao:\n"
                "  local mType = Game.createMonsterType(nome)\n"
                "  local monster = {}\n"
                "  monster.name = nome\n"
                "  monster.race = \"blood\"\n"
                "  mType:register(monster)\n\n"
            )
        prompt_corrigido = (
            prompt_corrigido_base +
            "Reescreva o CODIGO COMPLETO corrigido seguindo o padrao acima. "
            "Nao invente APIs. Responda APENAS com codigo Lua valido:"
        )
        codigo3 = _gerar_codigo_llm(prompt_corrigido)
        if codigo3:
            valido3, _ = _validar_sintaxe(codigo3)
            apis3 = _validar_semantica(codigo3, tipo)
            if valido3 and not apis3:
                codigo = codigo3
            else:
                return {'sucesso': False, 'erro': 'Codigo ainda contem APIs alucinadas apos correcao'}

    # Salva
    from mcr.paths import CANARY_NPC_DIR, CANARY_MONSTER_DIR
    from mcr.encoding import write_file

    nome_arquivo = nome.lower().replace(' ', '_').replace("'", '').replace('"', '')
    nome_arquivo = re.sub(r'[^a-z0-9_]', '', nome_arquivo) + '.lua'
    destino = (CANARY_NPC_DIR if tipo == 'npc' else CANARY_MONSTER_DIR) / nome_arquivo
    write_file(destino, codigo, language='lua')

    tempo = time.time() - t0
    print('[WorldBuilder] %s "%s" gerado em %.1fs (%d bytes)' % (
        tipo, nome, tempo, destino.stat().st_size))

    return {
        'sucesso': True,
        'arquivo': str(destino),
        'tamanho': destino.stat().st_size,
        'tempo': round(tempo, 1),
        'tipo': tipo,
        'nome': nome,
    }


# ─── Helpers ─────────────────────────────────────────────────

def _criar_dossie_fundacao(tarefa: dict, seed: dict) -> str:
    """Gera dossie para o codificador a partir de dados estruturados do WorldSeed."""
    nome = tarefa.get('nome', '')
    papel = tarefa.get('papel', '')
    tipo = tarefa.get('tipo', 'npc')

    contexto = json.dumps(seed, indent=2, ensure_ascii=False)

    dossie = (
        "[CONTEXTO DO MUNDO (WorldSeed)]\n"
        "%s\n\n" % contexto[:1500] +
        "[SUA TAREFA]\n"
        "Voce e %s. Papel: %s.\n" % (nome, papel) +
        "Escreva um script Lua para o servidor Canary.\n"
        "Use as APIs corretas do Canary (%s).\n" % (
            'Game.createNpcType, npcConfig, KeywordHandler' if tipo == 'npc' else
            'Game.createMonsterType, monsterConfig'
        ) +
        "Nao invente APIs. Siga o padrao estrutural Canary."
    )
    return dossie


def _gerar_codigo_llm(prompt: str, max_tokens: int = 1000) -> str:
    """Chama o qwen2.5-coder:7b e extrai o codigo Lua."""
    try:
        payload = json.dumps({
            "model": MODELO_CODIGO, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.4, "max_tokens": max_tokens}
        }).encode()
        req = urllib.request.Request(OLLAMA_CHAT, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=180) as r:
            resp = json.loads(r.read())
        codigo = resp.get('response', '').strip()
        if '```lua' in codigo:
            codigo = codigo.split('```lua')[1].split('```')[0]
        elif '```' in codigo:
            codigo = codigo.split('```')[1].split('```')[0]
        return codigo.strip()
    except Exception as e:
        print('[WorldBuilder] Erro no LLM: %s' % e)
        return ''


def _validar_sintaxe(codigo: str) -> tuple:
    """Valida sintaxe Lua. Retorna (valido, erro)."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'devia', 'kernel'))
        from LuaSyntaxValidator import verificar_sintaxe
        return verificar_sintaxe(codigo)
    except Exception as e:
        return False, str(e)


def _validar_semantica(codigo: str, tipo: str) -> list:
    """Valida se as APIs chamadas existem no Canary. Retorna lista de APIs desconhecidas."""
    try:
        from mcr.sanity_validator import SanityValidator
        val = SanityValidator()
        resultado = val.validar_codigo(codigo)
        if not resultado.get('valido', True):
            return resultado.get('apis_desconhecidas', [])
        return []
    except Exception as e:
        print('[WorldBuilder] SanityValidator erro: %s' % e)
        return []


# ─── Orquestrador ────────────────────────────────────────────

def construir_mundo(tema: str, modo: str = "padrao", min_elementos: dict = None) -> dict:
    """Orquestrador completo: tema -> lore -> entidades -> ordens -> codigos -> arquivos.
    
    Parametros:
        tema: descricao do mundo a construir
        modo: "padrao" (pipeline antigo com LLM pra lore) ou "fundacao" (WorldSeed estruturado)
        min_elementos: dict para modo="fundacao" com mins de regions, characters, monsters, quest_seeds
    
    Etapas (modo="padrao"):
    1. gerar_lore_com_feedback
    2. extrair_entidades
    3. arquitetar_mundo
    4. Para cada tarefa: planejar_contexto -> codificar
    5. Relatorio final
    
    Etapas (modo="fundacao"):
    1. generate_world_seed (LLM estruturado)
    2. validate_foundation
    3. generate_chronicle
    4. Para cada character -> codificar NPC, quest -> expandir
    5. Relatorio final
    """
    print('=' * 55)
    print('  CONSTRUINDO MUNDO: %s [modo=%s]' % (tema, modo))
    print('=' * 55)

    t_global = time.time()
    relatorio = {'tema': tema, 'modo': modo, 'etapas': {}, 'arquivos': []}

    # ─── MODO FUNDACAO ─────────────────────────────────────
    if modo == "fundacao":
        from mcr.mcr_world_foundation import generate_world_seed, validate_foundation, world_event
        from mcr.mcr_world_chronicle import generate_chronicle, append_chronicle
        from mcr.mcr_world_state import salvar_foundation, registrar_entidade

        # Etapa 1: Gerar WorldSeed
        print('\n[Fundacao 1/5] Gerando WorldSeed...')
        seed = generate_world_seed(tema, min_elementos)
        relatorio['etapas']['seed'] = {
            'world_name': seed.get('world_name', ''),
            'personagens': len(seed.get('characters', [])),
            'monstros': len(seed.get('monsters', [])),
            'regioes': len(seed.get('regions', [])),
            'quests': len(seed.get('quest_seeds', [])),
        }

        # Etapa 2: Validar
        print('\n[Fundacao 2/5] Validando WorldSeed...')
        valido, erros = validate_foundation(seed, min_elementos)
        if not valido:
            for e in erros:
                print('  ERRO: %s' % e)
            relatorio['erro'] = 'Validacao falhou: %s' % '; '.join(erros[:3])
            return relatorio
        print('  WorldSeed valido!')

        # Etapa 3: Gerar Cronica
        print('\n[Fundacao 3/5] Gerando Cronica...')
        cronica = generate_chronicle(seed)
        append_chronicle("## Preludio\n\n" + cronica, metadata={'type': 'world_creation'})
        relatorio['etapas']['cronica'] = {'chars': len(cronica)}

        # Etapa 4: Salvar Fundacao
        print('\n[Fundacao 4/5] Salvando Fundacao no Estado do Mundo...')
        salvar_foundation(seed)

        # Etapa 5: Criar NPCs e Monstros a partir do WorldSeed
        print('\n[Fundacao 5/5] Criando entidades do WorldSeed...')

        # Cria NPCs para cada personagem
        ordens_char = []
        for c in seed.get('characters', []):
            role = c.get('role', 'figura do mundo')
            papel = "%s de %s" % (role, c.get('location', 'regiao desconhecida'))
            if c.get('faction'):
                papel += " (Faccao: %s)" % c['faction']
            ordens_char.append({
                'tipo': 'npc',
                'nome': c['name'],
                'papel': papel,
            })

        # NPCs
        for i, tarefa in enumerate(ordens_char):
            print('\n--- NPC %d/%d: %s ---' % (i + 1, len(ordens_char), tarefa['nome']))
            dossie = _criar_dossie_fundacao(tarefa, seed)
            resultado = codificar(tarefa, dossie)
            if resultado.get('sucesso'):
                relatorio['arquivos'].append({
                    'tipo': resultado['tipo'],
                    'nome': resultado['nome'],
                    'arquivo': resultado['arquivo'],
                    'tamanho': resultado['tamanho'],
                    'tempo': resultado['tempo'],
                })
                registrar_entidade('npc', resultado['nome'], {
                    'file': resultado['arquivo'],
                    'role': tarefa.get('papel', ''),
                    'tamanho': resultado['tamanho'],
                    'quests': [],
                })
                print('  >> OK: %s (%d bytes, %.1fs)' % (
                    resultado['nome'], resultado['tamanho'], resultado['tempo']))
            else:
                print('  >> FALHA: %s' % resultado.get('erro', '?'))
            if i < len(ordens_char) - 1:
                time.sleep(1)

        # Monstros (placeholder — pipeline sera integrado)
        from mcr.paths import CANARY_MONSTER_DIR
        from mcr.encoding import write_file
        for m in seed.get('monsters', []):
            nome_m = m['name']
            print('\n  [monster] %s (placeholder)' % nome_m)
            # TODO: integrar pipeline de monstros quando disponivel
            relatorio['etapas'].setdefault('monstros_placeholder', []).append(nome_m)

        # Quests: expande os NPCs giver com as quests do seed
        from mcr.mcr_world_state import obter_entidade
        quests_injetadas = 0
        for quest in seed.get('quest_seeds', []):
            giver = quest.get('giver', '')
            if not giver:
                # Tenta primeiro de characters_involved
                chars_inv = quest.get('characters_involved', [])
                if chars_inv:
                    giver = chars_inv[0]
            if not giver:
                print('\n--- Quest: %s (sem giver, pulando) ---' % quest.get('title', '?'))
                continue

            print('\n--- Quest: %s (giver: %s) ---' % (quest.get('title', '?'), giver))
            instrucao_quest = (
                "Adicione uma quest ao NPC '%s'. "
                "Titulo: %s. Objetivo: %s. Recompensa: %s. "
                "Use keywordHandler:addKeyword com StdModule.say para o dialogo da quest. "
                "Use storageValue para controlar o estado da quest." % (
                    giver, quest.get('title', ''), quest.get('objective', ''),
                    quest.get('reward', '')))

            if obter_entidade('npc', giver):
                resultado_q = expandir_npc(giver, instrucao_quest)
                if resultado_q.get('sucesso'):
                    print('  >> Quest injetada em %s' % giver)
                    quests_injetadas += 1
                    nome_quest = quest.get('title', '') or 'quest_%s' % giver
                    try:
                        world_event('quest', nome_quest,
                                    new_state='active',
                                    narrative="Quest '%s' agora disponivel com %s." % (
                                        nome_quest, giver),
                                    source='world_foundation')
                    except Exception as e:
                        print('  (world_event ignorado: %s)' % e)
                else:
                    print('  >> FALHA quest: %s' % resultado_q.get('erro', '?'))
            else:
                print('  >> Giver %s nao encontrado no world_state.' % giver)

        # Relatorio final do modo fundacao
        t_total = time.time() - t_global
        print('\n' + '=' * 55)
        print('  FUNDACAO CONCLUIDA')
        print('=' * 55)
        print('  Mundo: %s' % seed.get('world_name', tema))
        print('  Cronica: %d chars' % len(cronica))
        print('  NPCs gerados: %d' % len(relatorio['arquivos']))
        print('  Quests registradas: %d' % len(seed.get('quest_seeds', [])))
        print('  Tempo total: %.1fs' % t_total)
        print('=' * 55)
        relatorio['tempo_total'] = round(t_total, 1)
        return relatorio

    # ─── MODO PADRAO (original, intacto) ────────────────────

    # Etapa 1
    print('\n[Etapa 1/5] Gerando lore...')
    lore = gerar_lore_com_feedback(tema)
    relatorio['etapas']['lore'] = {'chars': len(lore)}

    # Etapa 2
    print('\n[Etapa 2/5] Extraindo entidades...')
    entidades = extrair_entidades(lore)
    relatorio['etapas']['entidades'] = {
        'personagens': len(entidades.get('personagens', [])),
        'monstros': len(entidades.get('monstros', [])),
        'lugares': len(entidades.get('lugares', [])),
    }

    # Etapa 3
    print('\n[Etapa 3/5] Arquiteto...')
    ordens = arquitetar_mundo(entidades, tema=tema)
    relatorio['etapas']['ordens'] = len(ordens)
    print('  %d ordens de servico geradas' % len(ordens))

    # Etapa 4 + 5
    print('\n[Etapa 4+5/5] Planejando e codificando...')
    for i, tarefa in enumerate(ordens):
        if tarefa['tipo'] not in ('npc', 'monster'):
            print('  Pulando [%s] %s (nao implementado)' % (tarefa['tipo'], tarefa['nome']))
            continue

        print('\n--- Tarefa %d/%d: [%s] %s ---' % (i + 1, len(ordens), tarefa['tipo'], tarefa['nome']))
        dossie = planejar_contexto(tarefa, lore)
        resultado = codificar(tarefa, dossie)

        if resultado.get('sucesso'):
            relatorio['arquivos'].append({
                'tipo': resultado['tipo'],
                'nome': resultado['nome'],
                'arquivo': resultado['arquivo'],
                'tamanho': resultado['tamanho'],
                'tempo': resultado['tempo'],
            })
            print('  >> OK: %s (%d bytes, %.1fs)' % (
                resultado['nome'], resultado['tamanho'], resultado['tempo']))
            # Registra no Estado do Mundo
            try:
                from mcr.mcr_world_state import registrar_entidade
                registrar_entidade(resultado['tipo'], resultado['nome'], {
                    'file': resultado['arquivo'],
                    'role': tarefa.get('papel', ''),
                    'tamanho': resultado['tamanho'],
                    'quests': [],
                })
            except Exception:
                pass
        else:
            print('  >> FALHA: %s' % resultado.get('erro', '?'))

        # Pausa para nao saturar VRAM
        if i < len(ordens) - 1:
            print('  Aguardando 1s para proxima geracao...')
            time.sleep(1)

    # Relatorio final
    t_total = time.time() - t_global
    total_ok = sum(1 for a in relatorio['arquivos'] if a.get('sucesso', False))
    total_bytes = sum(a.get('tamanho', 0) for a in relatorio['arquivos'])

    print('\n' + '=' * 55)
    print('  CONSTRUCAO CONCLUIDA')
    print('=' * 55)
    print('  Tema: %s' % tema)
    print('  Lore: %d chars' % len(lore))
    print('  Entidades: %d personagens, %d monstros, %d lugares' % (
        len(entidades.get('personagens', [])),
        len(entidades.get('monstros', [])),
        len(entidades.get('lugares', [])),
    ))
    print('  Arquivos gerados: %d (%d bytes)' % (len(relatorio['arquivos']), total_bytes))
    for a in relatorio['arquivos']:
        print('    [%s] %s -> %s' % (a['tipo'], a['nome'], a['arquivo']))
    print('  Tempo total: %.1fs' % t_total)
    print('=' * 55)

    relatorio['tempo_total'] = round(t_total, 1)
    return relatorio


# ─── Expansao Cirurgica (Editar NPC existente) ─────────────

def _montar_retry_prompt(prompt_bloco: str, apis_invalidas: list) -> str:
    """Monta prompt de retry para APIs alucinadas."""
    return (
        prompt_bloco + '\n\n'
        'Seu bloco anterior usou APIs INEXISTENTES:\n'
        + '\n'.join('- %s' % a for a in apis_invalidas[:5])
        + '\n\nAs APIs corretas sao: player:getItemCount(id), player:addMoney(amt), '
        'player:removeItem(id, amt), player:addItem(id, amt), '
        'player:getStorageValue(id), player:setStorageValue(id, val), '
        'npcHandler:say({...}, npc, creature), MsgContains(message, "texto").\n'
        'Gere um NOVO bloco corrigido. Responda APENAS o bloco Lua:'
    )


def _limpar_bloco(bloco: str) -> str:
    """Remove marcacoes ``` do bloco gerado."""
    if not bloco:
        return ''
    if bloco.startswith('```'):
        bloco = bloco.split('\n', 1)[-1]
    if bloco.endswith('```'):
        bloco = bloco.rsplit('```', 1)[0]
    return bloco.strip()


def _validar_logica_expansao(bloco: str) -> list:
    """Valida logicas proibidas no bloco de expansao:
    - Nao pode usar Game.getPlayers()
    - Nao pode misturar callback + keyword para mesma quest
    """
    erros = []
    if 'Game.getPlayers()' in bloco or 'Game.getPlayers (' in bloco:
        erros.append('Game.getPlayers() proibido: storage e individual do jogador')
    if 'npcHandler:setCallback' in bloco and 'keywordHandler:addKeyword' in bloco:
        erros.append('Nao misture callback e keywordHandler para a mesma quest')
    return erros


def _ajustar_assinatura_callback(bloco: str) -> str:
    """Ajusta assinatura de funcoes callback no bloco.
    
    CALLBACK_MESSAGE_DEFAULT espera: function(npc, creature, type, message)
    Se o bloco usa function(creature, message) (assinatura TFS antiga),
    substitui para function(npc, creature, type, message).
    """
    import re
    # Pattern: local function nome(creature, message) sem npc
    resultado = re.sub(
        r'(local\s+function\s+\w+)\s*\(\s*creature\s*,\s*message\s*\)',
        r'\1(npc, creature, type, message)',
        bloco
    )
    return resultado

def expandir_npc(nome_npc: str, instrucao: str) -> dict:
    """Expande um NPC existente com novo bloco de codigo (quest, dialogo, shop).
    
    Fluxo:
    1. Le o Estado do Mundo para contexto.
    2. Le o arquivo .lua original do disco.
    3. LLM gera APENAS o novo bloco (sem reescrever o arquivo inteiro).
    4. Injeta o bloco antes de npcType:register.
    5. Valida (sintaxe + semantica) e salva.
    6. Atualiza o Estado do Mundo.
    """
    print('\n' + '=' * 55)
    print('  EXPANDINDO NPC: %s' % nome_npc)
    print('=' * 55)

    from mcr.mcr_world_state import obter_entidade, registrar_entidade, listar_entidades
    from mcr.paths import CANARY_NPC_DIR

    # Passo 1: Contexto do Estado do Mundo
    estado = obter_entidade('npc', nome_npc)
    if not estado:
        return {'sucesso': False, 'erro': 'NPC %s nao encontrado no Estado do Mundo' % nome_npc}

    arquivo_npc = estado.get('file', '')
    if not arquivo_npc or not os.path.exists(arquivo_npc):
        nome_arquivo = nome_npc.lower().replace(' ', '_').replace("'", '').replace('"', '')
        nome_arquivo = re.sub(r'[^a-z0-9_]', '', nome_arquivo) + '.lua'
        arquivo_npc = str(CANARY_NPC_DIR / nome_arquivo)
        if not os.path.exists(arquivo_npc):
            return {'sucesso': False, 'erro': 'Arquivo .lua nao encontrado em %s' % arquivo_npc}

    with open(arquivo_npc, 'r', encoding='latin-1') as f:
        codigo_atual = f.read()

    lores = listar_entidades('lore')
    lore_contexto = ''
    if lores:
        from mcr.paths import LORE_DIR
        for f in sorted(LORE_DIR.glob('*.txt')):
            try:
                lore_contexto = f.read_text('utf-8')[:500]
                break
            except Exception:
                continue

    # Passo 2: LLM gera APENAS o bloco
    prompt_bloco = (
        "Abaixo esta o codigo ATUAL de um NPC do servidor Canary (Tibia).\n"
        "O usuario quer ADICIONAR uma nova funcionalidade a este NPC.\n"
        "Escreva APENAS o novo bloco de codigo Lua que deve ser ADICIONADO ao arquivo.\n"
        "NAO reescreva o arquivo inteiro. NAO inclua linhas que ja existem.\n"
        "Retorne apenas o bloco (ex: keywordHandler:addKeyword, uma funcao, etc.).\n\n"
        "=== CODIGO ATUAL DO NPC %s ===\n%s\n\n" % (nome_npc, codigo_atual)
        + ("=== CONTEXTO DA LORE ===\n%s\n\n" % lore_contexto if lore_contexto else '')
        + "=== INSTRUCAO DO USUARIO ===\n%s\n\n" % instrucao
        + "=== REGRAS ===\n"
        "- Use apenas APIs reais do Canary:\n"
        "    player:getItemCount(clientId)  (NAO getItemCountByClientId)\n"
        "    player:removeItem(clientId, amount)\n"
        "    player:addItem(clientId, amount)\n"
        "    player:addMoney(amount)\n"
        "    player:getStorageValue(storageId)\n"
        "    player:setStorageValue(storageId, value)\n"
        "    npcHandler:say({texto1, texto2}, npc, creature)\n"
        "    MsgContains(message, \"palavra\")\n"
        "    npcHandler:setTopic(playerId, topic)\n"
        "    npcHandler:getTopic(playerId)\n"
        "    Player(creature)\n"
        "- PROIBIDO: NUNCA use Game.getPlayers() ou loops para setar storage de todos.\n"
        "  Storage e individual do jogador. Inicializacao e implicita: se getStorageValue\n"
        "  retornar -1 ou nil, a quest nao foi iniciada. Nao precisa de codigo explicito.\n"
        "- PROIBIDO: NUNCA misture callback e keywordHandler para a mesma quest.\n"
        "  Escolha UM mecanismo:\n"
        "    (a) CALLBACK: use npcHandler:setCallback(CALLBACK_MESSAGE_DEFAULT, fn)\n"
        "        + condicionais com MsgContains + npcHandler:say/player:removeItem/etc.\n"
        "    (b) KEYWORD: use keywordHandler:addKeyword com StdModule.say ou StdModule.travel\n"
        "        SEM callback. Nao crie funcao local nem setCallback.\n"
        "- Para trigger de palavras-chave:\n"
        '    keywordHandler:addKeyword({"palavra"}, StdModule.say, {npc = npcType, text = "Texto"})\n'
        "- Para callbacks de quest (logica condicional), use uma funcao local:\n"
        '    local function creatureSayCallback(npc, creature, type, message)\n'
        "        local player = Player(creature)\n"
        "        local playerId = player:getId()\n"
        "        if MsgContains(message, 'palavra') then\n"
        "            npcHandler:say('Texto', npc, creature)\n"
        "        end\n"
        "        return true\n"
        "    end\n"
        '    npcHandler:setCallback(CALLBACK_MESSAGE_DEFAULT, creatureSayCallback)\n'
        "- NAO use: Game.getPlayers, Callback, onSellCallback, addShop, getItemCountByClientId\n"
        "- Nao inclua 'end' soltos ou blocos incompletos\n"
        "- Responda APENAS com o bloco Lua, nada mais."
    )

    print('[Expansao] Gerando bloco para %s...' % nome_npc)
    t0 = time.time()
    bloco_gerado = _gerar_codigo_llm(prompt_bloco, max_tokens=800)

    if not bloco_gerado:
        return {'sucesso': False, 'erro': 'LLM nao gerou bloco'}

    if bloco_gerado.startswith('```'):
        bloco_gerado = bloco_gerado.split('\n', 1)[-1]
    if bloco_gerado.endswith('```'):
        bloco_gerado = bloco_gerado.rsplit('```', 1)[0]
    bloco_gerado = bloco_gerado.strip()
    print('[Expansao] Bloco gerado (%d chars) em %.1fs' % (len(bloco_gerado), time.time() - t0))

    # Passo 2.5: Garantir npcHandler se o bloco usar callback
    if 'npcHandler:setCallback' in bloco_gerado or 'npcHandler:say' in bloco_gerado:
        if 'local npcHandler' not in codigo_atual and 'NpcHandler:new' not in codigo_atual:
            print('[Expansao] Injetando NpcHandler faltante...')
            bloco_npchandler = (
                "local npcHandler = NpcHandler:new(keywordHandler)\n"
                "npcHandler:setMessage(MESSAGE_GREET, \"Ola, o que deseja?\")\n"
            )
            idx_npchandler = codigo_atual.find('npcType:register(')
            if idx_npchandler >= 0:
                codigo_atual = (codigo_atual[:idx_npchandler] + bloco_npchandler +
                                '\n' + codigo_atual[idx_npchandler:])

    # Passo 2.6: Validar assinatura de callback
    if 'npcHandler:setCallback' in bloco_gerado:
        bloco_gerado = _ajustar_assinatura_callback(bloco_gerado)

    print('[Expansao] Bloco gerado (%d chars) em %.1fs' % (len(bloco_gerado), time.time() - t0))

    # Passo 3: Injetar antes de npcType:register
    marcador_registro = 'npcType:register('
    idx_registro = codigo_atual.find(marcador_registro)
    if idx_registro == -1:
        return {'sucesso': False, 'erro': 'Linha npcType:register nao encontrada no codigo'}

    codigo_novo = codigo_atual[:idx_registro] + bloco_gerado + '\n' + codigo_atual[idx_registro:]

    # Passo 4: Validacao com retry (sintaxe + semantica + logica)
    for tentativa in range(3):
        print('[Expansao] Validando codigo modificado (tentativa %d)...' % (tentativa + 1))
        valido, erro_sintaxe = _validar_sintaxe(codigo_novo)
        if not valido:
            return {'sucesso': False, 'erro': 'Sintaxe invalida apos injecao: %s' % erro_sintaxe,
                    'bloco_gerado': bloco_gerado}

        apis_invalidas = _validar_semantica(codigo_novo, 'npc')
        if apis_invalidas:
            print('[Expansao] APIs alucinadas: %s. Regenerando...' % ', '.join(apis_invalidas[:3]))
            prompt_retry = _montar_retry_prompt(prompt_bloco, apis_invalidas)
            bloco_gerado = _gerar_codigo_llm(prompt_retry, max_tokens=800)
            bloco_gerado = _limpar_bloco(bloco_gerado)
            codigo_novo = codigo_atual[:idx_registro] + bloco_gerado + '\n' + codigo_atual[idx_registro:]
            continue

        # Validacao logica: Game.getPlayers, callback+keyword duplicado
        erros_logica = _validar_logica_expansao(bloco_gerado)
        if erros_logica:
            print('[Expansao] Erro logico: %s. Regenerando...' % '; '.join(erros_logica))
            prompt_retry = prompt_bloco + '\n\nSeu bloco anterior tem ERROS LOGICOS:\n'
            prompt_retry += '\n'.join('- %s' % e for e in erros_logica)
            prompt_retry += '\n\nGere um NOVO bloco corrigido. Responda APENAS o bloco Lua:'
            bloco_gerado = _gerar_codigo_llm(prompt_retry, max_tokens=800)
            bloco_gerado = _limpar_bloco(bloco_gerado)
            codigo_novo = codigo_atual[:idx_registro] + bloco_gerado + '\n' + codigo_atual[idx_registro:]
            continue

        break  # Passou todas as validacoes!
    else:
        # Todas as tentativas falharam
        return {'sucesso': False, 'erro': 'Bloco rejeitado apos %d tentativas' % (tentativa + 1),
                'bloco_gerado': bloco_gerado}

    # Salva
    from mcr.encoding import write_file
    write_file(arquivo_npc, codigo_novo, language='lua')
    tamanho_final = os.path.getsize(arquivo_npc)

    # Atualiza Estado do Mundo
    quests_existentes = estado.get('quests', [])
    quests_existentes.append({
        'instrucao': instrucao,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'bloco_tamanho': len(bloco_gerado),
    })
    registrar_entidade('npc', nome_npc, {
        'file': arquivo_npc,
        'tamanho': tamanho_final,
        'quests': quests_existentes,
        'role': estado.get('role', ''),
    })

    tempo_total = time.time() - t0
    print('[Expansao] %s expandido com sucesso (%d bytes, %.1fs)' % (
        nome_npc, tamanho_final, tempo_total))

    return {
        'sucesso': True,
        'arquivo': arquivo_npc,
        'tamanho_final': tamanho_final,
        'bloco_gerado': bloco_gerado,
        'tempo': round(tempo_total, 1),
    }


# ─── Pipeline Iterativo (Novo) ─────────────────────────────

def expandir_mundo(tema: str, quantidade: int = 10) -> dict:
    """Pipeline iterativo: semente -> ideias -> specs -> entidades -> conexoes.
    
    Args:
        tema: descricao do mundo
        quantidade: numero de entidades a criar (mix de NPCs, monsters, quests)
    
    Returns:
        relatorio detalhado do processo
    """
    print('=' * 55)
    print('  EXPANDINDO MUNDO (iterativo): %s' % tema)
    print('  Alvo: %d entidades' % quantidade)
    print('=' * 55)

    t_global = time.time()
    relatorio = {
        'tema': tema,
        'quantidade_alvo': quantidade,
        'etapas': {},
        'entidades': [],
        'falhas': [],
        'conexoes': [],
    }

    from mcr.mcr_world_seed import generate_world_seed_lite
    from mcr.emergir import Emergir
    from mcr.mcr_idea_to_spec import idea_to_entity_spec
    from mcr.mcr_entity_validator import validate_entity
    from mcr.mcr_entity_factory import create_entity
    from mcr.mcr_world_state import _carregar, salvar_foundation, registrar_entidade
    from mcr.mcr_world_chronicle import generate_chronicle, append_chronicle

    # 1. Semente
    print('\n[Etapa 1/5] Gerando semente do mundo...')
    seed = generate_world_seed_lite(tema)
    relatorio['etapas']['semente'] = {
        'world_name': seed.get('world_name'),
        'conceitos': seed.get('concepts', []),
    }
    print('  Mundo: %s (%d conceitos)' % (seed['world_name'], len(seed.get('concepts', []))))

    # 2. Ideias
    print('\n[Etapa 2/5] Gerando ideias (Emergir)...')
    emergir = Emergir(llm_func=None)
    ideias = emergir.gerar_ideias_tematicas(
        seed.get('concepts', []), n=quantidade * 3)
    print('  %d ideias geradas' % len(ideias))

    # 3. Ideias -> Specs -> Entidades
    print('\n[Etapa 3/5] Convertendo ideias em entidades...')
    estado_acumulado = _carregar()
    if 'characters' not in estado_acumulado:
        estado_acumulado['characters'] = []

    pending_names = set()
    entidades_criadas = 0
    tiers_count = {'template': 0, 'codificado': 0, 'codificado+quest': 0, 'injection': 0}

    for idx, ideia in enumerate(ideias):
        if entidades_criadas >= quantidade:
            break

        print('\n  --- Entidade %d/%d ---' % (entidades_criadas + 1, quantidade))
        print('  Ideia: %s' % ideia['ideia'][:80])

        # Busca golden exemplo
        golden = ''
        try:
            from mcr.mcr_idea_to_spec import _buscar_golden_exemplo
            golden = _buscar_golden_exemplo(ideia['ideia'])
        except Exception:
            pass

        # Converte ideia em spec
        # Portao Metacognicao: avalia se a ideia faz sentido no KG
        try:
            from mcr.metacognicao import Metacognicao
            _portao = Metacognicao()
            _avaliacao = _portao.avaliar_pedido(ideia['ideia'])
            if not _avaliacao.get('aprovado', False):
                print('  >> Metacognicao rejeitou: score=%.2f < threshold=%.2f' % (
                    _avaliacao.get('score', 0), _avaliacao.get('threshold', 0.7)))
                relatorio['falhas'].append({
                    'ideia': ideia['ideia'][:60],
                    'erro': 'metacognicao: score=%.2f %s' % (
                        _avaliacao.get('score', 0), _avaliacao.get('justificativa', ''))})
                continue
        except Exception as e:
            print('  >> Metacognicao erro (ignorado): %s' % e)
            pass

        spec = idea_to_entity_spec(ideia['ideia'], tema, golden_exemplo=golden)
        if not spec:
            print('  >> Spec falhou (LLM nao gerou JSON valido)')
            relatorio['falhas'].append({'ideia': ideia['ideia'][:60], 'erro': 'spec_falhou'})
            continue

        # Valida spec
        valido, erros = validate_entity(spec, estado_acumulado, pending_names)
        if not valido:
            print('  >> Validacao: %s' % '; '.join(erros[:2]))
            relatorio['falhas'].append({'ideia': ideia['ideia'][:60], 'erro': erros})
            continue

        # Cria entidade
        pending_names.add(spec.get('name', '') or spec.get('title', ''))
        resultado = create_entity(spec, estado_acumulado)

        if resultado.get('sucesso'):
            entidades_criadas += 1
            tier = resultado.get('tier', 'desconhecido')
            tiers_count[tier] = tiers_count.get(tier, 0) + 1
            relatorio['entidades'].append({
                'tipo': resultado.get('tipo', spec.get('type', '?')),
                'nome': resultado.get('entidade', spec.get('name', '?')),
                'tier': tier,
                'arquivo': resultado.get('arquivo', ''),
            })
            print('  >> CRIADO: %s [%s]' % (resultado.get('entidade', '?'), tier))

            # Atualiza estado acumulado
            estado_acumulado['characters'].append({
                'name': spec.get('name', ''),
                'role': spec.get('role', ''),
                'faction': spec.get('faction', ''),
                'state': 'alive',
            })
        else:
            print('  >> FALHA: %s' % resultado.get('erro', '?'))
            relatorio['falhas'].append({
                'ideia': ideia['ideia'][:60],
                'erro': resultado.get('erro', 'criacao_falhou'),
            })
            pending_names.discard(spec.get('name', '') or spec.get('title', ''))

        # Pausa para VRAM
        time.sleep(0.5)

    # 4. Conexoes (What If 2o nivel) — injeta quests de verdade
    print('\n[Etapa 4/5] Gerando conexoes narrativas (What If 2o nivel)...')
    quests_injetadas = 0
    try:
        from mcr.mcr_world_foundation import world_event
        from mcr.mcr_world_state import _carregar as _carregar_estado
        personagens = [e['nome'] for e in relatorio['entidades'] if e['tipo'] == 'npc']
        if personagens:
            prompt_conexao = (
                "Baseado nos personagens abaixo, sugira 3 novas quests que conectem "
                "dois ou mais personagens existentes.\n"
                "Personagens: %s\n\n" % ', '.join(personagens) +
                "Para cada quest, retorne EXATAMENTE no formato abaixo (uma quest por bloco):\n"
                "Titulo: ...\nGiver: ...\nObjetivo: ...\nRecompensa: ...\n\n"
                "As quests devem ser tematicamente coerentes com cada giver.\n"
                "Separe cada quest com uma linha em branco."
            )
            try:
                import urllib.request
                payload = json.dumps({
                    "model": MODELO_LORE, "prompt": prompt_conexao, "stream": False,
                    "options": {"temperature": 0.7, "max_tokens": 800}
                }).encode()
                req = urllib.request.Request(
                    "http://localhost:11434/api/generate", data=payload,
                    headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    resp = json.loads(r.read())
                texto_conexoes = resp.get('response', '')
                relatorio['conexoes_raw'] = texto_conexoes[:500]
                print('  Resposta bruta (%d chars)' % len(texto_conexoes))

                # Parseia blocos de quest no formato:
                # Titulo: ...\nGiver: ...\nObjetivo: ...\nRecompensa: ...
                import re as _re
                blocos = texto_conexoes.strip().split('\n\n')
                for bloco in blocos:
                    titulo_m = _re.search(r'T[ií]tulo:\s*(.+?)(?:\n|$)', bloco)
                    giver_m = _re.search(r'Giver:\s*(.+?)(?:\n|$)', bloco)
                    obj_m = _re.search(r'O[bj]etivo:\s*(.+?)(?:\n|$)', bloco)
                    recomp_m = _re.search(r'Recompensa:\s*(.+?)(?:\n|$)', bloco)

                    if not giver_m:
                        continue
                    titulo = titulo_m.group(1).strip() if titulo_m else 'Quest sem nome'
                    giver = giver_m.group(1).strip()
                    objetivo = obj_m.group(1).strip() if obj_m else 'Objetivo desconhecido'
                    recompensa = recomp_m.group(1).strip() if recomp_m else 'Recompensa desconhecida'

                    if not giver or giver.lower() in ('n/a', 'nenhum', 'none'):
                        continue

                    print('\n  --- Quest: %s (giver: %s) ---' % (titulo[:40], giver))

                    # Verifica se o giver existe no world_state
                    ws_atual = _carregar_estado()
                    giver_existe = False
                    for nome_npc in ws_atual.get('npcs', {}):
                        if giver.lower() in nome_npc.lower():
                            giver_existe = True
                            giver = nome_npc
                            break

                    if not giver_existe:
                        print('  >> Giver "%s" nao encontrado no world_state' % giver)
                        continue

                    instrucao = (
                        "Adicione uma quest ao NPC '%s'. "
                        "Titulo: %s. Objetivo: %s. Recompensa: %s." % (
                            giver, titulo, objetivo, recompensa))

                    try:
                        resultado_q = expandir_npc(giver, instrucao)
                        if resultado_q.get('sucesso'):
                            print('  >> Quest injetada em %s' % giver)
                            quests_injetadas += 1
                            try:
                                world_event('quest', titulo, new_state='active',
                                            narrative="Quest '%s' disponivel com %s." % (titulo, giver),
                                            source='what_if_2nivel')
                            except Exception:
                                pass
                        else:
                            print('  >> FALHA: %s' % resultado_q.get('erro', '?'))
                    except Exception as e:
                        print('  >> ERRO: %s' % e)
                    time.sleep(0.5)

            except Exception as e:
                print('  LLM conexoes falhou: %s' % e)
    except Exception as e:
        print('  Etapa 4 ignorada: %s' % e)

    relatorio['conexoes_injetadas'] = quests_injetadas

    # 5. Cronica final
    print('\n[Etapa 5/5] Gerando cronica final...')
    try:
        estado_final = _carregar()
        seed_final = estado_final.get('current_foundation', {})
        if isinstance(seed_final, dict) and seed_final.get('world_seed_lite'):
            seed_completo = {
                'world_name': seed_final['world_seed_lite'].get('world_name', tema),
                'characters': estado_final.get('characters', []),
                'regions': [{'name': c} for c in seed_final['world_seed_lite'].get('concepts', [])],
            }
            cronica = generate_chronicle(seed_completo)
            append_chronicle("## Expansao Iterativa\n\n" + cronica,
                             metadata={'type': 'world_expansion', 'entidades': entidades_criadas})
            print('  Cronica gerada (%d chars)' % len(cronica))
    except Exception as e:
        print('  Cronica ignorada: %s' % e)

    # Relatorio final
    t_total = time.time() - t_global
    print('\n' + '=' * 55)
    print('  EXPANSAO CONCLUIDA')
    print('=' * 55)
    print('  Mundo: %s' % seed.get('world_name', tema))
    print('  Entidades criadas: %d/%d' % (entidades_criadas, quantidade))
    print('  Tiers: %s' % ', '.join('%s=%d' % (k, v) for k, v in tiers_count.items() if v > 0))
    print('  Quests injetadas (What-If 2o nivel): %d' % relatorio.get('conexoes_injetadas', 0))
    print('  Falhas: %d' % len(relatorio['falhas']))
    print('  Tempo: %.1fs' % t_total)
    print('=' * 55)

    relatorio['tempo_total'] = round(t_total, 1)
    relatorio['entidades_criadas'] = entidades_criadas
    relatorio['tiers'] = tiers_count
    return relatorio
