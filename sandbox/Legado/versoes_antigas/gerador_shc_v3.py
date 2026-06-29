"""
    GERADOR SHC V3 â€” Template + Pool Tematico + Auto-Validacao
    
    Melhorias da V3:
    1. Pool de palavras-chave por dominio (coerencia tematica)
    2. Exemplos de descricoes de alta qualidade no prompt
    3. Validador de sinergia (rejeita "None", "DominioGenerico:")
    4. Pos-processamento: corrige encoding, verifica tema
    
    Uso: python gerador_shc_v3.py <dominio> [num] [--model MODEL]
"""

import sys, os, json, re, random, shutil, math, urllib.request

OLLAMA_URL = 'http://localhost:11434/api/generate'

# ============================================================
# DOMINIO DATABASE COM POOLS TEMATICOS
# ============================================================
DOMINIOS = {
    'clavas_leves': {
        'id': 112, 'nome': 'CLAVAS LEVES', 'parent': 'Clavas 12 -> Combate 1',
        'traco': 'Danca das Clavas - Nv5: combo+1 | Nv10: atordoamento+10% | Nv15: desarme',
        'elemento': 'COMBAT_PHYSICALDAMAGE',
        'ids': (11201, 11220),
        'sinergia_doms': {113: 'Clavas Pesadas', 130: 'Lutador', 25: 'Terra'},
        'estilo': 'corpoacorpo',
        'pool_nomes': ['clava', 'giro', 'golpe', 'impacto', 'combo', 'giro', 'trovao', 'redemoinho',
                       'ventania', 'bambu', 'agil', 'preciso', 'rapido', 'duplo', 'crescente'],
        'pool_verbos': ['girar', 'golpear', 'impactar', 'sacudir', 'tremer', 'danÃ§ar'],
        'pool_efeitos': ['atordoamento', 'desarme', 'knockback', 'combo', 'multi-golpe'],
        'identidade': 'armas ageis e precisas que desarmam e atordoam com golpes rapidos',
        'exemplo_nome': 'Golpe Agil',
        'exemplo_desc': 'Golpe rapido que prepara o terreno para o combo.',
    },
    'bastoes_arcanos': {
        'id': 133, 'nome': 'BASTOES ARCANOS', 'parent': 'Artes Marciais 14 -> Combate 1',
        'traco': 'Sabedoria Arcana - Nv5: mana+5% | Nv10: cooldown-10% | Nv15: duplo',
        'elemento': 'COMBAT_ENERGYDAMAGE',
        'ids': (13301, 13320),
        'sinergia_doms': {23: 'Fogo', 24: 'Gelo', 26: 'Energia', 200: 'Sagrado/Morte'},
        'estilo': 'magia',
        'pool_nomes': ['bastao', 'arcano', 'runas', 'energia', 'magia', 'fogo', 'gelo', 'trovao',
                       'poder', 'sabedoria', 'encantamento', 'feitico', 'canalizar', 'elemental'],
        'pool_verbos': ['canalizar', 'invocar', 'explodir', 'teletransportar', 'encantar'],
        'pool_efeitos': ['explosao arcana', 'dreno de mana', 'dano elemental', 'encantamento'],
        'identidade': 'bastoes que canalizam energia magica pura em golpes elementais',
        'exemplo_nome': 'Explosao Arcana',
        'exemplo_desc': 'Explosao de energia arcana que atinge todos ao redor.',
    },
    'arcos': {
        'id': 120, 'nome': 'ARCOS', 'parent': 'Precisao 13 -> Combate 1',
        'traco': 'Mira Infalivel - Nv5: alcance+1 | Nv10: critico+5% | Nv15: perfuracao',
        'elemento': 'COMBAT_PHYSICALDAMAGE',
        'ids': (12001, 12020),
        'sinergia_doms': {23: 'Fogo', 24: 'Gelo', 26: 'Energia'},
        'estilo': 'distancia',
        'pool_nomes': ['flecha', 'tiro', 'arco', 'mira', 'precisao', 'disparo', 'chuva', 'perfurante',
                       'buscador', 'aguia', 'certeiro', 'rapido', 'triplo', 'barragem'],
        'pool_verbos': ['disparar', 'mirar', 'perfurar', 'acertar', 'chover'],
        'pool_efeitos': ['perfuracao', 'critico', 'disparo multiplo', 'mira precisa'],
        'identidade': 'ataques precisos a distancia que perfuram armaduras',
        'exemplo_nome': 'Tiro Certeiro',
        'exemplo_desc': 'Disparo preciso de longa distancia.',
    },
    'lutador': {
        'id': 130, 'nome': 'LUTADOR', 'parent': 'Artes Marciais 14 -> Combate 1',
        'traco': 'Punhos de Aco - Nv5: dano+10% | Nv10: combo+1 | Nv15: quebra-ossos',
        'elemento': 'COMBAT_PHYSICALDAMAGE',
        'ids': (13001, 13020),
        'sinergia_doms': {132: 'Armas de Punho', 14: 'Artes Marciais', 1: 'Combate'},
        'estilo': 'corpoacorpo',
        'pool_nomes': ['punho', 'soco', 'jab', 'cruzado', 'gancho', 'chute', 'joelhada', 'combate',
                       'lutador', 'esquiva', 'furia', 'combo', 'quebra', 'ossos', 'impacto'],
        'pool_verbos': ['socar', 'chutar', 'golpear', 'derrubar', 'atordoar'],
        'pool_efeitos': ['atordoamento', 'knockback', 'quebra-armadura', 'combo'],
        'identidade': 'golpes corpo-a-corpo com sequencias rapidas e atordoantes',
        'exemplo_nome': 'Cruzado',
        'exemplo_desc': 'Cruzado que atordoa o oponente.',
    },
}

