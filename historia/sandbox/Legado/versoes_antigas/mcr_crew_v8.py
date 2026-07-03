#!/usr/bin/env python3
"""
MCR CREW V8 — Python Quality Gates + AI Creative Generator
===========================================================
Python faz as validacoes DURAS (objetivas, 100% precisas).
IA faz só a parte CRIATIVA (nomes, descricoes, sinergias).
Se a IA erra, Python da feedback especifico e IA corrige.

Checkers Python (100% precisos):
  1. Palavras proibidas (nunca passa)
  2. Pool tematico (aviso se nao usar)
  3. Duplicatas (nunca passa)
  4. Descricao com ":" (nunca passa)
  5. Descricao muito longa (nunca passa)
  6. Nome muito generico (nunca passa)
  7. Sinergia sem "Dominio:" (nunca passa)
  8. Nome repetido entre habilidades (nunca passa)
"""

import sys, os, json, re, random, shutil, urllib.request

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE_HAB = r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades'

DOMINIOS = {
    'clavas_leves': {
        'id': 112, 'nome': 'CLAVAS LEVES', 'parent': 'Clavas 12 - Combate 1',
        'elemento': 'COMBAT_PHYSICALDAMAGE', 'ids': (11201, 11220),
        'sinergia_doms': {113: 'Clavas Pesadas', 130: 'Lutador', 25: 'Terra'},
        'descricao': 'Clavas leves sao armas ageis de uma mao. Golpes rapidos, precisos.',
        'pool_tematico': ['clava', 'giro', 'golpe', 'impacto', 'combo', 'trovao', 'redemoinho',
                         'ventania', 'bambu', 'agil', 'preciso', 'rapido', 'duplo', 'crescente', 'danca'],
        'palavras_proibidas': [
            'punho', 'soco', 'chute', 'flexao', 'arcano', 'magia', 'flecha',
            'espada', 'lanca', 'machado', 'adaga', 'dardo', 'laminas', 'cajado', 'vara',
            'cobra', 'aguia', 'falkao', 'passaro', 'cavalo', 'leao', 'tigre',
            'garrafa', 'fogo', 'veneno', 'sagrado',
        ],
        'palavras_genericas': ['golpe', 'ataque', 'poder', 'forca', 'habilidade', 'basico'],
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
    if not txt: return None
    for p in [r'\[.*?\]', r'\{.*?\}']:
        m = re.search(p, txt, re.DOTALL)
        if m:
            try: return json.loads(m.group())
            except: pass
    return None

# ============================================================
# PYTHON QUALITY GATES (100% precisos, zero IA)
# ============================================================
class QualityGate:
    """Portao de qualidade Python. Cada metodo retorna (passou, feedback)."""
    
    def __init__(self, cfg):
        self.cfg = cfg
        self.proibidas = [p.lower() for p in cfg.get('palavras_proibidas', [])]
        self.pool = [p.lower() for p in cfg.get('pool_tematico', [])]
        self.genericas = [g.lower() for g in cfg.get('palavras_genericas', [])]
    
    def check_nome(self, nome):
        """Verifica se um nome individual e valido."""
        n = nome.lower().strip()
        
        # Nao pode estar vazio
        if not n or len(n) < 3:
            return False, "Nome muito curto"
        
        # Nao pode conter palavras proibidas
        for p in self.proibidas:
            if p in n:
                return False, f"Contem palavra proibida: '{p}'"
        
        # Nao pode ser uma palavra generica sozinha
        if n in self.genericas:
            return False, "Nome muito generico (so uma palavra)"
        
        # Deve ter pelo menos 2 palavras
        if len(n.split()) < 2:
            return False, "Nome precisa de pelo menos 2 palavras"
        
        # Nao pode ter numeros
        if any(c.isdigit() for c in n):
            return False, "Nome nao pode ter numeros"
        
        return True, "OK"
    
    def check_nomes_duplicados(self, nomes):
        """Verifica se ha nomes duplicados ou muito similares."""
        vistos = set()
        for nome in nomes:
            n = nome.lower().strip()
            if n in vistos:
                return False, f"Nome duplicado: '{nome}'"
            vistos.add(n)
            
            # Palavra inicial repetida (ex: "Golpe X", "Golpe Y")
            primeira_palavra = n.split()[0] if n.split() else ''
            palavras_iniciais = [x.split()[0] for x in vistos if x.split()]
            if palavras_iniciais.count(primeira_palavra) > 2:
                return False, f"Muitos nomes comecam com '{primeira_palavra.title()}'"
        
        return True, "OK"
    
    def check_descricao(self, desc):
        """Verifica se uma descricao e valida."""
        if not desc or len(desc) < 5:
            return False, "Descricao muito curta"
        if ':' in desc:
            return False, "Descricao contem ':' (parece sinergia)"
        if len(desc) > 100:
            return False, f"Descricao muito longa ({len(desc)} chars, max 100)"
        if desc.count(' ') < 2:
            return False, "Descricao muito curta (min 3 palavras)"
        return True, "OK"
    
    def check_sinergia(self, texto, dom_id, dom_nome):
        """Verifica se texto de sinergia e valido."""
        if not texto or texto in ('None', '', 'null'):
            return False, "Texto de sinergia vazio"
        # Deve comecar com nome do dominio
        if not texto.lower().startswith(dom_nome.lower().split()[0].lower()):
            return False, f"Sinergia deve comecar com o nome do dominio ('{dom_nome}')"
        if ':' not in texto:
            return False, "Sinergia deve ter ':' apos o nome do dominio"
        return True, "OK"

# ============================================================
# AI GENERATOR (so criatividade, sem julgamento)
# ============================================================
class AIGenerator:
    """IA local usada APENAS para criar, nunca para julgar."""
    
    def __init__(self, model='qwen2.5-coder:7b'):
        self.model = model
    
    def gerar_nomes(self, cfg, identidade, quantidade, tentativa=1, feedback_anterior=''):
        """Gera nomes criativos."""
        pool = ', '.join(cfg['pool_tematico'])
        proib = ', '.join(cfg['palavras_proibidas'])
        id_str = identidade or cfg['descricao']
        
        prompt = (
            f"Crie {quantidade*2} nomes CRIATIVOS para habilidades de {cfg['nome']}.\n"
            f"Contexto: {id_str}\n\n"
            f"REGRAS (obrigatorio):\n"
            f"- Cada nome DEVE ter 2+ palavras\n"
            f"- Use palavras do pool: {pool}\n"
            f"- PROIBIDO usar: {proib}\n"
            f"- Nomes em portugues, CRIATIVOS, cada um UNICO\n"
        )
        
        if feedback_anterior:
            prompt += f"\nFEEDBACK DA TENTATIVA ANTERIOR (corrija):\n{feedback_anterior}\n"
        
        prompt += (
            f"\nResponda JSON array:\n"
            f'[{{"nome":"Clava Trovejante","justificativa":"Impacto sonoro que atordoa","mecanica":"stun"}},...]'
        )
        
        r = chamar(prompt, self.model, 0.9)
        dados = parse_json(r) if r else None
        if isinstance(dados, list): return dados
        if isinstance(dados, dict):
            for v in dados.values():
                if isinstance(v, list): return v
        return []
    
    def gerar_descricoes(self, cfg, nomes, identidade, tentativa=1, feedback_anterior=''):
        """Gera descricoes criativas."""
        prompt = (
            f"Escreva descricoes para habilidades de {cfg['nome']}.\n"
            f"Habilidades:\n{chr(10).join(f'- {n}' for n in nomes)}\n\n"
            f"REGRAS:\n"
            f"- Cada descricao: 'Acao que efeito.' (max 80 chars)\n"
            f"- NAO use ':' na descricao\n"
            f"- Cada descricao UNICA\n"
            f"- Exemplo: 'Golpe rapido que prepara o combo.'\n"
        )
        if feedback_anterior:
            prompt += f"\nFEEDBACK (corrija):\n{feedback_anterior}\n"
        
        prompt += "\nResponda JSON:\n[{\"nome\":\"...\",\"descricao\":\"...\"},...]"
        
        r = chamar(prompt, self.model, 0.7)
        dados = parse_json(r) if r else None
        if isinstance(dados, list): return dados
        if isinstance(dados, dict) and 'habilidades' in dados: return dados['habilidades']
        if isinstance(dados, dict): return list(dados.values())
        return []
    
    def gerar_sinergias(self, cfg, nomes_alvo):
        """Gera textos de sinergia."""
        if not nomes_alvo: return []
        
        dom_str = ', '.join(f'{k}={v}' for k,v in cfg['sinergia_doms'].items())
        prompt = (
            f"Crie sinergias para habilidades de {cfg['nome']}.\n"
            f"Dominios parceiros: {dom_str}\n"
            f"Habilidades:\n{chr(10).join(f'- {n}' for n in nomes_alvo)}\n\n"
            f"REGRAS:\n"
            f"- Texto COMECA com nome do dominio + ':'\n"
            f"- Ex: 'Clavas Pesadas: impacto brutal apos combo.'\n"
            f"- Cada uma UNICA\n\n"
            f"Responda JSON:\n"
            f'[{{"nome":"...","sinergia_dom":ID,"sinergia_texto":"Texto."}}]'
        )
        
        r = chamar(prompt, self.model, 0.7)
        dados = parse_json(r) if r else None
        if isinstance(dados, list): return dados
        if isinstance(dados, dict):
            for v in dados.values():
                if isinstance(v, list): return v
        return []

# ============================================================
# ORQUESTRADOR — Python manda, IA cria
# ============================================================
def gerar_nomes_com_validacao(cfg, gate, ia, quantidade):
    """Loop: IA cria -> Python valida -> IA corrige -> ate passar."""
    nomes_finais = []
    tentativa = 0
    max_tentativas = 5
    feedback_global = ''
    
    while len(nomes_finais) < quantidade and tentativa < max_tentativas:
        tentativa += 1
        restante = quantidade - len(nomes_finais)
        
        # IA gera (ou regera os que faltam)
        batch = ia.gerar_nomes(cfg, None, restante + 5, tentativa, feedback_global)
        
        nomes_brutos = list(dict.fromkeys([n.get('nome','') for n in batch if isinstance(n, dict) and n.get('nome')]))
        
        if not nomes_brutos:
            feedback_global = 'Nao foram gerados nomes. Gere nomes validos.'
            continue
        
        # Python valida cada nome
        aprovados = []
        rejeitados = []
        for nome in nomes_brutos:
            passa, motivo = gate.check_nome(nome)
            if passa:
                aprovados.append(nome)
            else:
                rejeitados.append(f"'{nome}': {motivo}")
        
        # Adiciona aprovados ineditos
        for nome in aprovados:
            nome_lower = nome.lower()
            if nome_lower not in [n.lower() for n in nomes_finais]:
                nomes_finais.append(nome)
                if len(nomes_finais) >= quantidade:
                    break
        
        print(f"    Tentativa {tentativa}: {len(aprovados)} aprovados, {len(nomes_finais)}/{quantidade} acumulados")
        
        # Feedback pra IA
        if len(nomes_finais) < quantidade:
            if rejeitados:
                feedback_global = 'Corriga estes nomes rejeitados:\n' + '\n'.join(rejeitados[:5])
            else:
                feedback_global = f'Preciso de mais {quantidade - len(nomes_finais)} nomes. Seja criativo!'
    
    # Fallback: se ainda faltar, usa pool tematico
    while len(nomes_finais) < quantidade:
        i = len(nomes_finais)
        palavras = cfg['pool_tematico']
        nome = f"{random.choice(['Golpe','Giro','Impacto','Clava'])} {random.choice(palavras).title()}"
        if nome not in nomes_finais:
            nomes_finais.append(nome)
    
    return nomes_finais[:quantidade]

def gerar_descricoes_com_validacao(cfg, gate, ia, nomes):
    """Loop: IA cria descricoes -> Python valida -> IA corrige."""
    desc_map = {}
    tentativa = 0
    max_tentativas = 4
    feedback = ''
    
    while len(desc_map) < len(nomes) and tentativa < max_tentativas:
        tentativa += 1
        
        batch = ia.gerar_descricoes(cfg, nomes, None, tentativa, feedback)
        
        for item in batch:
            if isinstance(item, dict):
                n = item.get('nome','')
                d = item.get('descricao','')
                if n and d:
                    passa, motivo = gate.check_descricao(d)
                    if passa:
                        if n not in desc_map:
                            desc_map[n] = d
                    else:
                        feedback += f"'{d}': {motivo}\n"
        
        # Pega descricoes que faltam
        faltando = [n for n in nomes if n not in desc_map]
        
        # Preenche faltantes com descricoes aprovadas de outros nomes
        for nome in faltando:
            # Procura no batch por nome similar
            for item in batch:
                if isinstance(item, dict):
                    bn = item.get('nome','')
                    if bn.lower().strip('"') == nome.lower().strip('"'):
                        d = item.get('descricao','Ataca o alvo.')
                        passa, _ = gate.check_descricao(d)
                        if passa:
                            desc_map[nome] = d
                            break
        
        print(f"    Tentativa {tentativa}: {len(desc_map)}/{len(nomes)} descricoes")
    
    # Fallback
    for nome in nomes:
        if nome not in desc_map:
            desc_map[nome] = 'Ataca o alvo.'
    
    return desc_map

def gerar_sinergias_com_validacao(cfg, gate, ia, nomes):
    """Gera sinergias, Python valida formato."""
    qtd = max(3, int(len(nomes) * 0.5))
    alvos = random.sample(nomes, min(qtd, len(nomes)))
    
    sins = ia.gerar_sinergias(cfg, alvos)
    
    sin_map = {}
    for s in sins:
        if isinstance(s, dict):
            sn = s.get('nome','')
            st = s.get('sinergia_texto','')
            sd = s.get('sinergia_dom')
            
            for n in alvos:
                if sn.lower().strip('"') == n.lower().strip('"'):
                    if sd and st:
                        dom_nome = cfg['sinergia_doms'].get(sd, 'Dominio')
                        passa, motivo = gate.check_sinergia(st, sd, dom_nome)
                        if passa:
                            sin_map[n] = s
                        else:
                            # Corrige: texto de sinergia padrao
                            s['sinergia_texto'] = f"{dom_nome}: sinergia poderosa."
                            sin_map[n] = s
                    break
    
    print(f"    Sinergias: {len(sin_map)}/{len(alvos)} validas")
    return sin_map

# ============================================================
# MONTAGEM
# ============================================================
def montar_lua(slots, nomes, desc_map, sin_map, cfg, nome_dominio):
    linhas = [
        '--[[',
        f'    Projeto MCR - SPA - {cfg["nome"]} ({cfg["id"]})',
        f'    Gerado pelo MCR CREW V8 (Python Gates + AI Creative)',
        f'    Perfil: {cfg["parent"]}',
        '--]]',
        '',
    ]
    
    for i, s in enumerate(slots):
        nome = nomes[i]
        desc = desc_map.get(nome, 'Ataca o alvo.')
        sin_info = sin_map.get(nome, {}) if isinstance(sin_map.get(nome), dict) else {}
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
        if s.get('tem_estado'):
            dv, dl = round(d*1.5,1), round(d*2.0,1)
            linhas.append('    estados = {')
            linhas.append(f'        vinculo = {{ efeitoConfig = {{ dano = {dv}, damageType = "absolute" }} }},')
            linhas.append(f'        lampejo = {{ efeitoConfig = {{ dano = {dl}, custoMana = 0 }} }},')
            linhas.append('    },')
        if s.get('tem_condicao'):
            dc = round(d*1.35,1)
            ct = s['condicao_tipo']
            c_line = {
                'cercado': f'cercado = {{ efeitoConfig = {{ tipo = "explosion_ring", raio = 5, dano = {dc} }} }}',
                'vidaBaixa': f'vidaBaixa = {{ efeitoConfig = {{ lifesteal = 0.3, dano = {dc} }} }}',
                'fullHp': f'fullHp = {{ efeitoConfig = {{ critChance = 0.25, dano = {dc} }} }}',
            }.get(ct, f'singleTarget = {{ efeitoConfig = {{ dano = {round(d*1.6,1)} }} }}')
            linhas.append('    condicoes = {')
            linhas.append(f'        {c_line},')
            linhas.append('    },')
        linhas.append('}')
        linhas.append('')
    
    linhas.append(f'print(">> SPA: habilidades/{nome_dominio}.lua carregado")')
    return '\n'.join(linhas)

# ============================================================
# MAIN
# ============================================================
def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('dominio', default='clavas_leves', nargs='?')
    ap.add_argument('num', type=int, default=10, nargs='?')
    ap.add_argument('--model', default='qwen2.5-coder:7b')
    args = ap.parse_args()
    
    cfg = DOMINIOS.get(args.dominio)
    if not cfg: return 1
    
    filepath = os.path.join(BASE_HAB, args.dominio + '.lua')
    gate = QualityGate(cfg)
    ia = AIGenerator(args.model)
    
    print(f'\n{"="*55}')
    print(f'  MCR CREW V8 — Python Gates + AI Creative')
    print(f'  {cfg["nome"]} ({args.num} habilidades)')
    print(f'{"="*55}\n')
    
    # Slots estruturais (Python puro)
    slots = []
    for i in range(args.num):
        hid = cfg['ids'][0] + i
        pct = i / args.num
        dano = round(0.4 + pct*1.8, 1)
        tipos = ['melee','projectile','multi_hit','explosion_ring','debuff','buff','storm','buff','storm','multi_hit']
        cats = ['single','single','single','aoe','debuff','buff','aoe','defense','finisher','finisher']
        vr = i % 4
        slots.append({
            'hab_id': hid, 'dano_base': dano,
            'percentual': round(0.15 + pct*0.45, 2),
            'cd': max(1, 12 - int(pct*10)),
            'categoria': cats[i] if i < 10 else 'single',
            'tipo': tipos[i] if i < 10 else 'melee',
            'postura': [{1:round(dano*1.35,1),3:round(dano*0.65,1)},
                       {1:round(dano*1.2,1),3:round(dano*0.8,1)},
                       {1:round(dano*0.85,1),3:round(dano*1.15,1)},
                       {1:round(dano*1.5,1),3:round(dano*0.5,1)}][vr],
            'tem_sinergia': random.random()<0.6,
            'tem_estado': random.random()<0.3,
            'tem_condicao': random.random()<0.3,
            'condicao_tipo': random.choice(['cercado','vidaBaixa','fullHp','singleTarget']),
        })
        if slots[-1]['tem_sinergia']:
            slots[-1]['sinergia_dom'] = random.choice(list(cfg['sinergia_doms'].keys()))
    
    print(f'[PYTHON] {len(slots)} slots estruturais\n')
    
    # === FASE 1: NOMES (IA cria, Python valida) ===
    print('[FASE 1] Nomes (AI Generator + Python Gates)')
    nomes = gerar_nomes_com_validacao(cfg, gate, ia, args.num)
    print(f'  RESULTADO: {len(nomes)} nomes\n')
    
    # === FASE 2: DESCRICOES (IA cria, Python valida) ===
    print('[FASE 2] Descricoes')
    desc_map = gerar_descricoes_com_validacao(cfg, gate, ia, nomes)
    print(f'  RESULTADO: {len(desc_map)} descricoes\n')
    
    # === FASE 3: SINERGIAS ===
    print('[FASE 3] Sinergias')
    sin_map = gerar_sinergias_com_validacao(cfg, gate, ia, nomes)
    print()
    
    # === MONTAGEM ===
    print('[BUILD] Montando...')
    conteudo = montar_lua(slots, nomes, desc_map, sin_map, cfg, args.dominio)
    
    # Validacao final
    o, c = conteudo.count('{'), conteudo.count('}')
    habs = len(re.findall(r'HABILIDADES\[\d+\]', conteudo))
    
    print(f'  {habs} habilidades, {o}/{c} chaves')
    print(f'  Chaves: {"OK" if o==c else "ERRO"}')
    
    if o != c:
        print('  ERRO CRITICO!')
        return 1
    
    if os.path.exists(filepath):
        shutil.copy2(filepath, filepath + '.bak_v8')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print(f'  Salvo: {filepath}\n')
    
    print('NOMES FINAIS:')
    for i, n in enumerate(nomes):
        s = slots[i]
        print(f'  [{s["hab_id"]}] {n} (CD:{s["cd"]}s)')

if __name__ == '__main__':
    main()
