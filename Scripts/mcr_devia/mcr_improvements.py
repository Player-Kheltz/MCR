#!/usr/bin/env python3
"""
MCR-DevIA — IMPROVEMENTS: Runtime + C++ + Tests + Multi-file
===============================================================
Fecha as 4 lacunas principais de uma vez.
"""

import sys, os, json, re, urllib.request, subprocess, datetime

OLLAMA_URL = 'http://localhost:11434/api/generate'
SANDBOX = r'E:\Projeto MCR\sandbox'
OUT_DIR = os.path.join(SANDBOX, 'autogerados')
os.makedirs(OUT_DIR, exist_ok=True)

def ia(prompt, temp=0.5):
    try:
        d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
            'options':{'temperature':temp,'num_ctx':4096}}).encode()
        r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(r,timeout=120).read()).get('response','')
    except: return None

# ============================================================
# 1. RUNTIME LOOP — Executa, captura erro, IA corrige
# ============================================================

def corrigir_runtime(path, max_tentativas=5):
    """Executa um script. Se falhar, IA corrige e executa de novo."""
    print(f'\n[RUNTIME LOOP] Testando {os.path.basename(path)}...')
    
    for t in range(max_tentativas):
        r = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=15)
        
        if r.returncode == 0:
            print(f'  [OK] Execucao bem-sucedida!')
            print(f'  Output: {r.stdout.strip()[:200]}')
            return True
        
        erro = r.stderr.strip()[:500] or r.stdout.strip()[:500]
        print(f'  [ERRO] Tentativa {t+1}: {erro[:100]}...')
        
        # IA analisa erro e sugere correcao
        with open(path, 'r') as f:
            codigo = f.read()
        
        prompt = f"""O script Python abaixo tem um erro em tempo de execucao:

ERRO: {erro}

CODIGO:
{codigo}

Corrija o erro. Retorne APENAS o codigo completo corrigido."""
        
        correcao = ia(prompt, 0.4)
        if not correcao:
            print('  [FALHA] IA nao respondeu')
            return False
        
        # Extrai codigo
        correcao = re.sub(r'```python\n?', '', correcao).strip()
        correcao = re.sub(r'```\n?', '', correcao).strip()
        
        # Valida sintaxe
        try:
            compile(correcao, 'corrigido.py', 'exec')
            with open(path, 'w') as f:
                f.write(correcao)
            print(f'  [CORRIGIDO] Tentativa {t+1}')
        except SyntaxError as e:
            print(f'  [SINTAXE] {e.msg}')
            continue
    
    print(f'  [FALHA] Apos {max_tentativas} tentativas')
    return False


# ============================================================
# 2. C++ TEMPLATES (V12 aplicado a C++)
# ============================================================

TEMPLATE_CPP = '''// {descricao}
// Gerado pelo MCR-DevIA
#ifndef {header_guard}
#define {header_guard}

{class_def}

#endif // {header_guard}
'''

TEMPLATE_CPP_IMPL = '''// {descricao}
// Gerado pelo MCR-DevIA
#include "{header_name}.hpp"

{impl_def}
'''

def gerar_cpp(desc):
    """Gera um arquivo C++ .hpp + .cpp usando V12."""
    print(f'\n[C++ TEMPLATE] {desc[:60]}...')
    
    # IA gera a definicao da classe/funcao
    classe = ia(f"Crie uma classe ou funcao C++ que: {desc}. Retorne APENAS o codigo C++ completo.")
    if not classe: return
    
    # Extrai nome
    nome_match = re.search(r'(?:class|void|int|bool|std::string)\s+(\w+)', classe)
    nome = nome_match.group(1) if nome_match else 'Feature'
    header_guard = f'{nome.upper()}_HPP'
    
    # Monta .hpp
    hpp = TEMPLATE_CPP.format(descricao=desc, header_guard=header_guard, class_def=classe)
    
    # Valida sintaxe basica (so checa se tem chaves)
    if hpp.count('{') != hpp.count('}'):
        print('  [ERRO] Chaves desbalanceadas')
        return
    
    path_hpp = os.path.join(OUT_DIR, f'{nome}.hpp')
    with open(path_hpp, 'w') as f:
        f.write(hpp)
    print(f'  [OK] {path_hpp}')
    
    # Gera .cpp (implementacao)
    impl = ia(f"Crie a implementacao para: {classe}. Retorne APENAS o codigo.")
    if impl:
        cpp = TEMPLATE_CPP_IMPL.format(descricao=desc, header_name=nome, impl_def=impl)
        path_cpp = os.path.join(OUT_DIR, f'{nome}.cpp')
        with open(path_cpp, 'w') as f:
            f.write(cpp)
        print(f'  [OK] {path_cpp}')
    
    return path_hpp