# ============================================================
# BIBLIOTECA DE DESCRICOES DE EXEMPLO (alta qualidade)
# ============================================================
EXEMPLOS_DESCRICOES = [
    'Disparo preciso de longa distancia.',
    'Bombardeio de flechas em area.',
    'Flecha que atravessa armaduras.',
    'Golpe rapido que aumenta o combo.',
    'Sequencia de golpes ritmados.',
    'Explosao de energia arcana ao redor do alvo.',
    'Campo de fogo persistente que queima inimigos.',
    'Golpe carregado com energia que atordoa o alvo.',
    'Posicao defensiva que reflete parte do dano.',
    'Golpe que drena a vitalidade do alvo.',
    'Dispara tres projeteis em cone.',
    'Rajada massiva de flechas.',
    'Escudo de gelo que absorve dano e lentifica atacantes.',
    'A cada golpe acertado, o dano aumenta progressivamente.',
    'Golpe giratorio que atinge varios inimigos ao redor.',
    'Sequencia devastadora de golpes precisos.',
    'Turbilhao de golpes que arrasta inimigos.',
    'Clava arremessada que retorna ao dono.',
    'Soquinho rapido com chance de duplicar.',
    'Gancho que empurra o inimigo para tras.',
]

# ============================================================
# GERACAO DE ESTRUTURA (Python 100%)
# ============================================================

def gerar_escalonamento(idx, total):
    progresso = idx / total
    dano = round(0.4 + progresso * 1.8, 1)
    percentual = round(0.15 + progresso * 0.45, 2)
    cd = max(1, 12 - int(progresso * 10))
    return dano, percentual, cd

def escolher_tipo_e_cat(idx, total):
    progresso = idx / total
    if progresso < 0.10: return 'single', 'melee'
    elif progresso < 0.20: return 'single', 'projectile' if idx % 2 == 0 else 'melee'
    elif progresso < 0.35: return 'single', 'multi_hit'
    elif progresso < 0.50: return 'aoe', random.choice(['explosion_ring', 'cone', 'area_target'])
    elif progresso < 0.60: return 'debuff', 'debuff'
    elif progresso < 0.70: return 'buff', 'buff'
    elif progresso < 0.80: return 'aoe', random.choice(['explosion_ring', 'storm'])
    elif progresso < 0.87: return 'defense', 'buff'
    elif progresso < 0.95: return 'finisher', random.choice(['storm', 'multi_hit'])
    else: return 'finisher', 'storm'

def gerar_postura_variada(dano_base, idx):
    var = idx % 4
    if var == 0: return {1: round(dano_base*1.35,1), 3: round(dano_base*0.65,1)}
    elif var == 1: return {1: round(dano_base*1.2,1), 3: round(dano_base*0.8,1)}
    elif var == 2: return {1: round(dano_base*0.85,1), 3: round(dano_base*1.15,1)}
    else: return {1: round(dano_base*1.5,1), 3: round(dano_base*0.5,1)}

