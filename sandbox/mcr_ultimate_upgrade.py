#!/usr/bin/env python3
"""
MCR-DevIA — ULTIMATE UPGRADE: Rumo aos 100%
==============================================
Fecha os 4 gaps finais:
1. RAG nos arquivos REAIS do projeto (nao so KG)
2. C++ templates avancados (classes, metodos, inheritance)
3. Geracao multi-estagio (rascunho -> refinamento)
4. Auto-scan + aprendizado automatico
"""

import sys, os, json, re, urllib.request, hashlib, datetime

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR'
SANDBOX = r'E:\Projeto MCR\sandbox'
KG_PATH = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')

# ============================================================
# 1. RAG NOS ARQUIVOS REAIS — Busca no codigo fonte
# ============================================================

class RAGReal:
    """Busca nos ARQUIVOS do projeto, nao so no KG."""
    
    def buscar(self, pergunta, max_arquivos=3):
        """Busca arquivos relevantes para a pergunta."""
        palavras = set(re.findall(r'\w+', pergunta.lower()))
        resultados = []
        
        # Diretorios para buscar
        dirs = [
            os.path.join(BASE, 'Canary', 'src'),
            os.path.join(BASE, 'Canary', 'data-canary', 'scripts', 'MCR'),
        ]
        
        for diretorio in dirs:
            if not os.path.exists(diretorio): continue
            for root, dirs2, files in os.walk(diretorio):
                for f in files:
                    if not f.endswith(('.lua', '.cpp', '.hpp')): continue
                    path = os.path.join(root, f)
                    try:
                        with open(path, 'r', encoding='utf-8', errors='replace') as fp:
                            conteudo = fp.read()
                        score = sum(1 for p in palavras if len(p) > 3 and p in conteudo.lower())
                        if score > 0:
                            resultados.append((score, path, conteudo[:500]))
                    except: pass
        
        resultados.sort(key=lambda x: -x[0])
        return resultados[:max_arquivos]
    
    def contexto_para_prompt(self, pergunta):
        """Gera contexto enriquecido com codigo real."""
        arquivos = self.buscar(pergunta)
        if not arquivos: return ''
        ctx = ['\n[CODIGO RELEVANTE DO PROJETO:]']
        for score, path, conteudo in arquivos:
            rel_path = path.replace(BASE, '')
            ctx.append(f'\n--- {rel_path} (score:{score}) ---')
            ctx.append(conteudo[:300])
        return '\n'.join(ctx)


# ============================================================
# 2. C++ TEMPLATES AVANCADOS (V12 puro)
# ============================================================

TEMPLATE_CPP_CLASS = '''#ifndef {nome_upper}_HPP
#define {nome_upper}_HPP

#include <string>
#include <vector>
#include <memory>

class {nome} {{
public:
    {nome}() = default;
    ~{nome}() = default;
    
    // Metodos
    {metodos}
    
private:
    {atributos}
}};

#endif // {nome_upper}_HPP
'''

def gerar_cpp_avancado(desc):
    """Gera classe C++ completa com V12."""
    print(f'\n[C++ AVANCADO] {desc[:60]}...')
    
    # IA gera metodos e atributos
    r = ia(f"Crie os metodos e atributos para uma classe C++ que: {desc}\n\nResponda:\nMETODOS: (declaracoes separadas por ;)\nATRIBUTOS: (declaracoes separadas por ;)")
    if not r: return None
    
    metodos = ''
    atributos = ''
    for line in r.split('\n'):
        if line.upper().startswith('METODOS:'):
            metodos = line.split(':',1)[1].strip()
        elif line.upper().startswith('ATRIBUTOS:'):
            atributos = line.split(':',1)[1].strip()
    
    nome = re.search(r'(\w+)', desc)
    nome = nome.group(1) if nome else 'Feature'
    nome = nome.capitalize() + 'Handler'
    
    codigo = TEMPLATE_CPP_CLASS.format(
        nome=nome, nome_upper=nome.upper(),
        metodos=metodos or 'void execute();',
        atributos=atributos or 'int status_;',
    )
    
    path = os.path.join(SANDBOX, 'autogerados', f'{nome}.hpp')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(codigo)
    print(f'  [OK] {path}')
    return path


# ============================================================
# 3. GERACAO MULTI-ESTAGIO (rascunho -> refinamento)
# ============================================================

def gerar_multi_estagio(desc):
    """Gera em 3 estagios: rascunho, revisao, versao final."""
    print(f'\n[MULTI-ESTAGIO] {desc[:60]}...')
    
    # Estagio 1: Rascunho (IA livre)
    print(f'  Estagio 1: Rascunho...')
    rascunho = ia(f"Crie um rascunho para: {desc}. Pode ser imperfeito.", 0.8)
    if not rascunho: return None
    
    # Estagio 2: Auto-revisao (IA critica o proprio trabalho)
    print(f'  Estagio 2: Auto-revisao...')
    revisao = ia(f"Analise criticamente este rascunho e aponte 3 problemas:\n\n{rascunho[:1000]}", 0.5)
    
    # Estagio 3: Versao final (IA melhora com base na critica)
    print(f'  Estagio 3: Versao final...')
    prompt = f"Versao FINAL melhorada para: {desc}\n\nRASCUNHO ORIGINAL:\n{rascunho}\n\nCRITICAS:\n{revisao}\n\nVersao Final:"
    final = ia(prompt, 0.6)
    
    if final:
        path = os.path.join(SANDBOX, 'autogerados', f'multi_{desc[:10].replace(" ","_")}.txt')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f'# {desc}\n## Rascunho\n{rascunho}\n## Revisao\n{revisao}\n## Final\n{final}')
        print(f'  [OK] {path}')
    return final


