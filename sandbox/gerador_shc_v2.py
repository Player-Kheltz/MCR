"""
    GERADOR SHC V2 â€” Template + IA Local (Qwen Coder 7B)
    
    Como funciona:
    1. Python gera um "rascunho" com slots vazios para preencher
    2. Qwen Coder recebe o rascunho + exemplos reais e preenche os criativos
    3. Python monta o arquivo final e valida
    
    Uso: python gerador_shc_v2.py <dominio> [num_habilidades] [--model MODEL]
    
    Exemplo:
      python gerador_shc_v2.py clavas_leves 15 --model qwen2.5-coder:7b
"""

import sys, os, json, re, subprocess, random, math, shutil

OLLAMA_API = 'http://localhost:11434/api/generate'

# ============================================================
# DOMINIO CONFIG
# ============================================================
DOMINIOS = {
    'clavas_leves': {
        'id': 112, 'nome': 'CLAVAS LEVES', 'parent': 'Clavas 12 -> Combate 1',
        'traco': 'Danca das Clavas - Nv5: combo+1 | Nv10: atordoamento+10% | Nv15: desarme | Nv20: mestre das clavas',
        'cor': 'COR.DOM_CLAVAS',
        'elemento': 'COMBAT_PHYSICALDAMAGE',
        'ids': (11201, 11220),
        'sinergia_doms': [113, 130, 25, 23],
        'sinergia_nomes': ['Clavas Pesadas', 'Lutador', 'Terra', 'Fogo'],
        'estilo': 'corpoacorpo',
        'identidade': 'Clavas Leves sao armas ageis e precisas. Golpes rapidos que desarmam e atordoam. O usuario danca entre os inimigos com graca letal.',
    },
    'bastoes_arcanos': {
        'id': 133, 'nome': 'BASTOES ARCANOS', 'parent': 'Artes Marciais 14 -> Combate 1',
        'traco': 'Sabedoria Arcana - Nv5: mana+5% | Nv10: cooldown-10% | Nv15: duplo | Nv20: mestre arcano',
        'cor': 'COR.DOM_MAGIA_ARCANA',
        'elemento': 'COMBAT_ENERGYDAMAGE',
        'ids': (13301, 13320),
        'sinergia_doms': [23, 24, 26, 200],
        'sinergia_nomes': ['Fogo', 'Gelo', 'Energia', 'Sagrado/Morte'],
        'estilo': 'magia',
        'identidade': 'Bastoes Arcanos canalizam energia pura. Cada golpe e uma demonstracao de poder magico. Versateis e imprevisiveis.',
    },
    'arcos': {
        'id': 120, 'nome': 'ARCOS', 'parent': 'Precisao 13 -> Combate 1',
        'traco': 'Mira Infalivel - Nv5: alcance+1 | Nv10: critico+5% | Nv15: perfuracao | Nv20: olho de aguia',
        'cor': 'COR.DOM_COMBATE_PRECISAO',
        'elemento': 'COMBAT_PHYSICALDAMAGE',
        'ids': (12001, 12020),
        'sinergia_doms': [23, 24, 26],
        'sinergia_nomes': ['Fogo', 'Gelo', 'Energia'],
        'estilo': 'distancia',
        'identidade': 'Arcos sao precisos e mortais a distancia. Cada flecha e calculada. Paciencia e recompensada com dano devastador.',
    },
    'lutador': {
        'id': 130, 'nome': 'LUTADOR', 'parent': 'Artes Marciais 14 -> Combate 1',
        'traco': 'Punhos de Aco - Nv5: dano+10% | Nv10: combo+1 | Nv15: quebraossos | Nv20: mestre do combate',
        'cor': 'COR.DOM_COMBATE_IMPACTO',
        'elemento': 'COMBAT_PHYSICALDAMAGE',
        'ids': (13001, 13020),
        'sinergia_doms': [132, 14, 1],
        'sinergia_nomes': ['Armas de Punho', 'Artes Marciais', 'Combate'],
        'estilo': 'corpoacorpo',
        'identidade': 'Lutadores usam o corpo como arma. Golpes, chutes e quedas em sequencias devastadoras. Respeito e conquistado com os punhos.',
    },
    'sobrevivencia': {
        'id': 400, 'nome': 'SOBREVIVENCIA', 'parent': 'Natureza 4',
        'traco': 'Sobrevivente - Nv5: regen+1% | Nv10: velocidade+5% | Nv15: faro | Nv20: mestre da selva',
        'cor': 'COR.DOM_NATUREZA',
        'elemento': 'COMBAT_PHYSICALDAMAGE',
        'ids': (40001, 40020),
        'sinergia_doms': [24, 25, 120],
        'sinergia_nomes': ['Gelo', 'Terra', 'Arcos'],
        'estilo': 'distancia',
        'identidade': 'Sobrevivencia e a arte de prosperar na natureza. Armadilhas, rastreamento e ataque precisos. O selvagem e um cacador nato.',
    },
}

