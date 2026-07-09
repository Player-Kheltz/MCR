"""mcr.mcr_world_foundation — Fundacao do Mundo (WorldSeed + Eventos).
Gera, valida e muta o estado estruturado do mundo, conectado a cronica."""
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request
from typing import Dict, List, Optional, Tuple

# ─── Modelos LLM ───────────────────────────────────────────────
OLLAMA_CHAT = "http://localhost:11434/api/generate"
MODELO_SEED = "qwen2.5-coder:7b"
MODELO_CRONICA = "mistral:7b"

# ─── Schema do WorldSeed ────────────────────────────────────────
WORLD_SEED_SCHEMA = {
    "world_name": {"type": str, "required": True, "desc": "Nome do mundo"},
    "theme": {"type": str, "required": True, "desc": "Tema central"},
    "main_conflict": {"type": str, "required": True, "desc": "Conflito principal"},
    "regions": {
        "type": list, "required": True, "desc": "Lista de regiões",
        "items": {
            "name": {"type": str, "required": True, "desc": "Nome da região"},
            "description": {"type": str, "required": True, "desc": "Descrição"},
            "terrain_hints": {"type": dict, "required": False, "desc": "Sugestões de terreno"},
            "danger_level": {"type": str, "required": False, "desc": "low/medium/high"},
        }
    },
    "factions": {
        "type": list, "required": True, "desc": "Facções",
        "items": {
            "name": {"type": str, "required": True},
            "type": {"type": str, "required": True, "desc": "guild/cult/etc"},
            "goal": {"type": str, "required": True},
            "members": {"type": list, "required": False, "desc": "Nomes dos membros"},
        }
    },
    "characters": {
        "type": list, "required": True, "desc": "Personagens",
        "items": {
            "name": {"type": str, "required": True},
            "role": {"type": str, "required": True, "desc": "vendedor/guerreiro/mago"},
            "faction": {"type": str, "required": False},
            "location": {"type": str, "required": True, "desc": "Região onde está"},
            "motivation": {"type": str, "required": True},
            "state": {"type": str, "required": False, "desc": "alive/dead"},
        }
    },
    "monsters": {
        "type": list, "required": True, "desc": "Monstros",
        "items": {
            "name": {"type": str, "required": True},
            "habitat": {"type": str, "required": True, "desc": "Região"},
            "danger_level": {"type": str, "required": False},
        }
    },
    "quest_seeds": {
        "type": list, "required": True, "desc": "Sementes de quest",
        "items": {
            "title": {"type": str, "required": True},
            "giver": {"type": str, "required": True, "desc": "Nome do NPC"},
            "objective": {"type": str, "required": True},
            "reward": {"type": str, "required": True},
        }
    },
    "map_blueprint": {
        "type": dict, "required": True, "desc": "Layout do mapa",
        "items": {
            "overall_layout": {"type": str, "required": True},
        }
    },
}


# ─── Funcoes internas ──────────────────────────────────────────

def _call_llm(prompt: str, model: str, max_tokens: int = 1500, temp: float = 0.4) -> Optional[str]:
    """Chama o Ollama. Usa qwen para JSON, mistral para cronica."""
    try:
        payload = json.dumps({
            "model": model, "prompt": prompt, "stream": False,
            "options": {"temperature": temp, "max_tokens": max_tokens}
        }).encode()
        req = urllib.request.Request(OLLAMA_CHAT, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read())
        return resp.get('response', '').strip()
    except Exception as e:
        print('[Foundation] Erro LLM (%s): %s' % (model, e))
        return None


def _extrair_json(texto: str) -> Optional[str]:
    """Extrai JSON de resposta do LLM removendo marcacoes ``` do markdown."""
    if not texto:
        return None
    texto = texto.strip()
    if '```json' in texto:
        texto = texto.split('```json')[1].split('```')[0].strip()
    elif '```' in texto:
        texto = texto.split('```')[1].split('```')[0].strip()
    return texto


# ─── API publica ───────────────────────────────────────────────

