"""mcr.mcr_idea_to_spec — Converte ideias 'E se' em especificacoes de entidade.
Usa Qwen Coder para gerar JSON estruturado com tipo, nome, role, etc.
Busca Golden Examples no KG via Radar para guiar o LLM."""
import json
import re
import time
import urllib.request
from typing import Dict, List, Optional, Tuple

OLLAMA_CHAT = "http://localhost:11434/api/generate"
from mcr.config_llm import MODELO_CODIGO, OLLAMA_URL
MODELO = MODELO_CODIGO

_SPEC_SCHEMA_NPC = {
    "type": "npc",
    "name": "...",
    "role": "vendedor/guerreiro/mago/ferreiro/etc",
    "location": "regiao onde esta",
    "faction": "faccao (opcional)",
    "motivation": "motivacao do personagem",
    "shop_items": [{"name": "item", "clientId": 100, "buy": 50, "sell": 20}],
}

_SPEC_SCHEMA_MONSTER = {
    "type": "monster",
    "name": "...",
    "habitat": "regiao",
    "danger_level": "low/medium/high",
    "loot_hint": "sugestao de loot",
}

_SPEC_SCHEMA_QUEST = {
    "type": "quest",
    "title": "...",
    "giver": "nome do NPC que da a quest",
    "objective": "descricao do objetivo",
    "reward": "recompensa",
    "involves": ["npc ou monstro envolvido"],
}


def _buscar_golden_exemplo(ideia: str) -> str:
    """Busca golden example via busca textual simples no KG."""
    from mcr.paths import KG_DIR
    from mcr.encoding import read_file
    
    palavras = set(re.findall(r'\b[a-zA-Z]{4,}\b', ideia.lower()))
    melhor = ''
    melhor_score = 0
    
    for fpath in sorted(KG_DIR.glob('*.json')):
        if 'patterns' not in fpath.name:
            continue
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            items = dados.get('padroes', dados if isinstance(dados, list) else [])
            for p in items[:50]:  # limita para performance
                arquivo = p.get('arquivo', '')
                if not arquivo or not arquivo.endswith('.lua'):
                    continue
                if not arquivo.lower().endswith(('.lua')):
                    continue
                # Procura exemplos com tema similar
                texto_busca = (arquivo.lower() + ' ' +
                               ' '.join(p.get('api_calls', [])) + ' ' +
                               ' '.join(p.get('variaveis', [])))
                score = sum(1 for pw in palavras if pw in texto_busca)
                if score > melhor_score:
                    melhor_score = score
                    melhor = arquivo
        except Exception:
            continue
    
    if melhor and melhor_score > 0:
        try:
            return read_file(melhor)[:500]
        except Exception:
            return ''
    return ''


def idea_to_entity_spec(ideia: str, tema: str,
                         golden_exemplo: str = "") -> Optional[dict]:
    """Converte uma ideia 'E se' em especificacao JSON de entidade.
    
    Args:
        ideia: texto da ideia (ex: "E se um comerciante e um feiticeiro...")
        tema: tema do mundo
        golden_exemplo: codigo de exemplo opcional
    
    Returns:
        dict com type, name, role, etc. ou None se falhar.
    """
    if not golden_exemplo:
        golden_exemplo = _buscar_golden_exemplo(ideia)
    
    schema_exemplo = json.dumps({
        'npc': _SPEC_SCHEMA_NPC,
        'monster': _SPEC_SCHEMA_MONSTER,
        'quest': _SPEC_SCHEMA_QUEST,
    }, indent=2, ensure_ascii=False)
    
    prompt = (
        "Converta a ideia abaixo em uma especificacao de entidade JSON.\n"
        "Retorne APENAS o JSON, sem comentarios, sem ```.\n\n"
        "=== IDEIA ===\n%s\n\n" % ideia +
        "=== TEMA DO MUNDO ===\n%s\n\n" % tema +
        ("=== EXEMPLO DE CODIGO REAL (estude a estrutura) ===\n%s\n\n" % golden_exemplo
         if golden_exemplo else '') +
        "=== SCHEMAS DISPONIVEIS ===\n"
        "%s\n\n" % schema_exemplo +
        "Escolha UM dos tipos acima (npc, monster ou quest) e preencha os campos.\n"
        "Se for quest, o campo 'giver' deve ser um nome de personagem que combine "
        "com o tema da quest.\n"
        "Se for npc, inclua 'shop_items' se fizer sentido para o papel.\n\n"
        "JSON:"
    )
    
    for tentativa in range(3):
        try:
            payload = json.dumps({
                "model": MODELO, "prompt": prompt, "stream": False,
                "options": {"temperature": 0.4, "max_tokens": 600}
            }).encode()
            req = urllib.request.Request(OLLAMA_CHAT, data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                resp = json.loads(r.read())
            texto = resp.get('response', '').strip()
        except Exception as e:
            print('[IdeaToSpec] Erro LLM: %s' % e)
            continue
        
        # Extrai JSON
        if '```json' in texto:
            texto = texto.split('```json')[1].split('```')[0].strip()
        elif '```' in texto:
            texto = texto.split('```')[1].split('```')[0].strip()
        
        try:
            spec = json.loads(texto)
        except json.JSONDecodeError:
            prompt += "\nJSON invalido. Use aspas duplas, sem trailing commas.\n"
            continue
        
        # Valida campos minimos
        tipo = spec.get('type', '')
        if tipo not in ('npc', 'monster', 'quest'):
            prompt += "\nType deve ser 'npc', 'monster' ou 'quest'.\n"
            continue
        if tipo == 'npc' and not spec.get('name'):
            prompt += "\nNPC precisa de 'name'.\n"
            continue
        if tipo == 'quest' and not spec.get('giver'):
            prompt += "\nQuest precisa de 'giver'.\n"
            continue
        if tipo == 'monster' and not spec.get('name'):
            prompt += "\nMonster precisa de 'name'.\n"
            continue
        
        # Preenche defaults
        spec.setdefault('role', 'figura do mundo')
        spec.setdefault('location', 'regiao desconhecida')
        
        return spec
    
    return None
