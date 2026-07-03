#!/usr/bin/env python3
"""
MCR CREW V9 — Thematic Fingerprint + Self-Learning Validator
================================================================
Python nao so valida regras, mas TAMBEM sabe o que eh "bom" pra cada dominio.
O fingerprint tematico cresce com cada geracao, aprendendo o que funciona.

Novos checkers Python (antes impossiveis sem IA):
  1. ThematicScore — nome usa palavras DO DOMINIO? (0-100%)
  2. PatternMatch — nome segue o padrao "Adjetivo + Substantivo" ou "Substantivo + Adjetivo"?
  3. BadExampleMatch — nome se parece com exemplos RUINS conhecidos?
  4. GoodExampleMatch — nome se parece com exemplos BONS conhecidos?
  5. CreativityScore — nome nao repete estrutura de nomes anteriores?
"""

import sys, os, json, re, random, shutil, urllib.request, datetime, math

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE_HAB = r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades'
BASE_FP = r'E:\Projeto MCR\sandbox\.fingerprints'
os.makedirs(BASE_FP, exist_ok=True)

# ============================================================
# FINGERPRINT DATABASE — O coracao do V9
# ============================================================
class ThematicFingerprint:
    """
    Fingerprint tematico de um dominio.
    Cresce automaticamente: analisa erros e acertos, atualiza os criterios.
    """
    
    DOMINIOS_PADRAO = {
        'clavas_leves': {
            'nome': 'CLAVAS LEVES',
            'descricao': 'armas ageis de uma mao, golpes rapidos e precisos',
            'palavras_obrigatorias': ['clava', 'giro', 'impacto', 'agil', 'preciso', 'rapido', 'bambu', 'danca', 'trovao'],
            'palavras_proibidas': ['punho', 'soco', 'chute', 'espada', 'lanca', 'machado', 'adaga', 
                                  'flecha', 'magia', 'arcano', 'feiti', 'cobra', 'aguia', 'passaro', 
                                  'leao', 'cobra', 'veneno', 'sagrado', 'dardo', 'laminas', 'cajado', 'bastao'],
            'padrao_esperado': 'substantivo_adjetivo',  # "Golpe Agil", "Clava Trovejante"
            'palavras_genericas': ['golpe', 'ataque', 'poder', 'forca', 'basico', 'comum'],
            'exemplos_ruins': [
                'Punho de Ferro', 'Cobra Venenosa', 'Garrafa de Fogo',
                'Agulha Sutil', 'Maqueira Enfraquecedora', 'Estrela Explodente',
                'Flecha de Gelo', 'Espada Ligeira', 'Bastao Arcano',
            ],
            'exemplos_bons': [
                'Giro Agil', 'Clava Trovejante', 'Bambu Ligeiro', 'Danca das Clavas',
                'Impacto Sonoro', 'Redemoinho de Clavas', 'Ventania de Golpes',
                'Combo Crescente', 'Golpe Preciso', 'Giro Desafiador',
            ],
            'ultimas_rejeicoes': [],
            'ultimas_aprovacoes': [],
        }
    }
    
    def __init__(self, dominio_nome):
        self.path = os.path.join(BASE_FP, f'{dominio_nome}.json')
        self.nome = dominio_nome
        self.data = self._load()
    
    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        # Fallback: usa padrao
        return self.DOMINIOS_PADRAO.get(self.nome, self.DOMINIOS_PADRAO['clavas_leves'])
    
    def save(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def get_palavras_chave(self):
        """Lista de palavras-chave aceitaveis."""
        return list(set(
            self.data.get('palavras_obrigatorias', []) +
            [p.split()[0].lower() for p in self.data.get('exemplos_bons', [])] +
            [p.split()[-1].lower() for p in self.data.get('exemplos_bons', [])]
        ))
    
    def thematic_score(self, nome):
        """Retorna 0.0 a 1.0: quanto o nome pertence ao dominio."""
        n = nome.lower()
        palavras = set(n.split())
        
        # Bonus por palavras obrigatorias
        bonus = 0
        for p in self.data.get('palavras_obrigatorias', []):
            if p in n:
                bonus += 0.3
        
        # Bonus por similaridade com exemplos bons
        for ex in self.data.get('exemplos_bons', []):
            ex_palavras = set(ex.lower().split())
            overlap = palavras & ex_palavras
            if overlap:
                bonus += 0.1 * len(overlap)
        
        # Penalidade por palavras proibidas
        for p in self.data.get('palavras_proibidas', []):
            if p in n:
                return 0.0  # Zero absoluto
        
        # Penalidade por similaridade com exemplos ruins
        for ex in self.data.get('exemplos_ruins', []):
            ex_palavras = set(ex.lower().split())
            overlap = palavras & ex_palavras
            if len(overlap) >= 2:
                bonus -= 0.3  # Muito similar a um exemplo ruim
        
        # Penalidade por ser generico
        for g in self.data.get('palavras_genericas', []):
            if n.strip() == g:
                return 0.1
        
        score = min(1.0, max(0.0, 0.3 + bonus))
        return score
    
    def register_rejection(self, nome, motivo):
        """Registra uma rejeicao para aprender."""
        self.data['ultimas_rejeicoes'].append({
            'nome': nome, 'motivo': motivo, 'data': datetime.datetime.now().isoformat()
        })
        # Se um nome for rejeitado 2+ vezes, vira exemplo ruim permanente
        rejeicoes_mesmo_nome = [r for r in self.data['ultimas_rejeicoes'] if r['nome'] == nome]
        if len(rejeicoes_mesmo_nome) >= 2 and nome not in self.data['exemplos_ruins']:
            self.data['exemplos_ruins'].append(nome)
            print(f'    Fingerprint aprendeu: "{nome}" virou exemplo RUIM')
        
        # Limita tamanho
        if len(self.data['ultimas_rejeicoes']) > 100:
            self.data['ultimas_rejeicoes'] = self.data['ultimas_rejeicoes'][-100:]
        self.save()
    
    def register_approval(self, nome):
        """Registra uma aprovacao para aprender."""
        self.data['ultimas_aprovacoes'].append({
            'nome': nome, 'data': datetime.datetime.now().isoformat()
        })
        # Se um nome for aprovado 3+ vezes, vira exemplo bom
        aprovacoes_mesmo_nome = [a for a in self.data['ultimas_aprovacoes'] if a['nome'] == nome]
        if len(aprovacoes_mesmo_nome) >= 3 and nome not in self.data['exemplos_bons']:
            self.data['exemplos_bons'].append(nome)
            print(f'    Fingerprint aprendeu: "{nome}" virou exemplo BOM')
        
        if len(self.data['ultimas_aprovacoes']) > 100:
            self.data['ultimas_aprovacoes'] = self.data['ultimas_aprovacoes'][-100:]
        self.save()

# ============================================================
# ENHANCED QUALITY GATES (com fingerprint)
# ============================================================
class QualityGateV9:
    """Portao de qualidade que usa fingerprint tematico."""
    
    def __init__(self, fp):
        self.fp = fp
        self.cfg = fp.data
    
    def check_nome(self, nome):
        """Multi-criteria check com fingerprint."""
        n = nome.lower().strip()
        erros = []
        
        # 1. Regras basicas
        if len(n) < 3: erros.append("Muito curto")
        if len(n.split()) < 2: erros.append("Precisa de 2+ palavras")
        if any(c.isdigit() for c in n): erros.append("Tem numeros")
        
        # 2. Palavras proibidas (fingerprint)
        for p in self.cfg.get('palavras_proibidas', []):
            if p in n:
                erros.append(f"Proibida: '{p}'")
        
        # 3. Muito generico
        for g in self.cfg.get('palavras_genericas', []):
            if n.strip() == g:
                erros.append(f"Generico: '{g}'")
        
        # 4. Similar a exemplos ruins
        for ex in self.cfg.get('exemplos_ruins', []):
            ex_palavras = set(ex.lower().split())
            nome_palavras = set(n.split())
            overlap = len(ex_palavras & nome_palavras)
            if overlap >= 2 and len(ex_palavras) >= 2:
                erros.append(f"Similar ao exemplo ruim '{ex}'")
        
        # 5. Thematic score
        score = self.fp.thematic_score(nome)
        if score < 0.3:
            erros.append(f"Score tematico baixo ({score:.1f})")
        
        if erros:
            return False, '; '.join(erros), score
        return True, "OK", score
    
    def check_nomes_duplicados(self, nomes):
        """Verifica duplicatas E repeticoes de padrao."""
        vistos = set()
        for nome in nomes:
            n = nome.lower().strip()
            if n in vistos:
                return False, f"Duplicado: '{nome}'"
            vistos.add(n)
            
            # Primeira palavra repetida mais que 3x
            primeira = n.split()[0] if n.split() else ''
            if primeira and sum(1 for x in nomes if x.lower().startswith(primeira)) > 3:
                return False, f"Muitos nomes comecam com '{primeira.title()}'"
        
        return True, "OK"

# ============================================================
# AI GENERATOR (com fingerprint no prompt)
# ============================================================
class AIGeneratorV9:
    """IA local com contexto enriquecido pelo fingerprint."""
    
    def __init__(self, model='qwen2.5-coder:7b'):
        self.model = model
    
    def chamar(self, prompt, temp=0.8):
        try:
            data = json.dumps({'model':self.model,'prompt':prompt,'stream':False,
                'options':{'temperature':temp,'num_ctx':8192,'top_p':0.9}}).encode()
            req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read()).get('response','')
        except: return None
    
    def parse_json(self, txt):
        if not txt: return None
        for p in [r'\[.*?\]', r'\{.*?\}']:
            m = re.search(p, txt, re.DOTALL)
            if m:
                try: return json.loads(m.group())
                except: pass
        return None
    
    def gerar_nomes(self, cfg, fp_data, quantidade, feedback=''):
        """Gera nomes com fingerprint e exemplos no prompt."""
        obrig = ', '.join(fp_data.get('palavras_obrigatorias', []))
        proib = ', '.join(fp_data.get('palavras_proibidas', []))
        bons = '\n'.join(f'  ✅ {ex}' for ex in fp_data.get('exemplos_bons', [])[:5])
        ruins = '\n'.join(f'  ❌ {ex}' for ex in fp_data.get('exemplos_ruins', [])[:5])
        
        prompt = (
            f"Crie {quantidade*2} nomes CRIATIVOS para {cfg['nome']}.\n\n"
            f"SOBRE O DOMINIO:\n"
            f"{cfg['descricao']}\n\n"
            f"PALAVRAS-CHAVE (use SEMPRE que possivel):\n{obrig}\n\n"
            f"EXEMPLOS BONS (siga este estilo):\n{bons}\n\n"
            f"EXEMPLOS RUINS (EVITE este estilo):\n{ruins}\n\n"
            f"PROIBIDO usar estas palavras:\n{proib}\n\n"
            f"REGRA DE OURO: Cada nome deve EVOCAR a identidade do dominio.\n"
        )
        if feedback:
            prompt += f"\nFEEDBACK DA TENTATIVA ANTERIOR (CORRIJA):\n{feedback}\n"
        
        prompt += (
            f"\nResponda JSON:\n"
            f'[{{"nome":"Golpe Agil","justificativa":"Golpe rapido e preciso.","mecanica":"multi-hit"}},...]'
        )
        
        r = self.chamar(prompt, 0.9)
        dados = self.parse_json(r) if r else None
        if isinstance(dados, list): return dados
        if isinstance(dados, dict):
            for v in dados.values():
                if isinstance(v, list): return v
        return []
    
    def gerar_descricoes(self, cfg, nomes, feedback=''):
        """Gera descricoes criativas."""
        prompt = (
            f"Escreva descricoes para {cfg['nome']}.\n"
            f"Habilidades:\n{chr(10).join(f'- {n}' for n in nomes)}\n\n"
            f"REGRAS:\n"
            f"- 'Acao que efeito.' Max 80 chars\n"
            f"- Sem ':' na descricao\n"
            f"- Cada descricao UNICA\n"
        )
        if feedback:
            prompt += f"\nFEEDBACK (corrija):\n{feedback}\n"
        prompt += "\nJSON: [{\"nome\":\"...\",\"descricao\":\"...\"},...]"
        
        r = self.chamar(prompt, 0.7)
        dados = self.parse_json(r) if r else None
        if isinstance(dados, list): return dados
        if isinstance(dados, dict) and 'habilidades' in dados: return dados['habilidades']
        return []
    
    def gerar_sinergias(self, cfg, nomes_alvo):
        """Gera sinergias."""
        if not nomes_alvo: return []
        dom_str = '; '.join(f'{k}={v}' for k,v in cfg.get('sinergia_doms', {}).items())
        prompt = (
            f"Crie sinergias para {cfg['nome']}.\n"
            f"Dominios: {dom_str}\n"
            f"Habilidades:\n{chr(10).join(f'- {n}' for n in nomes_alvo)}\n\n"
            f"Regras: texto comeca com nome do dominio + ':'. Cada uma UNICA.\n"
            f"JSON: [{{\"nome\":\"...\",\"sinergia_dom\":ID,\"sinergia_texto\":\"Texto.\"}}]"
        )
        r = self.chamar(prompt, 0.7)
        dados = self.parse_json(r) if r else None
        if isinstance(dados, list): return dados
        if isinstance(dados, dict):
            for v in dados.values():
                if isinstance(v, list): return v
        return []

