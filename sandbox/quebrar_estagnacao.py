"""Quebra de estagnacao: quando IA retorna same code 3x, forcar mutacao"""
import os, re, json, urllib.request, sys

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR\sandbox\teste_cego_ultra'
SCANNER = r'E:\Projeto MCR\sandbox\resolver_ultra.py'
KG_PATH = r'E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json'

def ia(prompt, temp=0.7):
    try:
        d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
            'options':{'temperature':temp,'num_ctx':4096}}).encode()
        r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(r,timeout=60).read()).get('response','')
    except: return None

# Rastreia quantas vezes cada arquivo teve "same code"
same_code_counter = {}

def tentar_correcao_mutante(arquivo, path):
    """Tenta corrigir um arquivo com abordagem mutante apos 3 falhas."""
    global same_code_counter
    
    if arquivo not in same_code_counter:
        same_code_counter[arquivo] = 0
    
    with open(path, 'r', encoding='utf-8') as f:
        original = f.read()
    
    same_code_counter[arquivo] += 1
    tentativa = same_code_counter[arquivo]
    
    print(f'[{arquivo}] Tentativa {tentativa} de correcao...')
    
    if tentativa <= 3:
        # Tenta correcao normal (o scanner ja faz isso)
        return False
    
    # Apos 3 falhas, tenta MUTACAO
    print(f'  -> Mutacao ativada!')
    
    prompt = f"""O codigo abaixo NAO pode ser corrigido pelas tentativas normais.

ARQUIVO COM PROBLEMA:
{original[:800]}

Crie uma VERSAO MODIFICADA que resolva os problemas de forma DIFERENTE.
Use abordagem completamente nova. Nao apenas conserte — REESCREVA de forma criativa.

Retorne APENAS o codigo corrigido."""
    
    mutacao = ia(prompt, 0.9)  # Temperatura alta = mais criativo
    
    if mutacao and len(mutacao) > 20:
        mutacao = mutacao.replace('```lua', '').replace('```', '').strip()
        if mutacao != original:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(mutacao)
            print(f'  [MUTADO] Nova versao salva!')
            same_code_counter[arquivo] = 0  # Reset
            return True
    
    # Se mutacao tambem falhou, marca como "precisa revisao humana"
    with open(os.path.join(os.path.dirname(KG_PATH), '.mcr_precisa_revisao.txt'), 'a') as f:
        f.write(f'{arquivo}: nao foi possivel corrigir apos {tentativa} tentativas\n')
    print(f'  [REVISAO] Arquivado para revisao humana')
    return False

if __name__ == '__main__':
    print('=== QUEBRA DE ESTAGNACAO ===')
    print(f'Escanendo {BASE}...')
    
    # Importa scanner
    sys.path.insert(0, os.path.dirname(SCANNER))
    import importlib.util
    spec = importlib.util.spec_from_file_location('r', SCANNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    
    for f in sorted(os.listdir(BASE)):
        if f == '.GABARITO.txt': continue
        path = os.path.join(BASE, f)
        try:
            problemas = mod.scan(f, path)
            if problemas:
                print(f'[!] {f}: {problemas}')
                tentar_correcao_mutante(f, path)
            else:
                print(f'[OK] {f}')
        except Exception as e:
            print(f'[ERRO] {f}: {e}')
    
    print('=== CICLO CONCLUIDO ===')