def generate_world_seed(theme: str, min_elements: dict = None) -> dict:
    """Chama o LLM para gerar um WorldSeed JSON estruturado.
    
    Args:
        theme: tema do mundo (ex: "A Feira dos Mercadores de Eldoria")
        min_elements: dict com minimos (regions, characters, monsters, quest_seeds)
    
    Returns:
        dict validado com o WorldSeed
        
    Raises:
        ValueError se falhar apos 2 tentativas
    """
    if min_elements is None:
        min_elements = {"regions": 2, "characters": 3, "monsters": 2, "quest_seeds": 2}

    # Monta o schema completo para o prompt (converte types to string)
    def _type_str(t):
        if t == str: return 'string'
        if t == list: return 'array'
        if t == dict: return 'object'
        return str(t.__name__)

    def _serializar_schema(schema):
        if isinstance(schema, dict) and 'type' in schema and 'desc' in schema:
            return {'tipo': _type_str(schema['type']), 'obrigatorio': schema.get('required', False), 'descricao': schema['desc']}
        if isinstance(schema, dict) and 'items' in schema and 'type' in schema:
            s = {'tipo': _type_str(schema['type']), 'obrigatorio': schema.get('required', False), 'descricao': schema.get('desc', '')}
            if 'items' in schema:
                if isinstance(schema['items'], dict) and 'name' in schema['items']:
                    s['itens'] = {k: _serializar_schema(v) for k, v in schema['items'].items()}
                else:
                    s['itens'] = _serializar_schema(schema['items'])
            return s
        if isinstance(schema, dict):
            return {k: _serializar_schema(v) for k, v in schema.items()}
        return schema

    schema_serializado = _serializar_schema(WORLD_SEED_SCHEMA)
    schema_str = json.dumps(schema_serializado, indent=2, ensure_ascii=False)

    prompt = (
        "Gere um WorldSeed (fundacao de mundo de RPG) no formato JSON exato descrito abaixo.\n"
        "Retorne APENAS o JSON valido, sem comentarios, sem marcacao ```.\n"
        "Quantidades minimas: %s regioes, %s personagens, %s monstros, %s sementes de quest.\n"
        "Os dados devem ser COERENTES: personagens pertencem a faccoes/regioes existentes; "
        "quests referenciam personagens e monstros existentes.\n"
        "CADA quest_seed DEVE ter um campo \"giver\" com o nome exato de um personagem existente.\n"
        "CRITICO: Cada quest deve combinar tematicamente com o papel (role) e descricao do seu giver.\n"
        "  - Se o giver e um vendedor de flores, a quest deve ser sobre flores, plantas ou jardinagem.\n"
        "  - Se o giver e um ferreiro, a quest deve envolver armas, metal ou forja.\n"
        "  - Se o giver e um feiticeiro, a quest deve ser sobre magia, pocoes ou ingredientes magicos.\n"
        "  - Se o giver e um cacador de armadilhas, a quest deve ser sobre armadilhas, caca ou mecanismos.\n"
        "Garanta que o titulo e objetivo da quest reflitam claramente a profissao do giver.\n\n"
        "TEMA: %s\n\n"
        "SCHEMA:\n%s\n\n"
        "JSON:" % (
            min_elements.get('regions', 2),
            min_elements.get('characters', 3),
            min_elements.get('monsters', 2),
            min_elements.get('quest_seeds', 2),
            theme,
            schema_str,
        )
    )

    for tentativa in range(3):
        print('[Foundation] Gerando WorldSeed (tentativa %d)...' % (tentativa + 1))
        resposta = _call_llm(prompt, MODELO_SEED, max_tokens=2000, temp=0.4)
        json_str = _extrair_json(resposta)
        if not json_str:
            print('[Foundation] Resposta vazia. Retentando...')
            continue
        try:
            seed = json.loads(json_str)
        except json.JSONDecodeError as e:
            print('[Foundation] JSON invalido: %s. Retentando...' % e)
            prompt += "\n\nERRO: O JSON anterior era invalido. Garanta chaves, colchetes e virgulas corretos.\n"
            continue

        # Pre-valida chaves obrigatorias
        obrigatorias = ['world_name', 'theme', 'main_conflict', 'regions', 'factions',
                        'characters', 'monsters', 'quest_seeds', 'map_blueprint']
        faltando = [k for k in obrigatorias if k not in seed]
        if faltando:
            print('[Foundation] Chaves faltando: %s. Retentando...' % faltando)
            prompt += "\n\nERRO: Chaves obrigatorias ausentes: %s. Inclua todas." % ', '.join(faltando)
            continue

        # Preenche estados default
        for c in seed.get('characters', []):
            c.setdefault('state', 'alive')
        for m in seed.get('monsters', []):
            m.setdefault('state', 'alive')

        # Validacao final com coherence check
        valido, erros = validate_foundation(seed, min_elements)
        if not valido:
            erros_coerencia = [e for e in erros if 'Incoerencia tematica' in e]
            if erros_coerencia:
                print('[Foundation] Incoerencias tematicas detectadas. Retentando...')
                for e in erros_coerencia:
                    print('  %s' % e)
                prompt += "\n\nERROS DE COERENCIA TEMATICA (corrija TROCANDO o giver ou ajustando a role):\n"
                prompt += '\n'.join('- %s' % e for e in erros_coerencia)
                prompt += (
                    "\n\nCorrecao: para cada quest com erro, TROQUE o giver para um personagem "
                    "cuja role/descricao combine com o tema da quest.\n"
                    "Ex: quest sobre pocoes -> giver deve ser alquimista ou feiticeiro.\n"
                    "Ex: quest sobre armadilhas -> giver deve ser cacador ou comerciante de armadilhas.\n"
                    "Ex: quest sobre flores -> giver deve ser vendedor de flores ou jardineiro.\n"
                    "Se necessario, crie um novo personagem com a role adequada.\n"
                )
                continue
            # Outros erros de validacao
            print('[Foundation] Erros de validacao: %s' % '; '.join(erros[:3]))
            prompt += "\n\nERROS:\n" + '\n'.join('- %s' % e for e in erros[:5])
            prompt += "\n\nRegere o JSON corrigindo os erros acima.\n"
            continue

        print('[Foundation] WorldSeed gerado: %s (%d personagens, %d regioes, %d quests)' % (
            seed['world_name'], len(seed.get('characters', [])),
            len(seed.get('regions', [])), len(seed.get('quest_seeds', []))))
        return seed

    raise ValueError("Falha ao gerar WorldSeed apos 3 tentativas — incoerencias tematicas nao resolvidas")


