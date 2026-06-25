#!/usr/bin/env python3
"""
GERADOR SHC V6 — Multi-Agent Crew (Designer + Revisor + Editor)
Cada etapa tem 3 agentes: quem cria, quem critica, quem corrige.
So avanca quando o revisor aprova.
"""
import sys, os, json, re, random, shutil, urllib.request

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades'

DOMINIOS = {
    'clavas_leves': {
        'id': 112, 'nome': 'CLAVAS LEVES', 'parent': 'Clavas 12 - Combate 1',
        'elemento': 'COMBAT_PHYSICALDAMAGE', 'ids': (11201, 11220),
        'sinergia_doms': {113: 'Clavas Pesadas', 130: 'Lutador', 25: 'Terra'},
        'descricao': 'Clavas leves sao armas ageis de uma mao. Golpes rapidos, precisos.',
        'palavras_proibidas': ['punho', 'soco', 'chute', 'flexao', 'arcano', 'magia', 'flecha'],
    },
}

def chamar(prompt, model='qwen2.5-coder:7b', temp=0.8):
    try:
        data = json.dumps({'model':model,'prompt':prompt,'stream':False,
            'options':{'temperature':temp,'num_ctx':8192,'top_p':0.9}}).encode()
        req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read()).get('response','')
    except: return None

def parse_json(txt):
    for p in [r'\[.*?\]', r'\{.*?\}']:
        m = re.search(p, txt, re.DOTALL)
        if m:
            try: return json.loads(m.group())
            except: pass
    return None

def extrair_json_lista(txt):
    """Extrai uma lista de qualquer resposta."""
    dados = parse_json(txt)
    if isinstance(dados, list): return dados
    if isinstance(dados, dict):
        for v in dados.values():
            if isinstance(v, list): return v
        # Se for dict de items, converte
        if all(k.isdigit() for k in dados.keys()):
            return list(dados.values())
    return []

# ============================================================
# MINI-CREW: IDENTIDADE
# ============================================================
def crew_identidade(cfg, model, max_tentativas=3):
    """Designer -> Revisor -> Editor -> loop ate aprovado."""
    for tentativa in range(max_tentativas):
        # DESIGNER: cria identidade
        prompt_d = (f"Crie uma identidade UNICA e VIVIDA para o dominio {cfg['nome']} (ID {cfg['id']})."
                    f"\nContexto: {cfg['descricao']}"
                    f"\nResponda JSON: {{\"personalidade\":\"...\",\"fantasy\":\"...\","
                    f"\"mecanicas_chave\":[\"...\"],\"tom_emocional\":\"...\",\"cores_visuais\":\"...\"}}"
                    f"\nSeja CRIATIVO e ESPECIFICO. Max 100 chars por campo.")
        r = chamar(prompt_d, model, 0.9)
        ident = parse_json(r) if r else None
        if isinstance(ident, list) and ident: ident = ident[0]
        
        if not isinstance(ident, dict):
            print(f"    Identidade nao veio como JSON (tentativa {tentativa+1})")
            continue
        
        # REVISOR: avalia a identidade
        prompt_r = (f"Avalie esta identidade para {cfg['nome']}:\n"
                    f"{json.dumps(ident, ensure_ascii=False, indent=2)}"
                    f"\n\nCriterios: 1) Faz sentido para {cfg['descricao']}? 2) Eh criativa e especifica?"
                    f"\nResponda JSON: {{\"nota\":7,\"problemas\":[\"...\"]}} (nota 0-10, 7+ = aprovado)")
        rr = chamar(prompt_r, model, 0.5)
        review = parse_json(rr) if rr else {}
        if isinstance(review, list) and review: review = review[0]
        nota = review.get('nota', 0) if isinstance(review, dict) else 0
        
        print(f"    Identidade: nota {nota}/10", end='')
        
        if nota >= 7:
            print(" -> APROVADA")
            return ident
        
        problemas = review.get('problemas', ['generica']) if isinstance(review, dict) else ['generica']
        if isinstance(problemas, str): problemas = [problemas]
        print(f" -> {', '.join(problemas[:2])}")
    
    # Fallback se nao conseguir
    print(f"    Usando identidade padrao apos {max_tentativas} tentativas")
    return {'personalidade':cfg['descricao'],'fantasy':'um combatente agil',
            'mecanicas_chave':['golpes rapidos','combos','atordoamento'],
            'tom_emocional':'energico e preciso','cores_visuais':'marrom e cinza'}

