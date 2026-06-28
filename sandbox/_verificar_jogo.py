"""Verifica se o jogo gerado e valido."""
import sys
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.tool_orchestrator import ToolOrchestrator
from modulos.util import extrair_codigo_puro

tools = ToolOrchestrator()
BASE = 'E:/Projeto MCR/sandbox/jogo_python_tkinter/src'

modulos = ['main', 'entidades', 'fases', 'utils']
print("=== Validando modulos do jogo ===\n")
for mod in modulos:
    path = f'{BASE}/{mod}.py'
    with open(path) as f:
        codigo = f.read()
    r = tools.executar('validar_codigo', {'codigo': codigo})
    res = r.get('resultado', {})
    status = 'OK' if res.get('valido') else 'FAIL'
    print(f'  [{status}] {mod}.py ({len(codigo)} chars) lingua={res.get("linguagem","?")}')

# Testa se o codigo importa sem erros
print("\n=== Testando imports ===\n")
for mod in ['entidades', 'fases', 'utils']:
    path = f'{BASE}/{mod}.py'
    with open(path) as f:
        codigo = f.read()
    codigo_puro = extrair_codigo_puro(codigo)
    try:
        compile(codigo_puro, f'{mod}.py', 'exec')
        print(f'  [OK] {mod}.py compila sem erros')
    except SyntaxError as e:
        print(f'  [FAIL] {mod}.py: {e}')

# Mostra estrutura completa
import os
print("\n=== Estrutura do projeto ===\n")
for root, dirs, files in os.walk('E:/Projeto MCR/sandbox/jogo_pygame'):
    nivel = root.replace('E:/Projeto MCR/sandbox/jogo_pygame', '').count(os.sep)
    print(f"{'  ' * nivel}{os.path.basename(root)}/")
    for fname in sorted(files):
        fp = os.path.join(root, fname)
        print(f"{'  ' * (nivel+1)}{fname} ({os.path.getsize(fp)} bytes)")

print("\n=== Para jogar ===")
print("  cd sandbox\\jogo_pygame")
print("  pip install -r requirements.txt")
print("  python src/main.py")