def validate_foundation(seed: dict, min_elements: dict = None) -> Tuple[bool, List[str]]:
    """Valida um WorldSeed contra schema, suficiencia e consistencia interna.
    
    Returns:
        (True, []) se valido, (False, lista_de_erros) caso contrario.
    """
    erros = []
    if min_elements is None:
        min_elements = {"regions": 2, "characters": 3, "monsters": 2, "quest_seeds": 2}

    # Schema obrigatorio
    obrigatorias = ['world_name', 'theme', 'main_conflict', 'regions', 'factions',
                    'characters', 'monsters', 'quest_seeds', 'map_blueprint']
    for k in obrigatorias:
        if k not in seed:
            erros.append('Chave obrigatoria ausente: %s' % k)

    if erros:
        return False, erros

    # Suficiencia
    if len(seed.get('regions', [])) < min_elements.get('regions', 0):
        erros.append('Regioes: %d < minimo %d' % (len(seed['regions']), min_elements['regions']))
    if len(seed.get('characters', [])) < min_elements.get('characters', 0):
        erros.append('Personagens: %d < minimo %d' % (len(seed['characters']), min_elements['characters']))
    if len(seed.get('monsters', [])) < min_elements.get('monsters', 0):
        erros.append('Monstros: %d < minimo %d' % (len(seed['monsters']), min_elements['monsters']))
    if len(seed.get('quest_seeds', [])) < min_elements.get('quest_seeds', 0):
        erros.append('Quests: %d < minimo %d' % (len(seed['quest_seeds']), min_elements['quest_seeds']))

    # Nomes dos personagens e monstros para validacao
    nomes_personagens = {c['name'] for c in seed.get('characters', []) if 'name' in c}
    nomes_monstros = {m['name'] for m in seed.get('monsters', []) if 'name' in m}

    # Consistencia: membros das faccoes existem como personagens
    for faccao in seed.get('factions', []):
        for membro in faccao.get('members', []):
            if membro not in nomes_personagens:
                erros.append('Faccao "%s": membro "%s" nao existe em characters' % (faccao['name'], membro))

    # Consistencia: quest giver existe (OBRIGATORIO)
    for i, quest in enumerate(seed.get('quest_seeds', [])):
        quest_title = quest.get('title', '').strip()
        if not quest_title:
            erros.append('Quest %d: campo "title" obrigatorio e vazio' % (i + 1))
            # Gera nome artificial para continuar validacao
            quest_title = 'quest_%d' % i
            quest['title'] = quest_title
        giver = quest.get('giver', '')
        chars_inv = quest.get('characters_involved', [])
        if not giver and not chars_inv:
            erros.append('Quest %d "%s": precisa de campo "giver" ou "characters_involved"' % (
                i + 1, quest_title))
            continue
        # Usa giver se existir, senao o primeiro de characters_involved
        resolved = giver or (chars_inv[0] if chars_inv else '')
        if resolved:
            if resolved not in nomes_personagens and resolved not in nomes_monstros:
                erros.append('Quest "%s": giver "%s" nao existe em characters nem monsters' % (
                    quest.get('title', '?'), resolved))
            # Adiciona campo giver se nao existir (normaliza)
            if not giver and resolved:
                quest['giver'] = resolved
        for envolvido in quest.get('involves', []):
            if envolvido not in nomes_personagens and envolvido not in nomes_monstros:
                erros.append('Quest "%s": involves "%s" nao encontrado' % (quest.get('title', '?'), envolvido))

    # Personagens em locations que existem como regioes
    nomes_regioes = {r['name'] for r in seed.get('regions', []) if 'name' in r}
    for c in seed.get('characters', []):
        loc = c.get('location', '')
        if loc and loc not in nomes_regioes:
            erros.append('Personagem "%s": location "%s" nao e uma regiao declarada' % (c['name'], loc))

    # Nomes unicos
    if len(nomes_personagens) < len(seed.get('characters', [])):
        erros.append('Personagens com nomes duplicados')
    if len(nomes_monstros) < len(seed.get('monsters', [])):
        erros.append('Monstros com nomes duplicados')

    # Coerencia tematica quest -> giver
    erros.extend(_validar_coerencia_quests(seed))

    return (len(erros) == 0), erros


