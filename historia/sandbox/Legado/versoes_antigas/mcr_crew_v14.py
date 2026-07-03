#!/usr/bin/env python3
"""
MCR CREW V14 — AUTO-INDEX + UNIVERSAL MODULES + SELF-LEARN
=============================================================
Escaneia um projeto INTEIRO, identifica padroes de codigo,
cria templates automaticamente, e APRENDE A SER VOCE.

Filosofia: o sistema nao tem modulos fixos.
Ele escaneia, descobre os padroes, e cria os proprios modulos.
Cada execucao melhora a indexacao e o aprendizado.
"""

import sys, os, json, re, hashlib, urllib.request, datetime
from collections import Counter

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR\sandbox\.crew_v14'
os.makedirs(BASE, exist_ok=True)

# ============================================================
# AUTO-INDEX ENGINE — Escaneia projetos e descobre padroes
# ============================================================

class AutoIndex:
    """
    Escaneia arquivos e descobre padroes.
    Identifica:
    - Estruturas que se repetem (templates em potencial)
    - Partes FIXAS vs PARTES VARIAVEIS
    - Relacoes entre arquivos
    """
    
    # Padroes de arquivo por tipo
    PADROES = {
        '.lua': {
            'nome': 'Lua Script',
            'categorias': ['npc', 'quest', 'monster', 'item', 'spell', 'action', 'movement', 'creaturescript', 'globalevent', 'talkaction'],
        },
        '.otui': {
            'nome': 'OTClient UI',
            'categorias': ['window', 'panel', 'module'],
        },
        '.cpp': {
            'nome': 'C++ Source',
            'categorias': ['system', 'component', 'function'],
        },
        '.hpp': {
            'nome': 'C++ Header',
            'categorias': ['header', 'interface'],
        },
        '.xml': {
            'nome': 'XML Config',
            'categorias': ['config', 'data', 'map'],
        },
    }
    
    @staticmethod
    def escanear(caminho):
        """Escaneia um diretorio e retorna estrutura de padroes."""
        resultado = {
            'caminho': caminho,
            'total_arquivos': 0,
            'arquivos_por_tipo': {},
            'padroes': {},  # tipo -> [(estrutura_comum, variacoes)]
            'modulos_descobertos': [],
        }
        
        for root, dirs, files in os.walk(caminho):
            # Pula diretorios irrelevantes
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in 
                      ('node_modules', '__pycache__', 'build', '.git', 'vc17')]
            
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext not in ('.lua', '.otui', '.cpp', '.hpp', '.xml'):
                    continue
                
                resultado['total_arquivos'] += 1
                resultado['arquivos_por_tipo'][ext] = resultado['arquivos_por_tipo'].get(ext, 0) + 1
                
                # Tenta identificar categoria do arquivo
                caminho_completo = os.path.join(root, f)
                try:
                    with open(caminho_completo, 'r', encoding='utf-8', errors='replace') as fp:
                        conteudo = fp.read()
                except:
                    continue
                
                # Detecta padroes no conteudo
                padroes_encontrados = AutoIndex._detectar_padroes(conteudo, ext, f)
                if padroes_encontrados:
                    chave = f"{ext}:{padroes_encontrados['categoria']}"
                    if chave not in resultado['padroes']:
                        resultado['padroes'][chave] = {
                            'categoria': padroes_encontrados['categoria'],
                            'extensao': ext,
                            'exemplos': [],
                            'estrutura_comum': None,
                            'template': None,
                            'blanks': [],
                        }
                    resultado['padroes'][chave]['exemplos'].append(conteudo[:2000])
        
        # Gera templates a partir dos padroes
        for chave, info in resultado['padroes'].items():
            if info['exemplos']:
                template, blanks = AutoIndex._criar_template(info['exemplos'])
                info['template'] = template
                info['blanks'] = blanks
                if blanks:
                    resultado['modulos_descobertos'].append({
                        'nome': chave,
                        'categoria': info['categoria'],
                        'extensao': info['extensao'],
                        'blanks': blanks,
                        'exemplos': len(info['exemplos']),
                    })
        
        return resultado
    
    @staticmethod
    def _detectar_padroes(conteudo, ext, nome_arquivo):
        """Detecta que tipo de arquivo eh esse."""
        resultado = {'categoria': 'unknown', 'tipo': ext}
        
        # Detecta categoria por padroes no conteudo
        if ext == '.lua':
            if re.search(r'NPC\s*\(|npc\s*=|:setSaudacao', conteudo, re.IGNORECASE):
                resultado['categoria'] = 'npc'
            elif re.search(r'Quest\s*\(|quest\s*=|:addObjetivo', conteudo, re.IGNORECASE):
                resultado['categoria'] = 'quest'
            elif re.search(r'Monster\s*\(|monster\s*=|:setHealth|:addLoot', conteudo, re.IGNORECASE):
                resultado['categoria'] = 'monster'
            elif re.search(r'Item\s*\(|item\s*=|:setType|:setAttack', conteudo, re.IGNORECASE):
                resultado['categoria'] = 'item'
            elif re.search(r'Spell\s*\(|spell\s*=|:setDamage|:setManaCost', conteudo, re.IGNORECASE):
                resultado['categoria'] = 'spell'
            elif re.search(r'TalkAction\s*\(|talkAction', conteudo):
                resultado['categoria'] = 'talkaction'
            elif re.search(r'CreatureEvent|creaturescript', conteudo, re.IGNORECASE):
                resultado['categoria'] = 'creaturescript'
            elif re.search(r'GlobalEvent|globalevent', conteudo, re.IGNORECASE):
                resultado['categoria'] = 'globalevent'
            elif re.search(r'Action\s*\(|:aid\(', conteudo):
                resultado['categoria'] = 'action'
            elif re.search(r'Movement\s*\(', conteudo):
                resultado['categoria'] = 'movement'
        
        elif ext == '.otui':
            if re.search(r'<Window', conteudo):
                resultado['categoria'] = 'window'
            elif re.search(r'<Module', conteudo):
                resultado['categoria'] = 'module'
            elif re.search(r'<Panel', conteudo):
                resultado['categoria'] = 'panel'
        
        elif ext in ('.cpp', '.hpp'):
            if re.search(r'class\s+\w+', conteudo):
                resultado['categoria'] = 'class'
            elif re.search(r'void\s+\w+\(', conteudo):
                resultado['categoria'] = 'function'
            elif re.search(r'system|manager|handler', nome_arquivo, re.IGNORECASE):
                resultado['categoria'] = 'system'
        
        return resultado
    
    @staticmethod
    def _criar_template(exemplos):
        """Cria um template a partir de exemplos."""
        if not exemplos:
            return None, []
        
        # Pega o exemplo mais curto como base
        base = min(exemplos, key=len)
        
        # Encontra candidatos a blank (strings e numeros)
        blanks = set()
        template = base
        
        for m in re.finditer(r'["\']([^"\']{3,})["\']', base):
            val = m.group(1)
            if not val.isdigit() and not val.startswith('--'):
                bk = f'_{len(blanks)}'
                # Usa o proprio valor como sugestao de nome
                bk_name = re.sub(r'[^a-zA-Z]', '_', val.lower())[:15]
                template = template.replace(f'"{val}"', f'{{{bk_name}}}', 1)
                blanks.add(bk_name)
        
        # Encontra numeros
        for m in re.finditer(r'(?<!\w)(\d+)(?!\w)', template):
            pass  # Numeros sao contexto-dependentes
        
        return template, list(blanks)


