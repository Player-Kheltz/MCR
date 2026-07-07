"""mcr.anti_pattern_injector — Injeta Anti-Patterns no prompt do LLM.
Busca no KG os anti-patterns relevantes e formata como texto para o prompt."""
import json
import re
from pathlib import Path
from typing import List, Dict

from mcr.paths import KG_DIR

# Mapeamento de temas para palavras-chave de busca
_TEMA_PALAVRAS = {
    'npc': ['npc', 'npchandler', 'createnpctype', 'keywordhandler', 'npcconfig'],
    'monster': ['monster', 'createmonstertype', 'monsterconfig', 'monstertype'],
    'action': ['action', 'onuse', 'uid', 'actionid'],
    'spell': ['spell', 'magia', 'habilidade', 'cura', 'dano', 'efeito'],
    'quest': ['quest', 'storage', 'reward', 'missao'],
    'spa': ['spa', 'habilidade spa', 'efeitoconfig', 'dominio'],
    'item': ['item', 'itemtype', 'clientid', 'itemid'],
    'player': ['player', 'getname', 'additem', 'sendtextmessage'],
    'creatureevent': ['creatureevent', 'onkill', 'onlogin'],
    'globalevent': ['globalevent', 'onstart', 'onhour'],
}


def _carregar_anti_patterns(kg_dir: Path = None) -> List[Dict]:
    """Carrega todos os anti-patterns do KG."""
    kg_dir = kg_dir or KG_DIR
    anti_patterns = []

    for fpath in sorted(kg_dir.glob('patterns_*.json')):
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            anti_patterns.extend(dados.get('anti_patterns', []))
        except Exception:
            pass

    return anti_patterns


def extrair_anti_patterns_para_prompt(tema: str, linguagem: str = 'lua') -> str:
    """Busca anti-patterns relevantes ao tema e formata para injecao no prompt do LLM.
    
    Args:
        tema: classe/tipo do que esta sendo gerado (npc, monster, action, etc.)
        linguagem: lua, cpp, etc.
    
    Returns:
        string formatada com anti-patterns ou string vazia se nenhum.
    """
    anti_patterns = _carregar_anti_patterns()
    if not anti_patterns:
        return ''

    # Palavras-chave para filtrar pelo tema
    palavras_chave = _TEMA_PALAVRAS.get(tema.lower(), [tema.lower()])

    relevantes = []
    for ap in anti_patterns:
        ap_lower = json.dumps(ap).lower()
        score = 0
        for kw in palavras_chave:
            if kw in ap_lower:
                score += 1
        if score > 0:
            relevantes.append((score, ap))

    if not relevantes:
        return ''

    # Ordena por relevancia
    relevantes.sort(key=lambda x: -x[0])

    # Formata
    linhas = ['ANTI-PATTERNS CONHECIDOS (NAO COMETA ESTES ERROS):']
    linhas.append('=' * 55)
    for i, (_, ap) in enumerate(relevantes[:5], 1):
        api = ap.get('api_problematica', '?')
        categoria = ap.get('categoria', '?')
        ocorr = ap.get('ocorrencias', 1)
        solucao = ap.get('solucao_sugerida', '')
        linha = f'  {i}. [{categoria}] {api} ({ocorr}x)'
        if solucao:
            linha += f'\n     Solucao: {solucao}'
        linhas.append(linha)
    linhas.append('=' * 55)

    return '\n'.join(linhas)