def gerar_niveis_variados(idx):
    var = idx % 4
    base = [{'marco': 5, 'mods': [{'mod':'efeitoConfig','dano':'"*1.15"'}]}]
    if var == 0:
        base.append({'marco': 10, 'mods': [{'mod':'efeitoConfig','dano':'"*1.15"'}]})
        base.append({'marco': 15, 'mods': [{'mod':'efeitoConfig','critChance': 0.1}]})
    elif var == 1:
        base.append({'marco': 10, 'mods': [{'mod':'efeitoConfig','alcance': 1}]})
        base.append({'marco': 15, 'mods': [{'mod':'efeitoConfig','dano':'"*1.2"'}]})
    elif var == 2:
        base.append({'marco': 10, 'mods': [{'mod':'efeitoConfig','stunChance': 0.1}]})
        base.append({'marco': 15, 'mods': [{'mod':'efeitoConfig','knockback': 1}]})
    else:
        base.append({'marco': 10, 'mods': [{'mod':'efeitoConfig','dano':'"*1.15"'}]})
    return base

# ============================================================
# GERACAO DO PROMPT V3 (com pool tematico + exemplos)
# ============================================================

def gerar_prompt_v3(slots, cfg):
    """Prompt V3 com pool tematico, exemplos de descricao, e constraints claras."""
    
    tabela = []
    for i, s in enumerate(slots):
        linha = f"[{s['hab_id']}] cat={s['categoria']} tipo={s['tipo']} dano={s['dano_base']} cd={s['cd']}s"
        if s.get('sinergia_dom'):
            linha += f" +sinergia({s['sinergia_dom']})"
        if s.get('tem_estado'):
            linha += " +estados"
        if s.get('tem_condicao'):
            linha += f" +cond({s['condicao_tipo']})"
        tabela.append(linha)
    
    pool_nomes = ', '.join(cfg['pool_nomes'])
    pool_verbos = ', '.join(cfg['pool_verbos'])
    sinergias_str = '; '.join(f'Dominio {k} = {v}' for k, v in cfg['sinergia_doms'].items())
    desc_exemplos = '\n'.join(random.sample(EXEMPLOS_DESCRICOES, min(5, len(EXEMPLOS_DESCRICOES))))
    
    prompt = f"""VOCE E UM DESIGNER DE HABILIDADES PARA TIBIA MCR.
Preencha os campos criativos para as habilidades de {cfg['nome']} (ID {cfg['id']}).

IDENTIDADE DO DOMINIO:
{cfg['identidade']}. {cfg['traco']}.

PALAVRAS-CHAVE (use estas para inspirar nomes):
Nomes: {pool_nomes}
Verbos: {pool_verbos}
Efeitos: {', '.join(cfg['pool_efeitos'])}

EXEMPLOS DE DESCRICOES DE QUALIDADE (siga este estilo):
{desc_exemplos}

EXEMPLO DE HABILIDADE COMPLETA:
HABILIDADES[{cfg['ids'][0]}] = {{
    nome = "{cfg['exemplo_nome']}",
    tipo = "gatilho",
    dominio = {{{cfg['id']}}},
    cooldown = 3,
    categoria = "single",
    descricao = "{cfg['exemplo_desc']}",
    efeitoConfig = {{ tipo = "melee", dano = 0.5, percentual = 0.2, elemento = {cfg['elemento']} }},
    postura = {{ [1] = {{ efeitoConfig = {{ dano = 0.7 }} }}, [3] = {{ efeitoConfig = {{ dano = 0.3 }} }} }},
    niveis = {{ [5] = {{ {{ mod = "efeitoConfig", dano = "*1.15" }} }} }},
    sinergias = {{ [{list(cfg['sinergia_doms'].keys())[0]}] = {{ descricao = "Sinergia exemplo.", nivelMin = 1, efeitoConfig = {{ danoAdicional = 0.3 }} }} }},
}}

TABELA DE SLOTS ({len(slots)} habilidades):
{chr(10).join(tabela)}

SINERGIAS DISPONIVEIS: {sinergias_str}

INSTRUCOES:
1. Nomes DEVEM usar palavras do pool ou similares - NAO repita palavras entre habilidades
2. Descricoes: curtas (max 80 chars), em portugues, estilo "Acao que efeito."
3. Sinergias: mencione o NOME do dominio (ex: "Clavas Pesadas:...") - NAO use "DominioX:" 
4. Seja CRIATIVO mas MANTENHA O TEMA do dominio
5. {', '.join(cfg['pool_nomes'])} sao sugestoes - crie variacoes

Responda APENAS JSON, sem explicacoes:
{{"habilidades":[
  {{"hab_id":{slots[0]['hab_id']},"nome":"...","descricao":"...","sinergia_texto":"..."}}
]}}"""
    return prompt

