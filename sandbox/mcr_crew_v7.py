#!/usr/bin/env python3
"""
MCR AI CREW V7 — Self-Improving Multi-Agent System
===================================================
Gera habilidades SHC com qualidade comparavel a um designer humano.
A cada iteracao, aprende com os proprios erros e melhora.

Componentes:
  1. Generator   — cria conteudo (nomes, descricoes, etc.)
  2. Reviewer    — avalia rigorosamente contra criterios de qualidade
  3. Editor      — corrige baseado no feedback do reviewer
  4. Trainer     — analisa erros e atualiza a base de conhecimento
  5. Knowlege DB — criterios, padroes, anti-padroes (persistente)
"""

import sys, os, json, re, random, shutil, urllib.request, datetime

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE_HAB = r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades'
BASE_KNOW = r'E:\Projeto MCR\sandbox\.crew_knowledge'

os.makedirs(BASE_KNOW, exist_ok=True)

# ============================================================
# KNOWLEDGE BASE — Persistente, auto-melhoravel
# ============================================================
class KnowledgeBase:
    """Base de conhecimento que cresce com cada execucao."""
    
    def __init__(self, dominio_nome):
        self.path = os.path.join(BASE_KNOW, f'{dominio_nome}.json')
        self.data = self._load()
    
    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'dominio': '',
            'criterios_qualidade': [
                'Nome reflete a mecanica da habilidade',
                'Nome usa vocabulario do dominio (NAO usar palavras de outros dominios)',
                'Descricao curta (max 80 chars), estilo "Acao que efeito."',
                'Sinergia comeca com nome do dominio parceiro + ":"',
                'Cada habilidade tem proposito unico no kit',
            ],
            'anti_padroes': [
                'Nome contem palavra de OUTRO dominio (ex: "punho" em Clavas)',
                'Nome muito generico (serviria pra qualquer dominio)',
                'Descricao tem ":" (confunde com sinergia)',
                'Descricao repetida entre habilidades',
            ],
            'palavras_proibidas_por_dominio': {},
            'ultimos_erros': [],
            'melhores_exemplos': [],
            'versoes_geradas': [],
        }
    
    def save(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def add_erro(self, erro):
        self.data['ultimos_erros'].append({
            'erro': erro,
            'data': datetime.datetime.now().isoformat(),
        })
        if len(self.data['ultimos_erros']) > 50:
            self.data['ultimos_erros'] = self.data['ultimos_erros'][-50:]
        self.save()
    
    def add_exemplo(self, nome, qualidade, motivo):
        """Adiciona exemplo de qualidade (bom ou ruim)"""
        self.data['melhores_exemplos'].append({
            'nome': nome, 'qualidade': qualidade, 'motivo': motivo,
            'data': datetime.datetime.now().isoformat(),
        })
        self.save()
    
    def add_versao(self, nomes, nota_geral):
        self.data['versoes_geradas'].append({
            'nomes': nomes, 'nota': nota_geral,
            'data': datetime.datetime.now().isoformat(),
        })
        self.save()
    
    def set_palavras_proibidas(self, dominio, palavras):
        self.data['palavras_proibidas_por_dominio'][dominio] = palavras
        self.save()
    
    def get_contexto(self):
        """Retorna um resumo do conhecimento para usar em prompts."""
        ctx = []
        if self.data['ultimos_erros']:
            ctx.append('ERROS RECENTES (evite repetir):')
            for e in self.data['ultimos_erros'][-5:]:
                ctx.append(f'- {e["erro"]}')
        if self.data['melhores_exemplos']:
            ctx.append('\nEXEMPLOS DE QUALIDADE:')
            for ex in self.data['melhores_exemplos'][-5:]:
                ctx.append(f'- {ex["nome"]}: {ex["motivo"]} (qualidade: {ex["qualidade"]})')
        return '\n'.join(ctx)

# ============================================================
# DOMINIO CONFIG
# ============================================================
DOMINIOS = {
    'clavas_leves': {
        'id': 112, 'nome': 'CLAVAS LEVES', 'parent': 'Clavas 12 - Combate 1',
        'elemento': 'COMBAT_PHYSICALDAMAGE', 'ids': (11201, 11220),
        'sinergia_doms': {113: 'Clavas Pesadas', 130: 'Lutador', 25: 'Terra'},
        'descricao': 'Clavas leves sao armas ageis de uma mao. Golpes rapidos, precisos.',
        'pool_tematico': ['clava', 'giro', 'golpe', 'impacto', 'combo', 'trovao', 'redemoinho',
                         'ventania', 'bambu', 'agil', 'preciso', 'rapido', 'duplo', 'crescente',
                         'giro', 'danca', 'impacto', 'martelo', 'bastao'],
        'palavras_proibidas': ['punho', 'soco', 'chute', 'flexao', 'arcano', 'magia', 'flecha',
                               'espada', 'lanca', 'machado', 'adaga', 'dardo', 'laminas',
                               'cajado', 'bastao', 'vara'],
    },
}

# ============================================================
# CHAMADA OLLAMA
# ============================================================
def chamar(prompt, model='qwen2.5-coder:7b', temp=0.8):
    try:
        data = json.dumps({'model':model,'prompt':prompt,'stream':False,
            'options':{'temperature':temp,'num_ctx':8192,'top_p':0.9}}).encode()
        req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read()).get('response','')
    except Exception as e:
        return f"ERRO:{e}"

