#!/usr/bin/env python3
"""
MCR CREW FRAMEWORK — Orchestrador Universal
============================================
Aplica o padrao V9 (Python Gates + AI Creative + Fingerprint)
a QUALQUER tarefa no Projeto MCR.

Uso: python mcr_crew.py <modulo> [args...]

Modulos disponiveis:
  habilidades  — Gera habilidades SHC para dominios
  otclient     — Gera/refatora layouts OTUI e scripts Lua
  sistema      — Projeta e implementa novos sistemas
  mapa         — Gera estruturas de mapa (RME)
  codigo       — Refatora/otimiza codigo C++/Lua existente
"""

import sys, os, json, re, random, shutil, urllib.request, datetime, importlib.util

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE_MODULOS = os.path.join(os.path.dirname(__file__), 'crew_modulos')
BASE_FINGERPRINTS = os.path.join(os.path.dirname(__file__), '.crew_fingerprints')
os.makedirs(BASE_MODULOS, exist_ok=True)
os.makedirs(BASE_FINGERPRINTS, exist_ok=True)

# ============================================================
# NUCLEO DO FRAMEWORK (compartilhado entre todos os modulos)
# ============================================================

class Fingerprint:
    """Base de conhecimento que aprende com cada execucao."""
    
    def __init__(self, modulo, tarefa):
        self.path = os.path.join(BASE_FINGERPRINTS, f'{modulo}_{tarefa}.json')
        self.data = self._load()
    
    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'modulo': '', 'tarefa': '',
            'exemplos_bons': [], 'exemplos_ruins': [],
            'palavras_chave': [], 'palavras_proibidas': [],
            'padroes_qualidade': [], 'anti_padroes': [],
            'metricas': {'geracoes': 0, 'taxa_aprovacao': 0.0, 'aprovados': 0, 'rejeitados': 0},
            'ultimos_erros': [],
        }
    
    def save(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def registrar_acerto(self, item):
        """Registra um item aprovado. Se repetido 3x, vira exemplo bom."""
        if 'aprovados_recentes' not in self.data:
            self.data['aprovados_recentes'] = []
        self.data['aprovados_recentes'].append(item)
        self.data['metricas']['aprovados'] += 1
        
        count = sum(1 for a in self.data['aprovados_recentes'] if a == item)
        if count >= 3 and item not in self.data['exemplos_bons']:
            self.data['exemplos_bons'].append(item)
            print(f'    [Fingerprint] Aprendeu: "{item}" virou exemplo BOM')
        
        if len(self.data['aprovados_recentes']) > 50:
            self.data['aprovados_recentes'] = self.data['aprovados_recentes'][-50:]
        self.save()
    
    def registrar_erro(self, item, motivo):
        """Registra um item rejeitado. Se repetido 2x, vira exemplo ruim."""
        if 'rejeitados_recentes' not in self.data:
            self.data['rejeitados_recentes'] = []
        self.data['rejeitados_recentes'].append({'item': item, 'motivo': motivo})
        self.data['metricas']['rejeitados'] += 1
        
        count = sum(1 for r in self.data['rejeitados_recentes'] if r['item'] == item)
        if count >= 2 and item not in self.data['exemplos_ruins']:
            self.data['exemplos_ruins'].append(item)
            print(f'    [Fingerprint] Aprendeu: "{item}" virou exemplo RUIM')
        
        self.data['ultimos_erros'].append({'item': item, 'motivo': motivo, 'data': str(datetime.datetime.now())})
        if len(self.data['ultimos_erros']) > 50:
            self.data['ultimos_erros'] = self.data['ultimos_erros'][-50:]
        self.save()
    
    def get_contexto(self):
        """Gera contexto pra alimentar a IA."""
        ctx = []
        if self.data['exemplos_bons']:
            ctx.append('EXEMPLOS DE QUALIDADE (siga este padrao):')
            for ex in self.data['exemplos_bons'][-5:]:
                ctx.append(f'  [BOM] {ex}')
        if self.data['exemplos_ruins']:
            ctx.append('EXEMPLOS RUINS (EVITE):')
            for ex in self.data['exemplos_ruins'][-5:]:
                ctx.append(f'  [RUIM] {ex}')
        if self.data['ultimos_erros']:
            ctx.append('ERROS RECENTES (nao repita):')
            for err in self.data['ultimos_erros'][-3:]:
                ctx.append(f'  [ERRO] {err["item"]}: {err["motivo"]}')
        return '\n'.join(ctx)


class AILocal:
    """Interface unificada com a IA local."""
    
    def __init__(self, model='qwen2.5-coder:7b'):
        self.model = model
    
    def gerar(self, prompt, temp=0.8):
        try:
            data = json.dumps({'model':self.model,'prompt':prompt,'stream':False,
                'options':{'temperature':temp,'num_ctx':8192,'top_p':0.9}}).encode()
            req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read()).get('response','')
        except Exception as e:
            return None
    
    def extrair_json(self, txt):
        if not txt: return None
        for p in [r'\[.*?\]', r'\{.*?\}']:
            m = re.search(p, txt, re.DOTALL)
            if m:
                try: return json.loads(m.group())
                except: pass
        return None


