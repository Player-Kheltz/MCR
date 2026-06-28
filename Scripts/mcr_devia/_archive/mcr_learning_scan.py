#!/usr/bin/env python3
"""
MCR-DevIA — LEARNING SCAN (O PASSO ZERO QUE FALTOU)
======================================================
Em vez de procurar ERROS, ele PROCURA PADRÕES.
Escaneia o projeto inteiro e extrai:
  - Como os NPCs reais sao escritos (quais funcoes usam)
  - Como os monsters reais sao escritos
  - Como os itens reais sao escritos
  - Como as quests reais sao escritas
  - Como os spells reais sao escritos

Depois: ATUALIZA os templates do mcr_ultimate.py
Depois: ALIMENTA o Knowledge Graph com esse conhecimento
Depois: GERA codigo que USA as mesmas funcoes que o projeto real
"""

import sys, os, json, re, urllib.request, datetime

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR'
SANDBOX = r'E:\Projeto MCR\sandbox'
KG_PATH = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')
ULTIMATE_PATH = os.path.join(SANDBOX, 'mcr_ultimate.py')

def ia(prompt):
    try:
        d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
            'options':{'temperature':0.4,'num_ctx':4096}}).encode()
        r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(r,timeout=120).read()).get('response','')
    except Exception as e:
        print(f"[Fix] ERRO: {e}")