# ============================================================
# BIBLIOTECA DE MECANICAS CRIATIVAS (para inspirar o modelo local)
# ============================================================
MECANICAS = [
    'knockback', 'stun', 'lifesteal', 'manasteal', 'bleed', 'poison', 'slow',
    'reflect', 'shield', 'multi_hit', 'piercing', 'chain', 'pull', 'push',
    'root', 'silence', 'disarm', 'blind', 'fear', 'frenzy',
    'crit_chance', 'armor_break', 'progressive_damage', 'execute',
]

TIPOS_AOE = ['explosion_ring', 'cone', 'area_target', 'storm', 'field_aura']
TIPOS_SINGLE = ['projectile', 'melee', 'multi_hit']
TIPOS_UTIL = ['buff', 'debuff', 'trap', 'heal']

CATEGORIAS = {
    'single': ['single', 'single', 'single', 'single'],
    'aoe': ['aoe', 'aoe', 'aoe'],
    'buff': ['buff'],
    'debuff': ['debuff', 'debuff'],
    'defense': ['defense', 'defense'],
    'finisher': ['finisher'],
}

# Pesos para distribuicao
DISTRIBUICAO = [
    ('single', 0.4), ('aoe', 0.2), ('debuff', 0.1), ('buff', 0.1),
    ('defense', 0.1), ('finisher', 0.1),
]

# ============================================================
# FUNCOES DE GERACAO DE ESTRUTURA (Python 100%)
# ============================================================

def gerar_escalonamento(idx, total):
    """Gera valores escalonados baseados no indice da habilidade."""
    progresso = idx / total  # 0.0 a 1.0
    
    dano = round(0.4 + progresso * 1.8, 1)
    percentual = round(0.15 + progresso * 0.45, 2)
    cd = max(1, 12 - int(progresso * 10))
    
    return dano, percentual, cd

def escolher_categoria(idx, total):
    """Distribui categorias de forma variada."""
    progresso = idx / total
    if progresso < 0.15:  # primeiras: single
        return 'single', TIPOS_SINGLE[0] if progresso < 0.07 else TIPOS_SINGLE[1]
    elif progresso < 0.35:  # variedade
        return 'single', random.choice(TIPOS_SINGLE)
    elif progresso < 0.50:
        return 'aoe', random.choice(TIPOS_AOE)
    elif progresso < 0.60:
        return 'debuff', 'debuff'
    elif progresso < 0.70:
        return 'buff', 'buff'
    elif progresso < 0.80:
        return 'aoe', random.choice(TIPOS_AOE)
    elif progresso < 0.85:
        return 'defense', random.choice(['buff', 'melee'])
    elif progresso < 0.95:
        return 'finisher', random.choice(['storm', 'multi_hit', 'explosion_ring'])
    else:
        return 'finisher', 'storm'