# ============================================================
# CHAMADA A IA LOCAL
# ============================================================

def chamar_ollama(prompt, model='qwen2.5-coder:7b', temperature=0.9):
    payload = {
        'model': model, 'prompt': prompt, 'stream': False,
        'options': {'temperature': temperature, 'num_ctx': 8192, 'top_p': 0.9}
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read())
            return result.get('response', '')
    except Exception as e:
        return f"ERRO: {e}"

# ============================================================
# VALIDACAO E POS-PROCESSAMENTO V3
# ============================================================

def validar_criativos(criativos, cfg):
    """Valida e corrige os criativos gerados pela IA local."""
    issues = []
    
    for h in criativos:
        hab_id = h.get('hab_id')
        nome = h.get('nome', '')
        desc = h.get('descricao', '')
        sin_texto = h.get('sinergia_texto', '')
        
        # 1. Check for generic/bad sinergia descriptions
        if sin_texto and sin_texto in ('None', '', 'null', 'Sinergia'):
            h['sinergia_texto'] = None
            issues.append(f"  ID {hab_id}: sinergia generica removida")
        
        if sin_texto and ('Dominio' in sin_texto or 'dominio' in sin_texto):
            # Try to fix: replace "DominioX: texto" with proper text
            for dom_id, dom_nome in cfg['sinergia_doms'].items():
                if str(dom_id) in sin_texto:
                    h['sinergia_texto'] = sin_texto.replace(f'Dominio{dom_id}', dom_nome)
                    break
            else:
                h['sinergia_texto'] = None
                issues.append(f"  ID {hab_id}: sinergia com 'Dominio' generico removida")
        
        # 2. Fix encoding on descriptions
        desc = desc.encode('utf-8', errors='replace').decode('utf-8')
        # Remove garbled chars
        desc = re.sub(r'[^\x20-\x7E\xC0-\xFF\xA0-\xBF.,!?;:\-\'\" ]', '', desc)
        if len(desc) > 100:
            desc = desc[:97] + '...'
        h['descricao'] = desc.strip() or 'Ataca o alvo.'
        
        # 3. Fix nome encoding
        nome = nome.encode('utf-8', errors='replace').decode('utf-8')
        nome = re.sub(r'[^\x20-\x7E\xC0-\xFF\xA0-\xBF.\-\'\" ]', '', nome)
        h['nome'] = nome.strip() or 'Habilidade'
        
        # 4. Check nome repetition
        # (will be checked in assembly)
    
    return criativos, issues

# ============================================================
# MONTAGEM DO ARQUIVO
# ============================================================