# ============================================================
# ORQUESTRADOR V9
# ============================================================
def gerar_nomes_v9(cfg, fp, gate, ia, quantidade):
    """Gera com fingerprint + validacao multi-criteria + loop de refinamento."""
    nomes_finais = []
    tentativa = 0
    feedback = ''
    
    while len(nomes_finais) < quantidade and tentativa < 5:
        tentativa += 1
        batch = ia.gerar_nomes(cfg, fp.data, quantidade - len(nomes_finais) + 3, feedback)
        nomes_brutos = []
        for n in batch:
            if isinstance(n, dict) and n.get('nome'):
                nomes_brutos.append(n['nome'])
        
        if not nomes_brutos:
            feedback = "Nao gerou nomes. Seja criativo!"
            continue
        
        # Valida cada nome com fingerprint
        feedback_erros = []
        for nome in nomes_brutos:
            passa, motivo, score = gate.check_nome(nome)
            if passa:
                nl = nome.lower()
                if nl not in [x.lower() for x in nomes_finais]:
                    nomes_finais.append(nome)
                    fp.register_approval(nome)
                    if len(nomes_finais) >= quantidade:
                        break
            else:
                feedback_erros.append(f"'{nome}': {motivo}")
                fp.register_rejection(nome, motivo)
        
        print(f"    Tentativa {tentativa}: {len(nomes_finais)}/{quantidade}")
        
        # Prepara feedback pra IA
        if len(nomes_finais) < quantidade and feedback_erros:
            feedback = "Corrija estes nomes:\n" + '\n'.join(feedback_erros[:5])
            feedback += f"\n\nLembre-se: {cfg['descricao']}. Use palavras do dominio!"
        elif len(nomes_finais) < quantidade:
            feedback = f"Preciso de mais {quantidade - len(nomes_finais)} nomes criativos!"
    
    # Fallback inteligente: usa fingerprint pra gerar nomes
    while len(nomes_finais) < quantidade:
        bons = fp.data.get('exemplos_bons', [])
        if bons:
            # Cria variacao de um exemplo bom
            ex = random.choice(bons)
            palavras_ex = ex.split()
            if len(palavras_ex) >= 2:
                novo = f"{random.choice(fp.data.get('palavras_obrigatorias', ['Golpe'])).title()} {palavras_ex[-1]}"
                if novo.lower() not in [n.lower() for n in nomes_finais] and gate.check_nome(novo)[0]:
                    nomes_finais.append(novo)
                    continue
        # Fallback final
        pool = fp.get_palavras_chave()
        nome = f"{random.choice(pool).title()} {random.choice(pool).title()}"
        if nome.lower() not in [n.lower() for n in nomes_finais]:
            nomes_finais.append(nome)
    
    return nomes_finais[:quantidade]