class ModuloCrew:
    """Classe base para modulos da crew. Cada modulo herda desta."""
    
    def __init__(self, nome, fingerprint, ia):
        self.nome = nome
        self.fp = fingerprint
        self.ia = ia
    
    def executar(self, **kwargs):
        """Cada modulo implementa seu proprio fluxo."""
        raise NotImplementedError
    
    def validar(self, item):
        """Cada modulo implementa suas proprias validacoes."""
        return True, "OK"


# ============================================================
# MODULO: HABILIDADES SHC (ja existente, adaptado para o framework)
# ============================================================

class ModuloHabilidades(ModuloCrew):
    """Gera habilidades SHC com fingerprint tematico."""
    
    DOMINIOS = {
        'arcos': {
            'id': 120, 'nome': 'ARCOS', 'parent': 'Precisao 13 - Combate 1',
            'elemento': 'COMBAT_PHYSICALDAMAGE', 'ids': (12001, 12020),
            'sinergia_doms': {23: 'Fogo', 24: 'Gelo', 26: 'Energia'},
            'descricao': 'arco e flecha, ataques precisos a distancia, perfuracao',
            'pool_tematico': ['flecha', 'tiro', 'arco', 'mira', 'precisao', 'disparo', 'chuva', 'perfurante', 'buscador', 'aguia', 'certeiro', 'rapido', 'triplo', 'barragem', 'sniper'],
            'palavras_proibidas': ['punho', 'soco', 'chute', 'espada', 'clava', 'machado', 'magia', 'arcano', 'bastao', 'cajado'],
        },
        'lutador': {
            'id': 130, 'nome': 'LUTADOR', 'parent': 'Artes Marciais 14 - Combate 1',
            'elemento': 'COMBAT_PHYSICALDAMAGE', 'ids': (13001, 13020),
            'sinergia_doms': {132: 'Armas de Punho', 14: 'Artes Marciais', 1: 'Combate'},
            'descricao': 'luta corpo-a-corpo, socos, chutes e quedas',
            'pool_tematico': ['soco', 'punho', 'jab', 'cruzado', 'gancho', 'chute', 'joelhada', 'combate', 'lutador', 'esquiva', 'furia', 'combo', 'quebra', 'ossos', 'impacto'],
            'palavras_proibidas': ['flecha', 'arco', 'espada', 'clava', 'magia', 'arcano', 'bastao'],
        },
        'clavas_leves': {
            'id': 112, 'nome': 'CLAVAS LEVES', 'parent': 'Clavas 12 - Combate 1',
            'elemento': 'COMBAT_PHYSICALDAMAGE', 'ids': (11201, 11220),
            'sinergia_doms': {113: 'Clavas Pesadas', 130: 'Lutador', 25: 'Terra'},
            'descricao': 'armas ageis de uma mao, golpes rapidos e precisos',
            'pool_tematico': ['clava', 'giro', 'golpe', 'impacto', 'combo', 'trovao', 'redemoinho',
                             'ventania', 'bambu', 'agil', 'preciso', 'rapido', 'duplo', 'crescente', 'danca'],
            'palavras_proibidas': ['punho', 'soco', 'chute', 'espada', 'lanca', 'machado', 'adaga',
                                  'flecha', 'magia', 'arcano', 'cobra', 'aguia', 'passaro', 
                                  'leao', 'veneno', 'sagrado', 'dardo', 'cajado', 'bastao'],
        },
    }
    
    def __init__(self, fp, ia):
        super().__init__('habilidades', fp, ia)
    
    def validar_nome(self, nome, cfg):
        n = nome.lower().strip()
        if len(n) < 3: return False, "Muito curto"
        if len(n.split()) < 2: return False, "Precisa de 2+ palavras"
        # Verifica se tem palavras em portugues de verdade
        palavras_pt = ['de', 'da', 'do', 'das', 'dos', 'com', 'sem', 'para', 'por', 'em', 'no', 'na', 'um', 'uma', 'o', 'a', 'os', 'as']
        palavras_nome = n.split()
        # Se TODAS as palavras sao ingles (terminam em ing, er, ou sao ingles conhecidas)
        sufixos_ingles = ['ing', 'er', 'ly', 'ed', 'tion', 'sion', 'ment', 'ness']
        palavras_ingles_conhecidas = ['the', 'and', 'of', 'to', 'in', 'is', 'it', 'you', 'that', 'was',
                                      'for', 'are', 'with', 'his', 'they', 'this', 'has', 'but', 'not',
                                      'raging', 'iron', 'thunder', 'bear', 'sonic', 'mighty', 'blazing',
                                      'unyielding', 'titanic', 'cruel', 'fist', 'blade', 'saber', 'strike',
                                      'slash', 'master', 'hunter', 'knight', 'lord', 'king', 'queen']
        
        # Se alguma palavra for ingles conhecida ou tiver sufixo ingles, rejeita
        for p in palavras_nome:
            if p in palavras_ingles_conhecidas:
                return False, f"'{p}' parece ingles, use portugues"
            for suf in sufixos_ingles:
                if p.endswith(suf) and len(p) > 4:
                    return False, f"'{p}' termina em '{suf}' (parece ingles)"
        
        # Bonus: pelo menos uma palavra deve ser portuguesa
        for p in palavras_nome:
            if p in palavras_pt:
                break
        else:
            # Verifica se alguma palavra parece portuguesa (termina em vogal + 'o', 'a', 'e')
            pass  # Muito generico, pode dar falso positivo
        
        for p in cfg.get('palavras_proibidas', []):
            if p in n: return False, f"Proibida: '{p}'"
        # Fingerprint check
        for ex in self.fp.data.get('exemplos_ruins', []):
            ex_palavras = set(ex.lower().split())
            nome_palavras = set(n.split())
            if len(ex_palavras & nome_palavras) >= 2:
                return False, f"Similar ao exemplo ruim '{ex}'"
        return True, "OK"
    
    def gerar_nomes(self, cfg, quantidade):
        """Gera nomes com detector de ingles e fallback tematico."""
        fp_ctx = self.fp.get_contexto()
        pool = ', '.join(cfg.get('pool_tematico', []))
        proib = ', '.join(cfg.get('palavras_proibidas', []))
        
        prompt_base = (
            f"Crie {quantidade*2} nomes em PORTUGUES para {cfg['nome']}.\n"
            f"Contexto: {cfg['descricao']}\n"
            f"Palavras disponiveis: {pool}\n"
            f"PROIBIDO: {proib}\n"
            f"IMPORTANTE: Nomes DEVEM ser em PORTUGUES BRASILEIRO.\n"
            f"EXEMPLO BOM: 'Soco Certeiro', 'Esquiva Felina', 'Gancho Poderoso'\n"
            f"EXEMPLO RUIM: 'Iron Fist', 'Raging Tiger', 'Thunder Punch' (INGLES!)\n"
            f"{fp_ctx}\n"
            f"\nResponda JSON: [{{\"nome\":\"...\"}},...]"
        )
        
        for t in range(5):
            if t > 0:
                # Reforca a cada tentativa
                prompt = prompt_base + f"\n\nTentativa {t+1}: VOCE DEVE gerar em PORTUGUES BRASILEIRO. Rejeitamos nomes em ingles."
            else:
                prompt = prompt_base
            
            r = self.ia.gerar(prompt, 0.9)
            dados = self.ia.extrair_json(r) if r else None
            if isinstance(dados, list): 
                # Filtra ingles aqui mesmo
                pt_words = ['de', 'da', 'do', 'das', 'dos', 'com', 'sem', 'para', 'em', 'no', 'na', 'um', 'uma']
                en_suffixes = ['ing', 'er', 'ly', 'ed', 'tion', 'ment']
                en_words = ['the', 'and', 'of', 'raging', 'iron', 'thunder', 'mighty', 'blazing', 'cruel', 'fist', 'blade', 'strike', 'master', 'slash', 'king', 'queen', 'lord', 'knight', 'bear', 'sonic', 'titanic']
                
                filtered = []
                for item in dados:
                    nome = item.get('nome', '') if isinstance(item, dict) else ''
                    if not nome: continue
                    n = nome.lower()
                    palavras = n.split()
                    is_english = False
                    for p in palavras:
                        if p in en_words: is_english = True; break
                        for suf in en_suffixes:
                            if p.endswith(suf) and len(p) > 4: is_english = True; break
                        if is_english: break
                    if not is_english:
                        filtered.append(item)
                
                if filtered:
                    print(f'    (filtrados {len(dados) - len(filtered)} nomes em ingles)')
                    return filtered
                else:
                    prompt = prompt_base + f"\n\nTODOS os nomes estavam em ingles. Use palavras do pool: {pool}"
            elif isinstance(dados, dict):
                for v in dados.values():
                    if isinstance(v, list): 
                        filtered = [x for x in v if isinstance(x, dict) and x.get('nome')]
                        if filtered: return filtered
        
        # Fallback: gera nomes do pool
        print(f'    (usando fallback do pool tematico)')
        pool_list = cfg.get('pool_tematico', ['Golpe', 'Ataque'])
        result = []
        prefixos = ['Soco', 'Chute', 'Golpe', 'Esquiva', 'Combo']
        for i in range(quantidade * 2):
            p = prefixos[i % len(prefixos)]
            s = random.choice(pool_list)
            nome = f'{p} {s.title()}'
            if nome not in [x.get('nome','') for x in result]:
                result.append({'nome': nome})
        return result
    def executar(self, dominio_nome='clavas_leves', quantidade=10, model='qwen2.5-coder:7b'):
        """Fluxo completo de geracao de habilidades."""
        cfg = self.DOMINIOS.get(dominio_nome)
        if not cfg:
            print(f"Dominio invalido. Disponiveis: {list(self.DOMINIOS.keys())}")
            return
        
        print(f'\n[MODULO: HABILIDADES] {cfg["nome"]} ({quantidade})\n')
        
        # 1. Slots estruturais (Python)
        slots = []
        for i in range(quantidade):
            hid = cfg['ids'][0] + i
            pct = i / quantidade
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
        
        print(f'  [Python] {len(slots)} slots\n')
        
        # 2. Nomes (IA + Python Gates + Fingerprint)
        print('  [Fase 1] Nomes...')
        nomes_finais = []
        tentativa = 0
        while len(nomes_finais) < quantidade and tentativa < 5:
            tentativa += 1
            batch = self.gerar_nomes(cfg, quantidade - len(nomes_finais) + 3)
            for item in batch:
                if isinstance(item, dict) and item.get('nome'):
                    nome = item['nome']
                    passa, motivo = self.validar_nome(nome, cfg)
                    if passa and nome.lower() not in [n.lower() for n in nomes_finais]:
                        nomes_finais.append(nome)
                        self.fp.registrar_acerto(nome)
                        if len(nomes_finais) >= quantidade: break
                    else:
                        self.fp.registrar_erro(nome, motivo)
            print(f'    Tentativa {tentativa}: {len(nomes_finais)}/{quantidade}')
        
        print(f'  [OK] {len(nomes_finais)} nomes\n')
        
        # 3. Sintese final
        print('  [Relatorio]')
        for i, n in enumerate(nomes_finais):
            print(f'    [{slots[i]["hab_id"]}] {n}')
        
        print(f'\n  Fingerprint: {len(self.fp.data.get("exemplos_bons",[]))} bons, {len(self.fp.data.get("exemplos_ruins",[]))} ruins')
        print('  [CONCLUIDO]')


