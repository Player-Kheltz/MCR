#!/usr/bin/env python3
"""
MCR CREW V18 — PIPELINE FINAL
================================
Uma unica execucao que:
1. GERA NPC + Itens + Quest (templates V15)
2. CRIA LORE profundo (V16)
3. PONTUA qualidade (V17)
4. APRENDE com o resultado (cerebro)
5. RELATA tudo

Uso: python mcr_crew_v18.py "Nome do Sistema"
"""

import sys, os, json, re, hashlib, urllib.request, datetime, subprocess

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR\sandbox'
CEREBRO_PATH = r'E:\Projeto MCR\sandbox\.crew_v18_cerebro.json'

# ============================================================
# TEMPLATES V18 (unificados)
# ============================================================

TEMPLATES = {
    'npc': ('-- NPC: {nome}\nlocal npc = NPC("{nome}")\nnpc:setSaudacao("{saudacao}")\nnpc:addItem({item_id}, {item_preco})\nprint("NPC {nome} carregado.")',
            ['nome','saudacao','item_id','item_preco']),
    'item': ('-- Item: {nome}\nlocal item = Item({id}, "{nome}")\nitem:setType("{tipo}")\nitem:setWeight({peso})\nprint("Item {nome} carregado.")',
             ['nome','id','tipo','peso']),
    'quest': ('-- Quest: {nome}\nlocal quest = Quest("{nome}")\nquest:setDescricao("{descricao}")\nquest:addObjetivo("{objetivo}")\nquest:addRecompensa("xp", {xp})\nprint("Quest {nome} carregada.")',
              ['nome','descricao','objetivo','xp']),
}

# ============================================================
# QUALITY MATRIX (corrigido)
# ============================================================

class Quality:
    @staticmethod
    def pontuar_texto(texto):
        """Pontua texto de 0 a 100 sem usar regex complexo."""
        if not texto or len(texto) < 10: return 10
        palavras = texto.split()
        pontos = 50
        
        if len(palavras) > 30: pontos += 20
        elif len(palavras) > 15: pontos += 10
        
        # Palavras que indicam riqueza
        ricas = ['segredo','antigo','poder','historia','lendario','misterio',
                'sabedoria','destino','profecia','honra','esperanca']
        for r in ricas:
            if r in texto.lower(): pontos += 5
        
        if '.' in texto and texto.count('.') >= 2: pontos += 10
        if '"' in texto: pontos += 10
        
        return min(100, max(0, pontos))

# ============================================================
# IA LOCAL
# ============================================================

class IA:
    def __init__(self):
        self.cache = {}
    
    def gerar(self, prompt, temp=0.8):
        chave = hashlib.md5(prompt.encode()).hexdigest()
        if chave in self.cache: return self.cache[chave]
        try:
            data = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
                'options':{'temperature':temp,'num_ctx':4096,'top_p':0.95}}).encode()
            req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.loads(r.read()).get('response','')
                self.cache[chave] = resp
                return resp
        except: return None
    
    def preencher(self, modulo, blanks, contexto=''):
        prompt = f"Preencha para {modulo}:\n{contexto}\n"
        for b in blanks: prompt += f"  {b}: "
        prompt += "\n\nFormato:\n" + "\n".join(f"{b}: valor" for b in blanks)
        
        r = self.gerar(prompt, 0.7)
        vals = {}
        if r:
            for line in r.split('\n'):
                line = line.strip()
                for b in blanks:
                    if line.lower().startswith(b.lower() + ':'):
                        v = line.split(':', 1)[1].strip()
                        if v and v.lower() not in ('none','null',''):
                            vals[b] = v
        return vals

# ============================================================
# LORE SIMPLIFICADO (parser robusto)
# ============================================================