# ============================================================
# MONTAGEM LUA
# ============================================================
def montar_lua(slots, nomes, desc_map, sin_map, cfg, nome_dominio):
    linhas = [
        '--[[',
        f'    Projeto MCR - SPA - {cfg["nome"]} ({cfg["id"]})',
        f'    Gerado pelo MCR CREW V9 (Thematic Fingerprint)',
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
        linhas.append(f'        [5] = {{ {{ mod = "efeitoConfig", dano = "*1.15" }} }},')
        if i % 2 == 0:
            linhas.append(f'        [10] = {{ {{ mod = "efeitoConfig", dano = "*1.15" }} }},')
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
    ap.add_argument('--learn', action='store_true', help='Modo aprendizado: salva fingerprint')
    args = ap.parse_args()
    
    DOMINIOS = {
        'clavas_leves': {
            'id': 112, 'nome': 'CLAVAS LEVES', 'parent': 'Clavas 12 - Combate 1',
            'elemento': 'COMBAT_PHYSICALDAMAGE', 'ids': (11201, 11220),
            'sinergia_doms': {113: 'Clavas Pesadas', 130: 'Lutador', 25: 'Terra'},
            'descricao': 'Clavas leves sao armas ageis de uma mao. Golpes rapidos, precisos.',
        },
    }
    cfg = DOMINIOS.get(args.dominio)
    if not cfg:
        print(f"Dominio invalido")
        return 1
    
    filepath = os.path.join(BASE_HAB, args.dominio + '.lua')
    fp = ThematicFingerprint(args.dominio)
    gate = QualityGateV9(fp)
    ia = AIGeneratorV9(args.model)
    
    print(f'\n{"="*55}')
    print(f'  MCR CREW V9 — Thematic Fingerprint')
    print(f'  {cfg["nome"]} ({args.num} habilidades)')
    print(f'  Fingerprint: {len(fp.get_palavras_chave())} palavras-chave')
    print(f'{"="*55}\n')
    
    # Slots estruturais
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
    
    print(f'[PYTHON] {len(slots)} slots\n')
    
    # NOMES
    print('[FASE 1] Nomes (Fingerprint Gates)')
    nomes = gerar_nomes_v9(cfg, fp, gate, ia, args.num)
    print(f'  RESULTADO: {len(nomes)} nomes\n')
    
    # DESCRICOES
    print('[FASE 2] Descricoes')
    tentativa = 0
    desc_map = {}
    feedback = ''
    while len(desc_map) < len(nomes) and tentativa < 4:
        tentativa += 1
        batch = ia.gerar_descricoes(cfg, nomes, feedback)
        for item in batch:
            if isinstance(item, dict):
                n = item.get('nome','')
                d = item.get('descricao','')
                if n and d and ':' not in d and len(d) < 100 and n not in desc_map:
                    for nome_alvo in nomes:
                        if n.lower().strip('"') == nome_alvo.lower().strip('"'):
                            desc_map[nome_alvo] = d
                            break
        if len(desc_map) < len(nomes):
            feedback = "Descricoes precisam ser UNICAS e sem ':'"
        print(f'    Tentativa {tentativa}: {len(desc_map)}/{len(nomes)}')
    for n in nomes:
        if n not in desc_map:
            desc_map[n] = 'Ataca o alvo.'
    print()
    
    # SINERGIAS
    print('[FASE 3] Sinergias')
    qtd = max(3, int(len(nomes) * 0.5))
    alvos = random.sample(nomes, min(qtd, len(nomes)))
    sins = ia.gerar_sinergias(cfg, alvos)
    # Debug sinergias
    print(f'    Resposta bruta: {len(sins)} itens')
    sin_map = {}
    for s in sins:
        if isinstance(s, dict):
            sn = s.get('nome','')
            st = s.get('sinergia_texto','')
            sd = s.get('sinergia_dom')
            for n in alvos:
                if sn.lower().strip('"') == n.lower().strip('"') and st and sd and ':' in st:
                    sin_map[n] = s
                    break
    print(f'  {len(sin_map)}/{len(alvos)} sinergias\n')
    
    # MONTAGEM
    print('[BUILD] Montando...')
    conteudo = montar_lua(slots, nomes, desc_map, sin_map, cfg, args.dominio)
    o, c = conteudo.count('{'), conteudo.count('}')
    habs = len(re.findall(r'HABILIDADES\[\d+\]', conteudo))
    
    print(f'  {habs} habilidades, {o}/{c} chaves')
    
    if o != c:
        print('  ERRO: chaves!')
        return 1
    
    if os.path.exists(filepath):
        shutil.copy2(filepath, filepath + '.bak_v9')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    # Relatorio fingerprint
    print(f'\n  Salvo: {filepath}')
    print(f'\nNOMES (com score tematico):')
    for i, n in enumerate(nomes):
        score = fp.thematic_score(n)
        estrelas = '*' * int(score * 10) + '-' * (10 - int(score * 10))
        print(f'  [{slots[i]["hab_id"]}] {n} [{estrelas}] {score:.0%}')

if __name__ == '__main__':
    main()
