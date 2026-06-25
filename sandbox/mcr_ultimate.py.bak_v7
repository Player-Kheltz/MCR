#!/usr/bin/env python3
"""
MCR CREW — ARGS GENERATOR + EXECUTOR
=======================================
O cerebro que alimenta o template engine.

1. Voce da uma ideia: "Quest sobre dragoes em Eridanus"
2. IA local pensa: "Preciso de X NPCs, Y monsters, Z itens com stats W"
3. Template engine executa TUDO com args prontos
4. Resultado: sistema completo sem intervencao manual

Uso: python mcr_ultimate.py "ideia"
     python mcr_ultimate.py "Uma quest sobre os dragoes ancestrais de Eridanus"
"""

import sys, os, json, re, urllib.request, hashlib, subprocess

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR\sandbox'

# ============================================================
# ARGS GENERATOR — IA que planeja os args
# ============================================================

class ArgsGenerator:
    """
    Recebe uma ideia e gera args COMPLETOS para o template engine.
    - Decide QUANTOS NPCs, monsters, items criar
    - Escolhe NOMES contextualizados
    - Calcula STATS balanceados (HP, atk, def)
    - Define RELACOES entre entidades
    """
    
    def __init__(self):
        self.cache = {}
    
    def gerar(self, prompt, temp=0.8):
        chave = hashlib.md5(prompt.encode()).hexdigest()
        if chave in self.cache: return self.cache[chave]
        try:
            data = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
                'options':{'temperature':temp,'num_ctx':4096,'top_p':0.95}}).encode()
            req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req, timeout=180) as r:
                resp = json.loads(r.read()).get('response','')
                self.cache[chave] = resp
                return resp
        except: return None
    
    def planejar_sistema(self, ideia):
        """
        Recebe uma ideia e retorna um PLANO de execucao.
        O plano diz EXATAMENTE o que criar com quais args.
        """
        prompt = f"""Crie um plano DETALHADO para um sistema de quest no jogo Tibia.

IDEIA: {ideia}

Seu trabalho: planejar TODOS os elementos necessarios e calcular EXATAMENTE os args.

Responda EXATAMENTE neste formato (sem explicacoes):

SISTEMA: nome_do_sistema

NPCS:
  npc1: NomeDoNPC | saudacao: "fala do npc" | item_id: 101 | item_preco: 75
  npc2: NomeDoNPC2 | saudacao: "fala do npc2" | item_id: 102 | item_preco: 100

MONSTERS:
  monster1: NomeDoMonstro | hp: 300 | atk: 35 | def: 10 | loot_id: 41001 | loot_chance: 0.8
  monster2: NomeDoMonstro2 | hp: 600 | atk: 28 | def: 25 | loot_id: 41002 | loot_chance: 0.9

ITEMS:
  item1: NomeItem | id: 41001 | tipo: quest | atk: 0 | def: 0 | peso: 2
  item2: NomeItem2 | id: 41002 | tipo: quest | atk: 0 | def: 0 | peso: 1
  item3: NomeItem3 | id: 41003 | tipo: armor | atk: 5 | def: 25 | peso: 3

SPELLS:
  spell1: NomeSpell | elemento: holy | dano: 150 | mana: 60 | cd: 7

REGRAS DE BALANCEAMENTO:
- Monstro comum: HP 200-400, atk 20-40, def 5-15
- Mini-boss: HP 400-800, atk 25-45, def 15-30
- Boss final: HP 800-2000, atk 40-70, def 20-40
- Quest item: tipo quest, atk 0, def 0, peso 1-5
- Item recompensa: tipo armor/weapon, stats proporcionais ao nivel
- Spell de recompensa: dano 100-200, mana 40-80, cd 6-10

CONEXOES:
  - npc1 inicia a quest
  - monster1 dropa item1 (quest)
  - monster2 dropa item2 (quest)
  - npc2 finaliza a quest
  - spell1 e item3 sao recompensas

Mundo: Eridanus, uma cidade-estado magica fundada ha 300 anos por tres herois.

IMPORTANTE: Use APENAS numeros para item_id, loot_id. Nao use simbolos de moeda."""
        
        r = self.gerar(prompt, 0.75)
        return self._parse_plano(r) if r else self._plano_padrao(ideia)
    
    def _parse_plano(self, texto):
        """Extrai o plano do texto da IA."""
        plano = {
            'sistema': '',
            'npcs': [],
            'monsters': [],
            'items': [],
            'spells': [],
            'conexoes': [],
        }
        
        current_section = None
        for line in texto.split('\n'):
            line = line.strip()
            if not line: continue
            
            upper = line.upper()
            if upper.startswith('SISTEMA:'):
                plano['sistema'] = line.split(':', 1)[1].strip()
                current_section = None
            elif upper.startswith('NPCS:'):
                current_section = 'npcs'
            elif upper.startswith('MONSTERS:'):
                current_section = 'monsters'
            elif upper.startswith('ITEMS:'):
                current_section = 'items'
            elif upper.startswith('SPELLS:'):
                current_section = 'spells'
            elif upper.startswith('CONEXOES:'):
                current_section = 'conexoes'
            elif current_section and line.startswith('  '):
                # Linha de item
                if current_section == 'npcs':
                    m = re.match(r'\s*\w+:\s*(\w+)\s*\|\s*saudacao:\s*"([^"]*)"\s*\|\s*item_id:\s*(\d+)\s*\|\s*item_preco:\s*([\d.]+)', line)
                    if m:
                        plano['npcs'].append({
                            'nome': m.group(1), 'saudacao': m.group(2),
                            'item_id': m.group(3), 'item_preco': m.group(4)
                        })
                elif current_section == 'monsters':
                    m = re.match(r'\s*\w+:\s*(\w+)\s*\|\s*hp:\s*(\d+)\s*\|\s*atk:\s*(\d+)\s*\|\s*def:\s*(\d+)\s*\|\s*loot_id:\s*(\d+)\s*\|\s*loot_chance:\s*([\d.]+)', line)
                    if m:
                        plano['monsters'].append({
                            'nome': m.group(1), 'hp': m.group(2), 'atk': m.group(3),
                            'def': m.group(4), 'loot_id': m.group(5), 'loot_chance': m.group(6)
                        })
                elif current_section == 'items':
                    m = re.match(r'\s*\w+:\s*(\w+)\s*\|\s*id:\s*(\d+)\s*\|\s*tipo:\s*(\w+)\s*\|\s*atk:\s*(\d+)\s*\|\s*def:\s*(\d+)\s*\|\s*peso:\s*(\d+)', line)
                    if m:
                        plano['items'].append({
                            'nome': m.group(1), 'id': m.group(2), 'tipo': m.group(3),
                            'atk': m.group(4), 'def': m.group(5), 'peso': m.group(6)
                        })
                elif current_section == 'spells':
                    m = re.match(r'\s*\w+:\s*(\w+)\s*\|\s*elemento:\s*(\w+)\s*\|\s*dano:\s*(\d+)\s*\|\s*mana:\s*(\d+)\s*\|\s*cd:\s*(\d+)', line)
                    if m:
                        plano['spells'].append({
                            'nome': m.group(1), 'elemento': m.group(2),
                            'dano': m.group(3), 'mana': m.group(4), 'cd': m.group(5)
                        })
                elif current_section == 'conexoes':
                    plano['conexoes'].append(line)
        
        return plano
    
    def _plano_padrao(self, ideia):
        """Fallback se IA nao seguir o formato."""
        nome = re.sub(r'[^a-zA-Z]', '', ideia)[:15]
        return {
            'sistema': nome,
            'npcs': [{'nome': nome + 'NPC', 'saudacao': 'Ola!', 'item_id': '101', 'item_preco': '50'}],
            'monsters': [{'nome': nome + 'Monstro', 'hp': '200', 'atk': '25', 'def': '10', 'loot_id': '41001', 'loot_chance': '0.5'}],
            'items': [{'nome': nome + 'Item', 'id': '41001', 'tipo': 'quest', 'atk': '0', 'def': '0', 'peso': '1'}],
            'spells': [],
            'conexoes': [],
        }