def gerar_lore(ia, tipo, nome, contexto=''):
    """Gera lore com parser simples e robusto."""
    prompt = f"Crie LORE para {tipo} '{nome}' em Eridanus.\n{contexto}\n\n"
    prompt += "Responda em paragrafos simples:\n"
    prompt += f"HISTORIA: (2-3 frases sobre {nome})\n"
    if tipo == 'NPC':
        prompt += "PERSONALIDADE: (3 adjetivos)\nSAUDACAO: (uma fala curta)\nSEGREDO: (algo que esconde)\n"
    elif tipo == 'ITEM':
        prompt += "ORIGEM: (de onde veio)\nPODER: (o que faz)\n"
    elif tipo == 'QUEST':
        prompt += "CONTEXTO: (por que acontece)\nREVELACAO: (o que se descobre)\n"
    
    r = ia.gerar(prompt, 0.85)
    if not r: return {}
    
    # Parse: procura "CAMPO: texto" padrao
    lore = {}
    for line in r.split('\n'):
        line = line.strip()
        if ':' in line:
            partes = line.split(':', 1)
            campo = partes[0].strip().upper()
            valor = partes[1].strip()
            if campo in ('HISTORIA','PERSONALIDADE','SAUDACAO','SEGREDO','ORIGEM','PODER','CONTEXTO','REVELACAO'):
                if len(valor) > 10:
                    lore[campo] = valor[:500]
    
    return lore

# ============================================================
# CEREBRO PERSISTENTE
# ============================================================