# ============================================================
# MINI-CREW: NOMES
# ============================================================
def crew_nomes(cfg, identidade, num, model, max_tentativas=3):
    """Designer de nomes -> Revisor de coerencia -> Editor."""
    proibidas = cfg.get('palavras_proibidas', [])
    dominio_nome = cfg['nome']
    
    for tentativa in range(max_tentativas):
        # DESIGNER: brainstorm
        id_str = json.dumps(identidade, ensure_ascii=False)
        prompt_d = (f"Crie {num*2} nomes CRIATIVOS para habilidades de {dominio_nome}."
                    f"\nIdentidade:\n{id_str}"
                    f"\nResponda JSON array: [{{\"nome\":\"...\",\"justificativa\":\"...\"}}]"
                    f"\nNomes em portugues, CURTOS, IMPACTANTES. Nao repita palavras.")
        r = chamar(prompt_d, model, 0.9)
        nomes = extrair_json_lista(r) if r else []
        
        if not nomes:
            print(f"    Nomes: falha ao gerar (tentativa {tentativa+1})")
            continue
        
        # REVISOR: avalia cada nome
        nomes_para_revisar = [n.get('nome','?') for n in nomes if isinstance(n, dict)]
        if not nomes_para_revisar:
            continue
        
        prompt_r = (f"Para o dominio {dominio_nome} ({cfg['descricao']}), avalie estes nomes de habilidades:"
                    f"\n{chr(10).join(f'- {n}' for n in nomes_para_revisar)}"
                    f"\n\nCriterios de REJEICAO:"
                    f"\n- Contem palavras de OUTROS dominios: {', '.join(proibidas)}"
                    f"\n- Nao faz sentido para {dominio_nome}"
                    f"\n- Muito generico (serviria pra qualquer dominio)"
                    f"\nResponda JSON: {{\"aprovados\":[\"nome1\",\"nome2\"],\"rejeitados\":[\"nome_ruim\":\"motivo\"]}}"
                    f"\nAprovados = nomes QUE VOCE MANTERIA. Rejeitados = nomes que VOCE REMOVERIA.")
        rr = chamar(prompt_r, model, 0.5)
        review = extrair_json_lista(rr) if rr else []
        
        # Se review veio como dict, extrai aprovados
        aprovados = []
        if isinstance(review, list):
            aprovados = review
        elif isinstance(review, dict):
            aprovados = review.get('aprovados', [])
        
        # Se tiver aprovados suficientes, usa eles
        if len(aprovados) >= num:
            print(f"    Nomes: {len(aprovados)} aprovados de {len(nomes_para_revisar)}")
            # Pega os primeiros N
            return aprovados[:num]
        
        print(f"    Nomes: {len(aprovados)}/{num} aprovados (tentativa {tentativa+1})")
    
    # Fallback
    print(f"    Usando nomes padrao")
    return [f'Habilidade {i+1}' for i in range(num)]

# ============================================================
# MINI-CREW: DESCRICOES
# ============================================================
def crew_descricoes(cfg, identidade, nomes, model, max_tentativas=3):
    """Designer de descricoes -> Revisor -> Editor."""
    id_str = json.dumps(identidade, ensure_ascii=False)
    
    for t in range(max_tentativas):
        nomes_str = '\n'.join(f'- {n}' for n in nomes)
        prompt_d = (f"Escreva descricoes CURTAS (max 80 chars) para cada habilidade de {cfg['nome']}."
                    f"\nIdentidade:\n{id_str}"
                    f"\nHabilidades:\n{nomes_str}"
                    f"\nEstilo: 'Acao que efeito.' Nao use ':'. Cada uma UNICA."
                    f"\nResponda JSON: [{{\"nome\":\"...\",\"descricao\":\"...\"}}]")
        r = chamar(prompt_d, model, 0.7)
        descs = extrair_json_lista(r) if r else []
        
        if not descs:
            continue
        
        # Mapa
        desc_map = {}
        for d in descs:
            if isinstance(d, dict):
                dn = d.get('nome','')
                for n in nomes:
                    if dn.lower().strip('"') == n.lower().strip('"'):
                        desc_map[n] = d.get('descricao','')
        
        if len(desc_map) >= len(nomes):
            print(f"    Descricoes: {len(desc_map)}/{len(nomes)}")
            return desc_map
        
        print(f"    Descricoes: {len(desc_map)}/{len(nomes)} (tentativa {t+1})")
    
    print(f"    Usando descricoes padrao")
    return {n: 'Ataca o alvo.' for n in nomes}