# ============================================================
# MODULO: PROTOTIPO OTCLIENT (exemplo de como estender)
# ============================================================

class ModuloOTClient(ModuloCrew):
    """Gera/refatora layouts OTUI e scripts Lua do cliente."""
    
    def __init__(self, fp, ia):
        super().__init__('otclient', fp, ia)
    
    def executar(self, tarefa='criar_janela', **kwargs):
        """Gera um layout OTUI + script Lua."""
        print(f'\n[MODULO: OTCLIENT] {tarefa}\n')
        
        fp_ctx = self.fp.get_contexto()
        
        if tarefa == 'criar_janela':
            nome = kwargs.get('nome', 'MinhaJanela')
            prompt = (
                f"Crie um layout OTUI para uma janela chamada '{nome}' no OTClient.\n"
                f"Inclua: Panel, Button, Label, TextEdit, Image\n"
                f"{fp_ctx}\n\n"
                f"Responda JSON com:\n"
                f'{{"otui":"...codigo OTUI...","lua":"...codigo Lua...","descricao":"..."}}'
            )
            
            r = self.ia.gerar(prompt, 0.7)
            dados = self.ia.extrair_json(r) if r else None
            
            if isinstance(dados, dict):
                otui = dados.get('otui', '')
                lua = dados.get('lua', '')
                if otui:
                    path = f'E:\\Projeto MCR\\OTClient\\modules\\{nome}\\{nome}.otui'
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(otui)
                    print(f'  OTUI salvo: {path}')
                    self.fp.registrar_acerto(nome)
                if lua:
                    path = f'E:\\Projeto MCR\\OTClient\\modules\\{nome}\\{nome}.lua'
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(lua)
                    print(f'  Lua salvo: {path}')
            else:
                print('  ERRO: IA nao gerou JSON valido')
        
        print('  [CONCLUIDO]')