# ============================================================
# EXECUTOR — Roda mcr_ultimate.py com os args gerados
# ============================================================

class ExecutorAutomatico:
    """Executa o template engine com os args do generator."""
    
    def __init__(self):
        self.ultimate_path = os.path.join(BASE, 'mcr_ultimate.py')
    
    def executar(self, plano):
        """Executa o plano completo."""
        sistema = plano['sistema'] or 'Sistema'
        print(f'\n{"="*60}')
        print(f'  EXECUTANDO PLANO: {sistema}')
        print(f'  {len(plano["npcs"])} NPCs, {len(plano["monsters"])} Monsters, {len(plano["items"])} Items, {len(plano["spells"])} Spells')
        print(f'{"="*60}')
        
        resultados = []
        
        # NPCs
        for npc in plano['npcs']:
            cmd = f'python "{self.ultimate_path}" npc "{npc["nome"]}" "{npc["saudacao"]}" {npc["item_id"]} {npc["item_preco"]}'
            print(f'\n[GERANDO NPC] {npc["nome"]}...')
            resultados.append(subprocess.run(cmd, capture_output=True, text=True, shell=True))
        
        # Monsters
        for mon in plano['monsters']:
            cmd = f'python "{self.ultimate_path}" monster "{mon["nome"]}" {mon["hp"]} {mon["atk"]} {mon["def"]} {mon["loot_id"]} {mon["loot_chance"]}'
            print(f'\n[GERANDO MONSTER] {mon["nome"]}...')
            resultados.append(subprocess.run(cmd, capture_output=True, text=True, shell=True))
        
        # Items
        for item in plano['items']:
            cmd = f'python "{self.ultimate_path}" item "{item["nome"]}" {item["id"]} {item["tipo"]} {item["atk"]} {item["def"]} {item["peso"]}'
            print(f'\n[GERANDO ITEM] {item["nome"]}...')
            resultados.append(subprocess.run(cmd, capture_output=True, text=True, shell=True))
        
        # Spells
        for spell in plano['spells']:
            cmd = f'python "{self.ultimate_path}" spell "{spell["nome"]}" {spell["elemento"]} {spell["dano"]} {spell["mana"]} {spell["cd"]}'
            print(f'\n[GERANDO SPELL] {spell["nome"]}...')
            resultados.append(subprocess.run(cmd, capture_output=True, text=True, shell=True))
        
        # Relatorio
        sucessos = sum(1 for r in resultados if r.returncode == 0)
        total = len(resultados)
        print(f'\n{"="*60}')
        print(f'  PLANO EXECUTADO: {sucessos}/{total} sucesso')
        print(f'  Sistema: {sistema}')
        print(f'  Arquivos gerados: {total}')
        print(f'{"="*60}')
        
        return sucessos, total


