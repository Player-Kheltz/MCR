"""Teste do Validador Universal (_cmd_validar_codigo)."""
import sys, json
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.tool_orchestrator import ToolOrchestrator

tools = ToolOrchestrator()
print("=== Teste Validador Universal ===\n")

testes = [
    ("1. Python valido", 'x = 1; print(x)', True),
    ("2. Python invalido", 'x = ', False),
    ("3. JavaScript", 'const x = 1; console.log(x);', True),  # fallback sem node
    ("4. JSON valido", '{"nome": "Joao", "idade": 30}', True),
    ("5. JSON invalido", '{nome: Joao}', False),
    ("6. HTML", '<html><body>Oi</body></html>', True),
    ("7. Lua", 'local x = 1; print(x)', True),
    ("8. Rust (sem validador)", 'fn main() { println!("hi"); }', True),  # ignorado
    ("9. Codigo vazio", '', False),
    ("10. Markdown + Python", 'Explicacao\n```python\nprint("puro")\n```', True),
]

for nome, codigo, esperado in testes:
    r = tools.executar('validar_codigo', {'codigo': codigo})
    valido = r.get('sucesso') and r.get('resultado', {}).get('valido', False)
    linguagem = r.get('resultado', {}).get('linguagem', '?')
    aviso = r.get('resultado', {}).get('aviso', '')
    status = 'OK' if valido == esperado else 'FAIL'
    aviso_str = f' ({aviso})' if aviso else ''
    print(f"  [{status}] {nome:25s} -> valido={valido} (esperado={esperado}) lingua={linguagem}{aviso_str}")

print("\n=== FIM ===")
