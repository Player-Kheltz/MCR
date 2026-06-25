"""Final polish: fix markup in generated files + runtime loop"""
import os, re, subprocess, sys

OUT_DIR = r'E:\Projeto MCR\sandbox\autogerados'

def limpar_markup(codigo):
    """Remove ```python, ```cpp, ``` etc markup do codigo."""
    codigo = re.sub(r'```\w*\n?', '', codigo)
    codigo = re.sub(r'```\n?', '', codigo)
    return codigo.strip()

def corrigir_arquivos():
    """Corrige markup em TODOS os arquivos gerados."""
    print('[FINALIZANDO] Corrigindo markup nos arquivos gerados...')
    contagem = 0
    for f in os.listdir(OUT_DIR):
        if not f.endswith(('.py', '.cpp', '.hpp')):
            continue
        path = os.path.join(OUT_DIR, f)
        with open(path, 'r', encoding='utf-8') as fp:
            conteudo = fp.read()
        if '```' in conteudo:
            conteudo = limpar_markup(conteudo)
            with open(path, 'w', encoding='utf-8') as fp:
                fp.write(conteudo)
            contagem += 1
            print(f'  [CORRIGIDO] {f}')
    
    if contagem == 0:
        print('  Nenhum markup encontrado.')
    else:
        print(f'  {contagem} arquivos corrigidos')

def testar_scripts():
    """Tenta executar todos os scripts .py e ve quais passam."""
    print('\n[TESTANDO] Executando scripts...')
    passaram = 0
    falharam = 0
    for f in sorted(os.listdir(OUT_DIR)):
        if not f.endswith('.py') or f.startswith('test_'):
            continue
        path = os.path.join(OUT_DIR, f)
        try:
            r = subprocess.run([sys.executable, path],
                             capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                print(f'  [OK] {f}: {r.stdout.strip()[:80]}')
                passaram += 1
            else:
                print(f'  [FALHA] {f}: {r.stderr.strip()[:80]}')
                falharam += 1
        except:
            print(f'  [ERRO] {f}: timeout ou erro')
            falharam += 1
    
    print(f'\n  Total: {passaram} passaram, {falharam} falharam')

def status_final():
    """Mostra status de todos os arquivos gerados."""
    print('\n[STATUS] Arquivos em autogerados/:')
    for f in sorted(os.listdir(OUT_DIR)):
        path = os.path.join(OUT_DIR, f)
        size = os.path.getsize(path)
        print(f'  {f} ({size} bytes)')
    print(f'  Total: {len(os.listdir(OUT_DIR))} arquivos')

if __name__ == '__main__':
    corrigir_arquivos()
    testar_scripts()
    status_final()