def gerar_postura(dano_base, idx):
    """Gera variacao de postura.
    [1] = Impeto (ofensivo)
    [2] = Equilibrio (neutro) 
    [3] = Guarda (defensivo)
    """
    variacao = idx % 4
    if variacao == 0:
        # Impeto forte, Guarda fraco
        return {
            1: round(dano_base * 1.35, 1),
            3: round(dano_base * 0.65, 1),
        }
    elif variacao == 1:
        # Impeto medio, Guarda medio
        return {
            1: round(dano_base * 1.2, 1),
            3: round(dano_base * 0.8, 1),
        }
    elif variacao == 2:
        # Impeto fraco, Guarda forte (contra - ataque)
        return {
            1: round(dano_base * 0.85, 1),
            3: round(dano_base * 1.15, 1),
        }
    else:
        # Impeto muito forte, Guarda muito fraco
        return {
            1: round(dano_base * 1.5, 1),
            3: round(dano_base * 0.5, 1),
        }

def gerar_niveis(idx):
    """Gera melhorias por nivel (marcos 5/10/15)."""
    variacao = idx % 4
    niveis = []
    
    # Marco 5 sempre tem dano
    niveis.append({'marco': 5, 'mods': [{'mod': 'efeitoConfig', 'dano': '"*1.15"'}]})
    
    if variacao == 0:
        niveis.append({'marco': 10, 'mods': [{'mod': 'efeitoConfig', 'dano': '"*1.15"'}]})
        niveis.append({'marco': 15, 'mods': [{'mod': 'efeitoConfig', 'critChance': 0.1}]})
    elif variacao == 1:
        niveis.append({'marco': 10, 'mods': [{'mod': 'efeitoConfig', 'alcance': 1}]})
        niveis.append({'marco': 15, 'mods': [{'mod': 'efeitoConfig', 'dano': '"*1.2"'}]})
    elif variacao == 2:
        niveis.append({'marco': 10, 'mods': [{'mod': 'efeitoConfig', 'dano': '"*1.15"'}]})
        niveis.append({'marco': 15, 'mods': [{'mod': 'efeitoConfig', 'dano': '"*1.15"'}]})
    else:
        niveis.append({'marco': 10, 'mods': [{'mod': 'efeitoConfig', 'stunChance': 0.1}]})
        niveis.append({'marco': 15, 'mods': [{'mod': 'efeitoConfig', 'knockback': 1}]})
    
    return niveis

def gerar_slots_criativos(hab_id, idx, total, cfg):
    """Gera os SLOTS que a IA local vai preencher."""
    dano_base, percentual, cd = gerar_escalonamento(idx, total)
    categoria, tipo = escolher_categoria(idx, total)
    postura = gerar_postura(dano_base, idx)
    niveis = gerar_niveis(idx)
    
    slot = {
        'hab_id': hab_id,
        'idx': idx,
        'dano_base': dano_base,
        'percentual': percentual,
        'cd': cd,
        'categoria': categoria,
        'tipo': tipo,
        'postura': postura,
        'niveis': niveis,
        # Slots criativos (preenchidos pela IA local)
        'nome': '{{NOME}}',
        'descricao': '{{DESCRICAO}}',
        # Slots opcionais
        'tem_sinergia': random.random() < 0.6,  # 60% chance
        'tem_estado': random.random() < 0.3,    # 30% chance
        'tem_condicao': random.random() < 0.25,  # 25% chance
        'sinergia_texto': '{{SINERGIA}}',
        'sinergia_dom_extra': None,
        'condicao_tipo': random.choice(['cercado', 'vidaBaixa', 'fullHp', 'singleTarget']),
        'mecanica_extra': random.choice(MECANICAS),
    }
    
    if slot['tem_sinergia']:
        # Escolhe um dominio de sinergia
        sin_idx = random.randrange(len(cfg['sinergia_doms']))
        slot['sinergia_dom'] = cfg['sinergia_doms'][sin_idx]
        slot['sinergia_nome'] = cfg['sinergia_nomes'][sin_idx]
    
    if slot['tem_estado']:
        slot['dano_vinculo'] = round(dano_base * 1.5, 1)
        slot['dano_lampejo'] = round(dano_base * 2.0, 1)
    
    return slot