# ============================================================
# CEREBRO EXPANDIDO — Aprende, indexa, otimiza
# ============================================================

class CerebroExpanded:
    """
    Cerebro que nao so aprende, mas ENTENDE COMO aprendeu.
    - Mantem indexacao do projeto
    - Armazena templates criados
    - Mede performance de aprendizado
    - Sugere otimizacoes
    """
    
    def __init__(self):
        self.path = os.path.join(BASE, 'cerebro_v14.json')
        self.index_path = os.path.join(BASE, 'index.json')
        self.data = self._carregar()
        self.index = self._carregar_index()
    
    def _carregar(self):
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'meta': {'versoes': 0, 'acertos': 0, 'erros': 0, 'modulos_criados': 0, 'total_scan': 0},
            'modulos': {},
            'cache': {},
            'metricas_aprendizado': {
                'tempo_medio_por_blank': [],
                'taxa_acerto_por_modulo': {},
                'blanks_mais_faceis': [],
                'blanks_mais_dificeis': [],
            }
        }
    
    def _carregar_index(self):
        if os.path.exists(self.index_path):
            with open(self.index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'ultimo_scan': None, 'total_arquivos': 0, 'modulos_descobertos': []}
    
    def salvar(self):
        self.data['meta']['versoes'] += 1
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def salvar_index(self):
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)
    
    def aprender_modulo(self, nome, template, blanks, regras=None):
        if nome not in self.data['modulos']:
            self.data['modulos'][nome] = {
                'criado': str(datetime.datetime.now()),
                'uso': 0, 'acertos': 0, 'erros': 0,
                'template': template, 'blanks': blanks, 'regras': regras or {},
                'historico': {},
                'melhores_valores': {},
            }
            self.data['meta']['modulos_criados'] += 1
        mod = self.data['modulos'][nome]
        mod['uso'] += 1
        mod['template'] = template
        self.salvar()
    
    def registrar(self, modulo, acertou=True, valores=None):
        mod = self.data['modulos'].get(modulo)
        if not mod: return
        if acertou:
            mod['acertos'] += 1
            self.data['meta']['acertos'] += 1
            if valores:
                for k, v in valores.items():
                    mod['melhores_valores'][k] = v
        else:
            mod['erros'] += 1
            self.data['meta']['erros'] += 1
        self.salvar()
    
    def get_modulos_completos(self):
        """Retorna modulos que estao prontos pra uso (com acertos)."""
        return {k: v for k, v in self.data['modulos'].items() if v['acertos'] > 0}
    
    def analisar_aprendizado(self):
        """Analisa COMO o cerebro aprendeu e sugere melhorias."""
        mods = self.data['modulos']
        m = self.data['meta']
        metricas = self.data['metricas_aprendizado']
        
        analise = {
            'versao': m['versoes'],
            'total_acertos': m['acertos'],
            'total_erros': m['erros'],
            'taxa_geral': m['acertos'] / max(1, m['acertos'] + m['erros']) * 100,
            'modulos_aprendidos': len(self.get_modulos_completos()),
            'modulos_totais': len(mods),
            'modulos_sem_acerto': [k for k, v in mods.items() if v['acertos'] == 0],
            'modulos_mais_usados': sorted(mods.keys(), key=lambda k: mods[k]['uso'], reverse=True)[:5],
            'blanks_mais_comuns': {},
            'sugestoes': [],
        }
        
        # Sugestoes baseadas na analise
        if analise['modulos_sem_acerto']:
            analise['sugestoes'].append(f"Executar modulos sem acerto: {', '.join(analise['modulos_sem_acerto'][:3])}")
        
        if analise['taxa_geral'] < 50:
            analise['sugestoes'].append("Taxa de acerto baixa. Revisar templates ou usar args mais especificos.")
        
        return analise

    def resumo_aprendizado(self):
        """Resumo legivel do que o cerebro sabe."""
        m = self.data['meta']
        mods = self.data['modulos']
        
        linhas = []
        linhas.append(f'  Cerebro V{m["versoes"]}: {len(mods)} modulos, {m["acertos"]} acertos, {m["erros"]} erros')
        
        # Modulos aprendidos (com acertos)
        aprendidos = self.get_modulos_completos()
        if aprendidos:
            linhas.append(f'  Modulos DOMINADOS ({len(aprendidos)}):')
            for nome, info in sorted(aprendidos.items()):
                taxa = info['acertos'] / max(1, info['uso']) * 100
                linhas.append(f'    {nome}: taxa={taxa:.0f}% usos={info["uso"]} blanks={len(info["blanks"])}')
        
        # Modulos sem acerto
        sem_acerto = [k for k, v in mods.items() if v['acertos'] == 0]
        if sem_acerto:
            linhas.append(f'  Modulos EM APRENDIZADO ({len(sem_acerto)}):')
            for nome in sem_acerto[:5]:
                linhas.append(f'    {nome}: {mods[nome]["uso"]} tentativas, 0 acertos')
        
        # Indexacao
        idx = self.index
        if idx.get('ultimo_scan'):
            linhas.append(f'  Index: {idx["total_arquivos"]} arquivos, {len(idx.get("modulos_descobertos",[]))} modulos descobertos')
        
        return '\n'.join(linhas)