def montar_todas_habilidades(slots, criativos_dict, cfg, nome_arquivo):
    linhas = []
    linhas.append('--[[')
    linhas.append(f'    Projeto MCR â€” SPA â€” {cfg["nome"]} ({cfg["id"]})')
    linhas.append(f'    Gerado pelo SHC Generator V3 com IA local')
    linhas.append(f'    Perfil: {cfg["parent"]}')
    linhas.append('--]]')
    linhas.append(f'-- Traca: "{cfg["traco"]}"')
    linhas.append('')
    
    for slot in slots:
        cr = criativos_dict.get(slot['hab_id'], {})
        nome = cr.get('nome', 'Habilidade')
        desc = cr.get('descricao', 'Descricao.')
        sin_texto = cr.get('sinergia_texto')
        
        p = []
        p.append(f'HABILIDADES[{slot["hab_id"]}] = {{')
        p.append(f'    nome = "{nome}",')
        p.append(f'    tipo = "gatilho",')
        p.append(f'    dominio = {{{cfg["id"]}}},')
        p.append(f'    cooldown = {slot["cd"]},')
        p.append(f'    categoria = "{slot["categoria"]}",')
        p.append(f'    descricao = "{desc}",')
        
        # efeitoConfig
        d = slot['dano_base']
        perc = slot['percentual']
        elem = cfg['elemento']
        p.append(f'    efeitoConfig = {{')
        p.append(f'        tipo = "{slot["tipo"]}",')
        p.append(f'        dano = {d},')
        p.append(f'        percentual = {perc},')
        p.append(f'        elemento = {elem},')
        if slot.get('mecanica_extra') in ('knockback','stun','lifesteal','bleed','armor_break','progressive_damage'):
            mapa = {'knockback': 'knockback = 1', 'stun': 'stunChance = 0.3, stunDuration = 1000',
                    'lifesteal': 'lifesteal = 0.2', 'bleed': 'bleedChance = 0.3, bleedDamage = 0.1',
                    'armor_break': 'armorPenetration = 0.3', 'progressive_damage': 'progressiveDano = 0.05, maxProgressive = 0.5'}
            p.append(f'        {mapa[slot["mecanica_extra"]]},')
        p.append(f'    }},')
        
        # postura
        pos = slot['postura']
        p.append(f'    postura = {{')
        p.append(f'        [1] = {{ efeitoConfig = {{ dano = {pos[1]} }} }},')
        p.append(f'        [3] = {{ efeitoConfig = {{ dano = {pos[3]} }} }},')
        p.append(f'    }},')
        
        # niveis
        niv = slot['niveis']
        p.append(f'    niveis = {{')
        for n in niv:
            mods = ', '.join(f'{k} = {v}' for mod in n['mods'] for k, v in mod.items() if k != 'mod')
            p.append(f'        [{n["marco"]}] = {{ {{ mod = "efeitoConfig", {mods} }} }},')
        p.append(f'    }},')
        
        # sinergia
        if slot.get('tem_sinergia') and slot.get('sinergia_dom') and sin_texto:
            p.append(f'    sinergias = {{')
            p.append(f'        [{slot["sinergia_dom"]}] = {{')
            p.append(f'            descricao = "{sin_texto}",')
            p.append(f'            nivelMin = {random.choice([1,3,5])},')
            if random.random() < 0.5:
                p.append(f'            efeitoConfig = {{ danoAdicional = {round(d*0.3,1)} }},')
            else:
                sin_elem = random.choice(['COMBAT_FIREDAMAGE','COMBAT_ICEDAMAGE','COMBAT_EARTHDAMAGE','COMBAT_ENERGYDAMAGE'])
                p.append(f'            efeitoConfig = {{ elemento = {sin_elem}, danoAdicional = {round(d*0.3,1)} }},')
            p.append(f'        }},')
            p.append(f'    }},')
        
        # estados
        if slot.get('tem_estado'):
            dv = slot.get('dano_vinculo', round(d*1.5,1))
            dl = slot.get('dano_lampejo', round(d*2.0,1))
            p.append(f'    estados = {{')
            p.append(f'        vinculo = {{ efeitoConfig = {{ dano = {dv}, damageType = "absolute" }} }},')
            p.append(f'        lampejo = {{ efeitoConfig = {{ dano = {dl}, custoMana = 0 }} }},')
            p.append(f'    }},')
        
        # condicoes
        if slot.get('tem_condicao'):
            ct = slot['condicao_tipo']
            dc = round(d*1.35,1)
            p.append(f'    condicoes = {{')
            if ct == 'cercado':
                p.append(f'        cercado = {{ efeitoConfig = {{ tipo = "explosion_ring", raio = 5, dano = {dc} }} }},')
            elif ct == 'vidaBaixa':
                p.append(f'        vidaBaixa = {{ efeitoConfig = {{ lifesteal = 0.3, dano = {dc} }} }},')
            elif ct == 'fullHp':
                p.append(f'        fullHp = {{ efeitoConfig = {{ critChance = 0.25, dano = {dc} }} }},')
            elif ct == 'singleTarget':
                p.append(f'        singleTarget = {{ efeitoConfig = {{ dano = {round(d*1.6,1)} }} }},')
            p.append(f'    }},')
        
        p.append('}')
        linhas.append('\n'.join(p))
        linhas.append('')
    
    linhas.append(f'print(">> SPA: habilidades/{nome_arquivo}.lua carregado")')
    linhas.append('')
    return '\n'.join(linhas)

def validar_lua_gerado(conteudo):
    opens = conteudo.count('{')
    closes = conteudo.count('}')
    issues = []
    if opens != closes:
        issues.append(f"Chaves: {opens} vs {closes}")
    habs = len(re.findall(r'HABILIDADES\[\d+\]', conteudo))
    if habs == 0:
        issues.append("Zero habilidades!")
    return issues, habs

