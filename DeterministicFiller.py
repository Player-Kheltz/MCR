"""DeterministicFiller — preenche gaps de template com valores determinísticos.

Mapeia:
- Domínio ID → cor, elemento, tipo de dano
- Tipo de habilidade → cooldown, categoria, focoMin
- Tipo de NPC → outfit, vida, comportamento

Esses mapeamentos são extraídos do PERSONALIDADE.md e do código existente do SPA.
"""

# ─── DOMÍNIO → COR ────────────────────────────────────────────────

DOMINIO_COR = {
    1: "COR.DOM_COMBATE_LAMINAS",
    2: "COR.DOM_MAGIA_RUNOLOGIA",
    3: "COR.DOM_OFICIO_CRAFT",
    4: "COR.DOM_NATUREZA_SOBREV",
    10: "COR.DOM_COMBATE_LAMINAS",
    11: "COR.DOM_COMBATE_IMPACTO",
    12: "COR.DOM_COMBATE_IMPACTO",
    14: "COR.DOM_COMBATE_ARTES_MARCIAIS",
    15: "COR.DOM_ESCUDO",
    20: "COR.DOM_MAGIA_FOGO",
    23: "COR.DOM_MAGIA_FOGO",
    24: "COR.DOM_MAGIA_AGUA_GELO",
    25: "COR.DOM_MAGIA_TERRA",
    26: "COR.DOM_MAGIA_FOGO",
    28: "COR.DOM_MAGIA_RUNOLOGIA",
    100: "COR.DOM_COMBATE_PRECISAO",
    101: "COR.DOM_COMBATE_IMPACTO",
    111: "COR.DOM_COMBATE_IMPACTO",
    112: "COR.DOM_COMBATE_IMPACTO",
    113: "COR.DOM_COMBATE_IMPACTO",
    120: "COR.DOM_COMBATE_PRECISAO",
    130: "COR.DOM_COMBATE_ARTES_MARCIAIS",
    132: "COR.DOM_COMBATE_ARTES_MARCIAIS",
    133: "COR.DOM_MAGIA_RUNOLOGIA",
    140: "COR.DOM_ESCUDO",
    200: "COR.DOM_MAGIA_SAGRADO",
    400: "COR.DOM_NATUREZA_SOBREV",
}

# ─── DOMÍNIO → ELEMENTO DE DANO ───────────────────────────────────

DOMINIO_ELEMENTO = {
    23: "COMBAT_FIREDAMAGE",
    24: "COMBAT_ICEDAMAGE",
    25: "COMBAT_EARTHDAMAGE",
    26: "COMBAT_ENERGYDAMAGE",
    200: "COMBAT_HOLYDAMAGE",
    201: "COMBAT_DEATHDAMAGE",
    100: "COMBAT_PHYSICALDAMAGE",
    101: "COMBAT_PHYSICALDAMAGE",
    111: "COMBAT_PHYSICALDAMAGE",
    112: "COMBAT_PHYSICALDAMAGE",
    113: "COMBAT_PHYSICALDAMAGE",
    120: "COMBAT_PHYSICALDAMAGE",
    132: "COMBAT_PHYSICALDAMAGE",
    133: "COMBAT_FIREDAMAGE",
    14: "COMBAT_PHYSICALDAMAGE",
}

# ─── DOMÍNIO → CONST_ME (efeito visual padrão) ────────────────────

DOMINIO_MAGIC_EFFECT = {
    23: "CONST_ME_FIREAREA",
    24: "CONST_ME_ICEAREA",
    25: "CONST_ME_GROUNDSHAKER",
    26: "CONST_ME_ENERGYAREA",
    200: "CONST_ME_HOLYAREA",
    201: "CONST_ME_MORTAREA",
    100: "CONST_ME_DRAWBLOOD",
    101: "CONST_ME_HITAREA",
}

# ─── TIPO DE EFEITO → CATEGORIA PADRÃO ────────────────────────────

EFEITO_CATEGORIA = {
    "dano_extra": "single",
    "area_ground": "aoe",
    "area_target": "aoe",
    "ricochete": "aoe",
    "knockback": "single",
    "rajada": "aoe",
    "corrente": "aoe",
    "finisher": "finisher",
    "condicao": "debuff",
    "buff_speed": "buff",
    "buff_damage": "buff",
    "life_leech": "single",
    "mana_leech": "single",
    "defesa_cura": "defense",
    "defesa_barreira": "defense",
    "defesa_contra_ataque": "defense",
    "field": "aoe",
    "sinergia": "sinergia",
    "storm": "aoe",
    "orbit": "aoe",
    "rain": "aoe",
    "pulse": "aoe",
    "trap": "aoe",
    "summon": "sinergia",
    "melee": "single",
    "projectile": "single",
    "beam": "aoe",
    "explosion_ring": "aoe",
}

