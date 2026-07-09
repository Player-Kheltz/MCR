#!/usr/bin/env python3
"""mcr_server_toolset — Gera codigo Lua valido para o servidor Canary.
Usa PatternMiner + Qwen Coder + LuaValidator para produzir arquivos prontos para deploy."""
import sys
import os
import json
import re
import random
import time
import urllib.request
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'devia', 'kernel'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

from mcr.paths import CANARY_NPC_DIR, CANARY_MONSTER_DIR, KG_DIR, GOLDEN_EXAMPLES_DIR
from mcr.encoding import write_file

OLLAMA_CHAT = "http://localhost:11434/api/generate"
MODELO = "qwen2.5-coder:7b"

# Cache de padroes do KG
_PADROES_CACHE = {'npc': None, 'monster': None}


def _carregar_padroes(tipo: str) -> list:
    """Carrega padroes do KG para um tipo (npc/monster)."""
    if _PADROES_CACHE.get(tipo):
        return _PADROES_CACHE[tipo]

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

    _PADROES_CACHE[tipo] = padroes
    print('[Toolset] %d padroes de %s carregados do KG' % (len(padroes), tipo))
    return padroes


def _exemplos_para_prompt(padroes: list, max_exemplos: int = 2) -> str:
    """Gera exemplos formatados para o prompt do LLM."""
    amostra = random.sample(padroes, min(max_exemplos, len(padroes)))
    blocos = []
    for p in amostra:
        try:
            with open(p['arquivo'], 'r', encoding='latin-1') as f:
                codigo = f.read()[:600]
        except Exception:
            with open(p['arquivo'], 'r', encoding='utf-8', errors='replace') as f:
                codigo = f.read()[:600]
        blocos.append('--- ARQUIVO: %s\n```lua\n%s\n```' % (os.path.basename(p['arquivo']), codigo))
    return '\n'.join(blocos)


def _chamar_ollama(prompt: str) -> Optional[str]:
    """Chama o qwen2.5-coder:7b para gerar codigo."""
    try:
        payload = json.dumps({
            "model": MODELO, "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.4, "max_tokens": 800}
        }).encode()
        req = urllib.request.Request(OLLAMA_CHAT, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read())
        texto = resp.get('response', '').strip()
        # Extrai bloco ```lua se presente
        if '```lua' in texto:
            texto = texto.split('```lua')[1].split('```')[0]
        elif '```' in texto:
            texto = texto.split('```')[1].split('```')[0]
        return texto.strip()
    except Exception as e:
        print('[Toolset] Erro no Ollama: %s' % e)
        return None