def parse_json(txt):
    if not txt: return None
    for p in [r'\[.*?\]', r'\{.*?\}']:
        m = re.search(p, txt, re.DOTALL)
        if m:
            try: return json.loads(m.group())
            except: pass
    return None

# ============================================================
# GENERATOR — Criacao
# ============================================================
def gerar_identidade(cfg, kb, model):
    """Generator de identidade com contexto do knowledge base."""
    ctx = kb.get_contexto()
    prompt = (
        f"Crie uma identidade UNICA para o dominio {cfg['nome']} (ID {cfg['id']}).\n"
        f"Contexto: {cfg['descricao']}\n"
        f"Pool tematico: {', '.join(cfg['pool_tematico'])}\n"
        f"Palavras PROIBIDAS (nunca usar): {', '.join(cfg['palavras_proibidas'])}\n"
        f"{ctx}\n\n"
        f"Responda APENAS JSON (sem explicacoes):\n"
        f'{{"personalidade":"...","fantasy":"...","mecanicas_chave":["..."],"tom_emocional":"...","cores_visuais":"..."}}'
    )
    
    for t in range(3):
        r = chamar(prompt, model, 0.9)
        dados = parse_json(r)
        if isinstance(dados, list) and dados: dados = dados[0]
        if isinstance(dados, dict) and 'personalidade' in dados:
            return dados
        kb.add_erro(f'Identidade: resposta nao foi JSON valido (tentativa {t+1})')
    
    return None

def gerar_nomes(cfg, identidade, num, kb, model):
    """Generator de nomes com contexto + feedback de erros anteriores."""
    ctx = kb.get_contexto()
    id_str = json.dumps(identidade, ensure_ascii=False) if identidade else cfg['descricao']
    
    prompt = (
        f"Crie {num*2} nomes CRIATIVOS para habilidades de {cfg['nome']}.\n"
        f"Identidade:\n{id_str}\n"
        f"Pool tematico (USE estas palavras): {', '.join(cfg['pool_tematico'])}\n"
        f"PROIBIDO usar: {', '.join(cfg['palavras_proibidas'])}\n"
        f"{ctx}\n\n"
        f"Regras:\n"
        f"- Nomes em portugues, CURTOS, IMPACTANTES\n"
        f"- CADA nome DEVE conter ou sugerir palavra do pool tematico\n"
        f"- Nao repita palavras entre nomes\n"
        f"- Cada nome deve evocar a mecanica da habilidade\n\n"
        f"Responda JSON array:\n"
        f'[{{"nome":"Golpe Agil","justificativa":"Golpe rapido que inicia combos","mecanica":"multi-hit"}},...]'
    )
    
    for t in range(3):
        r = chamar(prompt, model, 0.9)
        nomes = parse_json(r) if r else None
        if isinstance(nomes, list): return nomes
        if isinstance(nomes, dict):
            for v in nomes.values():
                if isinstance(v, list): return v
    
    return []