# ============================================================
# GERACAO DO PROMPT PARA IA LOCAL
# ============================================================

def gerar_exemplos_alta_qualidade():
    """Busca exemplos reais de dominios de alta qualidade para few-shot."""
    exemplos_path = r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades\fogo.lua'
    if not os.path.exists(exemplos_path):
        return None
    
    with open(exemplos_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extrai as primeiras 3 habilidades completas
    habilidades = []
    matches = list(re.finditer(r'HABILIDADES\[\d+\]\s*=\s*\{', content))
    for m in matches[:3]:
        start = m.start()
        # Encontra o fechamento da chave
        brace_count = 1
        pos = m.end()
        while pos < len(content) and brace_count > 0:
            if content[pos] == '{': brace_count += 1
            elif content[pos] == '}': brace_count -= 1
            pos += 1
        habilidades.append(content[start:pos])
    
    return '\n\n'.join(habilidades) if habilidades else None

def gerar_prompt_para_ia_local(slots, cfg, exemplos):
    """Gera o prompt que sera enviado para a IA local preencher os slots."""
    
    # Tabela de slots para preencher
    tabela_slots = []
    for s in slots:
        linha = f"  ID {s['hab_id']}: categorÃ­a={s['categoria']}, tipo={s['tipo']}, dano_base={s['dano_base']}, cd={s['cd']}s"
        if s.get('sinergia_dom'):
            linha += f", sinergia_com_dominio_{s['sinergia_dom']}"
        if s.get('tem_estado'):
            linha += ", TEM_ESTADOS"
        if s.get('tem_condicao'):
            linha += f", condicao_tipo={s['condicao_tipo']}"
        tabela_slots.append(linha)
    
    prompt = f"""VOCE E UM DESIGNER DE HABILIDADES PARA O JOGO TIBIA (MCR SERVER).
Sua funcao e PREENCHER campos criativos em habilidades SHC.

CONTEXTO DO DOMINIO:
  Nome: {cfg['nome']} (ID: {cfg['id']})
  Identidade: {cfg['identidade']}
  Traco: {cfg['traco']}
  Estilo: {cfg['estilo']}
  Elemento: {cfg['elemento']}

EXEMPLOS DE HABILIDADES DE ALTA QUALIDADE (use como referencia de estilo):
```lua
{exemplos}
```

TABELA DE SLOTS PARA PREENCHER ({len(slots)} habilidades):
Voce DEVE preencher APENAS os campos marcados como "{{CAMPO}}".
Responda EXCLUSIVAMENTE no formato JSON abaixo, sem explicacoes.

FORMATO DE RESPOSTA (JSON puro, sem marcacao):
{{
  "habilidades": [
    {{
      "hab_id": {slots[0]['hab_id']},
      "nome": "nome criativo em portugues",
      "descricao": "descricao curta do efeito",
      "sinergia_texto": "DominioX: descricao da sinergia"  // null se sem sinergia
    }}
    // ... para cada habilidade
  ]
}}

REGRAS CRIATIVAS:
- Nomes DEVEM ser variados e interessantes (NAO repita palavras)
- Cada nome deve refletir a mecanica da habilidade
- Descricoes sao curtas (max 80 chars), em portugues
- Sinergias descrevem como outro dominio potencializa a habilidade
- Para IDs {cfg['ids'][0]}-{cfg['ids'][1]}: gere para TODOS da tabela
- Seja CRIATIVO e EVITE repeticoes

TABELA COMPLETA:
{chr(10).join(tabela_slots)}
"""
    return prompt

# ============================================================
# CHAMADA A IA LOCAL
# ============================================================

def chamar_ollama(prompt, model='qwen2.5-coder:7b', temperature=0.8):
    """Chama a API da Ollama."""
    import urllib.request
    payload = {
        'model': model,
        'prompt': prompt,
        'stream': False,
        'options': {
            'temperature': temperature,
            'num_ctx': 8192,
            'top_p': 0.9,
        }
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request('http://localhost:11434/api/generate', 
                                      data=data, 
                                      headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read())
            return result.get('response', '')
    except Exception as e:
        return f"ERRO: {e}"

# ============================================================
# MONTAGEM DO ARQUIVO FINAL
# ============================================================

def montar_habilidade(slot, creative):
    """Monta o codigo Lua de uma habilidade combinando estrutura + criativo."""
    
    partes = []
    partes.append(f'HABILIDADES[{slot["hab_id"]}] = {{')
    partes.append(f'    nome = "{creative.get("nome", "Habilidade")}",')
    partes.append(f'    tipo = "gatilho",')
    partes.append(f'    dominio = {{{slot["hab_id"] // 100}}},')
    partes.append(f'    cooldown = {slot["cd"]},')
    partes.append(f'    categoria = "{slot["categoria"]}",')
    partes.append(f'    descricao = "{creative.get("descricao", "Descricao.")}",')
    
    # Efeito config
    dano = slot['dano_base']
    percentual = slot['percentual']
    elem = 'COMBAT_PHYSICALDAMAGE'
    
    # Se buff/debuff/heal, muda estrutura
    if slot['tipo'] in ('buff', 'debuff', 'heal', 'trap', 'field_aura'):
        partes.append(f'    efeitoConfig = {{')
        partes.append(f'        tipo = "{slot["tipo"]}",')
        partes.append(f'        dano = {dano},')
        partes.append(f'        percentual = {percentual},')
        partes.append(f'        elemento = {elem},')
        if slot.get('mecanica_extra') in ('stun', 'knockback', 'lifesteal', 'bleed'):
            partes.append(f'        {slot["mecanica_extra"]} = 0.3,')
        partes.append(f'    }},')
    else:
        partes.append(f'    efeitoConfig = {{')
        partes.append(f'        tipo = "{slot["tipo"]}",')
        partes.append(f'        dano = {dano},')
        partes.append(f'        percentual = {percentual},')
        partes.append(f'        elemento = {elem},')
        if slot.get('mecanica_extra') == 'knockback':
            partes.append(f'        knockback = 1,')
        elif slot.get('mecanica_extra') == 'lifesteal':
            partes.append(f'        lifesteal = 0.2,')
        elif slot.get('mecanica_extra') == 'stun':
            partes.append(f'        stunChance = 0.3, stunDuration = 1000,')
        elif slot.get('mecanica_extra') == 'bleed':
            partes.append(f'        bleedChance = 0.3, bleedDamage = 0.1,')
        elif slot.get('mecanica_extra') == 'crit_chance':
            partes.append(f'        critChance = 0.15,')
        elif slot.get('mecanica_extra') == 'armor_break':
            partes.append(f'        armorPenetration = 0.3,')
        elif slot.get('mecanica_extra') == 'progressive_damage':
            partes.append(f'        progressiveDano = 0.05, maxProgressive = 0.5,')
        elif slot.get('mecanica_extra') == 'execute':
            partes.append(f'        executeTreshold = 0.2, executeMult = 2.0,')
        partes.append(f'    }},')
    
    # Postura
    postura = slot['postura']
    partes.append(f'    postura = {{')
    partes.append(f'        [1] = {{ efeitoConfig = {{ dano = {postura[1]} }} }},')
    partes.append(f'        [3] = {{ efeitoConfig = {{ dano = {postura[3]} }} }},')
    partes.append(f'    }},')
    
    # Niveis
    niveis = slot['niveis']
    partes.append(f'    niveis = {{')
    for n in niveis:
        mods_str = ', '.join(f'{k} = {v}' for mod in n['mods'] for k, v in mod.items() if k != 'mod')
        partes.append(f'        [{n["marco"]}] = {{ {{ mod = "efeitoConfig", {mods_str} }} }},')
    partes.append(f'    }},')
    
    # Sinergia (se tiver)
    if slot.get('tem_sinergia') and slot.get('sinergia_dom'):
        sin_texto = creative.get('sinergia_texto', 'Sinergia.')
        partes.append(f'    sinergias = {{')
        partes.append(f'        [{slot["sinergia_dom"]}] = {{')
        partes.append(f'            descricao = "{sin_texto}",')
        partes.append(f'            nivelMin = {random.choice([1, 3, 5])},')
        # Gera efeitoConfig da sinergia
        sin_elem = random.choice(['COMBAT_FIREDAMAGE', 'COMBAT_ICEDAMAGE', 'COMBAT_EARTHDAMAGE', 'COMBAT_ENERGYDAMAGE'])
        if random.random() < 0.5:
            partes.append(f'            efeitoConfig = {{ danoAdicional = {round(dano * 0.3, 1)} }},')
        else:
            partes.append(f'            efeitoConfig = {{ elemento = {sin_elem}, danoAdicional = {round(dano * 0.3, 1)} }},')
        partes.append(f'        }},')
        partes.append(f'    }},')
    
    # Estados (se tiver)
    if slot.get('tem_estado'):
        d_v = slot.get('dano_vinculo', round(dano * 1.5, 1))
        d_l = slot.get('dano_lampejo', round(dano * 2.0, 1))
        partes.append(f'    estados = {{')
        partes.append(f'        vinculo = {{ efeitoConfig = {{ dano = {d_v}, damageType = "absolute" }} }},')
        partes.append(f'        lampejo = {{ efeitoConfig = {{ dano = {d_l}, custoMana = 0 }} }},')
        partes.append(f'    }},')
    
    # Condicoes (se tiver)
    if slot.get('tem_condicao'):
        cond_tipo = slot['condicao_tipo']
        d_cond = round(dano * 1.35, 1)
        partes.append(f'    condicoes = {{')
        if cond_tipo == 'cercado':
            partes.append(f'        cercado = {{ efeitoConfig = {{ tipo = "explosion_ring", raio = 5, dano = {d_cond} }} }},')
        elif cond_tipo == 'vidaBaixa':
            partes.append(f'        vidaBaixa = {{ efeitoConfig = {{ lifesteal = 0.3, dano = {d_cond} }} }},')
        elif cond_tipo == 'fullHp':
            partes.append(f'        fullHp = {{ efeitoConfig = {{ critChance = 0.25, dano = {d_cond} }} }},')
        elif cond_tipo == 'singleTarget':
            partes.append(f'        singleTarget = {{ efeitoConfig = {{ dano = {round(dano * 1.6, 1)} }} }},')
        partes.append(f'    }},')
    
    partes.append('}')
    return '\n'.join(partes)

def validar_conteudo(conteudo):
    """Valida o Lua gerado."""
    issues = []
    
    opens = conteudo.count('{')
    closes = conteudo.count('}')
    if opens != closes:
        issues.append(f"Chaves desbalanceadas: {opens} abertas, {closes} fechadas")
    
    # Cada habilidade deve comeÃ§ar com HABILIDADES[ e terminar com }
    habilidades = re.findall(r'HABILIDADES\[\d+\]', conteudo)
    if not habilidades:
        issues.append("Nenhuma habilidade encontrada")
    
    # Verifica tipos SHC
    tipos_validos = {'projectile','melee','multi_hit','cone','explosion_ring',
                     'area_target','storm','buff','debuff','heal','trap',
                     'field_aura','orbit','pulse','rain','toggle'}
    
    return issues, len(habilidades)

# ============================================================
# FUNCAO PRINCIPAL
# ============================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Gerador SHC v2')
    parser.add_argument('dominio', help='Nome do dominio')
    parser.add_argument('num', type=int, default=15, nargs='?')
    parser.add_argument('--model', default='qwen2.5-coder:7b')
    parser.add_argument('--dry-run', action='store_true')
    
    args = parser.parse_args()
    
    if args.dominio not in DOMINIOS:
        print(f"Dominio nao encontrado. Disponiveis: {list(DOMINIOS.keys())}")
        return 1
    
    cfg = DOMINIOS[args.dominio]
    base_dir = r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades'
    filepath = os.path.join(base_dir, args.dominio + '.lua')
    
    # 1. GERAR SLOTS ESTRUTURAIS (Python)
    print(f"[1/5] Gerando {args.num} templates estruturais...")
    slots = []
    for i in range(args.num):
        hab_id = cfg['ids'][0] + i
        slot = gerar_slots_criativos(hab_id, i, args.num, cfg)
        slots.append(slot)
    print(f"       {len(slots)} slots criados")
    
    # 2. COLETAR EXEMPLOS (few-shot)
    print("[2/5] Coletando exemplos de alta qualidade...")
    exemplos = gerar_exemplos_alta_qualidade()
    if exemplos:
        print(f"       Exemplo carregado ({len(exemplos)} chars)")
    else:
        print("       AVISO: sem exemplos, usando instrucoes genericas")
    
    # 3. GERAR PROMPT E CHAMAR IA LOCAL
    print(f"[3/5] Chamando IA local ({args.model}) para preencher criativos...")
    prompt = gerar_prompt_para_ia_local(slots, cfg, exemplos or "N/A")
    
    if args.dry_run:
        print("\n=== PROMPT (dry-run) ===")
        # print(prompt[:2000])
        print("...")
        return 0
    
    resposta = chamar_ollama(prompt, args.model)
    if resposta.startswith("ERRO:"):
        print(f"       ERRO: {resposta}")
        return 1
    print(f"       Resposta recebida ({len(resposta)} chars)")
    
    # 4. MONTAR ARQUIVO (Python)
    print("[4/5] Montando arquivo final...")
    
    # Parse da resposta JSON
    criativos = {}
    try:
        # Extrai JSON da resposta
        json_match = re.search(r'\{.*"habilidades".*\}', resposta, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            for h in data.get('habilidades', []):
                criativos[h['hab_id']] = h
        else:
            # Tenta parse direto
            data = json.loads(resposta)
            for h in data.get('habilidades', []):
                criativos[h['hab_id']] = h
    except json.JSONDecodeError as e:
        print(f"       AVISO: resposta nao e JSON valido: {e}")
        print(f"       Usando valores genericos para nomes")
    
    # Monta header
    linhas = []
    linhas.append('--[[')
    linhas.append(f'    Projeto MCR â€” SPA â€” {cfg["nome"]} ({cfg["id"]})')
    linhas.append(f'    Gerado pelo SHC Generator v2 com IA local')
    linhas.append(f'    Perfil: {cfg["parent"]}')
    linhas.append('--]]')
    linhas.append(f'-- Tracjo: "{cfg["traco"]}"')
    linhas.append('')
    
    # Monta cada habilidade
    for slot in slots:
        creative = criativos.get(slot['hab_id'], {})
        codigo = montar_habilidade(slot, creative)
        linhas.append(codigo)
        linhas.append('')
    
    linhas.append(f'print(">> SPA: habilidades/{args.dominio}.lua carregado")')
    linhas.append('')
    
    conteudo = '\n'.join(linhas)
    
    # 5. VALIDAR
    print("[5/5] Validando...")
    issues, hab_count = validar_conteudo(conteudo)
    
    if issues:
        for issue in issues:
            print(f"       AVISO: {issue}")
    
    if hab_count == 0:
        print("       ERRO: Nenhuma habilidade valida!")
        return 1
    
    # Backup se existir
    if os.path.exists(filepath):
        bak = filepath + '.bak_v2'
        shutil.copy2(filepath, bak)
        print(f"       Backup: {bak}")
    
    # Salva
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print(f"       Salvo: {filepath}")
    print(f"       Total: {hab_count} habilidades, {len(linhas)} linhas")
    
    if not issues:
        print("\nâœ… GERACAO CONCLUIDA COM SUCESSO!")
    else:
        print(f"\nâš ï¸  GERADO COM {len(issues)} AVISOS")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