# ─── TIPO DE EFEITO → COOLDOWN PADRÃO ────────────────────────────

EFEITO_COOLDOWN = {
    "dano_extra": 3,
    "area_ground": 6,
    "area_target": 8,
    "ricochete": 5,
    "knockback": 7,
    "rajada": 10,
    "corrente": 8,
    "finisher": 12,
    "condicao": 6,
    "buff_speed": 15,
    "buff_damage": 12,
    "life_leech": 8,
    "defesa_cura": 10,
    "defesa_barreira": 15,
    "defesa_contra_ataque": 8,
    "field": 10,
    "sinergia": 6,
    "storm": 15,
    "orbit": 12,
    "rain": 15,
    "pulse": 10,
    "trap": 12,
    "summon": 20,
    "melee": 3,
    "projectile": 5,
    "beam": 8,
    "explosion_ring": 10,
}

# ─── TIPO DE EFEITO → CONDICAO_FOCO_MIN ──────────────────────────

EFEITO_FOCO = {
    "dano_extra": 0,
    "area_ground": 50,
    "area_target": 50,
    "ricochete": 25,
    "knockback": 75,
    "rajada": 50,
    "corrente": 25,
    "finisher": 90,
    "condicao": 25,
    "buff_speed": 0,
    "buff_damage": 0,
    "life_leech": 25,
    "defesa_cura": 0,
    "defesa_barreira": 0,
    "defesa_contra_ataque": 25,
    "field": 50,
    "sinergia": 25,
    "storm": 50,
    "orbit": 50,
    "rain": 50,
    "pulse": 50,
    "trap": 50,
    "summon": 50,
    "melee": 0,
    "projectile": 0,
    "beam": 50,
    "explosion_ring": 50,
}


def preencher_gap(gap_nome: str, task: dict = None) -> str:
    """Preenche um gap determinístico baseado no nome e no contexto da tarefa."""
    if task is None:
        task = {}
    
    dominio_id = task.get("dominio_id")
    tipo_efeito = task.get("tipo_efeito")
    
    # Mapeamento direto de gap_nome → valores determinísticos
    mapeamento = {
        "dominio_id": str(dominio_id) if dominio_id else "1",
        "cooldown_segundos": str(EFEITO_COOLDOWN.get(tipo_efeito, 5)) if tipo_efeito else "5",
        "foco_minimo": str(EFEITO_FOCO.get(tipo_efeito, 25)) if tipo_efeito else "25",
        "nivel_minimo": task.get("nivel_min", "5"),
    }
    
    if gap_nome in mapeamento:
        return str(mapeamento[gap_nome])
    
    # Mapeamentos que dependem do domínio
    if gap_nome == "cor_dominio" and dominio_id:
        return DOMINIO_COR.get(int(dominio_id), "COR.DOM_COMBATE_LAMINAS")
    
    if gap_nome == "elemento_dano" and dominio_id:
        return DOMINIO_ELEMENTO.get(int(dominio_id), "COMBAT_PHYSICALDAMAGE")
    
    if gap_nome == "magic_effect" and dominio_id:
        return DOMINIO_MAGIC_EFFECT.get(int(dominio_id), "CONST_ME_HITAREA")
    
    if gap_nome == "categoria_habilidade" and tipo_efeito:
        return EFEITO_CATEGORIA.get(tipo_efeito, "single")
    
    # Fallback: retorna o placeholder original
    return f"<<<{gap_nome}>>>"


def preencher_template(template: str, task: dict = None) -> str:
    """Preenche todos os gaps determinísticos de um template.
    
    Gaps que não podem ser preenchidos deterministicamente permanecem como placeholders
    para o LLM preencher (nomes, descrições, lore).
    """
    if task is None:
        task = {}
    
    import re
    resultado = template
    
    # Encontra todos os placeholders <<<nome>>>
    gaps = re.findall(r'<<<([^>]+)>>>', resultado)
    
    for gap_nome in gaps:
        valor = preencher_gap(gap_nome, task)
        resultado = resultado.replace(f'<<<{gap_nome}>>>', valor)
    
    return resultado


def gaps_restantes(template_preenchido: str) -> list:
    """Retorna a lista de gaps que ainda não foram preenchidos (precisam de LLM)."""
    import re
    return re.findall(r'<<<([^>]+)>>>', template_preenchido)