def gerar_descricoes(cfg, nomes, identidade, kb, model):
    """Generator de descricoes com exemplos de qualidade."""
    id_str = json.dumps(identidade, ensure_ascii=False) if identidade else cfg['descricao']
    
    prompt = (
        f"Escreva descricoes CURTAS (max 80 chars) para habilidades de {cfg['nome']}.\n"
        f"Identidade:\n{id_str}\n\n"
        f"Habilidades:\n{chr(10).join(f'- {n}' for n in nomes)}\n\n"
        f"EXEMPLOS DE QUALIDADE:\n"
        f"- 'Golpe rapido que prepara o terreno para o combo.'\n"
        f"- 'Explosao de energia arcana ao redor do alvo.'\n"
        f"- 'Posicao defensiva que reflete parte do dano.'\n\n"
        f"Regras:\n"
        f"- Estilo 'Acao que efeito.'\n"
        f"- NAO use ':' na descricao\n"
        f"- Cada descricao UNICA (nao repita estrutura)\n\n"
        f"Responda JSON array:\n"
        f'[{{"nome":"...","descricao":"..."}},...]'
    )
    
    for t in range(3):
        r = chamar(prompt, model, 0.7)
        descs = parse_json(r) if r else None
        dados = descs
        if isinstance(dados, dict) and 'habilidades' in dados: dados = dados['habilidades']
        if isinstance(dados, dict): dados = list(dados.values())
        if isinstance(dados, list):
            # Mapa
            mapa = {}
            for d in dados:
                if isinstance(d, dict):
                    for n in nomes:
                        if d.get('nome','').lower().strip('"\'') == n.lower().strip("\"'"):
                            mapa[n] = d.get('descricao','')
            if len(mapa) >= len(nomes) * 0.8:
                return mapa
    
    return {}

def gerar_sinergias(cfg, nomes, kb, model):
    """Generator de textos de sinergia."""
    qtd = max(3, int(len(nomes) * 0.6))
    alvos = random.sample(nomes, min(qtd, len(nomes)))
    dom_str = ', '.join(f'{k}={v}' for k,v in cfg['sinergia_doms'].items())
    
    prompt = (
        f"Crie sinergias para habilidades de {cfg['nome']}.\n"
        f"Dominios parceiros: {dom_str}\n"
        f"Habilidades:\n{chr(10).join(f'- {n}' for n in alvos)}\n\n"
        f"EXEMPLO:\n"
        f'- Para nome "Clava Trovejante": Clavas Pesadas: impacto brutal apos combo.\n'
        f'- Para nome "Redemoinho": Lutador: sincronia de golpes duplos.\n\n'
        f"Regras:\n"
        f"- Texto COMECA com nome do dominio + ':'\n"
        f"- Seja especifico, nao generico\n"
        f"- Cada sinergia UNICA\n\n"
        f"Responda JSON:\n"
        f'[{{"nome":"...","sinergia_dom":ID,"sinergia_texto":"Texto."}},...]\n'
        f'Use null para sinergia_texto se a habilidade nao tiver sinergia.'
    )
    
    for t in range(3):
        r = chamar(prompt, model, 0.7)
        sins = parse_json(r) if r else None
        if isinstance(sins, list): return sins
        if isinstance(sins, dict):
            for v in sins.values():
                if isinstance(v, list): return v
    
    return []

# ============================================================
# REVIEWER — Avaliacao rigorosa
# ============================================================
def revisar_nomes(nomes, cfg, kb, model):
    """Revisor ESPECIALISTA em coerencia tematica."""
    prompt = (
        f"Voce eh um REVISOR RIGOROSO de nomes de habilidades para {cfg['nome']}.\n"
        f"Descricao do dominio: {cfg['descricao']}\n"
        f"Palavras do pool tematico: {', '.join(cfg['pool_tematico'])}\n"
        f"Palavras PROIBIDAS (REJEITE imediatamente): {', '.join(cfg['palavras_proibidas'])}\n\n"
        f"Nomes para avaliar:\n{chr(10).join(f'- {n}' for n in nomes)}\n\n"
        f"CRITERIOS DE REJEICAO:\n"
        f"1. Contem palavra PROIBIDA (ex: 'punho', 'espada', 'magia' em clavas)\n"
        f"2. Nao faz NENHUM sentido para o dominio ('Garrafa', 'Cobra', 'Passaro')\n"
        f"3. Muito generico ('Golpe', 'Ataque', 'Poder')\n"
        f"4. Eh de outro dominio ('Flecha' em clavas, 'Feitico' em clavas)\n\n"
        f"Responda JSON:\n"
        f'{{"aprovados":["nome1","nome2",...],"rejeitados":{{"nome_ruim":"motivo_rejeicao",...}},"nota_geral":7}}'
    )
    
    r = chamar(prompt, model, 0.4)
    review = parse_json(r) if r else {}
    if isinstance(review, list): review = review[0] if review else {}
    if not isinstance(review, dict): review = {}
    
    return review

