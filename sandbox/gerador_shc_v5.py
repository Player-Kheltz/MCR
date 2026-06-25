#!/usr/bin/env python3
"""GERADOR SHC V5 — 5 Estagios Fragmentados com Contexto Progressivo"""
import sys, os, json, re, random, shutil, urllib.request

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades'

DOMINIOS = {
    'clavas_leves': {
        'id': 112, 'nome': 'CLAVAS LEVES', 'parent': 'Clavas 12 - Combate 1',
        'elemento': 'COMBAT_PHYSICALDAMAGE', 'ids': (11201, 11220),
        'sinergia_doms': {113: 'Clavas Pesadas', 130: 'Lutador', 25: 'Terra'},
        'descricao': 'Clavas leves sao armas ageis de uma mao. Golpes rapidos, precisos.',
    },
}

def ollama(prompt, model='qwen2.5-coder:7b', temp=0.9):
    try:
        data = json.dumps({'model':model,'prompt':prompt,'stream':False,
            'options':{'temperature':temp,'num_ctx':8192,'top_p':0.9}}).encode()
        req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read()).get('response','')
    except Exception as e:
        return None

def parse_json(txt):
    for p in [r'\[.*?\]', r'\{.*?\}']:
        m = re.search(p, txt, re.DOTALL)
        if m:
            try: return json.loads(m.group())
            except: pass
    return None

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('dominio', default='clavas_leves', nargs='?')
    ap.add_argument('num', type=int, default=10, nargs='?')
    ap.add_argument('--model', default='qwen2.5-coder:7b')
    args = ap.parse_args()
    
    cfg = DOMINIOS[args.dominio]
    filepath = os.path.join(BASE, args.dominio + '.lua')
    
    print("\n=== V5 - 5 ESTAGIOS FRAGMENTADOS ===")
    print(f"Dominio: {cfg['nome']} | {args.num} habilidades\n")
    
    # Slots estruturais
    slots = []
    for i in range(args.num):
        hid = cfg['ids'][0] + i
        p = i / args.num
        dano = round(0.4 + p*1.8, 1)
        perc = round(0.15 + p*0.45, 2)
        cd = max(1, 12 - int(p*10))
        
        if p < 0.10: ct, tp = 'single', 'melee'
        elif p < 0.20: ct, tp = 'single', 'projectile' if i%2==0 else 'melee'
        elif p < 0.35: ct, tp = 'single', 'multi_hit'
        elif p < 0.50: ct, tp = 'aoe', random.choice(['explosion_ring','cone','area_target'])
        elif p < 0.60: ct, tp = 'debuff', 'debuff'
        elif p < 0.70: ct, tp = 'buff', 'buff'
        elif p < 0.80: ct, tp = 'aoe', random.choice(['explosion_ring','storm'])
        elif p < 0.87: ct, tp = 'defense', 'buff'
        elif p < 0.95: ct, tp = 'finisher', random.choice(['storm','multi_hit'])
        else: ct, tp = 'finisher', 'storm'
        
        vr = i%4
        if vr==0: pos = {1:round(dano*1.35,1),3:round(dano*0.65,1)}
        elif vr==1: pos = {1:round(dano*1.2,1),3:round(dano*0.8,1)}
        elif vr==2: pos = {1:round(dano*0.85,1),3:round(dano*1.15,1)}
        else: pos = {1:round(dano*1.5,1),3:round(dano*0.5,1)}
        
        slots.append({
            'hab_id':hid,'dano_base':dano,'percentual':perc,'cd':cd,
            'categoria':ct,'tipo':tp,'postura':pos,
            'tem_sinergia':random.random()<0.6,'tem_estado':random.random()<0.3,
            'tem_condicao':random.random()<0.3,
            'condicao_tipo':random.choice(['cercado','vidaBaixa','fullHp','singleTarget']),
        })
        if slots[-1]['tem_sinergia']:
            slots[-1]['sinergia_dom'] = random.choice(list(cfg['sinergia_doms'].keys()))
    
    print(f"  [0] {len(slots)} slots estruturais criados")
    
    # ESTAGIO 1: Identidade
    print("  [1/5] IA definindo identidade...")
    p1 = (f"Crie uma identidade UNICA para o dominio de habilidades {cfg['nome']} (ID {cfg['id']})."
          f"\nContexto: {cfg['descricao']}"
          f"\nResponda JSON com: personalidade, fantasy, mecanicas_chave (array), tom_emocional, cores_visuais."
          f"\nSeja criativo e especifico. Esta identidade guiara todas as habilidades.")
    
    r1 = ollama(p1, args.model)
    identidade = parse_json(r1) if r1 else None
    if isinstance(identidade, list) and identidade:
        identidade = identidade[0]
    if isinstance(identidade, dict):
        print(f"    Personalidade: {str(identidade.get('personalidade','?'))[:60]}")
    else:
        identidade = {'personalidade': cfg['descricao'], 'fantasy': 'um combatente agil'}
        print(f"    (usando padrao)")
    
    # ESTAGIO 2: Brainstorm nomes
    print("  [2/5] IA fazendo brainstorm de nomes...")
    id_str = json.dumps(identidade, ensure_ascii=False)
    p2 = (f"Baseado na identidade do dominio {cfg['nome']}:\n{id_str}\n\n"
          f"Crie {args.num*2} ideias de nomes de habilidades. Para cada: nome (pt-br), justificativa, mecanica_sugerida."
          f"\nEx: [{{\"nome\":\"Golpe Agil\",\"justificativa\":\"Golpe rapido que inicia combos\",\"mecanica_sugerida\":\"multi-hit\"}}]"
          f"\nResponda APENAS JSON array.")
    
    r2 = ollama(p2, args.model)
    brainstorm = parse_json(r2) if r2 else []
    if isinstance(brainstorm, dict):
        for v in brainstorm.values():
            if isinstance(v, list): brainstorm = v; break
    print(f"    Ideias: {len(brainstorm)}")
    
    if not brainstorm:
        brainstorm = [{'nome':f'Habilidade {i+1}','justificativa':'','mecanica_sugerida':''} for i in range(args.num)]
    
    # ESTAGIO 3: Refinar
    print("  [3/5] IA refinando nomes...")
    lista_b = '\n'.join(f"- {b.get('nome','?')}: {b.get('justificativa','')}" for b in brainstorm[:15])
    p3 = (f"Selecione os {args.num} MELHORES nomes para {cfg['nome']}. Elimine nomes ruins ou fora do tema."
          f"\nIdeias:\n{lista_b}"
          f"\nResponda JSON array com exatamente {args.num} itens: [{{\"nome\":\"...\",\"explicacao\":\"...\"}}]")
    
    r3 = ollama(p3, args.model, 0.7)
    refinados = parse_json(r3) if r3 else []
    if isinstance(refinados, dict):
        for v in refinados.values():
            if isinstance(v, list): refinados = v; break
    print(f"    Refinados: {len(refinados)}")
    
    nomes = []
    for i in range(args.num):
        if i < len(refinados) and isinstance(refinados[i], dict):
            nomes.append(refinados[i].get('nome', f'Hab {i+1}'))
        elif i < len(brainstorm):
            nomes.append(brainstorm[i].get('nome', f'Hab {i+1}') if isinstance(brainstorm[i], dict) else str(brainstorm[i]))
        else:
            nomes.append(f'Habilidade {i+1}')
    
    # ESTAGIO 4: Descricoes
    print("  [4/5] IA escrevendo descricoes...")
    nomes_str = '\n'.join(f'- {n}' for n in nomes)
    p4 = (f"Escreva descricoes CURTAS (max 80 chars) para cada habilidade de {cfg['nome']}."
          f"\nIdentidade: {id_str}"
          f"\nHabilidades:\n{nomes_str}"
          f"\nRegras: estilo 'Acao que efeito.' Nao use ':'. Nao repita estruturas."
          f"\nEx: 'Golpe rapido que prepara o combo.'"
          f"\nResponda JSON array: [{{\"nome\":\"...\",\"descricao\":\"...\"}}]")
    
    r4 = ollama(p4, args.model, 0.7)
    descs = parse_json(r4) if r4 else []
    if isinstance(descs, dict) and 'habilidades' in descs:
        descs = descs['habilidades']
    if isinstance(descs, dict):
        descs = list(descs.values())
    print(f"    Descricoes: {len(descs)}")
    
    desc_dict = {}
    for d in descs:
        if isinstance(d, dict):
            dn = d.get('nome','')
            for n in nomes:
                if dn.lower() == n.lower():
                    desc_dict[n] = d.get('descricao','Ataca o alvo.')
    
    # ESTAGIO 5: Sinergias
    print("  [5/5] IA escrevendo sinergias...")
    dom_str = '; '.join(f'ID {k} = {v}' for k,v in cfg['sinergia_doms'].items())
    p5 = (f"Atribua sinergias para algumas habilidades de {cfg['nome']}."
          f"\nDominios parceiros: {dom_str}"
          f"\nHabilidades:\n{nomes_str}"
          f"\nRegras: texto comeca com nome do dominio parceiro + ':'. "
          f"\nEx: 'Clavas Pesadas: impacto brutal apos combo.'"
          f"\nResponda JSON: [{{\"nome\":\"...\",\"sinergia_dom\":ID,\"sinergia_texto\":\"...\"}}]"
          f"\nSe sem sinergia, sinergia_texto: null.")
    
    r5 = ollama(p5, args.model, 0.7)
    sins = parse_json(r5) if r5 else []
    if isinstance(sins, dict):
        sins = list(sins.values())
    print(f"    Sinergias: {len(sins)}")
    
    sin_dict = {}
    for s in sins:
        if isinstance(s, dict):
            sn = s.get('nome','')
            for i, n in enumerate(nomes):
                if sn.lower() == n.lower():
                    sin_dict[i] = s
                    break
    
    # MONTAGEM
    print("\n  Montando arquivo final...")
    linhas = [
        f'--[[',
        f'    Projeto MCR - SPA - {cfg["nome"]} ({cfg["id"]})',
        f'    Gerado pelo SHC Generator V5 (5 estagios fragmentados)',
        f'    Perfil: {cfg["parent"]}',
        f'--]]',
        '',
    ]
    
    for i, s in enumerate(slots):
        nome = nomes[i] if i < len(nomes) else f'Hab {s["hab_id"]}'
        desc = desc_dict.get(nome, 'Ataca o alvo.')
        sin_info = sin_dict.get(i, {}) if isinstance(sin_dict.get(i), dict) else {}
        st = sin_info.get('sinergia_texto') if isinstance(sin_info, dict) else None
        sd = sin_info.get('sinergia_dom') if isinstance(sin_info, dict) else s.get('sinergia_dom')
        if st in ('None','',None): st = None
        
        d = s['dano_base']
        linhas.append(f'HABILIDADES[{s["hab_id"]}] = {{')
        linhas.append(f'    nome = "{nome}",')
        linhas.append(f'    tipo = "gatilho",')
        linhas.append(f'    dominio = {{{cfg["id"]}}},')
        linhas.append(f'    cooldown = {s["cd"]},')
        linhas.append(f'    categoria = "{s["categoria"]}",')
        linhas.append(f'    descricao = "{desc}",')
        linhas.append(f'    efeitoConfig = {{')
        linhas.append(f'        tipo = "{s["tipo"]}",')
        linhas.append(f'        dano = {d},')
        linhas.append(f'        percentual = {s["percentual"]},')
        linhas.append(f'        elemento = {cfg["elemento"]},')
        linhas.append(f'    }},')
        pos = s['postura']
        linhas.append(f'    postura = {{')
        linhas.append(f'        [1] = {{ efeitoConfig = {{ dano = {pos[1]} }} }},')
        linhas.append(f'        [3] = {{ efeitoConfig = {{ dano = {pos[3]} }} }},')
        linhas.append(f'    }},')
        linhas.append(f'    niveis = {{')
        linhas.append(f'        [5] = {{ {{ mod = "efeitoConfig", dano = "*1.15" }} }},')
        vn = i % 4
        if vn in (0,2):
            linhas.append(f'        [10] = {{ {{ mod = "efeitoConfig", dano = "*1.15" }} }},')
        if vn == 0:
            linhas.append(f'        [15] = {{ {{ mod = "efeitoConfig", critChance = 0.1 }} }},')
        elif vn == 2:
            linhas.append(f'        [15] = {{ {{ mod = "efeitoConfig", knockback = 1 }} }},')
        elif vn == 1:
            linhas.append(f'        [10] = {{ {{ mod = "efeitoConfig", alcance = 1 }} }},')
        else:
            pass
        linhas.append(f'    }},')
        
        if st and sd:
            linhas.append(f'    sinergias = {{')
            linhas.append(f'        [{sd}] = {{')
            linhas.append(f'            descricao = "{st}",')
            linhas.append(f'            nivelMin = {random.choice([1,3,5])},')
            linhas.append(f'            efeitoConfig = {{ danoAdicional = {round(d*0.3,1)} }},')
            linhas.append(f'        }},')
            linhas.append(f'    }},')
        
        if s.get('tem_estado'):
            dv, dl = round(d*1.5,1), round(d*2.0,1)
            linhas.append(f'    estados = {{')
            linhas.append(f'        vinculo = {{ efeitoConfig = {{ dano = {dv}, damageType = "absolute" }} }},')
            linhas.append(f'        lampejo = {{ efeitoConfig = {{ dano = {dl}, custoMana = 0 }} }},')
            linhas.append(f'    }},')
        
        if s.get('tem_condicao'):
            dc = round(d*1.35,1)
            cmap = {'cercado':f'cercado = {{ efeitoConfig = {{ tipo = "explosion_ring", raio = 5, dano = {dc} }} }}',
                    'vidaBaixa':f'vidaBaixa = {{ efeitoConfig = {{ lifesteal = 0.3, dano = {dc} }} }}',
                    'fullHp':f'fullHp = {{ efeitoConfig = {{ critChance = 0.25, dano = {dc} }} }}',
                    'singleTarget':f'singleTarget = {{ efeitoConfig = {{ dano = {round(d*1.6,1)} }} }}'}
            linhas.append(f'    condicoes = {{')
            linhas.append(f'        {cmap.get(s["condicao_tipo"],"")},')
            linhas.append(f'    }},')
        
        linhas.append('}')
        linhas.append('')
    
    linhas.append(f'print(">> SPA: habilidades/{args.dominio}.lua carregado")')
    linhas.append('')
    conteudo = '\n'.join(linhas)
    
    # Validacao
    o, c = conteudo.count('{'), conteudo.count('}')
    habs = len(re.findall(r'HABILIDADES\[\d+\]', conteudo))
    sins_c = conteudo.count('sinergias')
    est_c = conteudo.count('estados')
    cond_c = conteudo.count('condicoes')
    
    print(f"\n  VALIDACAO: {habs} habilidades, {o}/{c} chaves")
    print(f"  Sinergias: {sins_c}, Estados: {est_c}, Condicoes: {cond_c}")
    print(f"  Chaves: {'OK' if o==c else 'ERRO'}")
    
    if o != c:
        print("  ERRO CRITICO: chaves desbalanceadas!")
        return 1
    
    # Salvar
    if os.path.exists(filepath):
        shutil.copy2(filepath, filepath + '.bak_v5')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print(f"  Salvo: {filepath}\n")
    
    print("  NOMES GERADOS:")
    for i, n in enumerate(nomes):
        s = slots[i]
        print(f"  [{s['hab_id']}] {n} (CD:{s['cd']} {s['categoria']})")

if __name__ == '__main__':
    main()