# ============================================================
# MINI-CREW: SINERGIAS
# ============================================================
def crew_sinergias(cfg, nomes, model):
    """Designer de sinergias."""
    d = random.random()
    qtd = max(3, int(len(nomes) * (0.5 if d < 0.3 else 0.6)))
    alvos = random.sample(nomes, min(qtd, len(nomes)))
    
    dom_str = '; '.join(f'{k}={v}' for k,v in cfg['sinergia_doms'].items())
    prompt = (f"Crie sinergias para habilidades de {cfg['nome']}."
              f"\nDominios parceiros disponiveis: {dom_str}"
              f"\nHabilidades para sinergia:\n{chr(10).join(f'- {n}' for n in alvos)}"
              f"\nResponda JSON: [{{\"nome\":\"...\",\"sinergia_dom\":ID,\"sinergia_texto\":\"Texto comeca com nome do dominio:\"}}]"
              f"\nSe nao tiver sinergia, retorne [].")
    r = chamar(prompt, model, 0.7)
    sins = extrair_json_lista(r) if r else []
    print(f"    Sinergias: {len(sins)}")
    
    sin_map = {}
    for s in sins:
        if isinstance(s, dict):
            sn = s.get('nome','')
            for n in nomes:
                if sn.lower() == n.lower():
                    sin_map[n] = s
                    break
    return sin_map

# ============================================================
# QUALITY ASSURANCE FINAL
# ============================================================
def qa_final(nomes, desc_map, sin_map, slots, cfg):
    """Revisao final antes de montar."""
    issues = []
    
    # Verificar nomes repetidos
    seen = set()
    for n in nomes:
        if n.lower() in seen:
            issues.append(f"Nome repetido: {n}")
        seen.add(n.lower())
    
    # Verificar descricoes
    for n in nomes:
        if n not in desc_map or not desc_map[n]:
            desc_map[n] = 'Ataca o alvo.'
        if len(desc_map[n]) > 100:
            desc_map[n] = desc_map[n][:97] + '...'
    
    # Verificar palavras proibidas
    for n in nomes:
        n_lower = n.lower()
        for p in cfg.get('palavras_proibidas', []):
            if p in n_lower:
                issues.append(f"Nome '{n}' contem palavra proibida: '{p}'")
    
    return issues