# ============================================================
# IA LOCAL
# ============================================================

class IALocal:
    def __init__(self, model='qwen2.5-coder:7b'):
        self.model = model
        self.cache = {}
    
    def gerar(self, prompt, temp=0.8):
        chave = hashlib.md5(prompt.encode()).hexdigest()
        if chave in self.cache:
            return self.cache[chave]
        try:
            data = json.dumps({'model':self.model,'prompt':prompt,'stream':False,
                'options':{'temperature':temp,'num_ctx':4096,'top_p':0.9}}).encode()
            req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.loads(r.read()).get('response','')
                self.cache[chave] = resp
                return resp
        except: return None


# ============================================================
# EXECUTOR UNIVERSAL
# ============================================================

class ExecutorUniversal:
    """Executa QUALQUER modulo com template + blanks."""
    
    def __init__(self, cerebro, ia):
        self.cerebro = cerebro
        self.ia = ia
    
    def executar(self, nome_mod, args=None):
        mod_info = self.cerebro.data['modulos'].get(nome_mod)
        if not mod_info:
            return False, f"Modulo '{nome_mod}' nao encontrado"
        
        template = mod_info['template']
        blanks = mod_info['blanks']
        regras = mod_info.get('regras', {})
        
        valores = {}
        
        # 1. Args da linha de comando
        if args:
            for i, b in enumerate(blanks):
                if i < len(args) and args[i]:
                    valores[b] = args[i]
        
        # 2. Melhores valores do historico
        for b in blanks:
            if b not in valores and b in mod_info.get('melhores_valores', {}):
                valores[b] = mod_info['melhores_valores'][b]
        
        # 3. IA para blanks criativos
        blanks_rest = [b for b in blanks if b not in valores]
        if blanks_rest:
            prompt = f"Preencha para {nome_mod}:\n" + "\n".join(f"  {b}: " for b in blanks_rest)
            prompt += "\n\nFormato:\n" + "\n".join(f"{b}: valor" for b in blanks_rest)
            
            r = self.ia.gerar(prompt, 0.7)
            if r:
                for line in r.split('\n'):
                    line = line.strip()
                    for b in blanks_rest:
                        if line.lower().startswith(b.lower() + ':'):
                            v = line.split(':', 1)[1].strip()
                            if v and v.lower() not in ('none', 'null', ''):
                                valores[b] = v
        
        # 4. Completar faltantes com padroes
        for b in blanks:
            if b not in valores:
                valores[b] = f"valor_{b}"
        
        # Preencher template
        try:
            resultado = template.format(**valores)
        except KeyError as e:
            return False, f"Template: campo {e} faltando"
        
        # Salvar
        nome_arquivo = valores.get('nome', nome_mod).lower().replace(' ', '_').replace('"','')
        ext = '.otui' if '.otui' in template else '.lua'
        path = os.path.join(r'E:\Projeto MCR\sandbox', f'v14_{nome_mod}_{nome_arquivo}{ext}')
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(resultado)
        
        self.cerebro.registrar(nome_mod, True, valores)
        return True, f"Salvo: {path}"