class Cerebro:
    def __init__(self):
        self.data = self._load()
    
    def _load(self):
        if os.path.exists(CEREBRO_PATH):
            with open(CEREBRO_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'versoes': 0, 'acertos': 0, 'erros': 0, 'modulos': {}, 'lore_criado': 0}
    
    def save(self):
        self.data['versoes'] += 1
        with open(CEREBRO_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def registrar_modulo(self, nome, info):
        self.data['modulos'][nome] = info
        self.data['acertos'] += 1
        self.save()

# ============================================================
# PIPELINE PRINCIPAL
# ============================================================

def pipeline(nome_sistema):
    ia = IA()
    cerebro = Cerebro()
    
    print(f'\n{"="*60}')
    print(f'  V18 PIPELINE: {nome_sistema}')
    print(f'  Cerebro V{cerebro.data["versoes"]}: {cerebro.data["acertos"]} acertos, {cerebro.data["erros"]} erros')
    print(f'{"="*60}')
    
    resultados = []
    
    # === FASE 1: GERAR NPC ===
    print(f'\n[1/5] Gerando NPC...')
    blanks_npc = TEMPLATES['npc'][1]
    nome_npc = nome_sistema.replace(' ', '')[:20]
    
    # IA preenche blanks criativos
    vals_npc = ia.preencher('npc', blanks_npc, f"Nome base: {nome_npc}")
    if not vals_npc.get('nome'): vals_npc['nome'] = nome_npc + 'NPC'
    if not vals_npc.get('saudacao'): vals_npc['saudacao'] = 'Ola!'
    if not vals_npc.get('item_id'): vals_npc['item_id'] = '30001'
    if not vals_npc.get('item_preco'): vals_npc['item_preco'] = '100'
    
    # Gera lore pro NPC
    lore_npc = gerar_lore(ia, 'NPC', vals_npc['nome'])
    qualidade = 0
    if lore_npc:
        vals_npc['saudacao'] = lore_npc.get('SAUDACAO', vals_npc['saudacao'])
        qualidade = Quality.pontuar_texto(str(lore_npc))
        print(f'  NPC: {vals_npc["nome"]} (lore: {qualidade}/100)')
        if 'PERSONALIDADE' in lore_npc: print(f'  Personalidade: {lore_npc["PERSONALIDADE"][:80]}')
        if 'SEGREDO' in lore_npc: print(f'  Segredo: {lore_npc["SEGREDO"][:80]}')
    
    # Salva NPC
    template_npc = TEMPLATES['npc'][0]
    codigo_npc = template_npc.format(**vals_npc)
    path_npc = os.path.join(BASE, f'v18_{nome_sistema[:15]}_npc.lua')
    with open(path_npc, 'w', encoding='utf-8') as f: f.write(codigo_npc)
    print(f'  [OK] {path_npc}')
    
    cerebro.registrar_modulo('npc_' + vals_npc['nome'], vals_npc)
    resultados.append(('NPC', vals_npc['nome'], qualidade))
    
    # === FASE 2: GERAR ITENS ===
    print(f'\n[2/5] Gerando itens...')
    itens_gerados = []
    for nome_item in [f'{nome_sistema[:10]}_Artefato1', f'{nome_sistema[:10]}_Artefato2']:
        vals_item = ia.preencher('item', ['nome','id','tipo','peso'], f"Nome: {nome_item}")
        if not vals_item.get('nome'): vals_item['nome'] = nome_item
        if not vals_item.get('id'): vals_item['id'] = str(30001 + len(itens_gerados))
        if not vals_item.get('tipo'): vals_item['tipo'] = 'quest'
        if not vals_item.get('peso'): vals_item['peso'] = '5'
        
        lore_item = gerar_lore(ia, 'ITEM', vals_item['nome'])
        qual_item = Quality.pontuar_texto(str(lore_item)) if lore_item else 0
        print(f'  Item: {vals_item["nome"]} (lore: {qual_item}/100)')
        if 'ORIGEM' in lore_item: print(f'  Origem: {lore_item["ORIGEM"][:80]}')
        
        codigo_item = TEMPLATES['item'][0].format(**vals_item)
        path_item = os.path.join(BASE, f'v18_{nome_sistema[:15]}_item_{len(itens_gerados)}.lua')
        with open(path_item, 'w', encoding='utf-8') as f: f.write(codigo_item)
        print(f'  [OK] {path_item}')
        itens_gerados.append(vals_item['nome'])
        resultados.append(('Item', vals_item['nome'], qual_item))
    
    # === FASE 3: GERAR QUEST ===
    print(f'\n[3/5] Gerando quest...')
    vals_quest = ia.preencher('quest', ['nome','descricao','objetivo','xp'],
        f"Sistema: {nome_sistema}, NPC: {vals_npc['nome']}, Itens: {', '.join(itens_gerados)}")
    if not vals_quest.get('nome'): vals_quest['nome'] = nome_sistema[:20]
    if not vals_quest.get('descricao'): vals_quest['descricao'] = f'Complete o sistema {nome_sistema}'
    if not vals_quest.get('objetivo'): vals_quest['objetivo'] = f'Encontre os artefatos'
    if not vals_quest.get('xp'): vals_quest['xp'] = '1000'
    
    lore_quest = gerar_lore(ia, 'QUEST', vals_quest['nome'], f"NPC: {vals_npc['nome']}, Itens: {', '.join(itens_gerados)}")
    qual_quest = Quality.pontuar_texto(str(lore_quest)) if lore_quest else 0
    print(f'  Quest: {vals_quest["nome"]} (lore: {qual_quest}/100)')
    if 'CONTEXTO' in lore_quest: print(f'  Contexto: {lore_quest["CONTEXTO"][:80]}')
    if 'REVELACAO' in lore_quest: print(f'  Revelacao: {lore_quest["REVELACAO"][:80]}')
    
    codigo_quest = TEMPLATES['quest'][0].format(**vals_quest)
    path_quest = os.path.join(BASE, f'v18_{nome_sistema[:15]}_quest.lua')
    with open(path_quest, 'w', encoding='utf-8') as f: f.write(codigo_quest)
    print(f'  [OK] {path_quest}')
    resultados.append(('Quest', vals_quest['nome'], qual_quest))
    
    # === FASE 4: PONTUACAO GERAL ===
    print(f'\n[4/5] Pontuacao geral...')
    nota_total = sum(r[2] for r in resultados) / max(1, len(resultados))
    print(f'  Nota media: {nota_total:.0f}/100')
    for tipo, nome, nota in resultados:
        barra = '*' * (nota // 10) + '-' * (10 - nota // 10)
        print(f'  {tipo}: [{barra}] {nota}/100 - {nome}')
    
    # === FASE 5: RELATORIO ===
    print(f'\n[5/5] Relatorio final...')
    cerebro.save()
    print(f'\n{"="*60}')
    print(f'  PIPELINE CONCLUIDO: {nome_sistema}')
    print(f'  Cerebro agora: V{cerebro.data["versoes"]}, {cerebro.data["acertos"]} acertos')
    print(f'  Arquivos: {len(resultados)}')
    print(f'  Nota geral: {nota_total:.0f}/100')
    print(f'{"="*60}')
    
    return nota_total


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    nome = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else 'Legado Perdido'
    pipeline(nome)