# ─── Mapa semantico para validacao de coerencia quest-giver ──
# Palavras-chave de quest -> papeis/descricoes esperados do giver
_MAPA_COERENCIA_QUEST = [
    (['flor', 'flores', 'jardim', 'jardinagem', 'plantar', 'plantas', 'rosa', 'buque'],
     ['flor', 'vendedor', 'comerciante', 'mercador', 'jardim', 'natureza', 'rural']),
    (['armadilha', 'desarmar', 'trap', 'mecanismo', 'armadilhas', 'caca', 'cacador'],
     ['armadilha', 'cacador', 'trap', 'mecanico', 'engenho', 'explorador']),
    (['magia', 'feitico', 'feiticeiro', 'mago', 'magico', 'encanto', 'pocao', 'pocoes',
      'aprendiz de magia', 'feiticaria', 'runas', 'encantamento'],
     ['mago', 'feiticeiro', 'magia', 'aprendiz', 'mistico', 'arcano', 'alquimista']),
    (['ferreiro', 'arma', 'armadura', 'espada', 'forja', 'metal', 'ferro', 'aco',
      'ferramenta'],
     ['ferreiro', 'arma', 'armadura', 'forja', 'metalurgico', 'guerreiro']),
    (['pocao', 'alquimia', 'herbologia', 'ervas', 'ingrediente', 'medicina'],
     ['alquimista', 'herborista', 'medico', 'curandeiro', 'pocao']),
    (['tesouro', 'baú', 'baú', 'reliquia', 'artefato', 'ruina', 'exploracao'],
     ['explorador', 'aventureiro', 'cacador de tesouro', 'mercenario']),
    (['guilda', 'guild', 'faccao', 'faccao', 'alianca', 'territorio', 'poder',
      'lideranca', 'comercio'],
     ['lider', 'comerciante', 'mercador', 'embaixador', 'negociador']),
    (['defesa', 'guarda', 'protetor', 'seguranca', 'ronda', 'patrulha', 'sentinela'],
     ['guarda', 'guerreiro', 'cavaleiro', 'soldado', 'protetor', 'vigilante']),
]


def _normalizar(texto: str) -> str:
    """Remove acentos e normaliza texto para comparacao."""
    # Decompoe acentos (ex: ç -> c, ã -> a)
    nfkd = unicodedata.normalize('NFKD', texto)
    return nfkd.encode('ASCII', 'ignore').decode('ASCII').lower()


def _correspondencia(palavras_quest: set, role_desc: str) -> bool:
    """Verifica se alguma palavra da quest tem correspondencia tematica com o giver."""
    role_lower = _normalizar(role_desc)
    texto_quest_normalizado = _normalizar(' '.join(palavras_quest))
    for keywords_quest, keywords_role in _MAPA_COERENCIA_QUEST:
        keywords_quest_norm = [_normalizar(k) for k in keywords_quest]
        keywords_role_norm = [_normalizar(k) for k in keywords_role]
        if any(kw in texto_quest_normalizado for kw in keywords_quest_norm):
            if any(kw in role_lower for kw in keywords_role_norm):
                return True
    return False


def _extrair_palavras(texto: str) -> set:
    """Extrai palavras significativas (>3 chars) de um texto."""
    palavras = re.findall(r'\b[a-zA-Zà-úÀ-Ú]{4,}\b', texto.lower())
    return set(palavras)