# ============================================================
# MAIN — Orquestrador Final
# ============================================================

def main():
    cerebro = CerebroExpanded()
    ia = IALocal()
    executor = ExecutorUniversal(cerebro, ia)
    
    if len(sys.argv) < 2:
        print('='*60)
        print('  MCR CREW V14 — AUTO-INDEX + UNIVERSAL MODULES')
        print('  O sistema que APRENDE A SER VOCE')
        print('='*60)
        print()
        print('COMANDOS:')
        print(f'  python {sys.argv[0]} --scan <caminho>    Escaneia projeto, descobre modulos')
        print(f'  python {sys.argv[0]} --executar <modulo> [args...]  Executa modulo com IA')
        print(f'  python {sys.argv[0]} --aprender <modulo> <template> <blanks...>')
        print(f'  python {sys.argv[0]} --status            Mostra estado do cerebro')
        print(f'  python {sys.argv[0]} --analisar          Analisa aprendizado')
        print(f'  python {sys.argv[0]} --run-all           Executa TODOS os modulos')
        print()
        
        # Mostra modulos disponiveis
        if cerebro.data['modulos']:
            print('MODULOS DISPONIVEIS:')
            for nome, info in sorted(cerebro.data['modulos'].items()):
                status = 'APRENDIDO' if info['acertos'] > 0 else 'novo'
                print(f'  {nome}: {len(info["blanks"])} blanks [{status}]')
        else:
            print('Nenhum modulo ainda. Use --scan ou --aprender.')
        print()
        print(cerebro.resumo_aprendizado())
        return
    
    cmd = sys.argv[1]
    
    if cmd == '--scan' and len(sys.argv) >= 3:
        caminho = sys.argv[2]
        print(f'\n[SCAN] Escaneando: {caminho}')
        resultado = AutoIndex.escanear(caminho)
        
        print(f'  Arquivos: {resultado["total_arquivos"]}')
        for ext, qtd in resultado['arquivos_por_tipo'].items():
            print(f'  {ext}: {qtd}')
        
        # Cria modulos para cada padrao descoberto
        for mod in resultado['modulos_descobertos']:
            if mod.get('template') and mod.get('blanks'):
                cerebro.aprender_modulo(mod['nome'], mod['template'], mod['blanks'])
                print(f'  [Modulo] {mod["nome"]}: {len(mod["blanks"])} blanks')
        
        cerebro.index = resultado
        cerebro.salvar_index()
        print(f'  Total modulos criados: {len(resultado["modulos_descobertos"])}')
    
    elif cmd == '--executar' and len(sys.argv) >= 3:
        nome_mod = sys.argv[2]
        args = sys.argv[3:]
        sucesso, msg = executor.executar(nome_mod, args)
        print(f'\n[EXEC] {msg}')
    
    elif cmd == '--run-all':
        modulos = cerebro.data['modulos']
        if not modulos:
            print('[RUN-ALL] Nenhum modulo para executar')
            return
        
        print(f'\n[RUN-ALL] Executando {len(modulos)} modulos...')
        resultados = {'sucesso': 0, 'falha': 0}
        for nome in sorted(modulos.keys()):
            sucesso, msg = executor.executar(nome)
            if sucesso:
                resultados['sucesso'] += 1
                print(f'  [OK] {nome}')
            else:
                resultados['falha'] += 1
                print(f'  [ERRO] {nome}: {msg}')
        print(f'\n  Resultado: {resultados["sucesso"]} sucesso, {resultados["falha"]} falha')
    
    elif cmd == '--status':
        print('\n[STATUS]')
        print(cerebro.resumo_aprendizado())
    
    elif cmd == '--analisar':
        print('\n[ANALISE]')
        analise = cerebro.analisar_aprendizado()
        for k, v in analise.items():
            print(f'  {k}: {v}')
    
    elif cmd == '--aprender' and len(sys.argv) >= 5:
        nome = sys.argv[2]
        template = sys.argv[3]
        blanks = sys.argv[4:]
        cerebro.aprender_modulo(nome, template, blanks)
        print(f'[APRENDER] Modulo "{nome}" criado com {len(blanks)} blanks')
    
    else:
        print(f'[ERRO] Comando invalido: {cmd}')

if __name__ == '__main__':
    main()