# ============================================================
# MODULO: SISTEMAS (projetar e implementar novos sistemas)
# ============================================================

class ModuloSistemas(ModuloCrew):
    """Projeta e implementa novos sistemas C++/Lua para o servidor."""
    
    def __init__(self, fp, ia):
        super().__init__('sistemas', fp, ia)
    
    def executar(self, tarefa='projetar', **kwargs):
        """Projeta ou implementa um novo sistema."""
        descricao = kwargs.get('descricao', '')
        linguagem = kwargs.get('linguagem', 'C++/Lua')
        
        print(f'\n[MODULO: SISTEMAS] {tarefa}: {descricao[:60]}...\n')
        fp_ctx = self.fp.get_contexto()
        
        if tarefa == 'projetar':
            # Modo texto: IA responde em texto, Python extrai info
            prompt = (
                "Projete um sistema para o servidor Tibia MCR.\n"
                f"Descricao: {descricao}\n"
                f"Linguagem: {linguagem}\n"
                f"{fp_ctx}\n\n"
                "Formato da resposta (siga exatamente):\n"
                "NOME: nome_do_sistema\n"
                "DESCRICAO: descricao em 1 linha\n"
                "ARQUIVOS: arquivo1.lua, arquivo2.cpp\n"
            )
        
        elif tarefa == 'implementar':
            prompt = (
                f"Implemente o sistema descrito.\n"
                f"Descricao: {descricao}\n"
                f"{fp_ctx}\n\n"
                f"Responda JSON com codigo completo:\n"
                f'{{"arquivos":[{{"path":"...","codigo":"..."}}],"instrucoes":"..."}}'
            )
        
        r = self.ia.gerar(prompt, 0.7)
        
        if r:
            # Extrai informacoes do texto
            nome = ''
            desc = ''
            arquivos = []
            for line in r.split('\n'):
                line = line.strip()
                if line.startswith('NOME:'):
                    nome = line[5:].strip()
                elif line.startswith('DESCRICAO:'):
                    desc = line[9:].strip()
                elif line.startswith('ARQUIVOS:'):
                    arqs = line[9:].strip()
                    arquivos = [a.strip() for a in arqs.split(',') if a.strip()]
            
            if nome:
                print(f'  Sistema: {nome}')
                print(f'  Descricao: {desc[:80]}')
                print(f'  Arquivos: {len(arquivos)}')
                self.fp.registrar_acerto(nome)
            else:
                print('  ERRO: IA nao seguiu o formato')
                self.fp.registrar_erro(descricao[:30], 'formato invalido')
        else:
            print('  ERRO: IA nao respondeu')
        
        print('  [CONCLUIDO]')


