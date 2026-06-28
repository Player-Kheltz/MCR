"""Testa o jogo tkinter diretamente."""
import sys, io
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.tool_orchestrator import ToolOrchestrator

tools = ToolOrchestrator()
BASE = 'E:/Projeto MCR/sandbox/jogo_python_tkinter/src'

modulos = ['main', 'entidades', 'fases', 'utils']
print("=== Validando modulos ===\n")
for mod in modulos:
    path = f'{BASE}/{mod}.py'
    with open(path, 'rb') as f:
        raw = f.read()
    # Tenta decodificar
    try:
        texto = raw.decode('utf-8')
    except:
        texto = raw.decode('latin-1')
    
    r = tools.executar('validar_codigo', {'codigo': texto})
    res = r.get('resultado', {})
    status = 'OK' if res.get('valido') else 'FAIL'
    print(f'  [{status}] {mod}.py ({len(texto)} chars) lingua={res.get("linguagem","?")}')

# Tenta compilar
print("\n=== Compilando ===\n")
for mod in modulos:
    path = f'{BASE}/{mod}.py'
    with open(path, 'rb') as f:
        raw = f.read()
    try:
        texto = raw.decode('utf-8')
        compile(texto, f'{mod}.py', 'exec')
        print(f'  [OK] {mod}.py compila')
    except SyntaxError as e:
        print(f'  [FAIL] {mod}.py: {e}')
        # Mostra a linha do erro
        linhas = texto.split('\n')
        if e.lineno and e.lineno <= len(linhas):
            print(f'    Linha {e.lineno}: {linhas[e.lineno-1][:80]}')

print("\n=== Para jogar ===")
print("  cd sandbox\\jogo_python_tkinter")
print("  python src\\main.py")