def revisar_descricoes(desc_map, cfg, model):
    """Revisor de descricoes."""
    items = '\n'.join(f'- {n}: {d}' for n,d in desc_map.items())
    prompt = (
        f"Reveja estas descricoes para {cfg['nome']}:\n{items}\n\n"
        f"CRITERIOS:\n"
        f"1. Descricao tem ':' ? (REJEITE - isso parece sinergia)\n"
        f"2. Descricao maior que 100 chars? (REJEITE - muito longa)\n"
        f"3. Descricao e igual a outra? (REJEITE - repetida)\n"
        f"4. Descricao nao descreve a acao? (REJEITE - muito generica)\n\n"
        f"Responda JSON:\n"
        f'{{"aprovados":{{"nome":"descricao_aprovada"}},"rejeitados":{{"nome":"motivo"}},"nota":7}}'
    )
    
    r = chamar(prompt, model, 0.4)
    return parse_json(r) if r else {}

# ============================================================
# EDITOR — Corrige baseado no feedback
# ============================================================
def editor_nomes(nomes_rejeitados, motivos, cfg, model):
    """Editor substitui nomes ruins por novos."""
    if not nomes_rejeitados: return {}
    
    prompt = (
        f"Substitua estes nomes RUINS para {cfg['nome']} por nomes MELHORES.\n"
        f"Pool tematico: {', '.join(cfg['pool_tematico'])}\n"
        f"Proibido: {', '.join(cfg['palavras_proibidas'])}\n\n"
        f"Nomes ruins e motivos:\n{chr(10).join(f'- {n}: {m}' for n,m in nomes_rejeitados)}\n\n"
        f"Responda JSON:\n"
        f'{{"nome_ruim":"nome_melhor","nome_ruim2":"nome_melhor2"}}'
    )
    
    r = chamar(prompt, model, 0.8)
    correcoes = parse_json(r) if r else {}
    if isinstance(correcoes, list):
        # Converte lista pra dict
        d = {}
        for item in correcoes:
            if isinstance(item, dict):
                for k,v in item.items():
                    d[k] = v
        return d
    return correcoes if isinstance(correcoes, dict) else {}

# ============================================================
# TRAINER — Aprende com os erros
# ============================================================
def treinar(nomes, review, desc_map, cfg, kb, model):
    """Trainer analisa o que deu errado e atualiza o knowledge base."""
    aprovados = review.get('aprovados', []) if isinstance(review, dict) else []
    rejeitados = review.get('rejeitados', {}) if isinstance(review, dict) else {}
    nota = review.get('nota_geral', 5) if isinstance(review, dict) else 5
    
    # Analisa rejeicoes
    for nome, motivo in rejeitados.items():
        if isinstance(motivo, str):
            kb.add_erro(f'{nome}: {motivo}')
            kb.add_exemplo(nome, 'ruim', motivo)
    
    # Analisa aprovados com nota
    for nome in aprovados:
        if isinstance(nome, str):
            kb.add_exemplo(nome, 'bom', 'Aprovado pelo revisor')
    
    # Se nota < 7, sugere melhorias
    if nota < 7:
        prompt = (
            f"Analise a geracao de nomes para {cfg['nome']} e sugira MELHORIAS no processo.\n"
            f"Nota geral: {nota}/10\n"
            f"Nomes rejeitados:\n{chr(10).join(f'- {n}: {m}' for n,m in rejeitados.items())}\n"
            f"Pool tematico atual: {', '.join(cfg['pool_tematico'])}\n"
            f"Palavras proibidas atuais: {', '.join(cfg['palavras_proibidas'])}\n\n"
            f"Responda JSON:\n"
            f'{{"novas_palavras_proibidas":["...","..."],"sugestoes_prompt":["..."],"problema_raiz":"..."}}'
        )
        r = chamar(prompt, model, 0.6)
        melhoria = parse_json(r) if r else {}
        if isinstance(melhoria, dict):
            novas_proib = melhoria.get('novas_palavras_proibidas', [])
            if novas_proib:
                atuais = cfg.get('palavras_proibidas', [])
                cfg['palavras_proibidas'] = list(set(atuais + novas_proib))
                kb.set_palavras_proibidas(cfg['nome'], cfg['palavras_proibidas'])
                print(f"    Trainer: +{len(novas_proib)} novas palavras proibidas")
    
    kb.add_versao(aprovados, nota)
    return nota