# ============================================================
# ORQUESTRADOR PRINCIPAL
# ============================================================

MODULOS = {
    'habilidades': ModuloHabilidades,
    'otclient': ModuloOTClient,
    'sistemas': ModuloSistemas,
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in MODULOS:
        print(__doc__)
        print(f"Modulos disponiveis: {', '.join(MODULOS.keys())}")
        print("Use: python mcr_crew.py <modulo> --help para ajuda do modulo")
        return 1
    
    nome_modulo = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    # Cada modulo tem seu proprio fingerprint
    tarefa = args[0] if args else 'default'
    fp = Fingerprint(nome_modulo, tarefa)
    ia = AILocal()
    
    modulo = MODULOS[nome_modulo](fp, ia)
    
    # Interpreta args como kwargs
    kwargs = {}
    for i, arg in enumerate(args):
        if '=' in arg:
            k, v = arg.split('=', 1)
            kwargs[k] = v
    
    if nome_modulo == 'habilidades':
        kwargs.setdefault('dominio_nome', args[0] if args else 'clavas_leves')
        kwargs.setdefault('quantidade', int(args[1]) if len(args) > 1 else 10)
        modulo.executar(**kwargs)
    
    elif nome_modulo == 'otclient':
        kwargs.setdefault('tarefa', args[0] if args else 'criar_janela')
        modulo.executar(**kwargs)
    
    elif nome_modulo == 'sistemas':
        kwargs.setdefault('tarefa', args[0] if args else 'projetar')
        modulo.executar(**kwargs)

if __name__ == '__main__':
    main()