def _validar_lua(codigo: str) -> tuple:
    """Valida sintaxe Lua via LuaSyntaxValidator."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'devia', 'kernel'))
        from LuaSyntaxValidator import verificar_sintaxe
        valido, erro = verificar_sintaxe(codigo)
        return valido, erro
    except Exception as e:
        return False, str(e)


def _gerar_nome_arquivo(prompt: str, prefixo: str) -> str:
    """Gera nome de arquivo a partir do prompt."""
    palavras = re.findall(r"'([^']+)'|\"([^\"]+)\"", prompt)
    nome = ''
    for p in palavras:
        nome = (p[0] or p[1])
        break
    if not nome:
        palavras_soltas = re.findall(r'chamado\s+(\w+)|de\s+nome\s+(\w+)', prompt.lower())
        for p in palavras_soltas:
            nome = p[0] or p[1]
            break
    if not nome:
        nome = prefixo + '_' + str(abs(hash(prompt)) % 10000)
    nome_arquivo = nome.lower().replace(' ', '_').replace("'", '').replace('"', '')
    nome_arquivo = re.sub(r'[^a-z0-9_]', '', nome_arquivo)
    return nome_arquivo + '.lua'


def criar_npc(prompt: str) -> str:
    """Cria um arquivo de NPC completo para o Canary."""
    padroes = _carregar_padroes('npc')
    if not padroes:
        return '[Erro] Nenhum padrao de NPC no KG. Execute o PatternMiner primeiro.'

    exemplos = _exemplos_para_prompt(padroes)
    nome_arquivo = _gerar_nome_arquivo(prompt, 'npc')
    destino = CANARY_NPC_DIR / nome_arquivo

    prompt_llm = (
        "Voce e um scripter Lua do servidor Canary (Open Tibia).\n"
        "Crie um arquivo de NPC completo baseado no pedido abaixo.\n"
        "Use os padroes fornecidos como referencia. NAO invente APIs.\n"
        "Use Game.createNpcType, npcConfig, KeywordHandler, npcType:register.\n\n"
        "PADROES DE REFERENCIA:\n%s\n\n" % exemplos +
        "PEDIDO: %s\n\n" % prompt +
        "GERAR APENAS O CODIGO LUA, sem explicacoes:"
    )

    print('[Toolset] Gerando NPC via Qwen Coder...')
    t0 = time.time()
    codigo = _chamar_ollama(prompt_llm)
    if not codigo:
        return '[Erro] Falha ao gerar codigo.'

    valido, erro = _validar_lua(codigo)
    if not valido:
        # Tenta uma segunda vez
        print('[Toolset] 1a tentativa invalida: %s. Tentando novamente...' % erro)
        prompt_fix = prompt_llm + '\n\nCORRIGA O ERRO: %s' % erro
        codigo2 = _chamar_ollama(prompt_fix)
        if codigo2:
            valido2, erro2 = _validar_lua(codigo2)
            if valido2:
                codigo = codigo2
                valido = True

    if not valido:
        return '[Erro] Codigo gerado nao passou na validacao Lua.'

    write_file(destino, codigo, language='lua')
    tempo = time.time() - t0
    return '[OK] NPC %s criado e validado em %.1fs no caminho:\n  %s' % (nome_arquivo, tempo, destino)


def criar_monstro(prompt: str) -> str:
    """Cria um arquivo de Monstro completo para o Canary."""
    padroes = _carregar_padroes('monster')
    if not padroes:
        return '[Erro] Nenhum padrao de Monstro no KG. Execute o PatternMiner primeiro.'

    exemplos = _exemplos_para_prompt(padroes)
    nome_arquivo = _gerar_nome_arquivo(prompt, 'monster')
    destino = CANARY_MONSTER_DIR / nome_arquivo

    prompt_llm = (
        "Voce e um scripter Lua do servidor Canary (Open Tibia).\n"
        "Crie um arquivo de MONSTRO completo baseado no pedido abaixo.\n"
        "Use os padroes fornecidos como referencia. NAO invente APIs.\n"
        "Use Game.createMonsterType, monsterConfig, monsterType:register.\n"
        "Use os campos: name, description, maxHealth, experience, outfit, "
        "flags (attackable, hostile), dropList com {id, chance, maxCount}.\n\n"
        "PADROES DE REFERENCIA:\n%s\n\n" % exemplos +
        "PEDIDO: %s\n\n" % prompt +
        "GERAR APENAS O CODIGO LUA, sem explicacoes:"
    )

    print('[Toolset] Gerando Monstro via Qwen Coder...')
    t0 = time.time()
    codigo = _chamar_ollama(prompt_llm)
    if not codigo:
        return '[Erro] Falha ao gerar codigo.'

    valido, erro = _validar_lua(codigo)
    if not valido:
        print('[Toolset] 1a tentativa invalida. Tentando novamente...')
        prompt_fix = prompt_llm + '\n\nCORRIGA O ERRO: %s' % erro
        codigo2 = _chamar_ollama(prompt_fix)
        if codigo2:
            valido2, _ = _validar_lua(codigo2)
            if valido2:
                codigo = codigo2
                valido = True

    if not valido:
        return '[Erro] Codigo gerado nao passou na validacao Lua.'

    write_file(destino, codigo, language='lua')
    tempo = time.time() - t0
    return '[OK] Monstro %s criado e validado em %.1fs no caminho:\n  %s' % (nome_arquivo, tempo, destino)
