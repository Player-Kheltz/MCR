"""Teste dos validadores atualizados."""
import sys, json
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.tool_orchestrator import ToolOrchestrator

tools = ToolOrchestrator()
print("=== Teste Validadores 3 Niveis ===\n")

testes = [
    # Já existentes (devem continuar funcionando)
    ("Python valido", 'x = 1; print(x)', True),
    ("Python invalido", 'x = ', False),
    ("JavaScript", 'const x = 1; console.log(x);', True),
    ("JSON valido", '{"nome": "Joao"}', True),
    ("JSON invalido", '{nome: Joao}', False),
    ("HTML com tags", '<html><body>Oi</body></html>', True),
    
    # NOVOS: linguagens sem checker especifico (devem passar com FAST)
    ("Bash valido", '#!/bin/bash\necho "hello world"', True),
    ("Bash aspas aberta", '#!/bin/bash\necho "hello', False),  # FAST deve detectar
    ("Makefile", 'target:\n\techo ok', True),
    ("Java classe", 'public class Test { public static void main(String[] args) {} }', True),
    
    # Codigos problematicos
    ("Codigo vazio", '', False),
    ("HTML tag unica", '<div>conteudo</div>', True),  # sem <html>, deve passar agora
]

for nome, codigo, esperado in testes:
    r = tools.executar('validar_codigo', {'codigo': codigo})
    valido = r.get('resultado', {}).get('valido', False)
    metodo = r.get('resultado', {}).get('metodo', '?')
    lingua = r.get('resultado', {}).get('linguagem', '?')
    status = 'OK' if valido == esperado else 'FAIL'
    print(f"  [{status}] {nome:25s} -> valido={valido} (esp={esperado}) lingua={lingua} metodo={metodo}")

print("\n=== FIM ===")