# ============================================================
# MAIN — Ciclo completo
# ============================================================

def main():
    if len(sys.argv) < 2:
        print('MCR CREW — ARGS GENERATOR + EXECUTOR')
        print()
        print('Da uma ideia, o sistema planeja e executa TUDO.')
        print()
        print(f'Uso: python {sys.argv[0]} "sua ideia de quest"')
        print(f'Ex:  python {sys.argv[0]} "Dragoes ancestrais em Eridanus"')
        print(f'     python {sys.argv[0]} "Uma guilda de ladroes na cidade"')
        print(f'     python {sys.argv[0]} "O despertar de um deus antigo"')
        return
    
    ideia = ' '.join(sys.argv[1:])
    
    print(f'\n{"="*60}')
    print(f'  MCR CREW — CICLO COMPLETO')
    print(f'  Ideia: {ideia}')
    print(f'{"="*60}')
    
    # FASE 1: Args Generator planeja
    print(f'\n[FASE 1] Args Generator planejando...')
    generator = ArgsGenerator()
    plano = generator.planejar_sistema(ideia)
    
    print(f'  Sistema: {plano["sistema"] or "Desconhecido"}')
    print(f'  NPCs planejados: {len(plano["npcs"])}')
    for n in plano['npcs']:
        print(f'    {n.get("nome","?")}: {n.get("saudacao","")[:40]}')
    print(f'  Monsters planejados: {len(plano["monsters"])}')
    for m in plano['monsters']:
        print(f'    {m.get("nome","?")}: HP={m.get("hp","?")} ATK={m.get("atk","?")}')
    print(f'  Items planejados: {len(plano["items"])}')
    for i in plano['items']:
        print(f'    {i.get("nome","?")}: tipo={i.get("tipo","?")} ID={i.get("id","?")}')
    print(f'  Spells planejados: {len(plano["spells"])}')
    
    # FASE 2: Executor roda com args
    print(f'\n[FASE 2] Executando plano...')
    executor = ExecutorAutomatico()
    sucessos, total = executor.executar(plano)
    
    # FASE 3: Relatorio
    print(f'\n{"="*60}')
    print(f'  CICLO COMPLETO: {ideia}')
    print(f'  Status: {sucessos}/{total} gerados com sucesso')
    if total > 0:
        taxa = sucessos / total * 100
        print(f'  Taxa de sucesso: {taxa:.0f}%')
        print(f'  Qualidade: {"EXCELENTE" if taxa >= 80 else "BOA" if taxa >= 50 else "PRECISA REVISAO"}')
    print(f'{"="*60}')
    
    # Mostra comando executados
    print(f'\nPara ver os arquivos:')
    print(f'  dir {BASE}\\ult_*')
    print(f'\nPara recriar manualmente com args diferentes:')
    print(f'  python {sys.argv[0]} "nova ideia"')

if __name__ == '__main__':
    main()
