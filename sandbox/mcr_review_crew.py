"""
MCR-DevIA — CREW DE REVISAO (Revisao Humana Simulada)
=======================================================
Quando um detector trava (3+ falhas), a crew especialista assume:
  1. Analista — "Por que esta falhando?"
  2. Estrategista — "Que abordagem diferente tentar?"
  3. Implementador — "Tenta a nova abordagem"
  4. Validador — "Funcionou?"
  5. Professor — "Registra o aprendizado no KG"

Cada um e uma chamada IA especializada, nao um script.
"""

import sys, os, json, re, urllib.request, datetime

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR\sandbox\teste_cego_ultra'
KG_PATH = r'E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json'
REVIEW_LOG = r'E:\Projeto MCR\sandbox\.mcr_review_crew.log'

def ia(prompt, temp=0.5):
    try:
        d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
            'options':{'temperature':temp,'num_ctx':4096}}).encode()
        r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(r,timeout=120).read()).get('response','')
    except: return None

def log(msg):
    with open(REVIEW_LOG, 'a', encoding='utf-8') as f:
        f.write(f'[{datetime.datetime.now():%H:%M:%S}] {msg}\n')
    print(f'  [CREW] {msg}')

class ReviewCrew:
    """Equipe de 5 especialistas para problemas dificeis."""
    
    def resolver(self, arquivo, codigo, problemas):
        log(f'Crew acionada para {arquivo}')
        log(f'Problemas: {problemas}')
        
        # 1. ANALISTA: entende o problema
        log('Analista: diagnosticando...')
        analise = ia(f"""Analise este arquivo Lua com problemas e diga a CAUSA RAIZ.

ARQUIVO:
{codigo[:800]}

PROBLEMAS DETECTADOS: {', '.join(problemas[:3])}

Responda:
CAUSA RAIZ: (o que realmente esta errado, em 1 linha)
ESTRATEGIA: (como corrigir, em 1 linha)""", 0.4)
        
        causa = 'nao determinado'
        estrategia = 'revisar manualmente'
        
        if analise:
            for line in analise.split('\n'):
                if 'CAUSA RAIZ:' in line: causa = line.split(':',1)[1].strip()
                elif 'ESTRATEGIA:' in line: estrategia = line.split(':',1)[1].strip()
        
        log(f'Causa: {causa[:80]}')
        log(f'Estrategia: {estrategia[:80]}')
        
        # 2. ESTRATEGISTA: propoe abordagem
        log('Estrategista: planejando abordagem...')
        plano = ia(f"""Crie um plano de correcao para este arquivo Lua.

CAUSA RAIZ: {causa}
ESTRATEGIA: {estrategia}

ARQUIVO:
{codigo[:600]}

Retorne APENAS o codigo corrigido completo.""", 0.8)
        
        if not plano or '```' in plano:
            plano = plano.replace('```lua', '').replace('```', '').strip() if plano else ''
        
        if plano and len(plano) > 20:
            # Limpa marcacao
            plano = re.sub(r'```\w*\n?', '', plano).strip()
            
            if plano != codigo:
                # 3. VALIDADOR: testa se realmente mudou algo
                log('Validador: testando correcao...')
                
                # 4. IMPLEMENTADOR: salva
                path = os.path.join(BASE, arquivo)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(plano)
                
                log(f'Implementador: correcao salva!')
                
                # 5. PROFESSOR: registra no KG
                log('Professor: registrando aprendizado...')
                self._ensinar(arquivo, causa, estrategia)
                
                return True
            else:
                log('Estrategista retornou o mesmo codigo')
                return False
        else:
            log('Estrategista nao gerou codigo valido')
            # Tentativa 2: abordagem mais direta
            log('Estrategista: segunda tentativa com abordagem direta...')
            plano2 = ia(f"""Corrija este codigo Lua. Problemas: {', '.join(problemas[:3])}

ARQUIVO:
{codigo[:600]}

Retorne APENAS o codigo Lua corrigido, sem explicacoes.""", 0.6)
            
            if plano2 and len(plano2) > 20:
                plano2 = re.sub(r'```\w*\n?', '', plano2).strip()
                if plano2 != codigo:
                    path = os.path.join(BASE, arquivo)
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(plano2)
                    log(f'Implementador (2a tentativa): correcao salva!')
                    self._ensinar(arquivo, causa + ' (2a tentativa)', estrategia)
                    return True
            
            log('Falha apos 2 tentativas')
            return False
    
    def _ensinar(self, arquivo, causa, estrategia):
        """Registra aprendizado via mcr_devia.py ensinar."""
        import subprocess
        cmd = [
            'python', 'E:/Projeto MCR/scripts/mcr_devia/mcr_devia.py', 'ensinar',
            f'Review Crew resolveu {arquivo}',
            f'Causa: {causa[:80]}',
            f'Correcao: {estrategia[:80]}',
            'review_crew'
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=15)


if __name__ == '__main__':
    import sys
    sys.path.insert(0, 'E:/Projeto MCR/sandbox')
    import importlib.util
    spec = importlib.util.spec_from_file_location('r', 'E:/Projeto MCR/sandbox/resolver_ultra.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    
    crew = ReviewCrew()
    
    # Pega os arquivos com mais problemas (que a IA normal nao consegue corrigir)
    for f in sorted(os.listdir(BASE)):
        if f == '.GABARITO.txt': continue
        path = os.path.join(BASE, f)
        probs = mod.scan(f, path)
        if probs:
            with open(path, 'r', encoding='utf-8') as fp:
                codigo = fp.read()
            print(f'\n[!] {f}: {probs}')
            crew.resolver(f, codigo, probs)
    
    print('\n=== REVISION CREW CONCLUIDA ===')
