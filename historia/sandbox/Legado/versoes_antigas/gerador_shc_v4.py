"""
    GERADOR SHC V4 — 2 Estagios + Validacao Cruzada
    
    Melhorias:
    1. Estagio 1: IA gera APENAS nomes (mais foco)
    2. Estagio 2: IA gera descricoes + sinergias com base nos nomes
    3. Validacao cruzada: descricao nao pode conter ":",
       sinergia_texto deve conter ":"
    4. Fallback: se IA nao seguir formato, usa valores gerados por templates
"""

import sys, os, json, re, random, shutil, math, urllib.request

OLLAMA_URL = 'http://localhost:11434/api/generate'

DOMINIOS = {
    'clavas_leves': {
        'id': 112, 'nome': 'CLAVAS LEVES', 'parent': 'Clavas 12 -> Combate 1',
        'traco': 'Danca das Clavas',
        'elemento': 'COMBAT_PHYSICALDAMAGE', 'ids': (11201, 11220),
        'sinergia_doms': {113: 'Clavas Pesadas', 130: 'Lutador', 25: 'Terra'},
        'pool_nomes': ['giro','golpe','impacto','combo','trovao','redemoinho','ventania','bambu','agil','preciso','rapido','duplo','crescente','clava'],
        'identidade': 'armas ageis e precisas que desarmam e atordoam',
    },
}

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
        return None