def _validar_coerencia_quests(seed: dict) -> list:
    """Valida que cada quest corresponde tematicamente ao papel do seu giver.
    
    Para cada quest, extrai palavras-chave do titulo e objetivo e verifica
    se ao menos uma se alinha com a role/descricao do personagem giver.
    """
    from mcr.paths import DEVIA_DIR
    erros = []
    personagens = {c['name']: c for c in seed.get('characters', [])}

    for quest in seed.get('quest_seeds', []):
        giver_nome = quest.get('giver', '')
        if not giver_nome or giver_nome not in personagens:
            continue  # ja validado antes

        giver = personagens[giver_nome]
        role = giver.get('role', '') + ' ' + giver.get('description', '')

        # Palavras do titulo + objetivo
        texto_quest = (quest.get('title', '') + ' ' + quest.get('objective', '') +
                       ' ' + quest.get('description', ''))
        palavras_quest = _extrair_palavras(texto_quest)

        if not palavras_quest:
            continue

        if not _correspondencia(palavras_quest, role):
            erros.append(
                "Incoerencia tematica: quest '%s' (sobre: %s) atribuida a '%s' (%s) "
                "- sem relacao tematica." % (
                    quest.get('title', '?'),
                    ', '.join(sorted(palavras_quest)[:5]),
                    giver_nome,
                    role[:60] if role else 'sem role',
                ))
    return erros


def world_event(entity_type: str, entity_name: str, new_state: any = None,
                narrative: str = "", source: str = "", metadata: dict = None) -> dict:
    """Evento atomico: altera estado de entidade no WorldSeed + registra na Cronica.
    
    Args:
        entity_type: 'npc', 'monster', 'region', 'faction', 'item', 'quest'
        entity_name: nome exato da entidade
        new_state: novo valor do campo state (ou controlling_faction para regions)
        narrative: texto narrativo do evento
        source: quem/qual sistema gerou o evento
        metadata: dict extra para registrar na cronica
    
    Returns:
        dict com resumo do evento
    
    Raises:
        ValueError se entidade nao encontrada
    """
    from mcr.mcr_world_state import carregar_foundation, salvar_foundation
    from mcr.mcr_world_chronicle import append_chronicle

    seed = carregar_foundation()
    if not seed:
        raise ValueError("Nenhum WorldSeed encontrado (current_foundation vazio)")

    # Mapa de tipos para listas no seed
    type_to_list = {
        'npc': 'characters',
        'monster': 'monsters',
        'region': 'regions',
        'faction': 'factions',
        'item': 'items_of_interest',
        'quest': 'quest_seeds',
    }
    lista_chave = type_to_list.get(entity_type)
    if not lista_chave or lista_chave not in seed:
        raise ValueError('Tipo de entidade invalido ou nao suportado: %s' % entity_type)

    # Encontra a entidade
    entidade = None
    for e in seed.get(lista_chave, []):
        if e.get('name') == entity_name or e.get('title') == entity_name:
            entidade = e
            break

    if entidade is None:
        raise ValueError('Entidade "%s" nao encontrada na lista %s' % (entity_name, lista_chave))

    # Atualiza estado
    if entity_type in ('npc', 'monster'):
        entidade['state'] = new_state if new_state is not None else entidade.get('state', 'alive')
    elif entity_type == 'region':
        entidade['controlling_faction'] = new_state if new_state is not None else entidade.get('controlling_faction', '')
    else:
        entidade['state'] = new_state if new_state is not None else entidade.get('state', 'active')

    # Gera ID do evento
    event_id = "%s_%s_%d" % (entity_type, entity_name, int(time.time()))

    # Monta metadata da cronica
    meta = {
        'event_id': event_id,
        'entity_type': entity_type,
        'entity_name': entity_name,
        'new_state': new_state,
        'source': source,
    }
    if metadata:
        meta.update(metadata)

    # Salva no chronicle
    entry = "**%s**: %s" % (entity_name, narrative) if narrative else \
            "**%s**: estado alterado para %s" % (entity_name, new_state)
    append_chronicle(entry, metadata=meta)

    # Salva fundacao atualizada
    salvar_foundation(seed)

    print('[Foundation] Evento: %s (%s -> %s)' % (event_id, entity_name, new_state))
    return {
        'event_id': event_id,
        'entity_type': entity_type,
        'entity_name': entity_name,
        'new_state': new_state,
        'chronicle_updated': True,
    }