# ============================================================
# MONTAGEM LUA
# ============================================================
def montar_lua(slots, nomes, desc_map, sin_map, cfg, nome_dominio):
    linhas = [
        '--[[',
        f'    Projeto MCR - SPA - {cfg["nome"]} ({cfg["id"]})',
        f'    Gerado pelo MCR AI CREW V7 (auto-melhoravel)',
        f'    Perfil: {cfg["parent"]}',
        '--]]',
        '',
    ]
    
    for i, s in enumerate(slots):
        nome = nomes[i] if i < len(nomes) else f'Hab {s["hab_id"]}'
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
# MAIN — Orquestrador da Crew
# ============================================================
def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('dominio', default='clavas_leves', nargs='?')
    ap.add_argument('num', type=int, default=10, nargs='?')
    ap.add_argument('--model', default='qwen2.5-coder:7b')
    ap.add_argument('--train', action='store_true', help='Ativa auto-treino (atualiza knowledge base)')
    args = ap.parse_args()
    
    cfg = DOMINIOS.get(args.dominio)
    if not cfg: return 1
    
    filepath = os.path.join(BASE_HAB, args.dominio + '.lua')
    kb = KnowledgeBase(args.dominio)
    
    print(f'\n{"="*55}')
    print(f'  MCR AI CREW V7 - {cfg["nome"]}')
    print(f'  {args.num} habilidades | Modelo: {args.model}')
    print(f'  Auto-treino: {"ON" if args.train else "OFF"}')
    print(f'{"="*55}\n')
    
    # Slots estruturais (Python puro, sem IA)
    slots = []
    for i in range(args.num):
        hid = cfg['ids'][0] + i
        pct = i / args.num
        dano = round(0.4 + pct*1.8, 1)
        slots.append({
            'hab_id': hid, 'dano_base': dano,
            'percentual': round(0.15 + pct*0.45, 2),
            'cd': max(1, 12 - int(pct*10)),
            'categoria': ['single','single','single','aoe','debuff','buff','aoe','defense','finisher','finisher'][i] if i < 10 else 'single',
            'tipo': ['melee','projectile','multi_hit','explosion_ring','debuff','buff','storm','buff','storm','multi_hit'][i] if i < 10 else 'melee',
            'postura': {1:round(dano*1.35,1),3:round(dano*0.65,1)} if i%4==0 else
                      {1:round(dano*1.2,1),3:round(dano*0.8,1)} if i%4==1 else
                      {1:round(dano*0.85,1),3:round(dano*1.15,1)} if i%4==2 else
                      {1:round(dano*1.5,1),3:round(dano*0.5,1)},
            'tem_sinergia': random.random()<0.6,
            'tem_estado': random.random()<0.3,
            'tem_condicao': random.random()<0.3,
            'condicao_tipo': random.choice(['cercado','vidaBaixa','fullHp','singleTarget']),
        })
        if slots[-1]['tem_sinergia']:
            slots[-1]['sinergia_dom'] = random.choice(list(cfg['sinergia_doms'].keys()))
    
    print(f'[INIT] {len(slots)} slots estruturais\n')
    
    # === CREW: IDENTIDADE ===
    print('[CREW] 1/4 — Identidade')
    identidade = gerar_identidade(cfg, kb, args.model)
    if identidade:
        print(f'  Generator: {identidade.get("personalidade","?")[:60]}...')
    else:
        print('  Generator: (usando padrao)')
    
    # === CREW: NOMES ===
    print('\n[CREW] 2/4 — Nomes (Generator + Reviewer + Editor + Trainer)')
    
    for ciclo in range(3):  # Max 3 ciclos de revisao
        # GENERATOR
        print(f'  Ciclo {ciclo+1}:')
        brainstorm = gerar_nomes(cfg, identidade, args.num, kb, args.model)
        nomes_brutos = [n.get('nome','?') for n in brainstorm if isinstance(n, dict)]
        nomes_brutos = nomes_brutos[:args.num*2]
        
        if not nomes_brutos:
            nomes_brutos = [f'Clava {i+1}' for i in range(args.num*2)]
        
        print(f'    Generator: {len(nomes_brutos)} nomes')
        
        # Filtrar palavras proibidas
        nomes_filtrados = []
        rejeitados_auto = {}
        for n in nomes_brutos:
            n_lower = n.lower()
            proibido = False
            for p in cfg['palavras_proibidas']:
                if p in n_lower:
                    rejeitados_auto[n] = f'Contem palavra proibida: {p}'
                    proibido = True
                    break
            if not proibido:
                nomes_filtrados.append(n)
        
        if rejeitados_auto:
            print(f'    Filtro automatico: {len(rejeitados_auto)} rejeitados')
        
        # REVIEWER
        review = revisar_nomes(nomes_filtrados, cfg, kb, args.model)
        aprovados = review.get('aprovados', []) if isinstance(review, dict) else nomes_filtrados
        rejeitados = review.get('rejeitados', {}) if isinstance(review, dict) else {}
        nota = review.get('nota_geral', 5) if isinstance(review, dict) else 5
        
        if isinstance(aprovados, list) and len(aprovados) >= args.num:
            print(f'    Reviewer: {len(aprovados)} aprovados (nota {nota}/10)')
            nomes_finais = aprovados[:args.num]
            break
        elif isinstance(aprovados, list) and len(aprovados) > 0:
            print(f'    Reviewer: {len(aprovados)}/{args.num} aprovados (nota {nota}/10)')
            
            # EDITOR: corrige nomes rejeitados
            faltam = args.num - len(aprovados)
            rejeitados_list = list(rejeitados.items())[:faltam] if isinstance(rejeitados, dict) else []
            correcoes = editor_nomes(rejeitados_list, cfg, args.model) if rejeitados_list else {}
            
            if isinstance(correcoes, dict):
                # Adiciona corrigidos
                for n_ruim, n_bom in correcoes.items():
                    if isinstance(n_bom, str) and len(aprovados) < args.num:
                        aprovados.append(n_bom)
            
            # Completa com fallback se ainda faltar
            while len(aprovados) < args.num:
                aprovados.append(f'Golpe {len(aprovados)+1}')
            
            nomes_finais = aprovados[:args.num]
            print(f'    Editor: corrigiu {len(correcoes)} nomes')
            break
        else:
            # Fallback: usa pool tematico pra gerar nomes
            pool = cfg['pool_tematico']
            prefixos = ['Golpe', 'Impacto', 'Giro', 'Clava', 'Combo']
            nomes_finais = []
            for i in range(args.num):
                p = prefixos[i % len(prefixos)]
                s = random.choice(pool)
                nome = f'{p} {s.title()}'
                if nome not in nomes_finais:
                    nomes_finais.append(nome)
                else:
                    nomes_finais.append(f'{p} {s.title()} {i}')
            print(f'    Fallback: {len(nomes_finais)} nomes do pool tematico')
    
    # TRAINER
    if args.train and 'rejeitados' in locals():
        nota_final = treinar(nomes_finais, review, {}, cfg, kb, args.model)
        print(f'    Trainer: nota {nota_final}/10 registrada')
    print(f'  Nomes: {", ".join(nomes_finais[:5])}...')
    
    # === CREW: DESCRICOES ===
    print('\n[CREW] 3/4 — Descricoes')
    desc_map = gerar_descricoes(cfg, nomes_finais, identidade, kb, args.model)
    
    if not desc_map:
        desc_map = {n: 'Ataca o alvo.' for n in nomes_finais}
    print(f'  {len(desc_map)} descricoes')
    
    # === CREW: SINERGIAS ===
    print('\n[CREW] 4/4 — Sinergias')
    sins = gerar_sinergias(cfg, nomes_finais, kb, args.model)
    sin_map = {}
    for s in sins:
        if isinstance(s, dict):
            sn = s.get('nome','')
            for n in nomes_finais:
                if sn.lower().strip('"') == n.lower().strip('"'):
                    sin_map[n] = s
                    break
    print(f'  {len(sin_map)} sinergias')
    
    # === MONTAGEM ===
    print('\n[BUILD] Montando...')
    conteudo = montar_lua(slots, nomes_finais, desc_map, sin_map, cfg, args.dominio)
    
    # Validacao
    o, c = conteudo.count('{'), conteudo.count('}')
    habs = len(re.findall(r'HABILIDADES\[\d+\]', conteudo))
    sins_c = conteudo.count('sinergias')
    est_c = conteudo.count('estados')
    cond_c = conteudo.count('condicoes')
    
    print(f'  {habs} habilidades, {sins_c} sinergias, {est_c} estados, {cond_c} condicoes')
    
    if o != c:
        print(f'  ERRO: chaves {o}/{c}')
        return 1
    
    # Salvar
    if os.path.exists(filepath):
        shutil.copy2(filepath, filepath + '.bak_v7')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print(f'  Salvo: {filepath}')
    print(f'\nNOMES FINAIS:')
    for i, n in enumerate(nomes_finais):
        s = slots[i]
        print(f'  [{s["hab_id"]}] {n} (CD:{s["cd"]}s)')

if __name__ == '__main__':
    main()