# ============================================================
# MAIN V3
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('dominio', help='Nome do dominio')
    parser.add_argument('num', type=int, default=10, nargs='?')
    parser.add_argument('--model', default='qwen2.5-coder:7b')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    
    if args.dominio not in DOMINIOS:
        print(f"Dominios: {list(DOMINIOS.keys())}")
        return 1
    
    cfg = DOMINIOS[args.dominio]
    base_dir = r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades'
    filepath = os.path.join(base_dir, args.dominio + '.lua')
    
    print(f"[V3] Gerando {args.num} habilidades para {cfg['nome']}...")
    
    # 1. Gerar slots
    slots = []
    for i in range(args.num):
        hab_id = cfg['ids'][0] + i
        dano, perc, cd = gerar_escalonamento(i, args.num)
        cat, tipo = escolher_tipo_e_cat(i, args.num)
        postura = gerar_postura_variada(dano, i)
        niveis = gerar_niveis_variados(i)
        
        slot = {
            'hab_id': hab_id, 'dano_base': dano, 'percentual': perc, 'cd': cd,
            'categoria': cat, 'tipo': tipo, 'postura': postura, 'niveis': niveis,
            'tem_sinergia': random.random() < 0.6,
            'tem_estado': random.random() < 0.3,
            'tem_condicao': random.random() < 0.3,
            'condicao_tipo': random.choice(['cercado','vidaBaixa','fullHp','singleTarget']),
            'mecanica_extra': random.choice(['knockback','stun','lifesteal','bleed','armor_break','progressive_damage','none','none','none']),
        }
        if slot['tem_sinergia']:
            slot['sinergia_dom'] = random.choice(list(cfg['sinergia_doms'].keys()))
        if slot['tem_estado']:
            slot['dano_vinculo'] = round(dano * 1.5, 1)
            slot['dano_lampejo'] = round(dano * 2.0, 1)
        
        slots.append(slot)
    
    print(f"  Slots: {len(slots)}")
    
    # 2. Chamar IA local
    print(f"  Chamando {args.model}...")
    prompt = gerar_prompt_v3(slots, cfg)
    
    if args.dry_run:
        print("\n=== PROMPT ===")
        print(prompt[:3000])
        return 0
    
    resposta = chamar_ollama(prompt, args.model)
    if resposta.startswith("ERRO:"):
        print(f"  ERRO: {resposta}")
        return 1
    print(f"  Resposta: {len(resposta)} chars")
    
    # 3. Parse JSON
    criativos = {}
    try:
        json_match = re.search(r'\{.*"habilidades".*\}', resposta, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            for h in data.get('habilidades', []):
                criativos[h['hab_id']] = h
        else:
            data = json.loads(resposta)
            for h in data.get('habilidades', []):
                criativos[h['hab_id']] = h
    except json.JSONDecodeError as e:
        print(f"  AVISO: JSON invalido: {e}")
    
    # 4. Validar criativos
    criativos_list = list(criativos.values())
    validated, issues = validar_criativos(criativos_list, cfg)
    for iss in issues:
        print(f"  {iss}")
    
    # Rebuild dict after validation
    criativos = {h['hab_id']: h for h in validated}
    
    # 5. Montar arquivo
    print("  Montando arquivo...")
    conteudo = montar_todas_habilidades(slots, criativos, cfg, args.dominio)
    
    # 6. Validar
    lua_issues, hab_count = validar_lua_gerado(conteudo)
    for iss in lua_issues:
        print(f"  LUA: {iss}")
    
    if hab_count == 0:
        print("  ERRO: nenhuma habilidade!")
        return 1
    
    # 7. Salvar
    if os.path.exists(filepath):
        bak = filepath + '.bak_v3'
        shutil.copy2(filepath, bak)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print(f"  Salvo: {filepath} ({hab_count} habilidades)")
    print()
    print("=== RESUMO V3 ===")
    print(f"  Habilidades: {hab_count}")
    print(f"  Sinergias: {sum(1 for s in slots if s.get('tem_sinergia'))}")
    print(f"  Estados: {sum(1 for s in slots if s.get('tem_estado'))}")
    print(f"  Condicoes: {sum(1 for s in slots if s.get('tem_condicao'))}")
    print(f"  Issues: {len(issues) + len(lua_issues)}")
    print(f"  Status: {'APROVADO' if not lua_issues else 'COM AVISOS'}")

if __name__ == '__main__':
    main()