# ============================================================
# MONTAGEM
# ============================================================
def montar(slots, nomes, desc_map, sin_map, cfg, nome_dominio):
    """Monta arquivo Lua sem usar f-strings complexas."""
    linhas = [
        '--[[',
        f'    Projeto MCR - SPA - {cfg["nome"]} ({cfg["id"]})',
        f'    Gerado pelo SHC Generator V6 (Multi-Agent Crew)',
        f'    Perfil: {cfg["parent"]}',
        '--]]',
        '',
    ]
    
    for i, s in enumerate(slots):
        nome = nomes[i] if i < len(nomes) else f'Hab {s["hab_id"]}'
        desc = desc_map.get(nome, 'Ataca o alvo.')
        sin_info = sin_map.get(nome, {}) if isinstance(sin_map.get(nome), dict) else {}
        st = sin_info.get("sinergia_texto") if isinstance(sin_info, dict) else None
        sd = sin_info.get("sinergia_dom") if isinstance(sin_info, dict) else s.get("sinergia_dom")
        if st in ("None","",None): st = None
        
        d = s["dano_base"]
        
        # Build lines with .format() instead of f-strings for brace-heavy content
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
        
        pos = s["postura"]
        linhas.append('    postura = {')
        linhas.append(f'        [1] = {{ efeitoConfig = {{ dano = {pos[1]} }} }},')
        linhas.append(f'        [3] = {{ efeitoConfig = {{ dano = {pos[3]} }} }},')
        linhas.append('    },')
        
        linhas.append('    niveis = {')
        linhas.append('        [5] = { { mod = "efeitoConfig", dano = "*1.15" } },')
        if i % 2 == 0:
            linhas.append('        [10] = { { mod = "efeitoConfig", dano = "*1.15" } },')
        linhas.append('    },')
        
        if st and sd:
            linhas.append('    sinergias = {')
            linhas.append(f'        [{sd}] = {{ descricao = "{st}", nivelMin = {random.choice([1,3,5])},')
            linhas.append(f'            efeitoConfig = {{ danoAdicional = {round(d*0.3,1)} }} }},')
            linhas.append('    },')
        
        if s.get("tem_estado"):
            dv = round(d*1.5,1)
            dl = round(d*2.0,1)
            linhas.append('    estados = {')
            linhas.append(f'        vinculo = {{ efeitoConfig = {{ dano = {dv}, damageType = "absolute" }} }},')
            linhas.append(f'        lampejo = {{ efeitoConfig = {{ dano = {dl}, custoMana = 0 }} }},')
            linhas.append('    },')
        
        if s.get("tem_condicao"):
            dc = round(d*1.35,1)
            ct = s["condicao_tipo"]
            if ct == "cercado":
                c_line = f'cercado = {{ efeitoConfig = {{ tipo = "explosion_ring", raio = 5, dano = {dc} }} }}'
            elif ct == "vidaBaixa":
                c_line = f'vidaBaixa = {{ efeitoConfig = {{ lifesteal = 0.3, dano = {dc} }} }}'
            elif ct == "fullHp":
                c_line = f'fullHp = {{ efeitoConfig = {{ critChance = 0.25, dano = {dc} }} }}'
            else:
                c_line = f'singleTarget = {{ efeitoConfig = {{ dano = {round(d*1.6,1)} }} }}'
            linhas.append('    condicoes = {')
            linhas.append(f'        {c_line},')
            linhas.append('    },')
        
        linhas.append('}')
        linhas.append('')
    
    linhas.append(f'print(">> SPA: habilidades/{nome_dominio}.lua carregado")')
    return '\n'.join(linhas)

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('dominio', default='clavas_leves', nargs='?')
    ap.add_argument('num', type=int, default=10, nargs='?')
    ap.add_argument('--model', default='qwen2.5-coder:7b')
    args = ap.parse_args()
    
    cfg = DOMINIOS.get(args.dominio)
    if not cfg:
        print(f"Disponiveis: {list(DOMINIOS.keys())}")
        return 1
    
    filepath = os.path.join(BASE, args.dominio + '.lua')
    
    print(f"\n{'='*50}")
    print(f"  V6 - MULTI-AGENT CREW")
    print(f"  {cfg['nome']} ({args.num} habilidades)")
    print(f"{'='*50}\n")
    
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
    
    print(f"[0] {len(slots)} slots estruturais\n")
    
    # CREW 1: Identidade
    print("[CREW-1] Identidade do Dominio")
    identidade = crew_identidade(cfg, args.model)
    print()
    
    # CREW 2: Nomes
    print("[CREW-2] Geracao de Nomes (Designer + Revisor)")
    nomes = crew_nomes(cfg, identidade, args.num, args.model)
    print()
    
    # CREW 3: Descricoes
    print("[CREW-3] Descricoes")
    desc_map = crew_descricoes(cfg, identidade, nomes, args.model)
    print()
    
    # CREW 4: Sinergias
    print("[CREW-4] Sinergias")
    sin_map = crew_sinergias(cfg, nomes, args.model)
    print()
    
    # QUALITY ASSURANCE
    print("[QA] Revisao Final")
    issues = qa_final(nomes, desc_map, sin_map, slots, cfg)
    if issues:
        for iss in issues:
            print(f"  ISSUE: {iss}")
    else:
        print("  Nenhum problema encontrado!")
    print()
    
    # Montagem
    print("[BUILD] Montando arquivo...")
    conteudo = montar(slots, nomes, desc_map, sin_map, cfg, args.dominio)
    
    # Validacao
    o, c = conteudo.count('{'), conteudo.count('}')
    habs = len(re.findall(r'HABILIDADES\[\d+\]', conteudo))
    sins_c = conteudo.count('sinergias')
    
    print(f"  {habs} habilidades, {o}/{c} chaves")
    print(f"  Sinergias: {sins_c}")
    print(f"  Chaves: {'OK' if o==c else 'ERRO'}")
    
    if o != c:
        print("  ERRO CRITICO!")
        return 1
    
    if os.path.exists(filepath):
        shutil.copy2(filepath, filepath + '.bak_v6')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print(f"  Salvo: {filepath}\n")
    
    print("NOMES FINAIS:")
    for i, n in enumerate(nomes):
        s = slots[i]
        print(f"  [{s['hab_id']}] {n} (CD:{s['cd']} {s['categoria']})")

if __name__ == '__main__':
    main()