def parse_json_from_response(resposta):
    """Extrai JSON valido de qualquer resposta."""
    # Tenta encontrar bloco JSON
    m = re.search(r'\[.*\]', resposta, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except:
            pass
    m = re.search(r'\{.*\}', resposta, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except:
            pass
    return None

def gerar_nomes(slots, cfg, model):
    """Estagio 1: IA local gera apenas nomes criativos."""
    prompt = f"""Gere nomes criativos em portugues para habilidades de {cfg['nome']} (ID {cfg['id']}).
Contexto: {cfg['identidade']}. {cfg['traco']}.

Regras:
- Use palavras como: {', '.join(cfg['pool_nomes'])}
- Cada nome DEVE ser UNICO e refletir a mecanica
- NAO repita palavras entre nomes
- Exemplo: "Golpe Agil", "Clava Trovejante", "Danca das Clavas"

IDs para nomear:
{chr(10).join(f'  {s["hab_id"]}: cat={s["categoria"]} tipo={s["tipo"]} cd={s["cd"]}s' for s in slots)}

Responda APENAS JSON no formato:
[{{"hab_id":{slots[0]["hab_id"]},"nome":"..."}},...]
"""
    resp = chamar_ollama(prompt, model)
    if not resp: return {}
    
    data = parse_json_from_response(resp)
    if not data: return {}
    
    # Normaliza: se veio dict com chave "habilidades", extrai
    if isinstance(data, dict) and 'habilidades' in data:
        data = data['habilidades']
    
    # Se veio dict com keys numericas
    if isinstance(data, dict):
        data = list(data.values())
    
    result = {}
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and 'hab_id' in item:
                result[item['hab_id']] = item.get('nome', 'Habilidade')
    return result

def gerar_descricoes(slots_com_nomes, cfg, model):
    """Estagio 2: IA local gera descricoes e sinergias com base nos nomes."""
    linhas = []
    for s in slots_com_nomes:
        nome = s['nome']
        linha = f"[{s['hab_id']}] {nome} | cat={s['categoria']} tipo={s['tipo']}"
        if s.get('sinergia_dom'):
            dom_nome = cfg['sinergia_doms'].get(s['sinergia_dom'], f'Dominio {s["sinergia_dom"]}')
            linha += f" +sinergia com {dom_nome}"
        linhas.append(linha)
    
    prompt = f"""Complete as habilidades de {cfg['nome']} com descricoes e textos de sinergia.

Para cada habilidade, forneca:
1. DESCRICAO: frase curta (max 80 chars) explicando o efeito. Ex: "Golpe rapido que aumenta o combo."
2. SINERGIA (se houver): texto explicando como outro dominio potencializa. Ex: "Clavas Pesadas: impacto brutal apos combo."

REGRAS:
- Descricao NAO pode ter ":"
- Sinergia DEVE comecar com o nome do dominio seguido de ":"
- Descricao termina com ponto final
- Seja variado e criativo

Habilidades:
{chr(10).join(linhas)}

Responda APENAS JSON:
[{{"hab_id":{slots_com_nomes[0]['hab_id']},"descricao":"...","sinergia_texto":"..."}},...]
"""
    resp = chamar_ollama(prompt, model)
    if not resp: return []
    
    data = parse_json_from_response(resp)
    if not data: return []
    
    if isinstance(data, dict) and 'habilidades' in data:
        data = data['habilidades']
    if isinstance(data, dict):
        data = list(data.values())
    
    if isinstance(data, list):
        # Validacao cruzada
        for item in data:
            desc = item.get('descricao', '')
            sin = item.get('sinergia_texto', '') or ''
            
            # Se descricao tem ":", provavelmente eh sinergia erroneamente colocada
            if ':' in desc:
                # Troca: sinergia vira descricao generica
                item['sinergia_texto'] = desc  # Era descricao, mas tem formato de sinergia
                item['descricao'] = 'Ataca o alvo.'
            
            # Se sinergia nao tem ":", provavelmente eh descricao erroneamente colocada
            if sin and ':' not in sin:
                item['descricao'] = sin
                item['sinergia_texto'] = None
            
            # Se descricao vazia, poe padrao
            if not item.get('descricao'):
                item['descricao'] = 'Ataca o alvo.'
            
            # Normaliza sinergia_texto
            if item.get('sinergia_texto') in ('None', '', 'null', None):
                item['sinergia_texto'] = None
        
        return data
    return []

def montar_habilidade(slot, nome, descricao, sinergia_texto, cfg):
    p = []
    p.append(f'HABILIDADES[{slot["hab_id"]}] = {{')
    p.append(f'    nome = "{nome}",')
    p.append(f'    tipo = "gatilho",')
    p.append(f'    dominio = {{{cfg["id"]}}},')
    p.append(f'    cooldown = {slot["cd"]},')
    p.append(f'    categoria = "{slot["categoria"]}",')
    p.append(f'    descricao = "{descricao}",')
    
    d, perc = slot['dano_base'], slot['percentual']
    p.append(f'    efeitoConfig = {{')
    p.append(f'        tipo = "{slot["tipo"]}",')
    p.append(f'        dano = {d},')
    p.append(f'        percentual = {perc},')
    p.append(f'        elemento = {cfg["elemento"]},')
    if slot.get('mecanica_extra') in ('knockback','stun','lifesteal','armor_break'):
        mapa = {'knockback': 'knockback = 1', 'stun': 'stunChance = 0.3, stunDuration = 1000',
                'lifesteal': 'lifesteal = 0.2', 'armor_break': 'armorPenetration = 0.3'}
        p.append(f'        {mapa[slot["mecanica_extra"]]},')
    p.append(f'    }},')
    
    pos = slot['postura']
    p.append(f'    postura = {{')
    p.append(f'        [1] = {{ efeitoConfig = {{ dano = {pos[1]} }} }},')
    p.append(f'        [3] = {{ efeitoConfig = {{ dano = {pos[3]} }} }},')
    p.append(f'    }},')
    
    niv = slot['niveis']
    p.append(f'    niveis = {{')
    for n in niv:
        mods = ', '.join(f'{k} = {v}' for mod in n['mods'] for k, v in mod.items() if k != 'mod')
        p.append(f'        [{n["marco"]}] = {{ {{ mod = "efeitoConfig", {mods} }} }},')
    p.append(f'    }},')
    
    if sinergia_texto and slot.get('sinergia_dom'):
        p.append(f'    sinergias = {{')
        p.append(f'        [{slot["sinergia_dom"]}] = {{')
        p.append(f'            descricao = "{sinergia_texto}",')
        p.append(f'            nivelMin = {random.choice([1,3,5])},')
        if random.random() < 0.5:
            p.append(f'            efeitoConfig = {{ danoAdicional = {round(d*0.3,1)} }},')
        else:
            sin_elem = random.choice(['COMBAT_FIREDAMAGE','COMBAT_ICEDAMAGE','COMBAT_EARTHDAMAGE','COMBAT_ENERGYDAMAGE'])
            p.append(f'            efeitoConfig = {{ elemento = {sin_elem}, danoAdicional = {round(d*0.3,1)} }},')
        p.append(f'        }},')
        p.append(f'    }},')
    
    if slot.get('tem_estado'):
        dv = slot.get('dano_vinculo', round(d*1.5,1))
        dl = slot.get('dano_lampejo', round(d*2.0,1))
        p.append(f'    estados = {{')
        p.append(f'        vinculo = {{ efeitoConfig = {{ dano = {dv}, damageType = "absolute" }} }},')
        p.append(f'        lampejo = {{ efeitoConfig = {{ dano = {dl}, custoMana = 0 }} }},')
        p.append(f'    }},')
    
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
    return '\n'.join(p)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('dominio', default='clavas_leves', nargs='?')
    parser.add_argument('num', type=int, default=10, nargs='?')
    parser.add_argument('--model', default='qwen2.5-coder:7b')
    args = parser.parse_args()
    
    cfg = DOMINIOS.get(args.dominio)
    if not cfg:
        print(f"Dominio invalido. Disponiveis: {list(DOMINIOS.keys())}")
        return 1
    
    base_dir = r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades'
    filepath = os.path.join(base_dir, args.dominio + '.lua')
    
    print(f"[V4] Gerando {args.num} habilidades para {cfg['nome']}...")
    
    # 1. Slots estruturais
    slots = []
    for i in range(args.num):
        hab_id = cfg['ids'][0] + i
        progresso = i / args.num
        dano = round(0.4 + progresso * 1.8, 1)
        perc = round(0.15 + progresso * 0.45, 2)
        cd = max(1, 12 - int(progresso * 10))
        
        if progresso < 0.10: cat, tipo = 'single', 'melee'
        elif progresso < 0.20: cat, tipo = 'single', 'projectile' if i%2==0 else 'melee'
        elif progresso < 0.35: cat, tipo = 'single', 'multi_hit'
        elif progresso < 0.50: cat, tipo = 'aoe', random.choice(['explosion_ring','cone','area_target'])
        elif progresso < 0.60: cat, tipo = 'debuff', 'debuff'
        elif progresso < 0.70: cat, tipo = 'buff', 'buff'
        elif progresso < 0.80: cat, tipo = 'aoe', random.choice(['explosion_ring','storm'])
        elif progresso < 0.87: cat, tipo = 'defense', 'buff'
        elif progresso < 0.95: cat, tipo = 'finisher', random.choice(['storm','multi_hit'])
        else: cat, tipo = 'finisher', 'storm'
        
        var = i % 4
        if var == 0: postura = {1: round(dano*1.35,1), 3: round(dano*0.65,1)}
        elif var == 1: postura = {1: round(dano*1.2,1), 3: round(dano*0.8,1)}
        elif var == 2: postura = {1: round(dano*0.85,1), 3: round(dano*1.15,1)}
        else: postura = {1: round(dano*1.5,1), 3: round(dano*0.5,1)}
        
        base_niv = [{'marco':5,'mods':[{'mod':'efeitoConfig','dano':'"*1.15"'}]}]
        if var == 0:
            base_niv += [{'marco':10,'mods':[{'mod':'efeitoConfig','dano':'"*1.15"'}]},
                         {'marco':15,'mods':[{'mod':'efeitoConfig','critChance':0.1}]}]
        elif var == 1:
            base_niv += [{'marco':10,'mods':[{'mod':'efeitoConfig','alcance':1}]}]
        elif var == 2:
            base_niv += [{'marco':10,'mods':[{'mod':'efeitoConfig','stunChance':0.1}]},
                         {'marco':15,'mods':[{'mod':'efeitoConfig','knockback':1}]}]
        else:
            base_niv += [{'marco':10,'mods':[{'mod':'efeitoConfig','dano':'"*1.15"'}]}]
        
        slot = {
            'hab_id': hab_id, 'dano_base': dano, 'percentual': perc, 'cd': cd,
            'categoria': cat, 'tipo': tipo, 'postura': postura, 'niveis': base_niv,
            'tem_sinergia': random.random() < 0.6,
            'tem_estado': random.random() < 0.3,
            'tem_condicao': random.random() < 0.3,
            'condicao_tipo': random.choice(['cercado','vidaBaixa','fullHp','singleTarget']),
            'mecanica_extra': random.choice(['knockback','stun','lifesteal','armor_break','none','none','none']),
        }
        if slot['tem_sinergia']:
            slot['sinergia_dom'] = random.choice(list(cfg['sinergia_doms'].keys()))
        if slot['tem_estado']:
            slot['dano_vinculo'] = round(dano * 1.5, 1)
            slot['dano_lampejo'] = round(dano * 2.0, 1)
        
        slots.append(slot)
    
    print(f"  Slots: {len(slots)}")
    
    # 2. ESTAGIO 1: Nomes
    print(f"  Estagio 1: gerando nomes com {args.model}...")
    mapa_nomes = gerar_nomes(slots, cfg, args.model)
    nomes_usados = len(mapa_nomes)
    print(f"  Nomes recebidos: {nomes_usados}/{args.num}")
    
    # Fallback para slots sem nome
    fallback_nomes = ['Golpe Agil','Golpe Preciso','Clava Trovejante','Ventania de Golpes',
                      'Redemoinho','Impacto Rapido','Giro Duplo','Combo Crescente','Bambu de Aco','Danca Final']
    for i, s in enumerate(slots):
        if s['hab_id'] not in mapa_nomes:
            mapa_nomes[s['hab_id']] = fallback_nomes[i] if i < len(fallback_nomes) else f'Habilidade {i+1}'
    
    # 3. ESTAGIO 2: Descricoes e sinergias
    print(f"  Estagio 2: gerando descricoes...")
    slots_com_nomes = [{**s, 'nome': mapa_nomes.get(s['hab_id'], f'Hab {s["hab_id"]}')} for s in slots]
    desc_data = gerar_descricoes(slots_com_nomes, cfg, args.model)
    print(f"  Descricoes recebidas: {len(desc_data)}")
    
    # Mapa descricoes
    mapa_desc = {d['hab_id']: d for d in desc_data}
    
    # 4. Montagem
    print("  Montando arquivo final...")
    linhas = []
    linhas.append('--[[')
    linhas.append(f'    Projeto MCR — SPA — {cfg["nome"]} ({cfg["id"]})')
    linhas.append(f'    Gerado pelo SHC Generator V4 com IA local')
    linhas.append(f'    Perfil: {cfg["parent"]}')
    linhas.append('--]]')
    linhas.append(f'-- Traca: "{cfg["traco"]}"')
    linhas.append('')
    
    for s in slots:
        nome = mapa_nomes.get(s['hab_id'], 'Habilidade')
        dc = mapa_desc.get(s['hab_id'], {})
        desc = dc.get('descricao', 'Ataca o alvo.')
        sin_texto = dc.get('sinergia_texto') if dc.get('sinergia_texto') not in ('None','',None) else None
        
        codigo = montar_habilidade(s, nome, desc, sin_texto, cfg)
        linhas.append(codigo)
        linhas.append('')
    
    linhas.append(f'print(">> SPA: habilidades/{args.dominio}.lua carregado")')
    linhas.append('')
    conteudo = '\n'.join(linhas)
    
    # 5. Validacao
    opens = conteudo.count('{')
    closes = conteudo.count('}')
    habs = len(re.findall(r'HABILIDADES\[\d+\]', conteudo))
    
    print(f"  Validacao: {habs} habilidades, {opens}/{closes} chaves")
    
    if opens != closes:
        print("  ERRO: chaves desbalanceadas!")
        return 1
    
    # Salva
    if os.path.exists(filepath):
        bak = filepath + '.bak_v4'
        shutil.copy2(filepath, bak)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    sin_count = conteudo.count('sinergias')
    est_count = conteudo.count('estados')
    cond_count = conteudo.count('condicoes')
    
    print(f"  Salvo: {filepath}")
    print()
    print("=== RESUMO V4 ===")
    print(f"  Habilidades: {habs}")
    print(f"  Sinergias: {sin_count}")
    print(f"  Estados: {est_count}")
    print(f"  Condicoes: {cond_count}")
    print("  STATUS: APROVADO")
    print()
    print("Nomes:")
    for s in slots:
        nome = mapa_nomes.get(s['hab_id'], '?')
        print(f"  [{s['hab_id']}] {nome} (CD:{s['cd']} {s['categoria']})")

if __name__ == '__main__':
    main()