class LearningScan:
    """
    Escaneia o projeto e EXTRAI CONHECIMENTO.
    Nao procura erros. Procura PADROES.
    """
    
    def __init__(self):
        self.padroes = {}  # tipo -> {funcao: contaminado}
        self.arquivos_por_tipo = {}
    
    def escanear(self, diretorios=None):
        """Escaneia diretorios e identifica padroes de codigo."""
        if not diretorios:
            diretorios = [
                os.path.join(BASE, 'Canary', 'data-canary', 'scripts', 'MCR'),
                os.path.join(BASE, 'Canary', 'data', 'scripts'),
                os.path.join(BASE, 'Canary', 'data', 'npclib'),
                os.path.join(BASE, 'Canary', 'data', 'monster'),
            ]
        
        print(f'\n[LEARNING SCAN] Escaneando {len(diretorios)} diretorios...')
        total_arquivos = 0
        
        for diretorio in diretorios:
            if not os.path.exists(diretorio):
                print(f'  [!] {diretorio} nao existe')
                continue
            
            for root, dirs, files in os.walk(diretorio):
                for f in files:
                    if not f.endswith('.lua'): continue
                    total_arquivos += 1
                    path = os.path.join(root, f)
                    
                    try:
                        with open(path, 'r', encoding='utf-8', errors='replace') as fp:
                            conteudo = fp.read()
                    except Exception as e:
                        print(f"[Fix] ERRO: {e}")
                    
                    # Detecta tipo do arquivo
                    tipo = self._detectar_tipo(conteudo, f)
                    if not tipo: continue
                    
                    # Extrai funcoes usadas
                    funcoes = self._extrair_funcoes(conteudo, tipo)
                    
                    if tipo not in self.padroes:
                        self.padroes[tipo] = {}
                        self.arquivos_por_tipo[tipo] = []
                    
                    for func in funcoes:
                        self.padroes[tipo][func] = self.padroes[tipo].get(func, 0) + 1
                    
                    self.arquivos_por_tipo[tipo].append(path)
        
        print(f'  {total_arquivos} arquivos escaneados')
        print(f'  Tipos encontrados: {list(self.arquivos_por_tipo.keys())}')
        for tipo, arquivos in self.arquivos_por_tipo.items():
            print(f'    {tipo}: {len(arquivos)} arquivos, {len(self.padroes[tipo])} funcoes unicas')
        
        return self.padroes
    
    def _detectar_tipo(self, conteudo, nome_arquivo):
        """Detecta o tipo de arquivo baseado no conteudo."""
        if re.search(r'NPC\(|npc:setSaudacao|npc:addItem', conteudo): return 'npc'
        if re.search(r'Monster\(|mon:setHealth|mon:addLoot', conteudo): return 'monster'
        if re.search(r'Item\(|item:setType', conteudo): return 'item'
        if re.search(r'Quest\(|quest:setDescricao', conteudo): return 'quest'
        if re.search(r'Spell\(|spell:setDamage', conteudo): return 'spell'
        if re.search(r'TalkAction\(', conteudo): return 'talkaction'
        if re.search(r'CreatureEvent\(', conteudo): return 'creaturescript'
        return None
    
    def _extrair_funcoes(self, conteudo, tipo):
        """Extrai funcoes SET e ADD usadas no tipo."""
        prefixos = {
            'npc': 'npc:', 'monster': 'mon:', 'item': 'item:',
            'quest': 'quest:', 'spell': 'spell:', 'talkaction': 'talk:',
            'creaturescript': 'cs:',
        }
        prefixo = prefixos.get(tipo, '')
        if not prefixo: return []
        
        funcoes = set()
        for m in re.finditer(rf'{prefixo}(set\w+|add\w+)\(', conteudo):
            funcoes.add(m.group(1))
        return funcoes
    
    def gerar_template(self, tipo):
        """
        Gera um template NOVO baseado nos padroes reais do projeto.
        Usa as funcoes que aparecem em MAIS de 1 arquivo.
        """
        if tipo not in self.padroes:
            print(f'  Nao ha dados para {tipo}')
            return None, []
        
        # Pega funcoes que aparecem em 2+ arquivos (padrao confirmado)
        funcoes_comuns = {
            func: count for func, count in self.padroes[tipo].items()
            if count >= 2 and func.startswith('set')
        }
        
        # Pega funcoes que aparecem em 1 arquivo (padrao possivel)
        funcoes_possiveis = {
            func: count for func, count in self.padroes[tipo].items()
            if count == 1 and func.startswith('set')
        }
        
        print(f'\n  Funcoes CONFIRMADAS para {tipo} (2+ arquivos):')
        for func, count in sorted(funcoes_comuns.items(), key=lambda x: -x[1]):
            print(f'    {func}: {count} arquivos')
        
        # IA gera o template — tipo DINAMICO, placeholders com $
        tipo_title = tipo.title()
        prompt = (
            f"Crie um template Lua para '{tipo}'.\n"
            f"\n"
            f"Funcoes CONFIRMADAS (usadas em 2+ arquivos):\n"
            + "\n".join(f"- {f}()" for f in funcoes_comuns) + "\n"
            + (("\nFuncoes POSSIVEIS (usadas em 1 arquivo):\n"
               + "\n".join(f"- {f}()" for f in funcoes_possiveis)) if funcoes_possiveis else "")
            + f"""
Formato esperado (use $placeholder para variaveis):
-- {tipo}: $nome
local {tipo} = {tipo_title}($nome)
$... funcoes CONFIRMADAS acima, adaptadas para {tipo}
print("{tipo} $nome carregado.")

REGRAS:
- Crie o objeto do tipo '{tipo}', NAO 'Monster'
- Use APENAS as funcoes listadas (existem no projeto real)
- Nao invente funcoes"""
        )
        
        template = ia(prompt)
        if not template:
            print('  IA nao gerou template')
            return None, []
        
        template = re.sub(r'```\w*\n?', '', template).strip()
        
        blanks = re.findall(r'\{(\w+)\}', template)
        
        print(f'\n  Template gerado com {len(blanks)} blanks:')
        print(f'  {template[:200]}...')
        
        return template, blanks
    
    def alimentar_kg(self):
        """Alimenta o Knowledge Graph com os padroes descobertos."""
        print(f'\n  Alimentando Knowledge Graph...')
        
        if not os.path.exists(KG_PATH):
            print('  KG nao encontrado')
            return
        
        with open(KG_PATH, 'r', encoding='utf-8', errors='replace') as f:
            kg = json.load(f)
        
        for tipo, funcoes in self.padroes.items():
            funcoes_lista = [f for f, c in sorted(funcoes.items(), key=lambda x: -x[1])[:10]]
            
            kg['licoes'].append({
                'id': f'L{len(kg["licoes"])+1:04d}',
                'erro': f'Padroes de codigo para {tipo} no MCR',
                'causa': f'Funcoes reais usadas em {len(self.arquivos_por_tipo.get(tipo,[]))} arquivos',
                'solucao': f'Usar: {", ".join(funcoes_lista[:5])}',
                'ctx': 'learning_scan',
                'usos': 0,
            })
        
        kg['versoes'] += 1
        kg['metricas']['licoes'] = len(kg['licoes'])
        
        with open(KG_PATH, 'w', encoding='utf-8') as f:
            json.dump(kg, f, ensure_ascii=False, indent=2)
        
        print(f'  KG atualizado: {len(kg["licoes"])} licoes')


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    scan = LearningScan()
    
    # 1. Escaneia padroes reais
    scan.escanear()
    
    # 2. Alimenta KG
    scan.alimentar_kg()
    
    # 3. Gera templates melhores
    print(f'\n{"="*60}')
    print('  GERANDO TEMPLATES BASEADOS EM PADROES REAIS')
    print(f'{"="*60}')
    
    for tipo in ['npc', 'monster', 'item', 'quest', 'spell']:
        print(f'\n--- {tipo.upper()} ---')
        template, blanks = scan.gerar_template(tipo)
    
    print(f'\n{"="*60}')
    print('  LEARNING SCAN CONCLUIDO!')
    print(f'  Proximo passo: ATUALIZAR mcr_ultimate.py com os novos templates')
    print(f'{"="*60}')
    
    # Salva resultado
    result_path = os.path.join(SANDBOX, '.mcr_learning_scan.json')
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump({
            'padroes': {k: dict(v) for k, v in scan.padroes.items()},
            'arquivos_por_tipo': {k: v for k, v in scan.arquivos_por_tipo.items()},
        }, f, ensure_ascii=False, indent=2)
    print(f'Resultado salvo em: {result_path}')
