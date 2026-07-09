"""mcr.mcr_entity_validator — Validacao de entidades individuais.
Verifica nome unico, consistencia de giver/quest, coerencia tematica
contra o estado acumulado do mundo."""
import re
from typing import List, Tuple, Set


def _normalizar_nome(nome: str) -> str:
    """Normaliza nome para comparacao: lowercase, sem acentos, sem espacos extras."""
    import unicodedata
    nfkd = unicodedata.normalize('NFKD', nome)
    ascii_str = nfkd.encode('ASCII', 'ignore').decode('ASCII')
    return re.sub(r'\s+', ' ', ascii_str.lower().strip())


# ─── Mapa semantico para validacao de coerencia quest-giver ──
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
    (['tesouro', 'bau', 'reliquia', 'artefato', 'ruina', 'exploracao'],
     ['explorador', 'aventureiro', 'cacador de tesouro', 'mercenario']),
    (['guilda', 'guild', 'faccao', 'alianca', 'territorio', 'poder',
      'lideranca', 'comercio'],
     ['lider', 'comerciante', 'mercador', 'embaixador', 'negociador']),
    (['defesa', 'guarda', 'protetor', 'seguranca', 'ronda', 'patrulha', 'sentinela'],
     ['guarda', 'guerreiro', 'cavaleiro', 'soldado', 'protetor', 'vigilante']),
]


def _normalizar(texto: str) -> str:
    import unicodedata
    nfkd = unicodedata.normalize('NFKD', texto)
    return nfkd.encode('ASCII', 'ignore').decode('ASCII').lower()


def _verificar_coerencia_quest(quest: dict, world_state: dict,
                                nomes_pendentes: Set[str]) -> List[str]:
    """Verifica se quest combina tematicamente com o giver."""
    erros = []
    giver_nome = quest.get('giver', '')
    if not giver_nome:
        return ['Quest sem giver']

    # Busca giver no estado + pendentes
    giver = None
    for c in world_state.get('characters', []):
        if _normalizar_nome(c.get('name', '')) == _normalizar_nome(giver_nome):
            giver = c
            break
    for c in world_state.get('npcs', {}).values():
        if _normalizar_nome(c.get('name', '')) == _normalizar_nome(giver_nome):
            giver = {'name': giver_nome, 'role': c.get('role', ''), 'description': ''}
            break
    if not giver and giver_nome in nomes_pendentes:
        giver = {'name': giver_nome, 'role': '', 'description': ''}
    if not giver:
        return ['Giver "%s" nao encontrado' % giver_nome]

    role = (giver.get('role', '') + ' ' + giver.get('description', '')).strip()
    if not role:
        return []  # sem role para verificar

    texto_quest = (quest.get('title', '') + ' ' + quest.get('objective', '') +
                   ' ' + quest.get('description', ''))
    palavras_quest = set(re.findall(r'\b[a-zA-Z]{4,}\b', _normalizar(texto_quest)))
    if not palavras_quest:
        return []

    role_normalizada = _normalizar(role)
    texto_quest_normalizado = _normalizar(' '.join(palavras_quest))

    for keywords_quest, keywords_role in _MAPA_COERENCIA_QUEST:
        kw_q = [_normalizar(k) for k in keywords_quest]
        kw_r = [_normalizar(k) for k in keywords_role]
        if any(k in texto_quest_normalizado for k in kw_q):
            if any(k in role_normalizada for k in kw_r):
                return []  # match encontrado
            # Palavra da quest encontrada mas role nao corresponde
            erros.append(
                "Incoerencia tematica: quest '%s' (sobre %s) atribuida a '%s' (%s)" % (
                    quest.get('title', '?'),
                    ', '.join(sorted(palavras_quest)[:3]),
                    giver_nome, role[:40]))
            return erros

    return []  # sem palavras de quest para verificar


def validate_entity(spec: dict, world_state: dict,
                    pending_names: Set[str] = None) -> Tuple[bool, List[str]]:
    """Valida uma entidade individual contra o estado acumulado do mundo.
    
    Args:
        spec: dict com 'type' (npc/monster/quest), 'name', 'role', etc.
        world_state: dict acumulado (npcs, monstros, characters, etc.)
        pending_names: set de nomes sendo criados neste batch
    
    Returns:
        (True, []) se valido, (False, lista_de_erros) caso contrario.
    """
    erros = []
    if pending_names is None:
        pending_names = set()

    tipo = spec.get('type', '')
    nome = spec.get('name', '') or spec.get('title', '')
    nome_norm = _normalizar_nome(nome)

    if not nome:
        return False, ['Entidade sem nome']
    if not tipo:
        return False, ['Entidade sem tipo']

    # Coleciona nomes existentes
    nomes_existentes = set()
    for chave in ('npcs', 'monstros', 'lores'):
        for nome_existente in world_state.get(chave, {}).keys():
            nomes_existentes.add(_normalizar_nome(nome_existente))
    for c in world_state.get('characters', []):
        nomes_existentes.add(_normalizar_nome(c.get('name', '')))
    for m in world_state.get('monsters', world_state.get('monstros', [])):
        nomes_existentes.add(_normalizar_nome(m.get('name', '')))

    # 1. Nome unico
    if nome_norm in nomes_existentes:
        erros.append('Nome "%s" ja existe no mundo' % nome)
    elif nome_norm in {_normalizar_nome(n) for n in pending_names}:
        erros.append('Nome "%s" ja esta pendente neste batch' % nome)

    # 2. Tipo especifico
    if tipo == 'quest':
        # Quest: verifica giver + coerencia
        giver = spec.get('giver', '')
        if not giver:
            erros.append('Quest sem giver')
        else:
            giver_norm = _normalizar_nome(giver)
            # Giver existe no estado ou pending?
            giver_exists = giver_norm in nomes_existentes or giver_norm in {
                _normalizar_nome(n) for n in pending_names}
            if not giver_exists:
                erros.append('Quest "%s": giver "%s" nao existe no mundo nem no batch atual' % (
                    spec.get('title', '?'), giver))
            # Coerencia tematica
            erros.extend(_verificar_coerencia_quest(spec, world_state, pending_names))

    elif tipo == 'npc':
        if not spec.get('role'):
            erros.append('NPC "%s" sem role' % nome)

    elif tipo == 'monster':
        if not spec.get('habitat'):
            erros.append('Monstro "%s" sem habitat' % nome)

    else:
        erros.append('Tipo desconhecido: %s' % tipo)

    return (len(erros) == 0), erros
