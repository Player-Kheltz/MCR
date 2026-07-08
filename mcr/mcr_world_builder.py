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
MODELO_LORE = "mistral:7b"
MODELO_CODIGO = "qwen2.5-coder:7b"

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

def arquitetar_mundo(entidades: dict) -> list:
    """Recebe entidades e retorna ordens de servico (Build Orders).
    
    Para cada personagem -> ordem npc.
    Para cada monstro -> ordem monster.
    Para cada lugar -> ordem lugar (armazenamento de contexto).
    O conflito vira o tema central.
    """
    ordens = []
    conflito = entidades.get('conflito', '')

    for nome in entidades.get('personagens', []):
        ordens.append({
            'tipo': 'npc',
            'nome': nome,
            'papel': 'Personagem da historia: %s' % (conflito if conflito else 'figura central'),
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

def _carregar_padroes(tipo: str, max_exemplos: int = 2) -> str:
    """Carrega exemplos do KG para o tipo solicitado."""
    from mcr.paths import KG_DIR
    padroes = []
    for fpath in sorted(KG_DIR.glob('patterns_*.json')):
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            for p in dados.get('padroes', dados if isinstance(dados, list) else []):
                if p.get('tipo') == tipo:
                    padroes.append(p)
        except Exception:
            continue
    import random
    amostra = random.sample(padroes, min(max_exemplos, len(padroes)))
    blocos = []
    for p in amostra:
        try:
            with open(p['arquivo'], 'r', encoding='latin-1') as f:
                codigo = f.read()[:600]
        except Exception:
            with open(p['arquivo'], 'r', encoding='utf-8', errors='replace') as f:
                codigo = f.read()[:600]
        blocos.append('-- %s\n%s' % (os.path.basename(p['arquivo']), codigo))
    return '\n\n'.join(blocos)


def codificar(tarefa: dict, dossie: str) -> dict:
    """Gera codigo Lua para uma tarefa (NPC ou Monster).
    
    Usa qwen2.5-coder:7b + padroes do KG + LuaValidator.
    """
    tipo = tarefa.get('tipo', '')
    nome = tarefa.get('nome', 'Entidade')
    papel = tarefa.get('papel', '')

    if tipo not in ('npc', 'monster'):
        return {'sucesso': False, 'erro': 'Tipo nao suportado: %s' % tipo}

    # Carrega padroes do KG
    padroes = _carregar_padroes(tipo)
    if not padroes:
        return {'sucesso': False, 'erro': 'Nenhum padrao de %s no KG' % tipo}

    # Monta prompt
    if tipo == 'npc':
        api_instrucao = 'Game.createNpcType, npcConfig, KeywordHandler, npcType:register'
    else:
        api_instrucao = 'Game.createMonsterType, monsterConfig, monsterType:register'

    prompt = (
        "%s\n\n" % dossie +
        "PADROES REAIS DO CANARY (nao invente APIs fora destes):\n"
        "%s\n\n" % padroes +
        "Escreva um arquivo Lua completo para %s '%s'.\n" % (tipo, nome) +
        "Papel: %s\n" % papel +
        "Use as APIs: %s\n" % api_instrucao +
        "Inclua dialogos que referenciem o conflito da historia.\n"
        "Nao invente APIs. Responda APENAS com o codigo Lua."
    )

    print('[WorldBuilder] Codificando %s "%s"...' % (tipo, nome))
    t0 = time.time()

    try:
        payload = json.dumps({
            "model": MODELO_CODIGO, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.4, "max_tokens": 1000}
        }).encode()
        req = urllib.request.Request(OLLAMA_CHAT, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read())
        codigo = resp.get('response', '').strip()
    except Exception as e:
        return {'sucesso': False, 'erro': 'LLM: %s' % e}

    if not codigo:
        return {'sucesso': False, 'erro': 'Codigo vazio'}

    # Extrai bloco markdown
    if '```lua' in codigo:
        codigo = codigo.split('```lua')[1].split('```')[0]
    elif '```' in codigo:
        codigo = codigo.split('```')[1].split('```')[0]
    codigo = codigo.strip()

    # Valida
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'devia', 'kernel'))
        from LuaSyntaxValidator import verificar_sintaxe
        valido, erro = verificar_sintaxe(codigo)
        if not valido:
            # Tenta uma vez com correcao
            prompt2 = prompt + '\n\nCORRIGA O ERRO: %s' % erro
            payload2 = json.dumps({"model": MODELO_CODIGO, "prompt": prompt2, "stream": False,
                                   "options": {"temperature": 0.3, "max_tokens": 1000}}).encode()
            req2 = urllib.request.Request(OLLAMA_CHAT, data=payload2,
                                          headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req2, timeout=120) as r:
                resp2 = json.loads(r.read())
            codigo2 = resp2.get('response', '').strip()
            if '```lua' in codigo2:
                codigo2 = codigo2.split('```lua')[1].split('```')[0]
            elif '```' in codigo2:
                codigo2 = codigo2.split('```')[1].split('```')[0]
            if codigo2:
                codigo = codigo2
                valido2, _ = verificar_sintaxe(codigo2)
                valido = valido2
    except Exception as e:
        return {'sucesso': False, 'erro': 'Validacao: %s' % e}

    if not valido:
        return {'sucesso': False, 'erro': 'Codigo invalido apos 2 tentativas'}

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


# ─── Orquestrador ────────────────────────────────────────────

def construir_mundo(tema: str) -> dict:
    """Orquestrador completo: tema -> lore -> entidades -> ordens -> codigos -> arquivos.
    
    Etapas:
    1. gerar_lore_com_feedback
    2. extrair_entidades
    3. arquitetar_mundo
    4. Para cada tarefa: planejar_contexto -> codificar
    5. Relatorio final
    """
    print('=' * 55)
    print('  CONSTRUINDO MUNDO: %s' % tema)
    print('=' * 55)

    t_global = time.time()
    relatorio = {'tema': tema, 'etapas': {}, 'arquivos': []}

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
    ordens = arquitetar_mundo(entidades)
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