# ============================================================
# 3. AUTO-TESTES — Gera testes junto com codigo
# ============================================================

def gerar_com_testes(desc, linguagem='python'):
    """Gera codigo + teste juntos."""
    print(f'\n[AUTO-TESTE] {desc[:60]} ({linguagem})')
    
    if linguagem == 'python':
        funcao = ia(f"Crie uma funcao Python que: {desc}. Retorne APENAS o codigo da funcao.")
        if not funcao: return
        
        # Extrai nome da funcao
        nome = re.search(r'def (\w+)', funcao)
        nome = nome.group(1) if nome else 'funcao'
        
        # Gera teste
        teste = ia(f"Crie um teste simples para esta funcao Python:\n{funcao}\n\nRetorne APENAS codigo de teste (assert).")
        
        # Salva funcao
        path_func = os.path.join(OUT_DIR, f'{nome}.py')
        with open(path_func, 'w') as f:
            f.write(funcao + '\n')
        
        # Salva teste
        path_test = os.path.join(OUT_DIR, f'test_{nome}.py')
        with open(path_test, 'w') as f:
            f.write(f'from {nome} import *\n{teste}\nprint("Teste passou!")' if teste else f'from {nome} import *\nprint("Import OK")')
        
        print(f'  [OK] {path_func}')
        print(f'  [OK] {path_test}')
        
        # Executa teste
        r = subprocess.run([sys.executable, path_test], capture_output=True, text=True, timeout=10)
        print(f'  [TESTE] {"PASSOU" if r.returncode == 0 else "FALHOU"}: {r.stdout.strip()[:100] or r.stderr.strip()[:100]}')
        
        return path_func, path_test
    
    return None


# ============================================================
# 4. SISTEMA MULTI-ARQUIVO — Coordena geração completa
# ============================================================

def gerar_sistema(desc):
    """Gera um sistema completo: NPC + itens + quest + lore."""
    print(f'\n[SISTEMA COMPLETO] {desc[:60]}...')
    print(f'  Planejando estrutura...')
    
    # IA planeja o sistema
    plano = ia(f"""Planeje um sistema de quest para: {desc}

Responda EXATAMENTE:
SISTEMA: nome
NPCS: (nomes e papeis)
ITENS: (nomes e ids)
MONSTERS: (nomes e stats)
HISTORIA: (resumo da lore em 2 frases)""", 0.6)
    
    if not plano:
        print('[ERRO] Falha no planejamento')
        return
    
    print(f'  Plano recebido!')
    for line in plano.split('\n')[:8]:
        if line.strip():
            print(f'    {line.strip()[:100]}')
    
    # Salva o plano
    path = os.path.join(OUT_DIR, f'sistema_{desc[:10].replace(" ","_")}.txt')
    with open(path, 'w') as f:
        f.write(f'# Sistema: {desc}\n# Gerado pelo MCR-DevIA\n{plano}')
    print(f'  [OK] Plano salvo em {path}')
    
    return path


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('MCR-DevIA IMPROVEMENTS')
        print()
        print('Comandos:')
        print(f'  {sys.argv[0]} --runtime <arquivo.py>     Corrige erro de runtime')
        print(f'  {sys.argv[0]} --cpp "descricao"          Gera C++ .hpp + .cpp')
        print(f'  {sys.argv[0]} --testes "descricao"        Gera codigo + testes')
        print(f'  {sys.argv[0]} --sistema "descricao"       Gera sistema completo')
        print(f'  {sys.argv[0]} --tudo "descricao"          Tudo em um comando')
        sys.exit(1)
    
    cmd = sys.argv[1]
    args = ' '.join(sys.argv[2:])
    
    if cmd == '--runtime':
        corrigir_runtime(args)
    
    elif cmd == '--cpp':
        gerar_cpp(args)
    
    elif cmd == '--testes':
        gerar_com_testes(args, 'python')
    
    elif cmd == '--sistema':
        gerar_sistema(args)
    
    elif cmd == '--tudo':
        desc = args
        print(f'\n{"="*60}')
        print(f'  MODO COMPLETO: {desc}')
        print(f'{"="*60}')
        gerar_sistema(desc)
        gerar_cpp(desc)
        gerar_com_testes(desc, 'python')
    
    else:
        print(f'Comando invalido: {cmd}')