# ============================================================
# 4. AUTO-SCAN + APRENDIZADO AUTOMATICO
# ============================================================

class AutoLearner:
    """Escaneia logs, erros, e aprende sozinho."""
    
    def __init__(self):
        self.kg_path = KG_PATH
        self.kg = self._load_kg()
    
    def _load_kg(self):
        if os.path.exists(self.kg_path):
            with open(self.kg_path, 'r', encoding='utf-8', errors='replace') as f:
                return json.load(f)
        return {'licoes': [], 'versoes': 0, 'metricas': {'licoes': 0}}
    
    def _save_kg(self):
        self.kg['versoes'] += 1
        self.kg['metricas']['licoes'] = len(self.kg['licoes'])
        with open(self.kg_path, 'w', encoding='utf-8') as f:
            json.dump(self.kg, f, ensure_ascii=False, indent=2)
    
    def scan_logs(self):
        """Escaneia logs do servidor e aprende erros novos."""
        logs_path = os.path.join(BASE, 'Canary', 'startup_log.txt')
        if not os.path.exists(logs_path): return 0
        
        with open(logs_path, 'r', encoding='utf-8', errors='replace') as f:
            log = f.read()
        
        # Encontra erros
        erros = re.findall(r'(Erro[^.]*\.)', log)
        aprendidos = 0
        
        for erro in erros[:5]:
            erro_limpo = erro.strip()[:100]
            # Verifica se ja conhece
            conhecido = False
            for l in self.kg['licoes']:
                if l.get('erro','')[:30] in erro_limpo:
                    conhecido = True; break
            if not conhecido:
                self.kg['licoes'].append({
                    'id': f'A{len(self.kg["licoes"])+1:04d}',
                    'erro': erro_limpo,
                    'causa': 'Descoberto por auto-scan de logs',
                    'solucao': 'Analise manual necessaria',
                    'ctx': 'autoscan',
                    'usos': 0,
                })
                aprendidos += 1
        
        if aprendidos:
            self._save_kg()
            print(f'  [AUTO-APRENDIDO] {aprendidos} novos erros dos logs')
        return aprendidos
    
    def scan_dir(self, diretorio):
        """Escaneia um diretorio por padroes de codigo."""
        encontrados = 0
        for root, dirs, files in os.walk(diretorio):
            for f in files:
                if not f.endswith('.lua'): continue
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8', errors='replace') as fp:
                        conteudo = fp.read()
                    # Procura padroes de erro
                    if 'FIXME' in conteudo or 'TODO' in conteudo:
                        encontrados += 1
                except: pass
        
        print(f'  [SCAN] {encontrados} arquivos com FIXME/TODO')
        return encontrados


# ============================================================
# IA LOCAL
# ============================================================

def ia(prompt, temp=0.5):
    try:
        d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
            'options':{'temperature':temp,'num_ctx':4096}}).encode()
        r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(r,timeout=120).read()).get('response','')
    except: return None


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('MCR-DevIA ULTIMATE UPGRADE')
        print()
        print('Comandos:')
        print(f'  {sys.argv[0]} --rag "pergunta"        RAG nos arquivos reais')
        print(f'  {sys.argv[0]} --cpp "desc"            Gera C++ avancado')
        print(f'  {sys.argv[0]} --multi "desc"           Geracao multi-estagio')
        print(f'  {sys.argv[0]} --scan                  Auto-scan + aprendizado')
        print(f'  {sys.argv[0]} --tudo                  Tudo em sequencia')
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == '--rag':
        pergunta = ' '.join(sys.argv[2:])
        print(f'\n[RAG REAL] {pergunta[:60]}...')
        rag = RAGReal()
        ctx = rag.contexto_para_prompt(pergunta)
        if ctx:
            print(ctx[:500])
        else:
            print('  Nenhum arquivo relevante encontrado')
    
    elif cmd == '--cpp':
        gerar_cpp_avancado(' '.join(sys.argv[2:]))
    
    elif cmd == '--multi':
        gerar_multi_estagio(' '.join(sys.argv[2:]))
    
    elif cmd == '--scan':
        print('\n[AUTO-LEARN] Escaneando...')
        learner = AutoLearner()
        l = learner.scan_logs()
        d = learner.scan_dir(os.path.join(BASE, 'Canary', 'data-canary', 'scripts', 'MCR'))
        print(f'  Logs: {l} novos erros | Dir: {d} FIXMEs')
    
    elif cmd == '--tudo':
        print(f'\n{"="*60}')
        print(f'  ULTIMATE UPGRADE — TUDO EM SEQUENCIA')
        print(f'{"="*60}')
        
        # 1. Scan e aprendizado
        print('\n[1/4] Auto-scan...')
        AutoLearner().scan_logs()
        
        # 2. RAG demo
        print('\n[2/4] RAG demo...')
        rag = RAGReal()
        ctx = rag.contexto_para_prompt('MCR SPA habilidades')
        print(f'  {ctx[:200]}...' if ctx else '  (vazio)')
        
        # 3. C++ avancado
        print('\n[3/4] C++ avancado...')
        gerar_cpp_avancado('gerenciar itens de quest com ID, nome, tipo e peso')
        
        # 4. Multi-estagio
        print('\n[4/4] Multi-estagio...')
        gerar_multi_estagio('descricao do sistema de crafting do MCR')
        
        print(f'\n{"="*60}')
        print(f'  ULTIMATE UPGRADE CONCLUIDO!')
        print(f'{"="*60}')
